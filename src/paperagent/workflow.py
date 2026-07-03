"""PaperAgent workflow for arXiv search, review, synthesis, and prototype planning."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from paperagent.agents import (
    ExperimentReviewerAgent,
    ImpactReviewerAgent,
    MethodExtractionAgent,
    NoveltyReviewerAgent,
    PaperReaderAgent,
    PaperSummary,
    PostdocAgent,
    ProfessorAgent,
    PrototypePlannerAgent,
    PrototypeWriterAgent,
    ReviewerAgent,
    write_paper_summaries,
    write_reviewer_feedback,
)
from paperagent.arxiv_tool import read_arxiv_pdf, search_arxiv
from paperagent.config import get_settings


@dataclass(frozen=True)
class PipelineResult:
    topic: str
    output_dir: Path
    paper_count: int
    paper_summaries_path: Path
    final_review_path: Path
    reviewer_feedback_path: Path | None = None
    professor_report_path: Path | None = None
    experiment_review_path: Path | None = None
    novelty_review_path: Path | None = None
    impact_review_path: Path | None = None
    method_extraction_path: Path | None = None
    implementation_plan_path: Path | None = None
    prototype_path: Path | None = None
    prototype_readme_path: Path | None = None


def run_pipeline(
    topic: str,
    max_papers: int | None = None,
    output_dir: str | None = None,
    enable_prototype: bool = True,
    enable_review: bool = True,
    enable_extra_reviewers: bool = False,
    enable_report: bool = True,
) -> PipelineResult:
    settings = get_settings()
    max_papers = max_papers or settings.arxiv_max_results
    out_dir = Path(output_dir or settings.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    reader = PaperReaderAgent(topic=topic)
    reviewer = ReviewerAgent()
    postdoc = PostdocAgent()
    professor = ProfessorAgent()
    method_agent = MethodExtractionAgent()
    planner_agent = PrototypePlannerAgent()
    writer_agent = PrototypeWriterAgent()

    print(f"[1] Searching arXiv directly for: {topic}")
    papers = search_arxiv(topic, max_results=max_papers)

    summaries: list[PaperSummary] = []
    reviewer_feedbacks: list[tuple[PaperSummary, str]] = []

    for index, paper in enumerate(papers, start=1):
        print(f"[2] Reading paper {index}/{len(papers)}: {paper.title}")
        full_text = read_arxiv_pdf(paper, out_dir)

        print(f"[3] PaperReaderAgent summarizing paper {index}/{len(papers)}")
        summary = reader.summarize_paper(paper, full_text)
        summaries.append(summary)

        if enable_review:
            print(f"[4] ReviewerAgent checking summary {index}/{len(papers)}")
            reviewer_feedbacks.append((summary, reviewer.review_summary(summary, full_text)))

    print("[5] Saving paper summaries")
    paper_summaries_path = out_dir / "paper_summaries.md"
    paper_summaries_path.write_text(write_paper_summaries(summaries), encoding="utf-8")

    reviewer_feedback_path: Path | None = None
    reviewer_feedback_text = ""
    if reviewer_feedbacks:
        reviewer_feedback_text = write_reviewer_feedback(reviewer_feedbacks)
        reviewer_feedback_path = out_dir / "reviewer_feedback.md"
        reviewer_feedback_path.write_text(reviewer_feedback_text, encoding="utf-8")

    print("[6] PostdocAgent writing final literature review")
    literature_review = postdoc.write_literature_review(
        topic=topic,
        summaries=summaries,
        reviewer_feedback=reviewer_feedback_text,
    )
    final_review_path = out_dir / "final_literature_review.md"
    final_review_path.write_text(literature_review, encoding="utf-8")

    experiment_review_path: Path | None = None
    novelty_review_path: Path | None = None
    impact_review_path: Path | None = None
    extra_review_text = ""
    if enable_extra_reviewers:
        print("[7] Running Experiment/Novelty/Impact reviewers")
        experiment_review = ExperimentReviewerAgent().review(topic, literature_review)
        novelty_review = NoveltyReviewerAgent().review(topic, literature_review)
        impact_review = ImpactReviewerAgent().review(topic, literature_review)

        experiment_review_path = out_dir / "experiment_review.md"
        novelty_review_path = out_dir / "novelty_review.md"
        impact_review_path = out_dir / "impact_review.md"
        experiment_review_path.write_text(experiment_review, encoding="utf-8")
        novelty_review_path.write_text(novelty_review, encoding="utf-8")
        impact_review_path.write_text(impact_review, encoding="utf-8")
        extra_review_text = "\n\n".join([experiment_review, novelty_review, impact_review])

    method_path: Path | None = None
    plan_path: Path | None = None
    prototype_path: Path | None = None
    prototype_readme_path: Path | None = None
    method_text = ""
    plan_text = ""

    if enable_prototype:
        print("[8] MethodExtractionAgent extracting implementable methods")
        method_text = method_agent.extract_implementable_method(topic, summaries)
        method_path = out_dir / "method_extraction.md"
        method_path.write_text(method_text, encoding="utf-8")

        print("[9] PrototypePlannerAgent writing implementation plan")
        plan_text = planner_agent.write_implementation_plan(topic, method_text)
        plan_path = out_dir / "implementation_plan.md"
        plan_path.write_text(plan_text, encoding="utf-8")

        print("[10] PrototypeWriterAgent writing prototype.py and README")
        code_text = writer_agent.generate_prototype_code(topic, plan_text)
        prototype_path = out_dir / "prototype.py"
        prototype_path.write_text(code_text, encoding="utf-8")

        readme_text = writer_agent.write_prototype_readme(topic, plan_text)
        prototype_readme_path = out_dir / "prototype_readme.md"
        prototype_readme_path.write_text(readme_text, encoding="utf-8")

    professor_report_path: Path | None = None
    if enable_report:
        print("[11] ProfessorAgent organizing final project report")
        report_text = professor.write_project_report(
            topic=topic,
            literature_review=literature_review,
            method_text=method_text,
            implementation_plan=plan_text,
            extra_reviews=extra_review_text,
        )
        professor_report_path = out_dir / "professor_report.md"
        professor_report_path.write_text(report_text, encoding="utf-8")

    return PipelineResult(
        topic=topic,
        output_dir=out_dir,
        paper_count=len(summaries),
        paper_summaries_path=paper_summaries_path,
        final_review_path=final_review_path,
        reviewer_feedback_path=reviewer_feedback_path,
        professor_report_path=professor_report_path,
        experiment_review_path=experiment_review_path,
        novelty_review_path=novelty_review_path,
        impact_review_path=impact_review_path,
        method_extraction_path=method_path,
        implementation_plan_path=plan_path,
        prototype_path=prototype_path,
        prototype_readme_path=prototype_readme_path,
    )
