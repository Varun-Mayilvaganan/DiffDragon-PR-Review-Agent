import json
import logging
import os
import sys
from typing import Any, Dict, List
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from .config import Settings


def configure_logging(level: str) -> None:

    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
    )


def save_artifact(filename: str, data: Any) -> None:

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main() -> int:

    settings = Settings()
    configure_logging(settings.log_level)

    logging.info("Starting AI PR Review Agent")

    if not settings.repository or not settings.pr_number:
        logging.error("Missing repository or PR number from environment")
        return 2

    # Lazy imports to keep startup fast
    from . import fetch_pr
    from . import analyzers
    from . import post_review

    try:
        changed_files = fetch_pr.get_changed_files(settings)
    except Exception as exc:  # noqa: BLE001
        logging.exception("Failed to discover changed files: %s", exc)
        return 3

    lint_results: Dict[str, Any] = {}
    if settings.enable_static_analysis:
        try:
            lint_results = analyzers.run_static_analyzers(changed_files, settings)
            save_artifact("lint-results.json", lint_results)
        except Exception as exc:  # noqa: BLE001
            logging.exception("Static analysis failed: %s", exc)

    ai_review: Dict[str, Any] = {}
    if settings.enable_llm_review:
        try:
            ai_review = analyzers.run_llm_review(changed_files, settings)
            save_artifact("review-results.json", ai_review)
        except Exception as exc:  # noqa: BLE001
            logging.exception("AI review failed: %s", exc)

    try:
        post_review.publish_review(
            changed_files=changed_files,
            lint_results=lint_results,
            ai_review=ai_review,
            settings=settings,
        )
    except Exception as exc:  # noqa: BLE001
        logging.exception("Failed to post review: %s", exc)

    logging.info("AI PR Review Agent complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())


