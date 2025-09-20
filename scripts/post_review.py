import logging
from typing import Any, Dict, List

from github import Github
from github.GithubException import GithubException

from config import Settings


def _compose_body(lint_results: Dict[str, Any], ai_review: Dict[str, Any], changed_files: List[str]) -> str:
    """Compose the review body with AI findings and static analysis results."""
    lines: List[str] = []
    lines.append("## 🤖 AI PR Review Report")
    
    if changed_files:
        lines.append(f"\n**Files reviewed:** {len(changed_files)}")
        lines.append("- " + "\n- ".join(changed_files[:10]))  # Show first 10 files
        if len(changed_files) > 10:
            lines.append(f"- ... and {len(changed_files) - 10} more files")
    
    # AI Review Section
    if ai_review and ai_review.get("findings"):
        lines.append("\n### 🧠 AI Analysis")
        findings = ai_review.get("findings", [])
        
        if isinstance(findings, list) and findings:
            severity_counts = {"high": 0, "medium": 0, "low": 0, "info": 0}
            
            for item in findings:
                sev = str(item.get("severity", "info")).lower()
                severity_counts[sev] = severity_counts.get(sev, 0) + 1
                
                file_path = item.get("file", "unknown")
                line_info = item.get("line", "?")
                title = item.get("title") or item.get("message", "Issue")
                recommendation = item.get("recommendation") or item.get("suggestion", "")
                
                # Format severity with emoji
                sev_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢", "info": "ℹ️"}.get(sev, "ℹ️")
                
                lines.append(f"\n**{sev_emoji} {sev.upper()}**: `{file_path}:{line_info}`")
                lines.append(f"**Issue**: {title}")
                if recommendation:
                    lines.append(f"**Recommendation**: {recommendation}")
            
            # Summary
            summary_parts = []
            for sev, count in severity_counts.items():
                if count > 0:
                    summary_parts.append(f"{count} {sev}")
            
            if summary_parts:
                lines.insert(-len(findings)*4, f"\n**Summary**: Found {', '.join(summary_parts)} issues")
        
        # Add AI summary if available
        if ai_review.get("summary"):
            lines.append(f"\n**AI Summary**: {ai_review['summary']}")
    
    elif ai_review:
        lines.append("\n### 🧠 AI Analysis")
        if ai_review.get("summary"):
            lines.append(f"{ai_review['summary']}")
        else:
            lines.append("AI review completed but no structured findings available.")

    # Static Analysis Section
    if lint_results:
        lines.append("\n### 🔍 Static Analysis")
        
        for tool, result in lint_results.items():
            if not result or (isinstance(result, dict) and result.get("error")):
                continue
                
            lines.append(f"\n**{tool.upper()}**:")
            
            if tool == "flake8":
                if isinstance(result, list) and result:
                    lines.append(f"- Found {len(result)} issues")
                    for issue in result[:5]:  # Show first 5 issues
                        if isinstance(issue, dict):
                            file_name = issue.get('file', '').replace('./', '')
                            line_num = issue.get('line', '?')
                            message = issue.get('message', 'Issue')
                            lines.append(f"  - `{file_name}:{line_num}` - {message}")
                        else:
                            lines.append(f"  - {str(issue)}")
                    if len(result) > 5:
                        lines.append(f"  - ... and {len(result) - 5} more issues")
                elif isinstance(result, dict) and result.get("raw"):
                    lines.append(f"- Issues found:\n```\n{result['raw'][:300]}...\n```")
                elif isinstance(result, dict) and result.get("error"):
                    lines.append(f"- ⚠️ Tool failed: {result['error']}")
                else:
                    lines.append("- ✅ No issues found")
            
            elif tool == "pylint":
                if isinstance(result, list) and result:
                    lines.append(f"- Found {len(result)} issues")
                    for issue in result[:5]:
                        if isinstance(issue, dict):
                            file_name = issue.get('path', '').replace('./', '')
                            line_num = issue.get('line', '?')
                            message = issue.get('message', 'Issue')
                            issue_type = issue.get('type', 'unknown')
                            lines.append(f"  - `{file_name}:{line_num}` - {message} ({issue_type})")
                        else:
                            lines.append(f"  - {str(issue)}")
                    if len(result) > 5:
                        lines.append(f"  - ... and {len(result) - 5} more issues")
                elif isinstance(result, dict) and result.get("raw"):
                    lines.append(f"- Issues found:\n```\n{result['raw'][:300]}...\n```")
                elif isinstance(result, dict) and result.get("error"):
                    lines.append(f"- ⚠️ Tool failed: {result['error']}")
                else:
                    lines.append("- ✅ No issues found")
            
            elif tool in ["black", "isort", "mypy"]:
                if result.get("code", 0) == 0:
                    lines.append("- ✅ No issues found")
                else:
                    if result.get("stdout"):
                        preview = result["stdout"][:200]
                        if len(result["stdout"]) > 200:
                            preview += "..."
                        lines.append(f"- Issues found:\n```\n{preview}\n```")
                    else:
                        lines.append("- Issues found (see details in artifacts)")
            
            elif tool == "bandit":
                if isinstance(result, dict) and result.get("results"):
                    issues = result["results"]
                    if isinstance(issues, list) and issues:
                        lines.append(f"- Found {len(issues)} security issues")
                        for issue in issues[:2]:  # Show first 2
                            if isinstance(issue, dict):
                                lines.append(f"  - {issue.get('test_name', 'Security issue')}: {issue.get('issue_text', '')}")
                            else:
                                lines.append(f"  - {str(issue)}")
                        if len(issues) > 2:
                            lines.append(f"  - ... and {len(issues) - 2} more issues")
                    else:
                        lines.append("- ✅ No security issues found")
                elif isinstance(result, dict) and result.get("raw"):
                    lines.append(f"- Issues found:\n```\n{result['raw'][:200]}...\n```")
                else:
                    lines.append("- ✅ No security issues found")

    if not ai_review and not any(lint_results.values()):
        lines.append("\n*No issues found or analysis tools were not run.*")

    lines.append("\n---")
    lines.append("*This review was automatically generated by AI. Please review the suggestions carefully.*")
    
    return "\n".join(lines)


def _label_for_severity(sev: str) -> str:
    """Convert severity level to GitHub label name."""
    sev_lower = sev.lower()
    mapping = {
        "high": "severity: high",
        "medium": "severity: medium", 
        "low": "severity: low",
        "info": "severity: info"
    }
    return mapping.get(sev_lower, "severity: info")


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

    if not settings.repository or not settings.pr_number:
        logging.warning("Missing repository or PR number; skipping posting review")
        return

    try:
        gh = Github(settings.github_token)
        repo = gh.get_repo(settings.repository)
        pr = repo.get_pull(settings.pr_number)

        body = _compose_body(lint_results, ai_review, changed_files)
        
        # Determine if we should request changes
        has_high_severity = False
        if isinstance(ai_review, dict) and ai_review.get("findings"):
            findings = ai_review["findings"]
            if isinstance(findings, list):
                has_high_severity = any(
                    str(item.get("severity", "")).lower() == "high" 
                    for item in findings
                )

        if settings.post_as_pr_review:
            # Post as PR review
            event = "REQUEST_CHANGES" if (settings.request_changes_on_high and has_high_severity) else "COMMENT"
            pr.create_review(body=body, event=event)
            logging.info(f"Posted PR review with event: {event}")
        else:
            # Post as regular comment
            pr.create_issue_comment(body)
            logging.info("Posted PR comment")

        # Add labels based on severity
        if settings.add_labels_based_on_severity and isinstance(ai_review, dict):
            labels_to_add: List[str] = []
            findings = ai_review.get("findings", [])
            
            if isinstance(findings, list):
                severities = {str(item.get("severity", "info")).lower() for item in findings if item.get("severity")}
                for sev in severities:
                    label_name = _label_for_severity(sev)
                    labels_to_add.append(label_name)
            
            if labels_to_add:
                try:
                    # Get existing labels on the PR
                    existing_labels = {lbl.name for lbl in pr.get_labels()}
                    
                    # Create labels if they don't exist in the repo
                    for label_name in labels_to_add:
                        if label_name not in existing_labels:
                            try:
                                # Try to get the label first
                                repo.get_label(label_name)
                            except GithubException:
                                # Label doesn't exist, create it
                                color_map = {
                                    "severity: high": "d73a49",
                                    "severity: medium": "fbca04", 
                                    "severity: low": "28a745",
                                    "severity: info": "0366d6"
                                }
                                color = color_map.get(label_name, "ededed")
                                try:
                                    repo.create_label(name=label_name, color=color, description=f"AI-generated {label_name}")
                                    logging.info(f"Created label: {label_name}")
                                except GithubException as e:
                                    logging.warning(f"Failed to create label {label_name}: {e}")
                    
                    # Add labels to PR
                    new_labels = [lbl for lbl in labels_to_add if lbl not in existing_labels]
                    if new_labels:
                        pr.add_to_labels(*new_labels)
                        logging.info(f"Added labels: {', '.join(new_labels)}")
                        
                except GithubException as e:
                    logging.warning(f"Failed to manage labels: {e}")

    except GithubException as e:
        logging.error(f"GitHub API error: {e}")
        raise
    except Exception as e:
        logging.error(f"Failed to post review: {e}")
        raise