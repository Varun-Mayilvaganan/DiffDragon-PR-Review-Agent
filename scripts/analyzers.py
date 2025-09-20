import json
import logging
import subprocess
from typing import Any, Dict, List

from config import Settings


def _run_tool(cmd: List[str]) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def run_static_analyzers(files: List[str], settings: Settings) -> Dict[str, Any]:
    """Run static analysis tools on the provided files."""
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

    # Only analyze Python files for Python tools
    python_files = [f for f in files if f.endswith('.py')]
    
    if not python_files:
        logging.info("No Python files to analyze")
        return results

    # flake8
    try:
        flake = _run_tool(["flake8", "--format=json", *python_files])
        if flake.stdout:
            try:
                results["flake8"] = json.loads(flake.stdout)
            except json.JSONDecodeError:
                results["flake8"] = {"raw": flake.stdout}
    except Exception as e:
        logging.warning(f"Flake8 failed: {e}")
        results["flake8"] = {"error": str(e)}

    # pylint
    try:
        pylint = _run_tool(["pylint", "-f", "json", *python_files])
        try:
            results["pylint"] = json.loads(pylint.stdout or "[]")
        except json.JSONDecodeError:
            results["pylint"] = {"raw": pylint.stdout}
    except Exception as e:
        logging.warning(f"Pylint failed: {e}")
        results["pylint"] = {"error": str(e)}

    # bandit
    try:
        bandit = _run_tool(["bandit", "-f", "json", "-q", "-r"] + python_files)
        try:
            results["bandit"] = json.loads(bandit.stdout or "{}")
        except json.JSONDecodeError:
            results["bandit"] = {"raw": bandit.stdout}
    except Exception as e:
        logging.warning(f"Bandit failed: {e}")
        results["bandit"] = {"error": str(e)}

    # mypy
    try:
        mypy = _run_tool(["mypy", "--no-error-summary", "--hide-error-context", "--pretty"] + python_files)
        results["mypy"] = {"stdout": mypy.stdout, "stderr": mypy.stderr, "code": mypy.returncode}
    except Exception as e:
        logging.warning(f"MyPy failed: {e}")
        results["mypy"] = {"error": str(e)}

    # black (check)
    try:
        black = _run_tool(["black", "--check", "--diff"] + python_files)
        results["black"] = {"stdout": black.stdout, "stderr": black.stderr, "code": black.returncode}
    except Exception as e:
        logging.warning(f"Black failed: {e}")
        results["black"] = {"error": str(e)}

    # isort (check)
    try:
        isort = _run_tool(["isort", "--check-only", "--diff"] + python_files)
        results["isort"] = {"stdout": isort.stdout, "stderr": isort.stderr, "code": isort.returncode}
    except Exception as e:
        logging.warning(f"isort failed: {e}")
        results["isort"] = {"error": str(e)}

    return results


def _get_diffs(files: List[str]) -> Dict[str, str]:
    """Get git diffs for the specified files."""
    diffs: Dict[str, str] = {}
    for path in files:
        try:
            proc = subprocess.run(
                ["git", "diff", "-U3", "HEAD^", "--", path], 
                capture_output=True, 
                text=True, 
                check=False
            )
            diffs[path] = proc.stdout
        except Exception as e:
            logging.warning(f"Failed to get diff for {path}: {e}")
            diffs[path] = f"Error getting diff: {e}"
    return diffs


def run_llm_review(files: List[str], settings: Settings) -> Dict[str, Any]:
    """Run LLM-based code review using Gemini."""
    if not files or not settings.gemini_api_key:
        return {"findings": [], "summary": "LLM disabled or no files."}

    try:
        import google.generativeai as genai
    except ImportError:
        logging.warning("Google Generative AI library not available")
        return {"findings": [], "summary": "LLM libraries missing."}

    try:
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        diffs = _get_diffs(files)
        
        if not any(diffs.values()):
            return {"findings": [], "summary": "No diffs to review"}

        system_prompt = """You are an experienced code reviewer. Analyze the provided git diffs and identify potential issues.

Return your response as a JSON object with this exact structure:
{
  "findings": [
    {
      "severity": "high|medium|low|info",
      "file": "filename",
      "line": "line_number_or_range",
      "title": "Brief issue description",
      "recommendation": "Suggested fix or improvement"
    }
  ],
  "summary": "Overall summary of the review"
}

Focus on:
- Security vulnerabilities
- Performance issues
- Code quality problems
- Logic errors
- Best practice violations

Be concise but helpful in your recommendations."""

        user_prompt = f"""Repository: {settings.repository}
PR: #{settings.pr_number}

Diffs to review:
{json.dumps(diffs, indent=2)}"""

        response = model.generate_content(f"{system_prompt}\n\n{user_prompt}")
        
        try:
            # Clean up the response text
            text = response.text.strip()
            if text.startswith('```json'):
                text = text[7:]
            if text.endswith('```'):
                text = text[:-3]
            text = text.strip()
            
            data = json.loads(text)
            return data
        except json.JSONDecodeError:
            logging.warning("Failed to parse LLM response as JSON")
            return {"findings": [], "summary": f"Raw LLM response: {response.text}"}

    except Exception as e:
        logging.error(f"LLM review failed: {e}")
        return {"findings": [], "summary": f"LLM review failed: {e}"}