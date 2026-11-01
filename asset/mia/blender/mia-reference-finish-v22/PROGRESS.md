# Current handoff — whole-face anatomy and identity correction

Read `face-anatomy-9/ACCEPTANCE.md`, `face-anatomy-9/DIAGNOSIS.md`, `asset/mia/CURRENT_STATE.json`, and the reference protocol. This handoff supersedes the earlier cheek-only instructions in `PROGRESS-history-before-face-anatomy9.md`. The user explicitly identified broad/short proportions, an abrupt cheek-to-pointed-chin taper, incorrect eyelid curves, and weak fatigue/makeup character. Exact old jaw/eye positions are NOT protected design targets.

## Actual editor and preserved baseline

Actual Blender still contains `integration-wip-8-review/Mia_ReferenceFinish_v22.blend`, SHA `ff2b61b2b2146fc4f73119cf10534571609dff75f6333fbec34d0926068b8bb4`. It is unapproved WIP, not a completed Mia. No anatomy9 trial has replaced it yet. Body23n, Hair24 and all earlier known failures remain unchanged; their current status is in CURRENT_STATE.json.

## Active work and evidence

- Whole-face proportion tests P1/P2 and eye-only P3 are unselected. P1 moved the mouth too far down. P2 improves the short V locally but looks heavy below the mouth. P3 changes eyes slightly; despite its filename, it does not change the middle face. Root and independent reviewer inspected the actual bare matte and still see diagonal creases and fragmented front-cheek/mouth/chin forms.
- Small exact trial evidence and historical recipes are in `face-anatomy-9/unselected-v25`. Large original natives are preserved in the producer worktree. These historical absolute-path recipes are not claimed portable replay.
- `face-anatomy-9/eye-spacing-p2.png` displays unchanged art/render pixels with uniform pupil-distance calibration. Unlike eye-to-chin registration, it exposes the disputed face height. Manual landmarks and pose/hair uncertainty are explicit; numerical ratios are not automatic art gates.
- A new connected midface producer works in `mia-final-face-v12/.../mia-face-connected-v26`. It must restore the broad orbital-to-malar-to-front/side cheek and mouth mass, rather than adding another isolated bump. Old arbitrary upper-malar vertex locks and frozen two-ring boundaries are superseded by actual feature/contact review.
- Material trials in `face-anatomy-9/material-work` leave geometry/UV/keys unchanged. WIP8's three packed maps exist and are consumed. Their appearance lacks a separate source-like fatigue/fold hierarchy. Shader trials are not new raster maps or finished source likeness; assess them after geometry and actual color-only/lit comparison.

## Required next decisions

Choose by actual source/front/profile/both-oblique and continuous matte evidence, not by version or producer completion. Preserve camera/light calibration and all original natives. Change eye aperture, skin, lash and visible eye surface together when needed; then inspect neutral/half/full blink. Equal Basis deltas do not automatically prove expression contact. Integrate only a visually useful result and verify the saved actual native through MCP before changing the editor pointer. Root owns integration, Git and Wiki.

Geometry, makeup and render evidence must remain distinguishable. Never infer completion from a successful save, generated-map dimensions, unchanged UVs, a reduced numerical residual, render count or subagent completion. The whole Mia body/head/hair finish and animation are still incomplete.
