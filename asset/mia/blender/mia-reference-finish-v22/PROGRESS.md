# Current handoff — Finish8 REVIEW ONLY

Read `static-finish-8/ACCEPTANCE.md`, `static-finish-8/REVIEW.md`, `asset/mia/CURRENT_STATE.json`, `WORKING_PROTOCOL.md`, `REFERENCE_INDEX.md` and `REFERENCE_REVIEW_GATE.md`. This is active source-style static modeling with actual maps, not heartbeat research. Historical progress is preserved in `PROGRESS-history-before-wip8.md`; its older face-only scope and WIP7 pointer do not override this handoff.

## Actual editor

`integration-wip-8-review/Mia_ReferenceFinish_v22.blend`, SHA `ff2b61b2b2146fc4f73119cf10534571609dff75f6333fbec34d0926068b8bb4`, is open in actual Blender MCP. It is a review checkpoint, not a completed or ART-approved model. Five rendered ORTHO MCP captures leave head center(0,0,1.55), distance0.63. Native bytes unchanged.32fresh source/diagnostic renders and3strict source packages are recorded in `integrated-review-wip-8`; actual saved-camera previews are in `production-preview-wip-8`.

## Current owners

- Face F2 `parts/face-finish8-f2-review` restores central cheek depth and lateral attachment on D. D's compact chin/nose and three consumed2Kpigment/masks are retained. Exact D→F2 replay and limitedblink/eye-boundary guards are recorded. Local recovery only: upper diagonal under-eye transition, nose/profile and whole likeness remain unfinished.
- Body23n `parts/body23n-work` changes lower/lateral thorax return only. Prior2KUVMap/pigment and common actual-light shader retained. No pelvis/glute/leg/neck improvement or newUV acceptance claimed. Failed unwraps remain unselected.
- Hair24 `parts/hair24-painted-work` adds three closed rear-curl owners with three consumed1024RGBA maps, hides but preserves old folds/binder, and preserves the main Pixal geometry. Bun height/concentric form and ear/nape extraction are unfinished.

## Active user feedback and next work

Latest: “볼이 너무 패인거아니야?” This was real missing support/abrupt depth transition, not merely makeup. D/E failed to restore the central volume; F added it but left a new side attachment band; F2 connects that support. Review images show a modest local gain, not full resolution. Preserve recovered high malar/central mass and existing eyes; do not globally flatten cheeks or fit each view independently. Upper orbital-to-buccal transition and source silhouette/profile are the next shape task. Whole-face normals/toon shading must be assessed against actual clay and source imagery, not used to conceal defects.

Camera/light/source comparison remains mandatory across front/profile/bothobliques and low/intermediate angles. Uniform SRT is frozen; no per-candidate refit or anisotropic stretching. Eye-to-chin normalization excludes that distance from measurement. Source profile yaw and hair occlusion are explicit uncertainties.

## Evidence corrections

Body producer source boards stretched width384→512 without height; root rejected them and rebuilt matched8renders using original SRT. A reviewer claimed glute improvement despite no glute deltas: rejected. BodynewUV per-face rescaling and later overlap/crash trials are unselected. Face white under-lid stripes were aperture-arc classification errors, fixed; mixed-lit cap color-only was replaced by corrected face+cap evidence. Mainhair4K map dimensions do not establish4K authored detail. Actual assigned-polygon shader audit reports12direct image datablocks/15materials, all packed, including duplicate bodyatlas; no invented specular-map completion.

## Reproducibility and gates

Root owns canonical integration/Git/liveMCP. Independent producers use separate existing worktrees. Original/failed natives remain preserved; exact selectednative hashes, maps, recipes, replay and diagnostics are archived. Original WIP7 remains unchanged. Face D checkpoint `a8d7dc9` was pushed; the enclosing commit adds this WIP8-review checkpoint. Allcritical ART gates remain unapproved; finalgarments/rig/events remain downstream. Do not infer PASS from successful save, imagecount, preservedUV, replay, subagentcompletion or this handoff.
