from __future__ import annotations


def test_package_importable() -> None:
    import paperagent

    assert paperagent.__version__ == "0.2.0"


def test_assignment_agents_importable() -> None:
    from paperagent.agents import (
        BaseAgent,
        ExperimentReviewerAgent,
        ImpactReviewerAgent,
        MethodExtractionAgent,
        NoveltyReviewerAgent,
        PaperReaderAgent,
        PostdocAgent,
        ProfessorAgent,
        PrototypePlannerAgent,
        PrototypeWriterAgent,
        ReviewerAgent,
        strip_code_fence,
    )

    assert BaseAgent()
    assert PaperReaderAgent("test").topic == "test"
    assert ReviewerAgent()
    assert PostdocAgent()
    assert ProfessorAgent()
    assert MethodExtractionAgent()
    assert PrototypePlannerAgent()
    assert PrototypeWriterAgent()
    assert ExperimentReviewerAgent()
    assert NoveltyReviewerAgent()
    assert ImpactReviewerAgent()
    assert strip_code_fence("```python\nprint('ok')\n```") == "print('ok')"


def test_settings_defaults() -> None:
    from paperagent.config import Settings

    settings = Settings()
    assert settings.llm_provider == "ollama"
    assert settings.llm_model == "qwen3:8b"
    assert settings.arxiv_max_results == 3
