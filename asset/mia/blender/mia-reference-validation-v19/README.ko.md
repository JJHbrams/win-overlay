# Mia 원화 대응 검토 v19

> 얼굴·헤어·바디와 검수 절차를 함께 재개방한 진단 기록이다. 모델을 완성하거나 원화 정합을 통과시킨 결과가 아니다.

현재 모델 입력은 v18 SHA `87334607c76f6c0e876807f10ff407e8ce60fc7055265ae3591257893ba7b88d`다. 이 검토에서는 모델·기준 원화를 수정하지 않았다. 모든 비교에서 비균일 배율과 부위별 워핑을 사용하지 않았다.

## 실제 비교 자료

- `front-registered-comparison.png`: 재확인 portrait와 실제 정면 렌더. 보이는 동공 두 점에 맞춘 회전·균일 확대·이동만 적용한다. 모델의 메시 턱끝/입 경계와 셰이더 동공 중심을 표시한다.
- `front-anchor-sensitivity.png`: 동공 두 점 정합과 눈 중심–턱끝 정합의 차이. 정규화한 거리는 해당 그림에서 독립적으로 검증할 수 없다.
- `front-registration.json`: 실제 점, 수동 원화 추정점의 정의, 변환행렬, 잔차, 원본 해시와 한계.
- `multi-view-registered-comparison.png`: v22 원화 정면·측면·후면·3/4와 동일 모델의 실제 대응 뷰.
- `multi-view-yaw-bracket.png`: 원화의 3/4 표기가 정확히45도를 뜻하지 않으므로20/35/45도 후보를 비교한다. 카메라 정합 완료 주장은 하지 않는다.
- `multi-view-visibility-supplement.png`: v06 가시성 보조 원화와 헤어를 숨긴 모델의 정면/측면.
- [바디 4뷰 비교](../mia-body-reference-audit-v19/body_reference_comparison_4rows.png)와 [바디 판정](../mia-body-reference-audit-v19/BODY_AUDIT.md).
- [셰이더/광원 조사](../mia-lookdev-audit-v19/LOOKDEV_AUDIT.md)와 [고정 검토 장면](../mia-lookdev-audit-v19/REVIEW_RIG_USAGE.md).

## 수치의 정의와 정정

동공은 원화의 보이는 검은 중심과 모델의 실제 보이는 pupil shader 중심을 대응했다. 윗눈꺼풀에 가려진 nominal iris UV 중심이나 보이는 회색 영역의 무게중심과 혼용하지 않는다. 원화의 수동 점은 대략±2px의 불확실성을 가진다.

이 정의에서 입 경계–턱끝 거리/동공 간격은 원화 약0.400, 모델 약0.364다. 이전 정합 전 육안 검토에서 제시된 “모델의 턱이 더 길다”는 방향은 철회한다. 여기서 보이는 약9% 차이를 즉시 턱 늘이기 명령으로 사용하지 않는다. 원화의 yaw/pitch/비대칭과 다른 뷰를 함께 확인해야 한다.

같은 이유로 앞선 홍채/눈 가로폭0.46→0.54와 얼굴 폭3% 축소는 수정량 기록일 뿐 원화 재현의 증거가 아니다. 겹침 이미지에는 눈꺼풀 곡선·가림·눈 크기, 볼/턱 윤곽, 코/입 대응의 차이가 남는다. 동공 두 점을 맞췄다는 사실이 그 나머지를 통과시키지 않는다.

다각도 그림도 완전한 카메라 캘리브레이션은 아니다. 정면 roll, 사선 yaw/pitch, 가려진 후면 nape 기준점의 불확실성을 JSON과 그림에 표시했다. 모든 모델 뷰는 하나의 동일 native이며 뷰마다 형상을 따로 맞추지 않았다.

## 전체 부위 상태

바디에는 가슴–흉곽/겨드랑이/하부 연결, 상부 골반–허벅지 단차, 엉덩이–뒤허벅지, 목–어깨 전환 문제가 남았다. 속옷에 가려진 정확한 피부 윤곽/부피는 미검증이다. 그 가림을 핑계로 실제 모델의 부자연스러운 연결을 PASS할 수 없고, 브라/팬티의 경계를 피부 형태로 복사해서도 안 된다.

피부·헤어의 활성 재질은 Emission 기반의 가상 음영이며 실제 조명 기반 diffuse/specular 재질이 아니다. 사용되지 않는 과거 PBR 슬롯과 활성 맵을 구분했다. 중립 무광/반사 프로브/UV/색 신호/기존 툰을 분리해서 검토해야 하며, 추가 맵 생성은 목표 셰이더 설계 이후다.

재개 기준은 [WORKING_PROTOCOL](../../WORKING_PROTOCOL.md)과 [CURRENT_STATE](../../CURRENT_STATE.json)에 있다. 파트별 FAIL을 독립적으로 유지하며 의상·최종 리깅의 다음 단계로 자동 승격하지 않는다.

## 독립 검토 결과

기존 원래 계약 ID를 유지한 독립 검토는 다음과 같다. 기술적 보존 증거는 별도 manifest에 있으며, 검토자가 직접 검사하지 않은 항목은 미검증으로 남겼다.

| 항목 | 독립 판정 |
|---|---|
| AC1 원본/독립 소유 보존 | UNVERIFIED by reviewer; root integration의140개 비헤어 메시 보존 검사는 별도 기술 증거 |
| AC2 Pixal 헤어 원화 디테일/실루엣 | FAIL |
| AC3 두상–헤어 정합/다각도 | FAIL |
| AC4 얼굴/눈/프로파일 원화 정합 | FAIL |
| AC5 고정 UV/색/실제 재질 품질 | UNVERIFIED |
| AC6 이후 변형을 위한 의미별 영역/소유 | UNVERIFIED |
| AC7 바디 다각도 조형 | FAIL |
| AC8 압축/재개 시 프로토콜 실행 지속 | UNVERIFIED; 문서 저장은 완료, 실제 이후 재개 행동은 아직 시험되지 않음 |

전체 판정은 **FAIL**이다. 파일 생성·44개 렌더·해시/키 보존으로 이를 바꾸지 않는다.

## 재현 입력 보존

정면 비교의 실제 RGBA 입력 `front_bare_rgba.png` / `front_hair_rgba.png`, 원화 수동점, 모델 투영점, 20/35도 실제 렌더와 생성 스크립트도 함께 보존했다. `front-landmarks.json`과 `front-points-ready.json`은 같은 바이트의 호환 파일이다. `multi-view-compose.py`는 보존된 원화와 `integrated-v18/fresh-review`의 실제 렌더를 읽는다. Blender용 `export_front_landmarks.py` / `multi-view-render.py`는 native를 저장하지 않는 진단 레시피다.

정면 그림 재생성 예시(이 폴더를 작업 디렉터리로 사용):

```powershell
python build_front_comparison.py --model-landmarks front-points-ready.json --ref-landmarks reference-point-estimates.json --model-bare front_bare_rgba.png --model-hair front_hair_rgba.png --reference ../../references/received/mia-face-reaffirmed-20261031.png --output-dir replay
```

스크립트의 Windows 폰트와 기존 로컬 작업 경로는 환경 의존성이다. 전체 과거 제작 과정을 깨끗한 환경에서 재생성한다고 주장하지 않는다. 두 packed native는 이 체크포인트의 실제 모델과 진단 장면이며, producer의 과거 중간 native들은 각 로컬 작업 공간에 보존한다.
