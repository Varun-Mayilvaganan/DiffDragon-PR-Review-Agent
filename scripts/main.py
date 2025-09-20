#!/usr/bin/env python3
"""
AI PR Review Agent - Main entry point
"""

import json
import logging
import sys
from typing import Any, Dict

from config import Settings


def configure_logging(level: str) -> None:
    """Configure logging with the specified level."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def save_artifact(filename: str, data: Any) -> None:
    """Save data to a JSON file."""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logging.info(f"Saved artifact: {filename}")
    except Exception as e:
        logging.error(f"Failed to save artifact {filename}: {e}")


def main() -> int:
    """Main entry point for the AI PR Review Agent."""
    try:
        settings = Settings()
        configure_logging(settings.log_level)
        
        logging.info("🤖 Starting AI PR Review Agent")
        logging.info(f"Repository: {settings.repository}")
        logging.info(f"PR Number: {settings.pr_number}")
        logging.info(f"LLM Review: {'enabled' if settings.enable_llm_review else 'disabled'}")
        logging.info(f"Static Analysis: {'enabled' if settings.enable_static_analysis else 'disabled'}")

        # Validate required settings
        if not settings.repository or not settings.pr_number:
            logging.error("Missing repository or PR number from environment")
            return 2

        # Import modules (lazy loading for faster startup)
        from scripts import fetch_pr, analyzers, post_review

        # Get changed files
        try:
            changed_files = fetch_pr.get_changed_files(settings)
            if not changed_files:
                logging.warning("No files to review")
                return 0
        except Exception as exc:
            logging.exception(f"Failed to discover changed files: {exc}")
            return 3

        # Initialize results
        lint_results: Dict[str, Any] = {}
        ai_review: Dict[str, Any] = {}

        # Run static analysis
        if settings.enable_static_analysis:
            try:
                logging.info("🔍 Running static analysis...")
                lint_results = analyzers.run_static_analyzers(changed_files, settings)
                save_artifact("lint-results.json", lint_results)
                
                # Count issues found
                issue_count = 0
                for tool, result in lint_results.items():
                    if isinstance(result, list):
                        issue_count += len(result)
                    elif isinstance(result, dict) and result.get("results"):
                        issue_count += len(result["results"])
                
                logging.info(f"Static analysis complete. Found {issue_count} potential issues.")
                
            except Exception as exc:
                logging.exception(f"Static analysis failed: {exc}")
                lint_results = {"error": str(exc)}

        # Run LLM review
        if settings.enable_llm_review:
            if not settings.gemini_api_key:
                logging.warning("GEMINI_API_KEY not provided, skipping LLM review")
                ai_review = {"findings": [], "summary": "LLM review skipped - no API key"}
            else:
                try:
                    logging.info("🧠 Running AI review...")
                    ai_review = analyzers.run_llm_review(changed_files, settings)
                    save_artifact("review-results.json", ai_review)
                    
                    findings_count = len(ai_review.get("findings", []))
                    logging.info(f"AI review complete. Found {findings_count} findings.")
                    
                except Exception as exc:
                    logging.exception(f"AI review failed: {exc}")
                    ai_review = {"findings": [], "summary": f"AI review failed: {exc}"}

        # Post review to GitHub
        try:
            logging.info("📝 Posting review to GitHub...")
            post_review.publish_review(
                changed_files=changed_files,
                lint_results=lint_results,
                ai_review=ai_review,
                settings=settings,
            )
            logging.info("✅ Review posted successfully")
            
        except Exception as exc:
            logging.exception(f"Failed to post review: {exc}")
            return 4

        logging.info("🎉 AI PR Review Agent completed successfully")
        return 0

    except KeyboardInterrupt:
        logging.info("🛑 Interrupted by user")
        return 130
    except Exception as exc:
        logging.exception(f"💥 Unexpected error: {exc}")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logging.info("🛑 Interrupted by user")
        sys.exit(130)
    except Exception as exc:
        logging.exception(f"💥 Unexpected top-level error: {exc}")
        sys.exit(1)
