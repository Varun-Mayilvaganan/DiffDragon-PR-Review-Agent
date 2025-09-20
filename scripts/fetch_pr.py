import logging
import subprocess
from typing import List

from config import Settings


def _run(cmd: List[str]) -> str:
    """Run a command and return stdout, raise on error."""
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\nError: {result.stderr}")
    return result.stdout


def _filter_files(files: List[str], settings: Settings) -> List[str]:
    """Filter files based on include/exclude patterns."""
    filtered = []
    for path in files:
        # Skip excluded patterns
        if any(pattern and pattern in path for pattern in settings.exclude_patterns):
            logging.debug(f"Excluding {path} due to exclude patterns")
            continue
            
        # Check if file exists and is readable
        try:
            with open(path, 'r', encoding='utf-8'):
                pass
        except (FileNotFoundError, PermissionError, UnicodeDecodeError):
            logging.debug(f"Skipping {path} - file not readable")
            continue
            
        # Include only specified extensions (if any)
        if settings.include_extensions and not any(path.endswith(ext) for ext in settings.include_extensions):
            logging.debug(f"Excluding {path} due to extension filter")
            continue
            
        filtered.append(path)
        
    # Limit number of files
    limited = filtered[:settings.max_files_to_review]
    if len(limited) < len(filtered):
        logging.info(f"Limited to {len(limited)} files (max: {settings.max_files_to_review})")
    
    return limited


def get_changed_files(settings: Settings) -> List[str]:
    """Get list of changed files for the PR."""
    logging.info(f"Fetching changed files for PR #{settings.pr_number}")
    
    try:
        if settings.base_sha and settings.head_sha:
            diff_range = f"{settings.base_sha}...{settings.head_sha}"
            logging.info(f"Using SHA range: {diff_range}")
        else:
            diff_range = "HEAD^...HEAD"
            logging.info(f"Using default range: {diff_range}")

        output = _run(["git", "diff", "--name-only", diff_range])
        files = [line.strip() for line in output.splitlines() if line.strip()]
        
        logging.info(f"Found {len(files)} changed files")
        
        filtered_files = _filter_files(files, settings)
        logging.info(f"{len(filtered_files)} files after filtering")
        
        return filtered_files
        
    except Exception as e:
        logging.error(f"Failed to get changed files: {e}")
        # Fallback: try to get any Python files in current directory
        try:
            import os
            fallback_files = []
            for root, dirs, files in os.walk('.'):
                # Skip hidden directories and common build directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'dist', 'build']]
                for file in files:
                    if file.endswith(('.py', '.js', '.jsx', '.ts', '.tsx')):
                        fallback_files.append(os.path.join(root, file).replace('./', ''))
            
            limited_files = fallback_files[:10]  # Limit to 10 files as fallback
            logging.info(f"Using fallback: found {len(limited_files)} files")
            return limited_files
        except Exception as fallback_error:
            logging.error(f"Fallback also failed: {fallback_error}")
            return []