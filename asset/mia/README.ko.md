# Mia 캐릭터 자산

## 현재 상태

v45는 mechanical Idle/Turn/Click 3클립을 보존하는 아카이브일 뿐, Mia 완성 모델이 아니다. 다각도 clay 검토에서 얼굴 절단/열린 표면과 정면에서 가려진 중복 strap·pin·braid가 확인되어 **artistic/geometry gate는 FAIL**이다.

새 [CC0 layered foundation](blender/mia-layered-foundation/README.ko.md)은 완전한 Mia 조형이 아닌 일반 해부학 바탕이며 **INCOMPLETE**다. Mia 얼굴·헤어·의상·가방·리그·이벤트 애니메이션을 주장하지 않는다.

## 보존된 v45 기계적 드래프트

- [Blender 파일](blender/mia-rig-draft-v45/Mia_RigDraft_v45.blend)
- [Idle](blender/mia-rig-draft-v45/Idle_90f.webp) · [Turn](blender/mia-rig-draft-v45/Turn_60f.webp) · [Click](blender/mia-rig-draft-v45/Click_30f.webp)
- [공통 idle 보정 프레임](blender/mia-rig-draft-v45/canonical-idle.png)
- [원화 및 투영 입력](references/README.ko.md)
- [범위·검증·남은 작업](blender/README.ko.md)
- [v45 감사 증거와 SHA-고정 수동 리뷰](blender/audits/v45/README.ko.md)
- [새 foundation의 범위·재현](blender/mia-layered-foundation/README.ko.md)
- [재렌더 명령](../../tools/mia/blender/README.ko.md)

실제 30fps 액션 Idle 90 / Turn 60 / Click 30프레임과 투명 PNG 180장을 포함한다. 세 액션은 같은 모델·카메라·idle 포즈를 공유한다. 최종 12개 Engram 이벤트 팩과 실시간 적용은 미완료이며, 현재 런타임을 변경하지 않는다.

Blender 파일은 Git LFS로 보관한다. Git LFS가 설치된 환경에서 clone한 뒤 필요하면 `git lfs pull`을 실행한다. `.blend`에는 텍스처와 승인 원화 세 장이 패킹되어 있다.
