# paperagent Package

`paperagent`는 arXiv 논문 검색, PDF 텍스트 추출, LLM 기반 요약, reviewer feedback, literature review, prototype 생성까지 이어지는 PaperAgent Mini의 핵심 Python package입니다.

이 폴더의 파일들은 역할별로 분리되어 있으며, 전체 실행 흐름은 `workflow.py`가 관리합니다.

## Package Structure

```text
src/paperagent/
├── __init__.py
├── __main__.py
├── agents.py
├── arxiv_tool.py
├── cli.py
├── config.py
├── llm.py
└── workflow.py
