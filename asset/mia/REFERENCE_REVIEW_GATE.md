# Required source-view review gate

This is an execution requirement, including after compaction, not an optional illustration checklist. The v20 model-before/after boards did not by themselves satisfy source-art matching. Do not repeat that substitution.

## Before changing shape or paint

1. Read `CURRENT_STATE.json`, `REFERENCE_INDEX.md`, `WORKING_PROTOCOL.md` and this file.
2. Identify the exact source-art panels and baseline native. Record file hashes, crops and what is observable versus occluded or uncertain.
3. Register a corresponding view before judging proportions. Record projection, camera matrix, lens or ortho scale, pixel aspect, shift, frame, active shape keys, lighting, material mode and color management. A drawing's side/three-quarter label is not proof of 90/45 degrees. Preserve the estimated yaw/pitch/roll and uncertainty.
4. Use the same camera, pose, light and display transform for baseline and candidate. Registration allows only uniform scale, rotation and translation. Do not reshape a comparison image by feature or change the mesh per view.

## Required output for each candidate

- Face/head: source-art | baseline | candidate for front, profile, left oblique and right oblique; include a subtle-angle expression panel when used to justify the edit. For a covered or non-matching reference, explicitly label the limit; do not silently substitute a front view.
- Body: front, profile, back and oblique using Body Foundation and the selected front anchor, with covered-volume uncertainty stated.
- Surface: the same paired views in the target toon look, plus neutral geometry and color-only diagnostics sufficient to distinguish paint from light. Name the actual UV and connected image/shader route.
- A `reference-review.json` package: native hashes, required views, reference path/hash/crop, actual baseline/candidate render paths/hashes, comparison-board path/hash, camera/pose/light/color record, registration, observed differences and unresolved issues per view.
- Run `blender/mia-reference-finish-v22/validate_reference_review.py` against the package. It checks evidence integrity and coverage only. An independent visual judgment is still required. FAIL or UNVERIFIED art stays open even if the validator succeeds.

## Resume and integration

The current state must link the selected package and validation record. A producer's completion message, new version, native save, render count or preserved topology cannot replace this package. On resume, inspect the actual paired boards before another edit. Keep rejected candidates and their reasons; do not silently select a later file.

User-facing preview must state its camera mode. Keep a head-centred orbit view and a full-body view available. Do not move mesh origins or rig coordinates merely to fix navigation. Actual viewport evidence and saved-camera renders are distinct evidence types.
