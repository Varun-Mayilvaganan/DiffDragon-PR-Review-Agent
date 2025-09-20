import logging
from typing import Any, Dict, List
import os
import sys
from github import Github
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import Settings


def _compose_body(lint_results: Dict[str, Any], ai_review: Dict[str, Any]) -> str:
    """Compose the review body with AI findings and static analysis results."""
    lines: List[str] = []
    lines.append("## 🤖 AI PR Review Report")
    
    if ai_review:
        lines.append("\n### AI Findings")
        findings = ai_review.get("findings") or ai_review.get("issues") or []
        if isinstance(findings, list) and findings:
            for item in findings:
                sev = str(item.get("severity", "info")).upper()
                file = item.get("file", "unknown")
                line = item.get("line", "?")
                title = item.get("title") or item.get("message", "Issue")
                rec = item.get("recommendation") or item.get("suggestion") or ""
                lines.append(f"- [{sev}] {file}:{line} - {title}")
                if rec:
                    lines.append(f"  - {rec}")
        else:
            raw = ai_review.get("raw") or ai_review
            lines.append(f"```\n{raw}\n```")

    if lint_results:
        lines.append("\n### Static Analysis Summary")
        for tool, result in lint_results.items():
            if not result:
                continue
            preview = str(result)
            if len(preview) > 800:
                preview = preview[:800] + "..."
            lines.append(f"- {tool}:\n```\n{preview}\n```")
    
    return "\n".join(lines)


def _label_for_severity(sev: str) -> str:
    """Convert severity level to GitHub label name."""
    sev_lower = sev.lower()
    if sev_lower == "high":
        return "severity: high"
    if sev_lower == "medium":
        return "severity: medium"
    if sev_lower == "low":
        return "severity: low"
    return "severity: info"


def publish_review(
    changed_files: List[str],
    lint_results: Dict[str, Any],
    ai_review: Dict[str, Any],
    settings: Settings,
) -> None:
    """Publish the review to GitHub as a PR review or comment with labels."""
    if not settings.github_token:
        logging.warning("GITHUB_TOKEN missing; skipping posting review")
        return

    gh = Github(settings.github_token)
    repo = gh.get_repo(settings.repository)
    pr = repo.get_pull(settings.pr_number)

    body = _compose_body(lint_results, ai_review)

    if settings.post_as_pr_review:
        # Post as PR review
        event = "REQUEST_CHANGES" if settings.request_changes_on_high else "COMMENT"
        pr.create_review(body=body, event=event)
    else:
        pr.create_issue_comment(body)

    # Add labels based on severity
    if settings.add_labels_based_on_severity:
        labels_to_add: List[str] = []
        findings = ai_review.get("findings") if isinstance(ai_review, dict) else []
        if isinstance(findings, list):
            severities = {str(item.get("severity", "info")).lower() for item in findings}
            for sev in severities:
                labels_to_add.append(_label_for_severity(sev))
        
        if labels_to_add:
            existing = {lbl.name for lbl in pr.get_labels()}
            for name in labels_to_add:
                if name not in existing:
                    try:
                        repo.create_label(name=name, color="ededed")
                    except Exception:  # noqa: BLE001
                        pass
            pr.add_to_labels(*labels_to_add)
