import logging
import subprocess
from typing import List
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import Settings


def _run(cmd: List[str]) -> str:

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stderr}")
    return result.stdout


def _filter_files(files: List[str], settings: Settings) -> List[str]:

    filtered = []
    for path in files:
        if any(pattern and pattern in path for pattern in settings.exclude_patterns):
            continue
        if settings.include_extensions and not any(path.endswith(ext) for ext in settings.include_extensions):
            continue
        filtered.append(path)
    return filtered[: settings.max_files_to_review]


def get_changed_files(settings: Settings) -> List[str]:

    logging.info("Fetching changed files for PR #%s", settings.pr_number)
    if settings.base_sha and settings.head_sha:
        diff_range = f"{settings.base_sha}...{settings.head_sha}"
    else:
        diff_range = "HEAD^...HEAD"

    output = _run(["git", "diff", "--name-only", diff_range])
    files = [line.strip() for line in output.splitlines() if line.strip()]
    files = _filter_files(files, settings)
    logging.info("%d files after filtering", len(files))
    return files


