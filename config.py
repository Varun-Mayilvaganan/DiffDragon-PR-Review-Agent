import os
from dataclasses import dataclass, field
from typing import List

from dotenv import load_dotenv

load_dotenv()


def _split_csv(value: str, default: List[str]) -> List[str]:
    """Split comma-separated string into list."""
    if not value:
        return default.copy()  # Return a copy to avoid mutation
    return [item.strip() for item in value.split(",") if item.strip()]


def _get_include_extensions() -> List[str]:
    """Get include extensions from environment."""
    return _split_csv(
        os.getenv("INCLUDE_EXTENSIONS", ".py,.js,.jsx,.ts,.tsx"), 
        [".py", ".js", ".jsx", ".ts", ".tsx"]
    )


def _get_exclude_patterns() -> List[str]:
    """Get exclude patterns from environment."""
    return _split_csv(
        os.getenv("EXCLUDE_PATTERNS", "node_modules/,dist/,__pycache__/,.git/"), 
        ["node_modules/", "dist/", "__pycache__/", ".git/"]
    )


@dataclass(frozen=True)
class Settings:
    # Required - only these two are needed for basic usage
    github_token: str = os.getenv("GITHUB_TOKEN", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    
    # Auto-set by GitHub Actions (you don't need to set these)
    repository: str = os.getenv("GITHUB_REPOSITORY", "")
    pr_number: int = int(os.getenv("PR_NUMBER", "0") or 0)
    head_sha: str = os.getenv("GITHUB_SHA", "")
    base_sha: str = os.getenv("BASE_SHA", "")

    # Optional - all have sensible defaults
    max_files_to_review: int = int(os.getenv("MAX_FILES_TO_REVIEW", "50"))
    enable_llm_review: bool = os.getenv("ENABLE_LLM_REVIEW", "true").lower() == "true"
    enable_static_analysis: bool = os.getenv("ENABLE_STATIC_ANALYSIS", "true").lower() == "true"
    include_extensions: List[str] = field(default_factory=_get_include_extensions)
    exclude_patterns: List[str] = field(default_factory=_get_exclude_patterns)
    request_changes_on_high: bool = os.getenv("REQUEST_CHANGES_ON_HIGH_SEVERITY", "false").lower() == "true"
    add_labels_based_on_severity: bool = os.getenv("ADD_LABELS_BASED_ON_SEVERITY", "true").lower() == "true"
    post_as_pr_review: bool = os.getenv("POST_AS_PR_REVIEW", "true").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()