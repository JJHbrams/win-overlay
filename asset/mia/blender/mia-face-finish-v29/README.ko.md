# Mia v29 눈머리·속눈썹·얼굴 표면 체크포인트

실제 눈머리 피부 접합부와 안검 안쪽 반환면을 먼저 수정하고, 위·아래 독립 속눈썹 메시와 얼굴 표면 레이어를 순서대로 구성했다. 바디L/기존 볼·광대와 무관한 데이터는 유지했다.

- [현재 Blender native](surface-C/native/Mia_FaceFinish_v29_C.blend)
- [정면 원화·기존·수정본 비교](final-review/source-boards/front-source-baseline-final.png)
- [측면 비교](final-review/source-boards/profile-source-baseline-final.png) · [왼쪽 사선](final-review/source-boards/left_oblique-source-baseline-final.png) · [오른쪽 사선](final-review/source-boards/right_oblique-source-baseline-final.png)
- [실제 회전 검토 GIF](final-review/Mia_v29_review_orbit.gif) · [24방향 모음](final-review/orbit-contactsheet.png)
- [화장/다크서클/쌍꺼풀 개별 조절](surface-C/review-supplement/individual-feature-gains.png)
- [실제 광원·반사·거칠기 검사](surface-C/review-supplement/actual-light-reflection-probes.png)
- [표정 변형 검사](surface-C/review-supplement/surface-closure-probes.png)
- [독립 검수](ACCEPTANCE_FINAL.md) · [원화와 남은 차이](FINAL_REVIEW.md)

적용된 맵은 얼굴 UV의 색/화장·피로 표현과 실제 diffuse/shadow·specular·roughness 제어로 구분된다. 생성 cosmetic art는1254square, 숫자 제어 맵은2048float이며 원래 packed pigment와 구분한다. 새 맵이 실제 출력과 조명에 영향을 주는지 native-map/flat-map 및 이동 광원 렌더로 확인했다.

검수 통과 범위는 이번 눈머리·속눈썹·얼굴 표면 수정이다. 전체 원화 닮음, 헤어 마감, 의상과 최종 이벤트/물리/30fps 애니메이션은 완료 상태가 아니다. 회전 GIF도 모델을 둘러보는 카메라 검사이며 캐릭터 애니메이션이 아니다.

현재 열린 Blender는 이 native와 일치하며, 원화 대응 조명/카메라와 머리 중심 정투영 탐색을 설정했다. 탐색 설정 때문에 모델/리그 원점은 이동하지 않았다. 재현용 runtime helper는 `show_live_final.py`이며 native를 덮어쓰지 않는다.
