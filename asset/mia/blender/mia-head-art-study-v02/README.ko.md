# Mia 얼굴·헤어 작화 연구 — 미완성

기준은 `asset/mia/references/mia-expression-style-confirmed-20261031.png`의
가늘고 무거운 눈매, 선명한 눈밑 톤, 건조한 입매와 부스스한 잿빛 웨이브다.
현재 모델은 원화 닮음 검수를 통과하지 못했다. 의상·소품·최종 rig/event도
완료되지 않았다.

`Mia_FaceHair_Study_v06.blend`는 최신 수정 기록이다. 얼굴의 눈 비율·선 압력,
홍채 대비·UV 눈밑 톤·입/코 선과 피부 윤곽을 수정했다. 원래 42개 facial key,
UV, Body 좌표와 원본 이미지 데이터는 보존했고 두 개의 corrective를 추가했다.
새 아이라인에는 원본 UV 삼각형의 morph/weight를 전달했다. 헤어는 별도
부피·지역별 파트와 단일 왼쪽 braid로 구성했다.

검사에서 확인한 동작은 기본 표정·blink·mouth-A·작은 시선 변화다. 헤어의
최종 움직임, 의상 충돌, 모든 표정 조합이나 이벤트 애니메이션 품질을
검증한 것은 아니다. 구조 검사를 할 때 `OUTLINE` 노드 modifier를 끄면
렌더용 ink shell과 원래 피부 메시를 구분할 수 있다.

`rejected/Mia_FaceHair_Study_v04.blend`의 실제 216뷰는
`../audits/v02/head-art-v04/`에 있다. 독립 검수는 얼굴 작화와 후방 헤어를
**FAIL**로 판정했다. 최신 v06은 그 뒤 얼굴 대비를 더 수정한 연구이며,
이전 SHA의 216뷰를 최신 모델의 승인 근거로 재사용하지 않는다. 헤어의
넓은 덩어리·경직된 gather 연결은 아직 해결해야 한다.

기반 anatomy와 권리 기록은 `../mia-layered-model-v02/` 및
`tools/mia/blender/sources/VRoid_Beta4_CC0.md`에 있다. 원본 archive와
완전한 anatomy master를 보존했다. 이 폴더는 실행 중인 overlay의 캐릭터를
교체하지 않는다.

재현 도구는 `build_mia_face_art_v02.py`, `build_mia_hair_surface_v02.py`,
`render_mia_head_style_review.py`, `audit_mia_layered_stage.py`다. 모두
`tools/mia/blender/`에 있으며 입력 native와 새 출력 경로를 명시한다.
원본 파일을 덮어쓰지 않는다. native/PNG 및 정규화한 JSON의 해시는
manifest에 기록한다.
