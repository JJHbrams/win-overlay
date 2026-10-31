# Mia v06 바디·헤드 제작 체크포인트

현재 Astra 통합 native SHA-256: `81773274ef99152728ad584488ba720a35d783a2cb12acb2b313c0ca14253d10`.

**Astra 제작 체크포인트 / 얼굴 ART 미승인.** 사용자 요청으로 실제 `gpt-6-astra` 제작 에이전트가 얼굴·눈·리그를 수정했다. 독립 검수에서 AC1·2·3·5·6은 통과했고 원화 정합 AC4는 여전히 실패했다. 구조 개선과 첫 모델링 pass를 보존한 결과이며, 최종 Mia 얼굴·헤어·의상·이벤트 애니메이션 승인본이 아니다.

[다각도 미리보기](review-board.png)

## Astra가 실제 수정한 부분

- 전체 머리와 Head/eye rest pivots를 함께 맞추고, 눈·눈썹·bridge의 연속적인 세로 배치를 조정했다. 평가 iris 높이 +9.38mm, chin→crown 눈 위치 41.43%→47.06%.
- 기존 iris X/Z 축소에 Y 곡률도 운반해 사선에서 홍채가 세로선처럼 보이던 현상을 개선했다.
- 코·입의 깊이와 입 폭을 모든 shape key에 일관되게 반영했다.
- Head 경계 36점을 최대 약1.61mm 재접속해 profile의 귀 앞/턱뒤 검은 틈을 제거했다. 용접·원본 삭제는 하지 않았다.
- 기존 UV에 좁은 눈밑 crease mask를 별도로 packed했다. 원래 pigment 픽셀과 UV는 유지했다.
- neutral Close는 0.48이며 두 identity 값 1.0을 유지한다. 보호된 Body 4,249 vertices는 v12와 delta 0이다.

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
- `independent-astra-v09-world-audit/`: 별도 fresh Blender 실행(exit 0), 원본·아카이브·UV·토폴로지·실제 변형 및 재열기 검사.
- `independent-astra-v09-audit/compare-runtime.json`: Astra v09 헤드와 44/44 key 좌표 일치, v12의 Head/Neck 밖 Body 4,249 vertices delta 0.
- `pose-world-space-corrections/`: 실제 world 축으로 바로잡은 arm-forward/torso-yaw 4프레임과 제어·복원 수치. 나머지 26프레임은 그대로 보존.
- `acceptance-audit.md`: 독립 planner의 아트/기술 판정과 접근 수준.

원본 source SHA는 `9ef40cabbd2dd73f67e14e38fd54713d4c5ac0ceaf1ce4aa32b64af33f3830a6`으로 불변이다. 원본 42개 key 좌표는 float32 hash로 대조했다. 참조 3장 packed, missing texture 0. 검사 중 native/source 파일은 저장하지 않았다.

첫 `independent-final-audit/`의 false는 감사 코드가 새 `coordinate_hash_float32` 필드를 구조 비교에서 제외하지 못한 오류였다. 명시적인 구조 키 비교로 수정하고 당시 같은 native SHA로 r2를 재실행해 기술 검사를 통과했다. 해당 이전 결과는 이력으로 보존한다.

Astra matrix/pose의 첫 실행이 부분 출력에서 끝나 v2로 복구했다. v2의 45+30 PNG 전체 decode·비공백·input SHA를 확인하고 canonical 폴더에 bit-identical 복사했다. 두 렌더 프로세스의 숫자 exit code는 미수집이며 exit 0로 주장하지 않는다. 별도 fresh native 감사와 frozen-input 비교의 exit code는 0이다.

후속 축 검증에서 기존 local-Z yaw가 실제로는 tilt임을 발견했다. Head/Chest yaw를 world-Z로, arm forward/raise를 실제 world -Y/+Z 이동으로 검증했다. arm-forward tail 0.140809m, raise 0.087262m; torso/head yaw의 실제 quaternion 축·각도와 pivot을 확인했다. 보정된 4프레임 생성 및 world-space fresh 감사는 exit 0이며 native는 동일 SHA로 불변이다. canonical pose JSON에 이 4프레임의 별도 renderer/utility provenance를 기록했다.

## 재현

현재 PC의 Blender 5.2.3과 원본 파일을 사용하는 PowerShell 명령이다. 저장소 루트에서 실행한다.

```powershell
$miaBlender = 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe'
$miaSource = 'D:/ai/Mia3DWork/model-v02/hair-surface-stage/Mia_HairSurface_v06.blend'
$miaOut = Join-Path (Get-Location).Path 'asset/mia/blender/mia-production-body-head-v06'
& $miaBlender --background --python tools/mia/blender/build_mia_body_head_v06.py -- --phase build --source $miaSource --output-dir $miaOut
& $miaBlender --background --python tools/mia/blender/render_mia_body_head_v06_matrix.py -- --input "$miaOut/Mia_BodyHead_v06.blend" --output-dir "$miaOut/final-matrix"
& $miaBlender --background --python tools/mia/blender/render_mia_body_head_v06_poses.py -- --input "$miaOut/Mia_BodyHead_v06.blend" --output-dir "$miaOut/final-poses"
& $miaBlender --background --python-exit-code 1 --python tools/mia/blender/audit_mia_body_head_v06_independent.py -- --source $miaSource --input "$miaOut/Mia_BodyHead_v06.blend" --output-dir "$miaOut/independent-astra-v09-world-audit"
```

빌드는 원본에서 새 파생본을 만들며 개선 헤드 helper를 한 번 적용한다. `astra_mia_fatigue_v08.py`도 함께 필요하며 두 helper의 hash는 `recipe-metadata.json`에 있다. 렌더/감사는 입력 native를 저장하지 않는다. 원본 Body/Face의 Rz180 object frame과 identity rig를 유지하고, keep-world parent 및 world-frame fitting을 사용한다.

저장 기준은 30fps, Standard / Medium High Contrast, exposure 0, gamma 1이다. 두 `MIA_FaceArt_*` identity 값은 1.0이며 표정 검사 중 유지한다. 이는 제작 기준 neutral/A-pose이고 최종 idle clip이 아니다.

## 남은 작업

미술 검수는 forehead/facial mask 비율, 눈매·공막 노출, profile의 코–입–턱–목 평면에서 원화 차이가 남는다고 판단했다. 이 차이를 사용자와 실제 그림 기준으로 교정한 뒤 별도 헤어·의상, 허용 포즈의 웨이트/보정·접촉·클리핑과 연속 프레임을 검증한다. 이전 실험과 v12 frozen native는 로컬 iterations 및 Git 이력에 보존했으며 중간 산출물을 승인본으로 승격하지 않는다.
