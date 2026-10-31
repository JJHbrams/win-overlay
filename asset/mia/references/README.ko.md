# Mia 원화·참조 관리

> 원화의 역할과 확인 상태를 구분한다. 가장 최근 파일이라는 이유로 기준 원화를 바꾸지 않는다.

## 역할별 기준

| 역할 | 원화 / 상태 |
|---|---|
| 캐릭터·의상·소품 디자인 | [v22 착의 마스터](mia-clean-master-v22.png) — 기존 승인 기준. 원화의 뷰별 포즈 차이가 있어 엄밀한 정투영 도면은 아님 |
| 얼굴·눈매·표정 그림체 | [사용자가 재확인한 표정 시트](mia-expression-style-confirmed-20261031.png) — 얼굴 판단 우선 기준 |
| 날씬한 체형 인상·노출 복부 | [2026-10-31 재첨부한 정면 기준](received/mia-front-body-reaffirmed-20261031.png) — 사용자가 v01보다 호리호리하고 abs가 보인다고 재확인. 옷에 가려진 부위까지 치수 확정한 자료는 아님 |
| 기존 전신·표정 보조 원화 | [정면 v22](mia-canonical-source-v22.png), [16표정 v22](mia-expressions-clean-16-v22.png) — 보존. 새 첨부와 파일 바이트가 다르므로 덮어쓰지 않음 |
| 사용자가 선택한 정면 본체형 | [원안에서 의상을 교체한 정면](body-foundation/anchors/mia-body-front-user-selected-20261031.png) — 골반·허벅지 라인을 유지한 추가 수정의 기준. 임의로 더 가늘게 만든 정면으로 바꾸지 않음 |
| 최신 정면 수정 후보 | [종아리 폭 수정안](body-foundation/front-revisions/calf-v01/mia-body-front-calf-v01.png) — 선택된 정면에서 양쪽 종아리의 볼륨만 소폭 줄이도록 요청한 파생안. 정확한 감소율·픽셀 불변을 보증하지 않음 |
| 최신 4뷰 체형 원화 후보 | [v05 메인 턴어라운드](body-foundation/v05/mia-body-turnaround-v05.png) — 선택 정면·종아리 수정에 맞춘 정면·좌측면·후면·사선 후보. 사용자 검토 전이며 정투영 도면이나 3D 승인본이 아님 |
| 머리 가림 해제 보조 원화 | [v05 body visibility guide](body-foundation/v05/mia-body-visibility-guide-v05.png) — 목·어깨·등을 확인하려고 긴 머리를 임시로 숨긴 모델링 보조본. 메인 원화의 헤어 디자인을 바꾸지 않음 |
| 기존 다각도 체형 검토 | [원안 파생 v03 4뷰](body-foundation/v03/mia-body-underwear-study-v03.png) — 긴 원래 헤어를 유지한 검토안. 이후 선택된 정면·종아리 수정과 아직 동기화되지 않음 |
| 이전 체형 시안 | [v01](body-foundation/v01/mia-body-underwear-study-v01.png), [v02](body-foundation/v02/mia-body-underwear-study-v02.png) — 헤어 변경·독립적인 체형 해석에 대한 사용자 피드백으로 대체됨. 비교 기록으로 보존 |
| 3D 생성 입력 | `inputs/` v30 A-pose — 승인 원화를 바탕으로 만든 파생 입력이며 디자인 마스터가 아님 |
| 재구성 전처리 | `conditioning/` — 당시 body/head 재구성에 실제 사용한 파생 자료. 기준 원화로 역승격하지 않음 |

## 체형 시트

각 버전 폴더에 전체 시트, 생성 프롬프트, 출처·입력 해시·검토 상태를 둔다. v01–v03에는 정면·측면·후면·사선의 개별 lossless crop도 있고, v05는 메인·body visibility guide 전체 시트만 보존한다.

- v01: 착의 마스터와 재확인 표정 시트에서 파생한 최초 속옷 4뷰.
- v02: 재첨부 정면 원화의 날씬한 허리·복부 중앙선/복사근 표현을 반영했으나, 머리를 올려 묶고 체형을 새로 해석한 점을 사용자가 지적했다. 현재 기준으로 쓰지 않는다.
- v03: 원안의 얼굴·긴 웨이브·반묶음·왼쪽 땋은 머리를 유지하며 의상만 속옷으로 교체한 정면을 먼저 만들고, 이를 바탕으로 다각도를 파생했다. 머리카락에 가린 등은 그대로 가린다.
- v05: 선택된 정면·종아리 수정본을 기준으로 4뷰를 새로 맞췄다. [메인](body-foundation/v05/mia-body-turnaround-v05.png)은 긴 헤어를 포함한 디자인 기준이고, [visibility guide](body-foundation/v05/mia-body-visibility-guide-v05.png)는 머리 가림을 해제해 본체 조형을 보는 보조 시트다. 입력·반복 이력은 [provenance](body-foundation/v05/provenance.json), 독립 검토와 한계는 [review](body-foundation/v05/review.ko.md)에 남겼다.
- v05 프롬프트는 [초기 배치](body-foundation/v05/01-layout-prompt.txt), [사선 보정](body-foundation/v05/02-angle-prompt.txt), [종아리 일관성 보정](body-foundation/v05/03-calf-consistency-prompt.txt), [body visibility guide](body-foundation/v05/04-body-visibility-prompt.txt) 순으로 보존했다. 초기 배치·사선 보정 이미지는 iterations/에 남기며, 메인 시트의 최종 대체본으로 해석하지 않는다.
- 사용자는 v03 다각도에 사용한 추가 슬리밍 정면보다 **최초 원안 파생 정면**을 후속 수정 기준으로 선택했다. 이 선택본과 종아리 수정본은 별도 경로에 보존한다.
- v04 측면 볼륨 조정은 이미지 생성 도구의 출력 안전필터에서 `sexual` 분류로 차단되어 **이미지가 없다**. [generation-status.json](body-foundation/v04/generation-status.json)과 프롬프트만 기록했다. 기존 다각도 이미지가 이 수정까지 완료한 결과라고 설명하지 않는다.
- v01–v03의 개별 뷰는 전체 시트를 **리사이즈 없이 자른 파일**이다. crop 좌표를 기록했으며 뷰마다 인체를 늘이거나 재정렬하지 않았다. v05에는 개별 crop을 임의로 만들지 않았다.
- 모든 그림은 생성된 검토용 원화다. 사선 각도·머리 기울기·포즈·투영이 정확히 고정됐다고 가정하지 않는다. 같은 3D 카메라에서 체형을 맞추고 원화와 다시 대조해야 한다.
- 골반·허벅지·둔부는 착의 기준 원화에서 대부분 가려진 영역이다. 새 검토안의 해당 부피는 보수적인 추정이며 승인된 치수가 아니다.

## 파일·버전 규칙

- 기존 원화의 경로와 바이트를 보존한다. Blender 도구가 참조하는 원본을 이동하거나 덮어쓰지 않는다.
- 새 체형 시트는 `body-foundation/vNN/`, 선택된 정면은 `body-foundation/anchors/`, 국소 수정은 `body-foundation/front-revisions/`에 추가한다. 수정 사유와 원본 버전을 `provenance.json`/`review.json`에 남긴다.
- [reference-catalog.json](reference-catalog.json)은 역할·우선 기준·후보 상태·파생 관계를 관리한다. [files.json](files.json)은 이전 형식을 유지하며 이미지 상대 경로·해시·크기를 기록한다.
- 사용자 확인 전 생성 시트를 `approved`로 올리거나, 그 시트를 사용했다는 사실만으로 모델 검수를 PASS하지 않는다.

캐릭터 디자인 참고용으로 첨부했던 타 캐릭터·실사 사진은 이 카탈로그의 Mia 기준 원화에 포함하지 않는다. GLB·Blender 모델 체크포인트는 이 이미지 폴더의 관리 대상이 아니다. 이전 생성 입력의 절대 경로와 모델 관찰 기록은 `../blender/mia-rig-draft-v45/provenance/`에 보존되어 있다.
