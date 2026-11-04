# Mia 모델링 중간 보고 및 Claude Code 인계 상태

작성: 2026-11-04 (Asia/Seoul). **제작 중간 보고이며 전체 모델·ART 승인 보고가 아니다.**

## 완료한 범위

- 인계문서: [CLAUDE_CODE_HANDOFF.md](CLAUDE_CODE_HANDOFF.md). 정본·후보·실패·미적용 코드, 최신 사용자 피드백, 재개 순서, 실제 검증 근거를 분리했다.
- 문서와 작은 증거를 `c4cf541`로 커밋하고 `origin/codex/mia-v003-fit`에 푸시했다. 큰 native/NPZ/원시 렌더는 추가로 Git에 넣지 않았다.
- `handoff/20261104/manifest.json`, `verification.json`, `live-state.json`에 파일 해시와 인계 시점 검증을 보존했다. 코드 스냅샷은 실행 대상이 아닌 `.py.txt`다.
- 모델링 에이전트를 중단했다. 이번 인계·기록 단계에서는 Blender 모델·리깅을 변경하지 않았다.

## 실제 재개 정본

루트: `C:/Users/antio/.codex/worktrees/mia-current/win-overlay`.

- native: `.mia-cache/production-resume-20261104/Mia_Waist02_Static_WIP.blend`
- native SHA256: `25c638a4406193dd0ff73efd3d253330bda7405a9c8c6ae83632fedaaa5725a8`
- live body 좌표 SHA256: `ba6537406312273401ad22367e34ba8226979ffb980babe5fd95a0c6f59ed829`
- Blender 표시 경로의 `migration-to-C/Mia_Current_STATIC_WIP.blend`는 오래된 파일이다. 최신 저장본과 혼동하지 않는다.
- Rib01V3는 **미적용**이다. `arm_pose01`는 축·가중치·복구 처리 등이 미완료인 **실행 금지 후보**다.

## 남은 제작 과제

1. 기본 자세에서 상완–전완 꺾임과 길이·근육량을 바로잡고 실제 평가 표면을 확인한다.
2. 광배보다 옆으로 튀는 갈비와 흉곽–허리–골반 곡선을 조정한다.
3. 원화 대비 허리의 세로 길이를 확인한다.
4. 최신 피드백인 과대한 머리 비율을 원화와 실측한다. 과거의 머리 확대 요청을 재적용하지 않는다.
5. 뒷머리 중앙 공백과 원래 헤어 대비 스타일·밀도·측면 볼륨 불일치를 수정한다.
6. 측면 목–흉부–허리 S라인과 부족한 둔부 볼륨을 다듬는다.

단일 뷰 맞춤이나 벌크 좌표 변경으로 다른 채택 파트를 망가뜨리지 않는다. 수정 전후 보호 영역 해시, 원화 원비율, 동일 카메라·조명·포즈, 헤어 ON/OFF 및 위·아래·중간각도 비교를 유지한다. 기본 조형 검수 이후 UV·원화 기반 재질맵·표정·최종 동작 단계로 진행한다.

## 지정 Claude Code 세션 전달 결과

대상: `7c59915f-756b-4e5e-9663-25183fe3d89b`.

로컬 세션 기록의 ID와 기존 작업 경로를 확인하고, 공식 CLI `--resume <ID> --print --output-format json`으로 인계문서 전체와 최신 커밋 정보를 제출했다. 이번 호출에서는 인수 확인만 요청하고 제작 도구를 비활성화했다.

**실패:** CLI exit code 1, `terminal_reason=api_error`, `Failed to authenticate: OAuth session expired and could not be refreshed`. 대상 세션 ID는 결과에 일치했지만 수신자의 인수 확인은 없다. 전달·인계 완료라고 보고하지 않는다. Claude Code 인증 복구 후 같은 ID로 재전달하고 응답을 확인해야 한다. 인증 설정은 임의 변경하지 않았다.

## Engram 기록

- `engram_save_memory`: `memory_saved` 확인.
- `kg_update_node(mia-character-rebuild)`: `status=ok` 확인. 최신 정본·해시·6과제·미적용 후보·인증 실패를 기록했다. 기존 모델링/조사 기록은 보존한다.
- 세션 중간 요약의 최초 호출은 `scope_mismatch`, 다음 자동 탐색은 `no_open_session`이었다. 에피소드 기억 저장 성공과 세션 체크포인트 성공은 구분한다. 올바른 `overlay` 범위 재호출은 `no_new_messages`를 반환하여 새 세션 체크포인트 작성 성공으로 계산하지 않았다.
- 동기화·lint의 실제 결과와 접수 기록은 `handoff/20261104/report-receipts.json`을 따른다. Wiki 전체의 기존 경고를 모델 승인으로 해석하지 않는다.

## 근거와 재개 순서

현재 상태 → 인계문서 → 원화 색인·작업 프로토콜 → 실제 최신 native와 다각도 원화 비교 → 범위를 제한한 한 가지 조형 과제 순서로 재개한다. Wiki 관련 노트는 `mia-character-rebuild`, `mia-reference-mcp-review`, `blender-character-workflow`다.

문서·해시 검증 통과는 조형의 자연스러움이나 원화 닮음을 증명하지 않는다. 사용자 최신 6과제가 해결되었다는 주장도 하지 않는다.
