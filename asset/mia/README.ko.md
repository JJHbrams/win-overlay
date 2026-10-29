# Mia 캐릭터 자산

현재 결과는 원화 기반 **v45 3D·기본 리깅 드래프트**다.

- [Blender 파일](blender/mia-rig-draft-v45/Mia_RigDraft_v45.blend)
- [Idle](blender/mia-rig-draft-v45/Idle_90f.webp) · [Turn](blender/mia-rig-draft-v45/Turn_60f.webp) · [Click](blender/mia-rig-draft-v45/Click_30f.webp)
- [공통 idle 보정 프레임](blender/mia-rig-draft-v45/canonical-idle.png)
- [원화 및 투영 입력](references/README.ko.md)
- [범위·검증·남은 작업](blender/README.ko.md)
- [재렌더 명령](../../tools/mia/blender/README.ko.md)

실제 30fps 액션 Idle 90 / Turn 60 / Click 30프레임과 투명 PNG 180장을 포함한다. 세 액션은 같은 모델·카메라·idle 포즈를 공유한다. 최종 12개 Engram 이벤트 팩과 실시간 적용은 미완료이며, 현재 런타임을 변경하지 않는다.

Blender 파일은 Git LFS로 보관한다. Git LFS가 설치된 환경에서 clone한 뒤 필요하면 `git lfs pull`을 실행한다. `.blend`에는 텍스처와 승인 원화 세 장이 패킹되어 있다.
