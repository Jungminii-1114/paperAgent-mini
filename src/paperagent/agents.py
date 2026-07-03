"""Small multi-agent roles inspired by Agent Laboratory."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from paperagent.llm import ask_llm


@dataclass(frozen=True)
class PaperSummary:
    paper_id: str
    title: str
    abstract: str
    summary: str


class BaseAgent:
    """Common parent for prompt-only agents."""

    name = "BaseAgent"
    role = "general research assistant"

    def ask(self, user_prompt: str) -> str:
        system_prompt = (
            f"You are {self.name}, a {self.role}. "
            "Work carefully, cite concrete evidence from the provided text, "
            "and write in clear Korean unless code is requested."
        )
        return ask_llm(system_prompt, user_prompt)


class PaperReaderAgent(BaseAgent):
    """PhDStudent-like agent for paper reading and per-paper summaries."""

    name = "PaperReaderAgent"
    role = "PhD student agent responsible for literature review"

    def __init__(self, topic: str):
        self.topic = topic

    def summarize_paper(self, paper: Any, full_text: str) -> PaperSummary:
        user_prompt = f"""
Research topic:
{self.topic}

Paper title:
{paper.title}

Paper abstract:
{paper.summary}

Paper text:
{full_text}

아래 항목을 포함해 한국어 요약을 작성하세요.
- Problem: 논문이 해결하려는 문제
- Key idea: 핵심 아이디어
- Method: 방법론, 모델 구조, 알고리즘
- Experiments or evidence: 실험 설정, 결과, 근거
- Limitations: 한계와 약한 가정
- Why this matters for our project: 우리 paper agent 프로젝트에 적용할 점
"""
        return PaperSummary(
            paper_id=paper.get_short_id(),
            title=paper.title,
            abstract=paper.summary,
            summary=self.ask(user_prompt),
        )


class ReviewerAgent(BaseAgent):
    """Reviewer-like agent that checks whether a summary matches the paper."""

    name = "ReviewerAgent"
    role = "peer reviewer checking factual consistency and missing details"

    def review_summary(self, summary: PaperSummary, full_text: str) -> str:
        user_prompt = f"""
Paper title:
{summary.title}

Paper abstract:
{summary.abstract}

Paper text excerpt:
{full_text[:12000]}

Student summary:
{summary.summary}

요약 품질을 검토하세요. 아래 형식을 지켜주세요.
1. Accuracy score: 1-5
2. Missing details: 누락된 핵심 내용
3. Possible hallucinations: 원문 근거가 약한 주장
4. Rewrite advice: 더 나은 요약을 위한 수정 제안
"""
        return self.ask(user_prompt)


class PostdocAgent(BaseAgent):
    """Postdoc-like agent that synthesizes multiple summaries."""

    name = "PostdocAgent"
    role = "postdoc mentor synthesizing papers into a research direction"

    def write_literature_review(
        self,
        topic: str,
        summaries: list[PaperSummary],
        reviewer_feedback: str = "",
    ) -> str:
        user_prompt = f"""
Research topic:
{topic}

Paper summaries:
{_join_summaries(summaries)}

Reviewer feedback:
{reviewer_feedback or "No reviewer feedback was generated."}

위 자료를 바탕으로 한국어 literature review를 작성하세요.
반드시 포함할 항목:
1. Overall research trend
2. Paper comparison table
3. Common methods
4. Open problems
5. Implementation hints for our mini paper agent
6. Project ideas our team could build next
"""
        return self.ask(user_prompt)


class ProfessorAgent(BaseAgent):
    """Professor-like agent that turns agent outputs into a report."""

    name = "ProfessorAgent"
    role = "professor agent responsible for final report organization"

    def write_project_report(
        self,
        topic: str,
        literature_review: str,
        method_text: str = "",
        implementation_plan: str = "",
        extra_reviews: str = "",
    ) -> str:
        user_prompt = f"""
Research topic:
{topic}

Literature review:
{literature_review}

Implementable methods:
{method_text or "Not generated."}

Implementation plan:
{implementation_plan or "Not generated."}

Extra reviewer reports:
{extra_reviews or "Not generated."}

발표나 과제 제출에 쓸 수 있는 최종 보고서 초안을 한국어로 작성하세요.
포함할 항목:
- Abstract
- Background
- Agent architecture
- What we implemented
- What remains
- Next milestones
"""
        return self.ask(user_prompt)


class MethodExtractionAgent(BaseAgent):
    """Extract implementable methods, formulas, and algorithms."""

    name = "MethodExtractionAgent"
    role = "ML/SW engineer extracting implementable methods"

    def extract_implementable_method(self, topic: str, summaries: list[PaperSummary]) -> str:
        user_prompt = f"""
Research topic:
{topic}

Paper summaries:
{_join_summaries(summaries)}

실제 코드로 구현 가능한 알고리즘, 수식, 데이터 흐름, agent 설계를 추출하세요.
가능하면 pseudo-code와 구현 난이도도 함께 정리하세요.
"""
        return self.ask(user_prompt)


class PrototypePlannerAgent(BaseAgent):
    """Convert extracted methods into a concrete prototype plan."""

    name = "PrototypePlannerAgent"
    role = "technical project manager planning a prototype"

    def write_implementation_plan(self, topic: str, method_text: str) -> str:
        user_prompt = f"""
Research topic:
{topic}

Extracted method:
{method_text}

mock data만으로 실행 가능한 `prototype.py`를 만들기 위한 개발 계획을 작성하세요.
포함할 항목:
1. Requirements & dependencies
2. Core modules
3. Input/Output specifications
4. Step-by-step execution steps
5. Validation scenario
"""
        return self.ask(user_prompt)


class PrototypeWriterAgent(BaseAgent):
    """Write a mock-data prototype and a short execution guide."""

    name = "PrototypeWriterAgent"
    role = "Python developer writing a self-contained prototype"

    def generate_prototype_code(self, topic: str, implementation_plan: str) -> str:
        user_prompt = f"""
Research topic:
{topic}

Implementation Plan:
{implementation_plan}

위 계획을 바탕으로 동작하는 Python 코드를 작성하세요.
조건:
1. 외부 데이터 없이 mock data를 생성해야 합니다.
2. 표준 라이브러리 위주로 작성하세요.
3. markdown 코드 블록 하나에 Python 코드만 담으세요.
4. 마지막에는 `if __name__ == "__main__":` 실행 블록을 포함하세요.
"""
        return strip_code_fence(self.ask(user_prompt))

    def write_prototype_readme(self, topic: str, implementation_plan: str) -> str:
        user_prompt = f"""
Research topic:
{topic}

Implementation Plan:
{implementation_plan}

생성된 `prototype.py` 실행 안내 README를 한국어로 작성하세요.
설치, 실행 명령, 예상 출력, 다음 개선점을 포함하세요.
"""
        return self.ask(user_prompt)


class ExperimentReviewerAgent(BaseAgent):
    """Review whether the proposed experiments are convincing."""

    name = "ExperimentReviewerAgent"
    role = "reviewer evaluating experiment design"

    def review(self, topic: str, literature_review: str) -> str:
        return self.ask(_review_prompt(topic, literature_review, "실험 설계, metric, baseline, ablation"))


class NoveltyReviewerAgent(BaseAgent):
    """Review novelty and differentiation from prior work."""

    name = "NoveltyReviewerAgent"
    role = "reviewer evaluating novelty"

    def review(self, topic: str, literature_review: str) -> str:
        return self.ask(_review_prompt(topic, literature_review, "novelty, 차별점, incremental risk"))


class ImpactReviewerAgent(BaseAgent):
    """Review academic and practical impact."""

    name = "ImpactReviewerAgent"
    role = "reviewer evaluating research impact"

    def review(self, topic: str, literature_review: str) -> str:
        return self.ask(_review_prompt(topic, literature_review, "impact, 활용 가능성, 한계"))


def write_paper_summaries(summaries: list[PaperSummary]) -> str:
    lines = ["# 논문 요약 모음집 (Paper Summaries)\n"]
    for index, summary in enumerate(summaries, start=1):
        lines.append(f"## {index}. {summary.title}")
        lines.append(f"- **arXiv ID**: [{summary.paper_id}](https://arxiv.org/abs/{summary.paper_id})")
        lines.append(f"\n### Abstract\n{summary.abstract}\n")
        lines.append(f"### 요약 내용\n{summary.summary}\n")
        lines.append("---\n")
    return "\n".join(lines)


def write_reviewer_feedback(feedbacks: list[tuple[PaperSummary, str]]) -> str:
    lines = ["# Reviewer Feedback\n"]
    for index, (summary, feedback) in enumerate(feedbacks, start=1):
        lines.append(f"## {index}. {summary.title}")
        lines.append(f"- **arXiv ID**: [{summary.paper_id}](https://arxiv.org/abs/{summary.paper_id})")
        lines.append(f"\n{feedback}\n")
        lines.append("---\n")
    return "\n".join(lines)


def strip_code_fence(raw_code: str) -> str:
    text = raw_code.strip()
    if "```python" in text:
        return text.split("```python", 1)[1].split("```", 1)[0].strip()
    if "```" in text:
        return text.split("```", 1)[1].split("```", 1)[0].strip()
    return text


def _join_summaries(summaries: list[PaperSummary]) -> str:
    return "\n\n".join(
        f"## {item.title}\nID: {item.paper_id}\nAbstract: {item.abstract}\n\n{item.summary}"
        for item in summaries
    )


def _review_prompt(topic: str, literature_review: str, review_focus: str) -> str:
    return f"""
Research topic:
{topic}

Literature review:
{literature_review}

아래 관점으로 peer review를 작성하세요: {review_focus}
형식:
1. Score: 1-5
2. Strengths
3. Weaknesses
4. Concrete suggestions
"""
