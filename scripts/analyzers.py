import json
import logging
import subprocess
from typing import Any, Dict, List
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import Settings


def _run_tool(cmd: List[str]) -> subprocess.CompletedProcess:

    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def run_static_analyzers(files: List[str], settings: Settings) -> Dict[str, Any]:

    results: Dict[str, Any] = {
        "flake8": {},
        "pylint": {},
        "bandit": {},
        "mypy": {},
        "black": {},
        "isort": {},
    }

    if not files:
        return results

    # flake8
    flake = _run_tool(["flake8", "--format=json", *files])
    if flake.stdout:
        try:
            results["flake8"] = json.loads(flake.stdout)
        except json.JSONDecodeError:
            results["flake8"] = {"raw": flake.stdout}

    # pylint
    pylint = _run_tool(["pylint", "-f", "json", *files])
    try:
        results["pylint"] = json.loads(pylint.stdout or "[]")
    except json.JSONDecodeError:
        results["pylint"] = {"raw": pylint.stdout}

    # bandit
    bandit = _run_tool(["bandit", "-f", "json", "-q", "-r", *files])
    try:
        results["bandit"] = json.loads(bandit.stdout or "{}")
    except json.JSONDecodeError:
        results["bandit"] = {"raw": bandit.stdout}

    # mypy
    mypy = _run_tool(["mypy", "--no-error-summary", "--hide-error-context", "--pretty", *files])
    results["mypy"] = {"stdout": mypy.stdout, "stderr": mypy.stderr, "code": mypy.returncode}

    # black (check)
    black = _run_tool(["black", "--check", "--diff", *files])
    results["black"] = {"stdout": black.stdout, "stderr": black.stderr, "code": black.returncode}

    # isort (check)
    isort = _run_tool(["isort", "--check-only", "--diff", *files])
    results["isort"] = {"stdout": isort.stdout, "stderr": isort.stderr, "code": isort.returncode}

    return results


def _get_diffs(files: List[str]) -> Dict[str, str]:

    diffs: Dict[str, str] = {}
    for path in files:
        proc = subprocess.run(["git", "diff", "-U3", "HEAD^", "--", path], capture_output=True, text=True, check=False)
        diffs[path] = proc.stdout
    return diffs


def run_llm_review(files: List[str], settings: Settings) -> Dict[str, Any]:

    if not files or not settings.gemini_api_key:
        return {"findings": [], "summary": "LLM disabled or no files."}

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.prompts import ChatPromptTemplate
    except Exception as exc:  # noqa: BLE001
        logging.warning("LLM libraries not available: %s", exc)
        return {"findings": [], "summary": "LLM libraries missing."}

    diffs = _get_diffs(files)

    system_prompt = (
        "You are an experienced code reviewer. Analyze the provided unified diffs and"
        " return JSON with issues. For each issue provide: severity (high|medium|low),"
        " file, line (best guess), title, and recommendation."
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "Repository: {repo}, PR: {pr}\nDiffs JSON: {diffs}"),
        ]
    )

    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", api_key=settings.gemini_api_key, temperature=0)
    chain = prompt | llm
    response = chain.invoke({"repo": settings.repository, "pr": settings.pr_number, "diffs": json.dumps(diffs)})

    text = getattr(response, "content", "") or str(response)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = {"raw": text}
    return data


