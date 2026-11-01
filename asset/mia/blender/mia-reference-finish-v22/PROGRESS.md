# Current handoff — whole-face anatomy and identity correction

Read `face-anatomy-9/ACCEPTANCE.md`, `face-anatomy-9/DIAGNOSIS.md`, `asset/mia/CURRENT_STATE.json`, and the reference protocol. This handoff supersedes the earlier cheek-only instructions in `PROGRESS-history-before-face-anatomy9.md`. The user explicitly identified broad/short proportions, an abrupt cheek-to-pointed-chin taper, incorrect eyelid curves, and weak fatigue/makeup character. Exact old jaw/eye positions are NOT protected design targets.

## Actual editor and preserved baseline

Actual Blender now contains `integration-wip-9-review/Mia_FaceReview_v22_WIP9.blend`, SHA `fb85468a623e1befc590176a24636548b944491ce4ae19decaece625304945b2`. Root opened it through actual MCP and inspected viewport front/left oblique; five captures and unchanged native hash are in `live-wip-9-review`. This is unapproved working review, not a completed Mia. Immutable WIP8 remains at `integration-wip-8-review/Mia_ReferenceFinish_v22.blend`, SHA `ff2b61b2b2146fc4f73119cf10534571609dff75f6333fbec34d0926068b8bb4`. Body23n/Hair24 remain unfinished.

## Active work and evidence

- Earlier P1/P2/P3 trials are not standalone selected results. P2 actually moved the mouth boundary down4mm despite earlier root claims that it was held fixed. Q9 restores the measured error while retaining the useful chin extension; the incorrect claim is explicitly retracted in DIAGNOSIS.md.
- Small exact trial evidence and historical recipes are in `face-anatomy-9/unselected-v25`. Large original natives are preserved in the producer worktree. These historical absolute-path recipes are not claimed portable replay.
- `face-anatomy-9/eye-spacing-p2.png` displays unchanged art/render pixels with uniform pupil-distance calibration. Unlike eye-to-chin registration, it exposes the disputed face height. Manual landmarks and pose/hair uncertainty are explicit; numerical ratios are not automatic art gates.
- Q7 dense rest-space bake retains keys/UV/weights and makes a local connected anterior-surface improvement. Q9 repairs the actual mouth shift and makes a bounded1.2mm cheek taper. Exact replay packages and source/matte evidence are archived in `parts/face-anatomy9-q7-working` and `parts/face-anatomy9-q9-mouth-repair`. These are actual local gains, not full facial-anatomy completion.
- E2 reshapes actual upper/lower eyelid arcs with lash followers; M4 strengthens consumed fatigue pigment and a short procedural outer fold. Combined WIP9 has fresh source4views, bare matte, neutral/half/fullblink and lit/color-only evidence. See `integration-wip-9-review/REVIEW.md`. The source upper crease/irregular light-and-fine lines remain absent. No new raster/normal/specular map is claimed.
- Q10 section/depth loft and Q11 global X-only jaw mapping are both REJECTED. Q10 adds a hollow; Q11 improves the outline but creates visible horizontal lower-cheek grooves in matte and the actual material. A positive mapping Jacobian and unchanged Y do not prevent undesirable surface-normal curvature. Exact failures are archived in `parts/face-anatomy9-jaw-rejected`; no more geometry variants are running. WIP9 geometry is retained as partial work, with jaw failure explicitly open. A separate measured-UV upper-fold M5 look is being evaluated under `face-anatomy-9/material-work/upperfold-m5`; it is not selected yet.

## Required next decisions

Choose by actual source/front/profile/both-oblique and continuous matte evidence, not by version or producer completion. Preserve camera/light calibration and all original natives. Change eye aperture, skin, lash and visible eye surface together when needed; then inspect neutral/half/full blink. Equal Basis deltas do not automatically prove expression contact. Integrate only a visually useful result and verify the saved actual native through MCP before changing the editor pointer. Root owns integration, Git and Wiki.

Geometry, makeup and render evidence must remain distinguishable. Never infer completion from a successful save, generated-map dimensions, unchanged UVs, a reduced numerical residual, render count or subagent completion. The whole Mia body/head/hair finish and animation are still incomplete.
