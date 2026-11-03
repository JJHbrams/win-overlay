# Mia 제작 파이프라인: 현재 바디 작업부터 적용

2026-11-03 / Asia/Seoul. 사용자가 사이드에서 프로젝트 전용 스킬·훅 파이프라인을
구성해 메인에 전달하고, 현재 제작 과제부터 점진 확대하도록 요청했다.

## 범위와 비간섭

- 별도 소형 sparse worktree/branch: `codex/mia-modeling-pipeline`.
- 이 변경은 root AGENTS routing, 전용 skill, 보조 검사 CLI, project hooks와 테스트만 추가한다.
- 메인 dirty 상태, H 계약/생산 코드, CURRENT_STATE, 모델/UV/맵/카메라/광원/Blender
  프로세스, global Codex/Engram hooks·권한·신뢰 저장소는 수정하지 않았다.
- 새 MCP 서버·외부 자산·의존성·예약·자동 ART 판정은 없다. 기존 Blender MCP는
  설정 항목만 확인했다. 실제 연결/도구 호출 성공은 이 사이드의 검증 범위가 아니다.
- 현재 제작을 중단/교체하라는 전달이 아니다. 메인의 다음 안전한 체크포인트에 검토한다.

## 원래 요청에 대한 수용 기준

| ID | 관찰 가능한 결과 / 런타임 | 검증과 근거 |
|---|---|---|
| P1 | 프로젝트용 스킬이 현재 작업/승인/미결을 읽고 전문 조형 근거를 실제 수정에 연결 / Codex skill | quick_validate, 참조 링크·접근 수준·기존 계약 유지·accepted face 보존 검토 |
| P2 | 재개/압축 후 짧은 맥락, 증거 변경 안내 / project command hooks | 격리 Git fixture에서 실제 Windows hook command 및 이벤트 응답 시험. 실제 Codex 신뢰 후 자동 발화는 메인 도입 시 확인 |
| P3 | 현재 capture를 재사용하고 stale 파일·누락 뷰·조건 변경을 검출 / Python CLI | 실제 H baseline4 검사 + 양성/음성 테스트. source-review/ART/조형 개선은 별개 |
| P4 | 메인 모델·설정에 비간섭, 작은 저장량 / local Git | 별도 sparse worktree, 입력 해시 확인, raw 출력은 author cache. global hooks/trust 변경 없음 |
| P5 | 메인이 적용 가능한 커밋·명령·한계를 받음 / main-thread handoff | 사용자 승인에 따른 send_message_to_thread 1회 전달. 제작 완료·ART PASS로 확대하지 않음 |

스킬 문서의 유효성과 도구 테스트는 실제 조형 효율/품질의 검증을 대신하지 않는다.
첫 실제 제작 사용과 결과 비교는 메인 파일럿에 남는다. 사이드의 subagent 사용은
금지되어 있어 별도 에이전트 검수는 하지 않았다.

## 포함 구성

- `.agents/skills/mia-reference-modeling/SKILL.md`: 진입/자료 선택/진단/국소 편집/검수/복구.
- `references/body-shaping.md`: 지금의 목–어깨–겨드랑이 작업. 해부 구조를 원화에
  적용하는 가설과 관찰해야 할 면을 연결. CGBUMP 목차를 본편 학습으로 포장하지 않음.
- `references/face-and-hair.md`: ASW 실제 슬라이드의 볼/눈/턱 지식과 hair 진단.
  현재 accepted 얼굴을 역사적 피드백만으로 재작성하지 않음.
- `mia_pipeline.py context`: 기존 production state의 짧은 색인. stage_plan_index는
  폐기안도 포함할 수 있으므로 버전 이름만으로 활성 계획을 선택하지 않는다.
- `inspect`: 기존 H capture JSON의 native/PNG 해시, 원본 PNG 크기, 뷰 목록,
  카메라/pose/light/display 기록과 선택적 before/after 조건 비교. 렌더를 새로 하지 않음.
- `reference-review`: 기존 v22 `validate_reference_review.py`를 그대로 호출.
- `.codex/hooks.json`: SessionStart(startup/resume), PostCompact, Stop.
  시작/압축 후에는 짧은 색인만 제공. Stop은 선택된 receipt의 size/mtime 변경만
  빠르게 알려주며, 재해시는 명시적 CLI 검사에서 한다.

훅은 실제 본 스킬+Mia state가 있고 해당 worktree가 `inspect --activate`로 opt-in한
경우에만 작동한다. Stop은 block/자동 연속 실행을 반환하지 않는다. 실패/미완료로
정직하게 종료하는 것을 허용한다. 훅은 모델·캡처·production state를 쓰지 않는다.

## 메인의 도입 순서

1. 현재 mesh/solver/Blender 작업을 계속한다. 안전한 checkpoint에서 변경 diff를 검토한다.
   기존 dirty 변경은 stash/reset/덮어쓰기하지 않는다. 동일 경로가 새로 생겼다면 병합을
   중단하고 조정한다. 저장소 통합 정책에 따라 `git merge --no-ff codex/mia-modeling-pipeline`
   등 적합한 통합을 수행한다. 자동 push나 production state 승격은 이 패키지에 없다.
2. 현재 세션에서 `.agents/skills/mia-reference-modeling/SKILL.md`를 명시적으로 읽는다.
   metadata 재탐색/프로젝트 훅 재로드는 실제 Codex runtime에서 확인한다.
3. 신규 project hooks는 global Engram hooks와 함께 추가 실행되는 구조다. 기존 것을
   덮어쓰거나 신뢰 hash를 직접 수정하지 않는다. Codex의 Review hooks/Settings > Hooks
   또는 CLI `/hooks`에서 새 정의를 검토·신뢰해야 실제 자동 실행된다.
4. 아래 `context`와 현재 baseline `inspect`를 실행해 기준과 artifact binding을 확인한다.
   이 단계는 geometry/reference correspondence/ART를 승인하지 않는다.
5. 다음 실제 H 후보의 캡처가 생기면 `--candidate`로 같은 조건인지 확인하고, 기존
   source/baseline/candidate package validator 및 실제 이미지를 함께 검토한다.
   4뷰 baseline은 Gray6/high/low/full64frame 최종 요구의 대체물이 아니다.
6. 파일럿에서는 원화 분석/가설/수정 방법/전후 판독을 기존 trial log에 간결히 남긴다.
   첫 효과를 확인하기 전 추가 MCP/큰 프레임워크/새 강제 훅을 만들지 않는다.

## 현재 작업에 바로 쓰는 명령

메인의 canonical 작업공간에서, 기존 Python 3 환경으로 실행한다.

```powershell
python -X utf8 tools/mia/pipeline/mia_pipeline.py context --root .

python -X utf8 tools/mia/pipeline/mia_pipeline.py inspect --root . --capture .mia-cache/body-h/baseline4/capture.json --source asset/mia/references/received/mia-body-v06-confirmed-20261102.png --source asset/mia/references/body-foundation/v06/mia-body-visibility-guide-v06.png --views front,profile,back,oblique --output .mia-cache/mia-pipeline/body-h-baseline.json --activate
```

첫 `--activate`는 ignored receipt와 active pointer만 작성한다. 원본 이미지를
복사하거나 모델을 저장/승격하지 않는다. 현재 baseline 파일의 위치가 바뀌었다면
CURRENT_STATE/active plan을 읽어 실제 경로로 바꾼다.

다음 후보에서는 기존 baseline과 candidate 둘 다 동일한 H-style capture 구조를
사용해야 한다. `--candidate <actual-candidate-capture.json>`를 추가한다. 새 상태가
다른 진단 재질/가림을 쓰면 무조건 같게 바꿔 맞추지 말고 목적에 맞는 비교를 따로
촬영한다. 기존 fixture가 원화와 맞는지는 시각적 source registration으로 확인한다.

최종 원화 패키지는 기존 validator를 사용한다.

```powershell
python -X utf8 tools/mia/pipeline/mia_pipeline.py reference-review --root . --package <actual-reference-review.json>
```

`inspect`의 원본 참조 목록은 기준 바이트를 명시할 뿐 source crop/SRT/시각 대조를
검증하지 않는다. `reference-review` 역시 자동 ART 판정이 아니다. stage 선택,
관찰한 차이와 회귀, 실제 이미지 검토는 제작자의 책임으로 남는다.

중단/비활성화는 `python tools/mia/pipeline/mia_pipeline.py deactivate --root .`.
active pointer만 없애고 모델/receipt/global hooks는 보존한다.

## 실제 확인 결과

- skill-creator quick_validate: 유효.
- 자동 시험: 15개. stale native/PNG, 누락 high/low, 중복 뷰, camera/visibility/shader
  불일치, 출력 경계, receipt 변경, opt-in/해제, 훅 read-only/nonblocking,
  Windows 하위 디렉터리에서 실제 configured command 실행을 포함.
- 실제 H baseline4 native + 4 PNG + 기준 원화 2개의 읽기 전용 검사: integrity true,
  baseline_capture, paired_capture_checked false, source_art_reviewed false,
  art_acceptance NOT_EVALUATED. 첫 실측 약0.32초(단일 실행; 일반 성능 보증 아님).
- actual evidence: author worktree의 `.mia-cache/pipeline-evaluation/current-baseline.json`.
- 실제 Blender 편집/MCP 연결/새 H candidate/조형 개선/최종 source-review/자동 훅 발화:
  이번 사이드에서 검증하지 않았다. 기존 baseline을 새 후보로 보고하지 않는다.
- Engram tool catalogue가 이 사이드에 노출되지 않아 kg/activity 호출은 수행하지 못했다.
  Wiki 동기화나 독립 조형 검수 완료를 주장하지 않는다.

## 점진 확대 판단

현재 body 파일럿에서 채택 가능한 개선까지 걸리는 시간, 효과 없는 재시도,
조건 불일치 재촬영, 다른 각도의 회귀를 기존 작업과 비교한다. 프레임 수나 해시 검사
통과율만으로 효율/품질 향상을 선언하지 않는다. 유효한 작은 패턴만 재사용 helper로
추출한다. 다음은 face/eye 현재 미결, 이어 hair silhouette/UV 진단으로 확대하되,
각 단계의 조형/변형 승인은 유지한다.

## 확인한 공식 운용 문서

- Skills/MCP 역할: https://developers.openai.com/plugins/concepts/skills
- Codex hooks/이벤트/신뢰/경계: https://learn.chatgpt.com/docs/hooks
- Project guidance: https://learn.chatgpt.com/docs/agent-configuration/agents-md

이벤트 입력/출력을 격리 shell에서 시험한 것과 실제 Codex가 trusted hooks를 자동
실행한 것은 구분한다. 기존 런타임과 프로젝트 trust의 실제 적용 결과가 우선한다.

## 2026-11-03 후속: 백그라운드 제작과 live MCP 조형 분담

사용자는 후속 대화에서 초안/배치 작업과 세부 조형을 구분하고, 현재처럼 세밀한
인체 볼륨을 다듬을 때는 열린 Blender에서 MCP로 작업하도록 요청했다. 이 후속은
스킬의 기존 "연결돼 있으면 MCP 사용"을 작업 종류에 따른 구체적 선택 기준으로
보강한다. 위의 최초 도입 안내가 solver 작업의 무조건적 지속을 뜻하지는 않는다.

- 백그라운드: 큰 비율/블록아웃 후보, 검토된 변경의 재현, 기술 검사, UV 처리,
  렌더/턴테이블/베이크/내보내기. 초안도 다음 조형 전에 실제 다각도 검토한다.
- live MCP: 안와/볼/턱, 목/어깨/겨드랑이, 흉곽/유방 연결, 눈꺼풀 접촉,
  헤어 실루엣/가닥 간격/국소 클리핑 등 실제 표면을 보며 판단해야 하는 수정.
  현재 상체 세부 보정의 기본 경로다. MCP 경유 bpy/스크립트 편집은 허용한다.
- 실제 씬/후보 식별 → 수정 영역 확인 → 작은 편집 → 실제 전후·인접 시점·원화
  확인 → 유지/복구 순으로 진행하고, 쓸 만한 후보에 기존 전체 검증을 수행한다.
  상태 조회만 하거나 배치 결과를 마지막에 한 번 불러오는 것은 이 루프의 대체가 아니다.
- 작업 방식 전환 시 같은 후보/상태를 보고 있는지 확인한다. 다른 세션의 씬이나
  무관한 미저장 편집을 덮어쓰지 않고, 작은 수정마다 큰 native를 중복 저장하지 않는다.

SessionStart/PostCompact의 기존 opt-in 안내에도 이 분담을 넣었다. 훅 정의/전역
설정/신뢰 저장소는 바꾸지 않았으며, 안내는 MCP 사용이나 실제 조형 개선을 강제로
보증하지 않는다. 자동 훅 발화와 실제 제작 적용 여부는 메인에서 별도 확인한다.
기존 수용 기준, accepted 얼굴, production 상태와 Blender 프로세스는 변경하지 않는다.

후속 검증: 기존 격리 행동 시험 15개, skill quick_validate, git diff --check 통과.
이 결과는 수정된 안내/훅의 검증이며, 실제 live 조형 작업이나 품질 개선의 증거는 아니다.
