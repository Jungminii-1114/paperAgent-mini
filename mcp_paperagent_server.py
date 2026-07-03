"""Claude Desktop MCP server for the PaperAgent mini project.

Claude MCP 설정 예시:

{
  "mcpServers": {
    "paperagent-mini": {
      "command": "/path/to/python",
      "args": ["/path/to/Paper Agent/mcp_paperagent_server.py"]
    }
  }
}
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
os.chdir(PROJECT_ROOT)

from paperagent.workflow import run_pipeline  # noqa: E402

mcp = FastMCP("paperagent-mini")
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs"


@mcp.tool()
def start_paperagent_review() -> str:
    """Start an interactive paper-agent run by asking the user for missing inputs."""
    return (
        "paperagent-mini MCP 실행을 시작합니다.\n\n"
        "Claude는 사용자에게 아래 정보를 한 단계씩 물어본 뒤 "
        "`run_paper_literature_review` tool을 호출하세요.\n\n"
        "1. 찾아볼 논문 주제(topic)를 물어보세요.\n"
        "2. 읽을 논문 개수(max_papers)를 물어보세요. 사용자가 모르겠다고 하면 3개를 사용하세요.\n"
        "3. prototype.py까지 만들지(enable_prototype)를 물어보세요. 사용자가 모르겠다고 하면 true를 사용하세요.\n"
        "4. 실험/novelty/impact reviewer까지 돌릴지(enable_extra_reviewers)를 물어보세요. 모르면 false를 사용하세요.\n"
        "5. 답변을 모아 `run_paper_literature_review`를 실행하세요.\n"
        "6. tool 실행이 끝나면 반환된 '채팅창 표시용 요약' 표를 사용자에게 그대로 보여주세요."
    )


@mcp.tool()
def run_paper_literature_review(
    topic: str,
    max_papers: int = 3,
    enable_prototype: bool = True,
    enable_extra_reviewers: bool = False,
) -> str:
    """Search arXiv using the user's topic, read papers, run agents, and save outputs.

    If the user only says "mcp 실행해줘" or does not provide a topic, ask for:
    topic, max_papers, and enable_prototype before calling this tool.
    """
    topic = topic.strip()
    if not topic:
        return (
            "topic이 비어 있습니다. 사용자에게 찾아볼 논문 주제를 먼저 물어본 뒤 "
            "다시 `run_paper_literature_review`를 호출하세요."
        )

    DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        result = run_pipeline(
            topic=topic,
            max_papers=max_papers,
            output_dir=str(DEFAULT_OUTPUT_DIR),
            enable_prototype=enable_prototype,
            enable_extra_reviewers=enable_extra_reviewers,
        )
    except RuntimeError as exc:
        return f"# PaperAgent 실행 실패\n\n{exc}"
    return _render_mcp_response(result)


def _render_mcp_response(result) -> str:
    paper_rows = _extract_paper_table_rows(result.paper_summaries_path)
    review_summary = _extract_review_summary(result.final_review_path)

    optional_paths = [
        ("요약 검토 피드백", result.reviewer_feedback_path),
        ("최종 프로젝트 보고서", result.professor_report_path),
        ("실험 설계 리뷰", result.experiment_review_path),
        ("Novelty 리뷰", result.novelty_review_path),
        ("Impact 리뷰", result.impact_review_path),
        ("구현 가능 방법 추출", result.method_extraction_path),
        ("구현 계획", result.implementation_plan_path),
        ("프로토타입 코드", result.prototype_path),
        ("프로토타입 README", result.prototype_readme_path),
    ]
    optional_lines = [
        f"- {label}: `{path}`" for label, path in optional_paths if path is not None
    ]

    return (
        "# PaperAgent 실행 완료\n\n"
        "아래는 **채팅창 표시용 요약**입니다. 자세한 내용은 저장된 파일을 확인하세요.\n\n"
        f"- 주제: **{result.topic}**\n"
        f"- 읽은 논문 수: **{result.paper_count}개**\n"
        f"- 출력 폴더: `{result.output_dir}`\n\n"
        "## 읽은 논문 요약표\n\n"
        "| # | 논문 | 아주 짧은 요약 |\n"
        "|---|---|---|\n"
        f"{paper_rows}\n\n"
        "## 전체 리뷰 한줄 요약\n\n"
        f"{review_summary}\n\n"
        "## 저장된 파일\n\n"
        f"- 논문별 요약: `{result.paper_summaries_path}`\n"
        f"- 최종 문헌 리뷰: `{result.final_review_path}`\n"
        f"{chr(10).join(optional_lines)}\n\n"
        "Claude는 위 표와 한줄 요약을 사용자에게 그대로 보여주고, 필요하면 저장 파일을 열어 더 자세히 보면 됩니다."
    )


def _extract_paper_table_rows(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    matches = list(re.finditer(r"^##\s+(\d+)\.\s+(.+)$", text, flags=re.MULTILINE))
    if not matches:
        return "| - | 제목 추출 실패 | `paper_summaries.md`를 확인하세요. |"

    rows: list[str] = []
    for position, match in enumerate(matches):
        number = match.group(1)
        title = _table_cell(match.group(2))
        start = match.end()
        end = matches[position + 1].start() if position + 1 < len(matches) else len(text)
        block = text[start:end]
        short_summary = _table_cell(_shorten(_first_meaningful_line(block), 120))
        rows.append(f"| {number} | {title} | {short_summary} |")
    return "\n".join(rows)


def _extract_review_summary(path: Path) -> str:
    text = path.read_text(encoding="utf-8").strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    line = _first_meaningful_line(text)
    return _shorten(line, 220) if line else f"전체 리뷰는 `{path}`에 저장되었습니다."


def _first_meaningful_line(text: str) -> str:
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(("#", "-", "*", "|", "---")):
            continue
        if line.startswith("**arXiv ID**"):
            continue
        return re.sub(r"\s+", " ", line)
    return ""


def _shorten(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def _table_cell(text: str) -> str:
    return text.replace("|", "/").replace("\n", " ").strip()


if __name__ == "__main__":
    mcp.run(transport="stdio")
