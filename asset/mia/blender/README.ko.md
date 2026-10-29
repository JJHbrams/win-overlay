# Mia Blender 자산

## 현재 드래프트

- [Mia_RigDraft_v45.blend](mia-rig-draft-v45/Mia_RigDraft_v45.blend)
- [Idle 90f](mia-rig-draft-v45/Idle_90f.webp), [Turn 60f](mia-rig-draft-v45/Turn_60f.webp), [Click 30f](mia-rig-draft-v45/Click_30f.webp)
- `mia-rig-draft-v45/sequences/{idle,turn,click}/`의 실제 512×768 RGBA PNG 90/60/30장
- [공통 idle](mia-rig-draft-v45/canonical-idle.png), [검증 해시](mia-rig-draft-v45/FINAL-ARTIFACTS.md), [미완료 항목](mia-rig-draft-v45/DRAFT-LIMITATIONS.md)

네이티브 타임라인은 30fps이며 WebP도 90/60/30프레임, 3/2/1초다. 동일한 모델·카메라와 공통 시작/끝 포즈를 검증했다. 작은 팔 동작(어깨 5°, 팔꿈치 14°)에서 소매 분리 문제가 UV 경계 정점의 동일 가중치 처리와 공간 블렌딩으로 수정됐다. 메시 기하와 UV는 변경하지 않았다.

얼굴·블링크·손가락, 큰 동작 범위, 충돌·세컨더리 품질, 사선 헤어와 가방·액세서리 형상은 완성 자산 기준을 통과하지 못했다. 전체 12개 이벤트 팩도 미완료다.

## 저장 범위

최종 v45, 원화/투영 입력, 재현 스크립트와 검수 기록을 저장한다. v22~v44 모델링 실험, 백업 `.blend1`, 캐시와 대형 모델 체크포인트/원본 GLB는 로컬에 보존하며 Git에서는 제외한다. 원화가 패킹된 최종 `.blend`는 해당 로컬 파일 없이 재열기·렌더가 가능하다.

보고서의 원래 `D:/ai/...` 경로는 생성 당시의 출처 기록이다. 배포된 프레임은 위의 상대 경로에서 찾으면 된다. 원래 보고서 자체의 측정값은 보존한다.

## 출처

[provenance/](mia-rig-draft-v45/provenance/)에 모델/입력 해시와 실행 기록을 보관한다. 3D 재구성은 로컬 ComfyUI에서 실행됐고, A-pose 입력 제작은 OpenAI ImageGen을 사용한 별도 단계다. 모델별 라이선스 관찰은 일괄적인 사용권 부여가 아니다. 구체적인 모델 출처는 provenance를 확인한다.
