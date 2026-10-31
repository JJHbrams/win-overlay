# Mia v06 바디·헤드 제작 체크포인트

현재 native SHA-256: `97b05f5bef8e2291669c49119e1cf8bcabe638e93c117c4e8b9d55f15ed4b75f`.

**진행 중 / 얼굴 ART 미승인.** 독립 검수에서 AC1·2·3·5·6은 통과했고 AC4는 실패했다. 바디 원화 정합과 기존 표정·리그 기반은 확보했지만, 성숙한 Mia 얼굴의 두상 비율·눈매·입체감은 추가 수정 중이다. 헤어·의상·소품·최종 텍스처·secondary motion·이벤트 애니메이션 완료본이 아니다.

## 실제 구성

| 대상 | native owner | 내용 |
| --- | --- | --- |
| 본체 피부 | `MIA_V06_BODY_SKIN` | 4,648 vertices / 7,732 polygons, UVMap 유지. 몸통·사지 및 머리 뒤쪽 피부. |
| 얼굴 | `MIA_V06_FACE_SKIN` | 2,339 vertices / 3,150 polygons. 원본 42 keys와 owned 2 keys, UV·인덱스 대응 유지. |
| 리그 | `MIA_V06_RIG` | 분리된 production copy. Body/Face parent와 Armature modifier가 같은 리그를 가리킴. |
| 기준 원화 | `REF_*` 3개 | v06 turnaround, 가림 해제 가이드, 확정 표정 스타일을 packed/non-rendering으로 보존. |
| 원본 아카이브 | 기존 source 이름 | 피부·얼굴·표정 원본 데이터는 변경하지 않고 숨김 보존. |

헤어·의상을 피부에 합치지 않는다. 얼굴의 눈·눈썹·속눈썹·입 등 기존 material islands와 표정 인덱스도 유지한다. 조형을 위해 파생 좌표는 변경했으며, 원본 42개 key의 source 좌표와 파생 좌표를 혼동하지 않는다.

## 검증 자료

- `final-matrix/`: 정면·측면·후면·양 사선 × 전신·몸통·헤드 × actual/clay/wire, 45 PNG.
- `final-poses/`: 정면/사선 표정·시선, 약한 상하 시점, body stress와 neutral return, 30 PNG.
- `independent-final-audit-r2/`: 별도 fresh Blender 실행, 원본·아카이브·UV·토폴로지·실제 변형 및 재열기 검사.
- `independent-final-audit-r2/face44-v12-independent-compare.json`: 동결 헤드와 44/44 key 좌표 일치, v12의 Head/Neck 밖 Body 4,249 vertices delta 0.
- `acceptance-audit.md`: 독립 planner의 아트/기술 판정과 접근 수준.

원본 source SHA는 `9ef40cabbd2dd73f67e14e38fd54713d4c5ac0ceaf1ce4aa32b64af33f3830a6`으로 불변이다. 원본 42개 key 좌표는 float32 hash로 대조했다. 참조 3장 packed, missing texture 0. 검사 중 native/source 파일은 저장하지 않았다.

첫 `independent-final-audit/`의 false는 감사 코드가 새 `coordinate_hash_float32` 필드를 구조 비교에서 제외하지 못한 오류였다. 명시적인 구조 키 비교로 수정하고 같은 native SHA로 r2를 재실행해 기술 검사를 통과했다. 첫 결과도 이력으로 보존한다.

## 재현

현재 PC의 Blender 5.2.3과 원본 파일을 사용하는 PowerShell 명령이다. 저장소 루트에서 실행한다.

```powershell
$miaBlender = 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe'
$miaSource = 'D:/ai/Mia3DWork/model-v02/hair-surface-stage/Mia_HairSurface_v06.blend'
$miaOut = 'asset/mia/blender/mia-production-body-head-v06'
& $miaBlender --background --python tools/mia/blender/build_mia_body_head_v06.py -- --phase build --source $miaSource --output-dir $miaOut
& $miaBlender --background --python tools/mia/blender/render_mia_body_head_v06_matrix.py -- --input "$miaOut/Mia_BodyHead_v06.blend" --output-dir "$miaOut/final-matrix"
& $miaBlender --background --python tools/mia/blender/render_mia_body_head_v06_poses.py -- --input "$miaOut/Mia_BodyHead_v06.blend" --output-dir "$miaOut/final-poses"
& $miaBlender --background --python tools/mia/blender/audit_mia_body_head_v06_independent.py -- --source $miaSource --input "$miaOut/Mia_BodyHead_v06.blend" --output-dir "$miaOut/independent-final-audit-r2"
```

빌드는 원본에서 새 파생본을 만들며 개선 헤드 helper를 한 번 적용한다. 최종 recipe/native hash는 `recipe-metadata.json`에 있다. 렌더/감사는 입력 native를 저장하지 않는다. 원본 Body/Face의 Rz180 object frame과 identity rig를 유지하고, keep-world parent 및 world-frame fitting을 사용한다.

저장 기준은 30fps, Standard / Medium High Contrast, exposure 0, gamma 1이다. 두 `MIA_FaceArt_*` identity 값은 1.0이며 표정 검사 중 유지한다. 이는 제작 기준 neutral/A-pose이고 최종 idle clip이 아니다.

## 남은 작업

AC4를 통과하도록 두상과 얼굴 비율·사선 눈 깊이·Mia의 피로한 눈매를 보완한다. 얼굴 기반이 안정된 뒤 별도 헤어·의상을 맞추고, 허용 포즈의 웨이트/보정·접촉·클리핑과 실제 연속 프레임을 검증한다. 이전 실험과 v12 frozen native는 로컬 iterations에 보존했으며 전체 중간 산출물을 승인본으로 승격하지 않는다.
