# v02 헤어 제작 실험 — 작화 미통과

이 폴더는 실패를 보존한 실험 기록이다. 현재 Mia 헤어로 채택하지 않는다.

| 스크립트 | 실제 확인한 한계 |
|---|---|
| build_mia_hair_v02.py | 같은 비중의 독립 clump가 로프·잎사귀 형태로 반복됐다. |
| build_mia_hair_mass_v02.py | 후두부 덮임과 긴 머리의 단면·윤곽이 불충분했고 판처럼 보였다. |
| rework_mia_hair_donor.py | CC0 샘플의 반듯한 앞머리와 장발 실루엣이 남았다. 좌표·alpha·색상 수정은 원화 작화 통과를 뜻하지 않는다. |
| build_mia_hair_hierarchy_v08.py | 5개 주 덩어리와 6개 보조 덩어리로 다시 구성했지만 넓은 판·덩어리와 경직된 cap/gather가 남았다. 작화 FAIL. 원본 커밋 0493418. |

원본과 시안·실제 렌더는 `D:/ai/Mia3DWork/model-v02/`의 hair-stage,
hair-mass-stage, hair-donor-stage에 보존했다. 이 실험은 해당 로컬 경로를
입력으로 사용하는 역사 코드이며 휴대 가능한 제작 CLI가 아니다.

donor 시안에서 발견한 별도 구현 결함은 해결했다. 숨겨진 원본의 갱신되지
않은 world matrix로 추출하면 앞뒤가 잘못 등록된다. 활성 임시 복사본을
평가해 좌표를 측정한다. 재현 근거는 `probe_source_frames.py`와 anatomy
audit의 source-frame-probe.json이다. 투명 텍스처와 UV를 무조건 불투명
재질로 바꿔 얼굴 앞 커튼처럼 보이는 문제와 혼동하지 않는다.

표정 시트가 요구하는 불규칙하고 겹치는 잿빛 웨이브, 무거운 눈매와 함께
검수하기 전까지 이들 시안을 의상 제작의 승인 기반으로 사용하지 않는다.
