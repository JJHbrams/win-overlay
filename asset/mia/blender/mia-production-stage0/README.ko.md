# Stage 0 — 실제 source 비교

다섯 후보의 원본 SHA, preview root 변환과 실제 active/evaluated camera는 `source-inventory.json`에 있다. 머리 프록시는 정확한 해부학 landmark가 아니며 원화도 엄밀한 정투영이 아니므로 크기 차이는 정성적으로 판독한다. source shader는 actual pass에 유지하고 clay를 별도로 확인했다.

- `head-review-actual.png`, `head-review-clay.png`: 머리 다각도 비교.
- `full-review-actual.png`: 전신 후보 정/측/후 비교.
- `mia-stage0-native-comparison-reviewed.blend`: 실제 재열기 확인. 한 후보가 기본 표시되며 다른 후보는 collection으로 전환한다.
- 부위별 판단: `../mia-animation-production-workflow/part-decisions.md`.

재현 순서: `build_mia_stage0_comparison.py`로 원본을 무저장 import/append해 비교 장면을 만든다. 그 장면을 background Blender에서 열고 `render_stage0_full_frames.py -- <absolute-output-directory>`를 실행해 전신 프레임과 기본 표시 상태를 마무리한다. `make_stage0_review_boards.py <directory>`는 원본 렌더를 변형 없이 배열한다.

이 비교는 후보 전체의 아트 승인이나 rig-ready 판정이 아니다. 실제 다음 결과는 Stage 1 디자인 검토본이다.
