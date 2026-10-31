# Mia 얼굴 기반 재사용·분리 조립 연구

> **부분 결과 / ART FAIL.** 얼굴 기반 재사용과 표정 기능은 확인했지만 원화 닮음·헤어 접합은 미완료다. 이 폴더의 최신 번호를 승인 모델로 해석하지 않는다.

사용자는 기존 새벽 연구안의 바디/헤드·UV·눈/입 구조를 활용하고 정교한 헤어를 별도로 조립하는 방식을 우선 검토하라고 정정했다. 기존 조형을 참고하는 것과 생성 통짜 메시를 제작용 기반으로 쓰는 것은 구분한다. 바디·헤드의 단일 오브젝트 병합은 요구하지 않는다. 기존 얼굴의 눈·입은 명시적 재질·기하 영역과 본/키로 관리하며, 헤어·피부·의상을 같은 생성 표면에 종속시키지 않는다.

## 실제 결과

| 산출물 | 역할 / 상태 |
|---|---|
| `v05/Mia_ReusedFace_ArtStudy.blend` | 실제 02:40 `Mia_HairSurface_v06.blend`의 기반을 보존한 얼굴 보정 연구. 원본 42개 키에 eye-proportion/brow-placement 보정 2개와 UV 피부 색·물리적 상안검 선을 추가. 원화 직접 투영 텍스처를 완성한 결과가 아님 |
| `v07/Mia_ReusedFoundation_DetailedHair.blend` | 기존 바디·헤드·리그와 별도 상세 헤어의 조립 시험. 헤어 경계·목덜미에 눈에 띄는 절단/판형 면이 남아 **검수 FAIL**. 기준 모델로 게시하지 않음 |
| `v07/fresh-native-audit.json` | 새 Blender 프로세스에서 원본과 직접 비교: 기존 Face42 좌표/토폴로지/UV, body fingerprint, 원본 F00 이미지 픽셀 모두 동일. 원본 SHA 불변. 44개 키, 32개 FILE 이미지 내장, active linked IDs 0 |
| `v07/eye-matrix-30.png` | 실제 3 blink × 5 gaze × 정면/사선 렌더 30장. 좌우 독립 blink·입·감정은 별도 10장 |
| `v07/review-board.png` | 원화, 동일 카메라의 02:40 원본, 조립 실패, 피부 단독, 표정 비교 |
| `v07/hair-extraction-equivalence.json` | 승인되지 않은 얼굴 fitting native를 거치지 않고 Stage1에서 직접 분리해도 시험 헤어의 실제 기하/UV가 동일함을 확인 |

원본: `D:/ai/Mia3DWork/model-v02/hair-surface-stage/Mia_HairSurface_v06.blend`, SHA256 `9ef40cabbd2dd73f67e14e38fd54713d4c5ac0ceaf1ce4aa32b64af33f3830a6`. 원본·기존 Stage1·라이브 GUI는 덮어쓰지 않았다.

## 재현 경로

1. 기존 `tools/mia/blender/build_mia_face_art_v02.py`에 원본 native를 전달한다. 이번 연구 값은 `--neutral-close 0.35 --under-eye-strength 0.40 --outline-width 0.0005 --resolution 640`. 원본 UV/42키/Body/원본 픽셀 보존 검사를 실제 실행했다.
2. `tools/mia/blender/build_mia_reused_base_assembly.py`에 `--input` 얼굴 보정 연구, `--hair-source` 보존된 Stage1 v11 native, `--output` 새 절대 경로, `--proofs`를 전달한다. 원래 v07 실행은 로컬 v04의 헤어만 읽었으나, 이후 Stage1 직접 추출의 기하/UV 동일성을 별도로 검증하여 실패 얼굴 실험을 필수 입력에서 제거했다.
3. 색/좌표 분리는 **초기 디자인 후보**다. 이것만으로 production hair boundary나 애니메이션 품질을 승인하지 않는다.

## 다음 제작에서 지킬 것

- 기존 바디·헤드와 UV/리그를 유지하며 얼굴·눈·입과 원화 피부 작화를 다듬는다. 새 수학적 두상/전체 hair-bbox fitting으로 회귀하지 않는다.
- 원화 기반 피부 텍스처를 적용할 때 헤어·eyeline·입이 피부에 중복 투영되지 않도록 마스크와 시점 정합을 확인한다. 이번 UV pigment는 최종 원화 텍스처가 아니다.
- 상세 헤어는 관자/이마/귀/목덜미의 실제 파트 경계를 수작업 수준으로 정리해야 한다. 현재 RGB 규칙이 만든 톱니 경계와 하단 판형 면을 그대로 리깅하지 않는다.
- 가림 피부는 편집 원본을 보존하고 의상별 허용 포즈/교체 조합에서 검증한 조립본 마스크로 처리한다. 최종 한 메시 병합은 필수가 아니다.
- 정적 조립 확인 후 헤어의 proxy/cage·본/수동 weight·corrective와 필요한 제한적 secondary를 시험한다. 고해상도 표면 전체를 곧바로 자동 웨이트 처리하지 않는다.

## 실패 실험 보존

v01은 whole-head bbox fitting/평면 눈/단순 이동 blink 등 핵심 결함으로 실행 결과 없이 중단했다. v02~v04는 좌표계·원화 정합·조립 경계가 실패한 얼굴 fitting 실험이다. v06은 기존 내부 헤어 볼륨이 상세 헤어보다 위로 튀어나왔다. 이 중간 native는 로컬에 보존하고 생산 기준으로 사용하지 않는다. 코드 기록은 `tools/mia/blender/experiments/stage2-rejected/`에 격리했다.

## 판단 근거

- [Blender Studio Modeling](https://studio.blender.org/tools/artist-guide/asset-creation/modeling): 디자인 조형과 production topology를 구분하고 눈/입 helper shape와 후속 텍스처·리그 의존성을 설명한다. 공개 검색 색인 본문 확인, 직접 open 402. 이것이 특정 donor나 완전한 단일 피부 메시를 강제한다는 뜻은 아니다.
- [Frozenbyte Retopology](https://wiki.frozenbyte.com/index.php/3D_Asset_Workflow%3A_Retopology): 계층형 기하의 간격과 초기 관통 문제를 모델 단계에서 다룬다. 공개 검색 색인 본문 확인.
- [VRoid Skin Masks](https://vroid.pixiv.help/hc/en-us/articles/4405516267033-How-to-use-Skin-Masks): 피부/의상 두 메시 층과 의상별 비파괴 가림의 실제 구현 사례. Blender의 필수 기능/규칙으로 확대하지 않는다.

조회·직접 실행: 2026-10-31. 최종 얼굴 아트·의상·헤어 변형·이벤트 30fps 출력은 미완료다.
