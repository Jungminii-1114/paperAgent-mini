"""arXiv search and PDF reading utilities.

This module intentionally does not use hard-coded fallback papers. It searches
arXiv directly and fails with a clear message when arXiv rate-limits requests.
"""

from __future__ import annotations

import os
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

MAX_PAPER_CHARS = 30_000
ARXIV_API_URL = "https://export.arxiv.org/api/query"
USER_AGENT = "PaperAgentMini/0.2 contact: local-study-project"


@dataclass(frozen=True)
class ArxivPaper:
    paper_id: str
    title: str
    summary: str
    pdf_url: str
    abs_url: str

    def get_short_id(self) -> str:
        return self.paper_id


def search_arxiv(query: str, max_results: int = 5) -> list[ArxivPaper]:
    """Search arXiv directly without static fallback papers."""
    max_attempts = int(os.getenv("ARXIV_MAX_ATTEMPTS", "3"))
    base_wait = int(os.getenv("ARXIV_RETRY_WAIT_SECONDS", "10"))

    for attempt in range(1, max_attempts + 1):
        try:
            xml_text = _request_arxiv_search(query, max_results=max_results)
            papers = _parse_arxiv_feed(xml_text)
            if not papers:
                raise RuntimeError(f"arXiv 검색 결과가 0개입니다: {query}")
            return papers
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == max_attempts:
                raise RuntimeError(_format_arxiv_error(exc, query)) from exc
            wait_seconds = base_wait * (2 ** (attempt - 1))
            print(f"[arxiv retry] HTTP 429 rate-limit. {wait_seconds}s 후 재시도...")
            time.sleep(wait_seconds)
        except urllib.error.URLError as exc:
            raise RuntimeError(f"arXiv 네트워크 연결 실패: {exc}") from exc

    raise RuntimeError("arXiv 검색이 모든 재시도 후에도 실패했습니다.")


def read_arxiv_pdf(paper: ArxivPaper, work_dir: Path) -> str:
    work_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = work_dir / f"{paper.get_short_id().replace('/', '_')}.pdf"

    request = urllib.request.Request(
        paper.pdf_url,
        headers={"User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        pdf_path.write_bytes(response.read())

    text_parts = []
    reader = PdfReader(str(pdf_path))
    for page_index, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        text_parts.append(f"\n--- Page {page_index} ---\n{page_text}")

    pdf_path.unlink(missing_ok=True)
    return "\n".join(text_parts)[:MAX_PAPER_CHARS]


def _request_arxiv_search(query: str, max_results: int) -> str:
    params = {
        "search_query": f"abs:{query}",
        "sortBy": "relevance",
        "sortOrder": "descending",
        "start": "0",
        "max_results": str(max_results),
    }
    url = f"{ARXIV_API_URL}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8")


def _parse_arxiv_feed(xml_text: str) -> list[ArxivPaper]:
    root = ET.fromstring(xml_text)
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }
    papers: list[ArxivPaper] = []

    for entry in root.findall("atom:entry", ns):
        abs_url = (entry.findtext("atom:id", default="", namespaces=ns) or "").strip()
        paper_id = _paper_id_from_abs_url(abs_url)
        title = _normalize_space(entry.findtext("atom:title", default=paper_id, namespaces=ns))
        summary = _normalize_space(entry.findtext("atom:summary", default="", namespaces=ns))
        pdf_url = _find_pdf_url(entry, ns) or f"https://arxiv.org/pdf/{paper_id}.pdf"

        papers.append(
            ArxivPaper(
                paper_id=paper_id,
                title=title,
                summary=summary,
                pdf_url=pdf_url,
                abs_url=abs_url or f"https://arxiv.org/abs/{paper_id}",
            )
        )

    return papers


def _find_pdf_url(entry: ET.Element, ns: dict[str, str]) -> str:
    for link in entry.findall("atom:link", ns):
        title = link.attrib.get("title", "").lower()
        link_type = link.attrib.get("type", "").lower()
        href = link.attrib.get("href", "")
        if title == "pdf" or link_type == "application/pdf":
            return href
    return ""


def _paper_id_from_abs_url(abs_url: str) -> str:
    paper_id = abs_url.rstrip("/").rsplit("/", 1)[-1]
    return paper_id or "unknown"


def _normalize_space(text: str | None) -> str:
    return " ".join((text or "").split())


def _format_arxiv_error(exc: urllib.error.HTTPError, query: str) -> str:
    if exc.code == 429:
        return (
            "arXiv가 현재 HTTP 429 rate-limit을 반환했습니다. "
            "fallback 논문을 쓰지 않도록 만들어서, 실제 검색 제한이 그대로 보이는 상태입니다.\n"
            f"- query: {query}\n"
            "- 해결: 5-10분 뒤 다시 실행하거나 `.env`에서 "
            "`ARXIV_MAX_ATTEMPTS=5`, `ARXIV_RETRY_WAIT_SECONDS=30`처럼 늘려주세요."
        )
    return f"arXiv 검색 실패: HTTP {exc.code} {exc.reason}"
