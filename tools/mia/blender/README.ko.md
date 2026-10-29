# Mia 드래프트 도구

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

외부 GLB의 새 재구성에는 별도 로컬 ComfyUI/모델이 필요하며, 이 저장소는 그 체크포인트나 모든 이전 실험본을 배포하지 않는다. 세부 생성 기록은 자산 번들의 `provenance/`에 있다. 전 동작 범위·손가락·표정·충돌 검증까지 완료된 제작 도구로 간주하지 않는다.
