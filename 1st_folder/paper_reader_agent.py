"""1st-folder style entry point for the minimal paper-reading mission.

This keeps the assignment-friendly command while reusing the package code:

    python paper_reader_agent.py "LLM agents for scientific discovery"
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from paperagent.config import load_dotenv  # noqa: E402
from paperagent.workflow import run_pipeline  # noqa: E402


def main() -> None:
    load_dotenv(Path(".env"))
    load_dotenv(PROJECT_ROOT / ".env")

    topic = " ".join(sys.argv[1:]).strip()
    if not topic:
        topic = input("Research topic: ").strip()
    if not topic:
        raise SystemExit("Research topic is required.")

    max_papers = int(os.getenv("ARXIV_MAX_RESULTS", "3"))
    output_dir = os.getenv("OUTPUT_DIR", str(PROJECT_ROOT / "outputs"))
    try:
        result = run_pipeline(
            topic=topic,
            max_papers=max_papers,
            output_dir=output_dir,
            enable_prototype=False,
            enable_review=True,
            enable_extra_reviewers=False,
            enable_report=False,
        )
    except RuntimeError as exc:
        raise SystemExit(f"\nError: {exc}") from exc

    print("\nDone.")
    print(f"Paper summaries: {result.paper_summaries_path}")
    print(f"Reviewer feedback: {result.reviewer_feedback_path}")
    print(f"Final review: {result.final_review_path}")


if __name__ == "__main__":
    main()
