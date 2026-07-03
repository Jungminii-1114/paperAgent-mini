# PaperAgent 구현 로드맵

Agent Laboratory의 큰 구조는 `문헌조사 -> 실험 -> 보고서 작성`입니다. 이 미니 프로젝트는 우선 문헌조사와 구현 계획까지 작게 가져오고, 이후 실험/보고서 agent를 단계적으로 붙이는 방향으로 갑니다.

## 현재 구현된 agent

| Agent | 역할 | 상태 |
|---|---|---|
| `BaseAgent` | 공통 prompt 호출 부모 클래스 | 구현 |
| `PaperReaderAgent` | 논문별 요약 생성 | 구현 |
| `ReviewerAgent` | 요약 정확성, 누락, hallucination 가능성 검토 | 구현 |
| `PostdocAgent` | 여러 논문 요약을 literature review로 종합 | 구현 |
| `ProfessorAgent` | 제출/발표용 최종 보고서 초안 정리 | 구현 |
| `MethodExtractionAgent` | 구현 가능한 방법, 수식, 알고리즘 추출 | 구현 |
| `PrototypePlannerAgent` | prototype 구현 계획 작성 | 구현 |
| `PrototypeWriterAgent` | mock data 기반 `prototype.py` 작성 | 구현 |
| `ExperimentReviewerAgent` | 실험 설계, metric, baseline, ablation 검토 | 옵션 구현 |
| `NoveltyReviewerAgent` | novelty와 차별점 평가 | 옵션 구현 |
| `ImpactReviewerAgent` | 활용 가능성, 학술/실용 impact 평가 | 옵션 구현 |

## 다음으로 추가할 agent

| 우선순위 | Agent | 목표 역할 | 구현 힌트 |
|---|---|---|---|
| 1 | `SWEngineerAgent` | 생성된 `prototype.py` 정리, 테스트 추가 | `outputs/prototype.py`를 읽고 refactor plan과 테스트 코드 생성 |
| 1 | `MLEngineerAgent` | mock prototype을 실제 실험 코드 구조로 확장 | dataset loader, baseline, metric, runner scaffold 생성 |
| 2 | `PaperSolver` | literature review와 결과를 paper draft로 변환 | abstract, introduction, method, limitation 형식으로 출력 |
| 2 | `MLESolver` | 실험 코드 생성/실행/수정 loop | subprocess 실행 로그를 읽어 코드 수정 |
| 3 | `AgentRxiv` | 읽은 논문 metadata와 요약 저장/검색 | SQLite 또는 JSONL 기반 local paper index |

## 추천 구현 순서

1. `SWEngineerAgent`
   - 지금 생성되는 `prototype.py`가 LLM 출력 그대로라 실행 품질 검증이 약합니다.
   - 가장 먼저 테스트와 코드 정리 agent를 붙이면 결과물 신뢰도가 올라갑니다.

2. `MLEngineerAgent`
   - prototype을 실제 실험 코드 구조로 바꾸는 단계입니다.
   - `data/`, `src/`, `experiments/`, `metrics.py` 같은 scaffold를 만들면 됩니다.

3. `PaperSolver`
   - 발표/과제 제출 형식의 paper draft를 자동 생성합니다.
   - `ProfessorAgent`를 더 강하게 만든 별도 solver로 분리하면 좋습니다.

4. `AgentRxiv`
   - 이전에 읽은 논문을 저장해두고 다시 검색하는 기능입니다.
   - 같은 논문을 반복 다운로드하지 않게 cache 역할도 할 수 있습니다.

## 구현 체크리스트

- `src/paperagent/agents.py`에 agent class 추가
- `src/paperagent/workflow.py`에 실행 단계 연결
- 결과를 `outputs/`에 markdown 또는 code 파일로 저장
- `src/paperagent/cli.py`에 실행 옵션 추가
- `mcp_paperagent_server.py` 응답에 새 산출물 경로 표시
- `tests/test_smoke.py`에 import/smoke test 추가
