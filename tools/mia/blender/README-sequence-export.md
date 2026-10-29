# 고정 카메라 시퀀스 내보내기

저장소 루트에서 실행한다. Blender 경로는 설치 위치에 맞게 변경한다.

```powershell
$miaBlender = 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe'
& $miaBlender --background --disable-autoexec --python tools/mia/blender/render_trial_action_sequences.py -- --input asset/mia/blender/mia-rig-draft-v45/Mia_RigDraft_v45.blend --output-dir artifacts/mia-v45/sequences --report artifacts/mia-v45/sequence-report.json --render
python tools/mia/blender/png_sequence_to_webp.py --frames-dir artifacts/mia-v45/sequences/idle --output artifacts/mia-v45/Idle_90f.webp
```

`--render`를 지정해야 실제 프레임을 만든다. 기존 Idle_90f/Turn_60f/Click_30f 액션과 공통 시작/끝 포즈를 검사하고, 30fps·고정 카메라·512×768 투명 PNG로 내보낸다. 각 클립의 보정 참조는 자산 번들의 단일 `canonical-idle.png`다. 이 보정과 재렌더 성공은 손가락·얼굴·충돌 등 미완료 항목의 통과를 의미하지 않는다.
