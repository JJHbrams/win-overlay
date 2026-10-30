# Mia 드래프트 도구

## v45 상태: 기계적 드래프트만 통과

`mia-rig-draft-v45/Mia_RigDraft_v45.blend`는 최종 Mia 모델이 아니다. 저장된 Idle/Turn/Click 3개 클립은 좁은 범위의 기계적 재생 시험일 뿐이며, 예술·기하 수용 기준은 **FAIL**이다. 실제 다각도 clay 점검에서 얼굴의 열린/절단된 표면, 정면 투영에 가려진 중복 strap/pin/braid, 원화와 다른 상체 볼륨 및 불완전한 후두부 헤어가 확인되었다. 이전 보고서나 시퀀스를 수정해 이 실패를 감추지 않는다.

다음 단계의 기준은 `audit_multiview.py`의 source-as-saved/clay 진단과 사람의 버전-고정 리뷰다. 오브젝트 수·밝기·프레임 수만으로 품질 PASS를 선언하지 않는다.

Blender 5.2.3에서 만든 v45를 기준으로 한다. 저장소 루트에서 실행한다. 최종 `.blend`와 참조 이미지는 패킹되어 있으므로, 과거 로컬 GLB/체크포인트 없이도 최종 파일을 다시 렌더할 수 있다.

## 저장된 리그 다시 렌더

```powershell
$miaBlender = 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe'
& $miaBlender --background --disable-autoexec --python tools/mia/blender/render_trial_action_sequences.py -- --input asset/mia/blender/mia-rig-draft-v45/Mia_RigDraft_v45.blend --output-dir artifacts/mia-v45/sequences --report artifacts/mia-v45/sequence-report.json --render
python tools/mia/blender/png_sequence_to_webp.py --frames-dir artifacts/mia-v45/sequences/idle --output artifacts/mia-v45/Idle_90f.webp
```

WebP 변환에는 Python 3와 Pillow가 필요하다. PNG 시퀀스는 고정 카메라의 30fps·512×768 RGBA다. `--render`를 생략하면 포즈/액션 검증만 하고 프레임을 렌더하지 않는다. [추가 설명](README-sequence-export.md)

## 모델링 단계

- `import_generated_candidate.py`: 외부 GLB의 원래 메시/UV를 가져온다. `--reference-dir` 기본값은 저장소의 `asset/mia/references`다.
- `project_head_art.py`, `project_generated_body_art.py`: 원화 투영. 몸체의 `--front-art`/`--back-art` 기본값은 `asset/mia/references/conditioning/`다.
- `graft_generated_head.py`: 이름으로 몸체/머리 소유권을 확인하여 통합한다.
- `build_mia_rig_mechanism.py`, `build_mia_rig_trial_binding.py`: FK/IK 시험과 초기 스키닝. 최종 수리된 파일에 초기 바인더를 다시 실행하면 보정 가중치를 덮어쓰므로 주의한다.
- `arm_weight_boundary_trial.py`: 초기 바인딩을 별도 복사본에서 보정하고 실제 포즈 전후를 비교한다. 심 정점의 가중치 보정 근거는 번들의 audit JSON에 있다.
- `add_trial_actions_and_render.py`: 보정된 리그에 Idle/Turn/Click 시험 액션을 만든다.
- `toon_generated_candidate.py`: 기하를 유지한 toon 검토 렌더.

`graft_generated_head.py`는 v45 계열의 과거 실험 재현용이며 **새 foundation/제작 경로에서는 사용 금지**다. 색/좌표 ROI로 얼굴을 절단하는 방식은 보이는 이마·눈·관자놀이를 보호하지 못할 수 있으므로, 이 도구를 새 해부학 마스터의 복구 도구로 해석하지 않는다. 이는 현재 v45 손상의 가능한 경로를 단정하는 것이 아니라, 재발 방지용 경계다.

## 저장하지 않는 다각도 점검

```powershell
& $miaBlender --background --factory-startup --disable-autoexec --python tools/mia/blender/audit_multiview.py -- `
  --input asset/mia/blender/mia-rig-draft-v45/Mia_RigDraft_v45.blend `
  --output-dir artifacts/mia-v45/multiview --report artifacts/mia-v45/multiview-report.json `
  --manual-review asset/mia/blender/audits/v45/manual-review.json
```

이 도구는 0–330도 궤도, full/torso/head 배율, 상·하 시점을 저장된 재질과 이미지/normal 노드를 쓰지 않는 neutral clay로 렌더한다. 입력 파일 SHA-256 전후를 검증하며, 기본 gate는 언제나 `UNVERIFIED`다. 수동 review JSON은 정확히 같은 `source_sha256`에만 묶여 사용된다.

외부 GLB의 새 재구성에는 별도 로컬 ComfyUI/모델이 필요하며, 이 저장소는 그 체크포인트나 모든 이전 실험본을 배포하지 않는다. 세부 생성 기록은 자산 번들의 `provenance/`에 있다. 전 동작 범위·손가락·표정·충돌 검증까지 완료된 제작 도구로 간주하지 않는다.

## v02 얼굴 제작 접근 재평가

`experiments/v02-procedural-rejected/`는 원화 닮음에 실패한 절차적 얼굴 실험의 보존본이다. 자동 생성 얼굴 표면/CDT·스무딩·접합 반복을 표준 버튜버 제작 공정으로 설명하거나, 다음 Mia 얼굴 제작 기반으로 자동 선택하지 않는다. 실패 native/key view는 `asset/mia/blender/audits/v02/rejected-procedural-face/`에 있다.

후속 제작 계약은 `model_v02_contract.json`에 있다. 출처·권리를 검증한 anime 얼굴 topology와 눈·눈썹·속눈썹·texture·toon/normal·Shape Key를 함께 편집하고 구조 QA와 작화 QA를 구분한다. 얼굴 부품의 일체 봉합을 의무로 삼지 않는다. 기존 실패는 PASS로 재분류하지 않는다.
