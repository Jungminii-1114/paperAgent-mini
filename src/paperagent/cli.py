"""Small CLI for the PaperAgent mini project."""

from __future__ import annotations

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description="PaperAgent mini literature-review workflow.")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run the paper-reading workflow")
    run_parser.add_argument("topic", help="Research topic to search on arXiv")
    run_parser.add_argument("--max-papers", "-n", type=int, default=None)
    run_parser.add_argument("--output-dir", default=None)
    run_parser.add_argument("--no-prototype", action="store_true")
    run_parser.add_argument("--no-review", action="store_true")
    run_parser.add_argument("--extra-reviewers", action="store_true")
    run_parser.add_argument("--no-report", action="store_true")

    args = parser.parse_args()
    if args.command != "run":
        parser.print_help()
        return

    from paperagent.workflow import run_pipeline

    try:
        result = run_pipeline(
            topic=args.topic,
            max_papers=args.max_papers,
            output_dir=args.output_dir,
            enable_prototype=not args.no_prototype,
            enable_review=not args.no_review,
            enable_extra_reviewers=args.extra_reviewers,
            enable_report=not args.no_report,
        )
    except RuntimeError as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print("\nDone.")
    print(f"Output dir: {result.output_dir}")
    print(f"Paper summaries: {result.paper_summaries_path}")
    print(f"Final review: {result.final_review_path}")
    if result.reviewer_feedback_path:
        print(f"Reviewer feedback: {result.reviewer_feedback_path}")
    if result.professor_report_path:
        print(f"Professor report: {result.professor_report_path}")
    if result.experiment_review_path:
        print(f"Experiment review: {result.experiment_review_path}")
    if result.novelty_review_path:
        print(f"Novelty review: {result.novelty_review_path}")
    if result.impact_review_path:
        print(f"Impact review: {result.impact_review_path}")
    if result.method_extraction_path:
        print(f"Method extraction: {result.method_extraction_path}")
    if result.implementation_plan_path:
        print(f"Implementation plan: {result.implementation_plan_path}")
    if result.prototype_path:
        print(f"Prototype: {result.prototype_path}")


if __name__ == "__main__":
    main()
