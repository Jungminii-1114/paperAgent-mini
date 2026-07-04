# PaperAgent Mini

Agent Laboratory 논문의 문헌조사 단계를 작게 재현한 미니 프로젝트입니다.

## 구현 범위

현재 pipeline은 다음 순서로 실행됩니다.

1. arXiv 직접 검색 및 PDF 텍스트 추출
2. `PaperReaderAgent`가 논문별 한국어 요약 생성
3. `ReviewerAgent`가 요약 정확성, 누락, hallucination 가능성 검토
4. `PostdocAgent`가 최종 literature review 작성
5. `MethodExtractionAgent`가 구현 가능한 방법/수식/알고리즘 추출
6. `PrototypePlannerAgent`가 구현 계획 작성
7. `PrototypeWriterAgent`가 mock data 기반 `prototype.py`와 실행 README 생성
8. `ProfessorAgent`가 발표/과제 제출용 최종 보고서 초안 정리

| Agent | 역할 |
|---|---|
| `BaseAgent` | 모든 prompt 기반 agent의 공통 부모 클래스 |
| `PaperReaderAgent` | 논문 PDF/abstract를 읽고 논문별 요약 생성 |
| `ReviewerAgent` | 논문 요약이 원문과 맞는지 검토 |
| `PostdocAgent` | 여러 논문 요약과 reviewer feedback을 종합해 literature review 작성 |
| `ProfessorAgent` | 최종 프로젝트 보고서 초안 정리 |
| `MethodExtractionAgent` | 논문 요약에서 구현 가능한 방법론/수식/알고리즘 추출 |
| `PrototypePlannerAgent` | 추출된 방법론을 바탕으로 구현 계획 작성 |
| `PrototypeWriterAgent` | mock data 기반 `prototype.py`와 README 생성 |
| `ExperimentReviewerAgent` | 실험 설계, metric, baseline, ablation 관점 평가 |
| `NoveltyReviewerAgent` | novelty, 차별점, incremental risk 평가 |
| `ImpactReviewerAgent` | 연구 의의, 활용 가능성, impact 평가 |

선택 옵션으로 `ExperimentReviewerAgent`, `NoveltyReviewerAgent`, `ImpactReviewerAgent`도 실행할 수 있습니다.

## Task 반영

### Task 1: fallback 제거

### Task 2: API 없이 쓸 Ollama 모델 선정

기본 모델은 `qwen3:8b`로 선정하였습니다.

이유:

- Ollama의 Qwen3 페이지 기준 Qwen3는 dense/MoE 모델군이며 reasoning, code, agent tool use, 다국어 성능을 강조합니다.
- `qwen3:8b`는 약 5.2GB라 개인 노트북에서도 테스트하기 비교적 쉽습니다.
- 더 좋은 성능이 필요하고 RAM/VRAM 여유가 있으면 `qwen3:30b`가 우선 후보입니다. Ollama 설명 기준 작은 MoE 30B 모델은 훨씬 큰 QwQ-32B와 비교될 정도로 강한 성능을 목표로 합니다.
- 긴 추론이 필요한 리뷰에는 `deepseek-r1:8b`도 후보입니다. 다만 reasoning 출력이 길어 로컬 실행 시간이 늘 수 있습니다.
- 이미지까지 읽는 multimodal 실험이 필요하면 `gemma3:12b` 또는 `gemma3:27b`가 후보입니다.

참고:

- Agent Laboratory: https://github.com/SamuelSchmidgall/AgentLaboratory
- Qwen3 on Ollama: https://ollama.com/library/qwen3
- DeepSeek-R1 on Ollama: https://ollama.com/library/deepseek-r1
- Gemma3 on Ollama: https://ollama.com/library/gemma3

## 설치

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

테스트까지 돌릴 때:

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

Ollama를 쓸 경우:

```bash
ollama pull qwen3:8b
ollama serve
```

성능 우선 테스트:

```bash
ollama pull qwen3:30b
```

## 환경 설정

```bash
cp .env.example .env
```

기본값:

```env
LLM_PROVIDER=ollama
LLM_MODEL=qwen3:8b
OLLAMA_URL=http://localhost:11434/api/chat
ARXIV_MAX_RESULTS=3
ARXIV_MAX_ATTEMPTS=3
ARXIV_RETRY_WAIT_SECONDS=5
OUTPUT_DIR=outputs
```

OpenAI를 쓰고 싶으면 `.env.example`의 OpenAI 설정을 참고해 `LLM_PROVIDER=openai`, `OPENAI_API_KEY`를 설정하면 됩니다.

## CLI 실행

1st folder 방식으로 최소 문헌조사만 실행:

```bash
cd 1st_folder
cp .env.example .env
python paper_reader_agent.py "LLM agents for scientific discovery"
```

2nd folder 방식의 패키지 CLI:

가볍게 문헌조사만:

```bash
python -m paperagent run "LLM agents for scientific discovery" --max-papers 2 --no-prototype --no-report
```

기본 pipeline:

```bash
python -m paperagent run "paper agent for literature review" --max-papers 3
```

추가 reviewer까지 실행:

```bash
python -m paperagent run "multi-agent research assistants" --max-papers 3 --extra-reviewers
```

## 생성 파일

실행 결과는 `outputs/`에 저장됩니다.

- `paper_summaries.md`
- `reviewer_feedback.md`
- `final_literature_review.md`
- `method_extraction.md`
- `implementation_plan.md`
- `prototype.py`
- `prototype_readme.md`
- `professor_report.md`
- `experiment_review.md` (`--extra-reviewers` 사용 시)
- `novelty_review.md` (`--extra-reviewers` 사용 시)
- `impact_review.md` (`--extra-reviewers` 사용 시)

## MCP 실행

Claude Desktop MCP에 연결할 때는 `mcp_paperagent_server.py`를 stdio server로 등록합니다.

```json
{
  "mcpServers": {
    "paperagent-mini": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["/Users/ijeongmin/Documents/Paper Agent/mcp_paperagent_server.py"]
    }
  }
}
```

Claude에서:

```text
paperagent-mini MCP 실행해줘.
```

## 다음 확장 방향

짧게는 prompt 품질과 결과 요약 UI를 다듬고, 중기적으로는 `MLESolver`, `SWEngineerAgent`, `PaperSolver`, `AgentRxiv`를 추가하면 Agent Laboratory 구조에 더 가까워집니다. 자세한 후보는 `AGENT_ROADMAP.md`를 참고하세요.
