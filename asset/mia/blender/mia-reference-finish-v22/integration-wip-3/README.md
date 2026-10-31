# Mia v22 surface WIP3 — not completed anatomy

Editable native: `Mia_ReferenceFinish_v22.blend`.
SHA256: `fc939a759707cace22a71012aa9c422c263e8e611be6828198110bc419059e05`.

This combines locally reviewed Face5 under-eye pigment, hair0d UV paint, and the interim continuous Body5 mesh. Body5 is not an accepted source-matched body. Body8–11 were rejected for lower ledge and broad upper masses; no rejected replacement was silently promoted here.

Face5 changes only a fixed-UV lower-lid crescent relative to Face4. Geometry, iris, lashes, lighting and packed69 image bytes remain unchanged. The oblique displayed under-eye/cheek ratio moved from1.010 to0.839; this is an image contrast observation, not physical reflectance. Face width/profile/identity and expression gates remain FAIL.

Hair0d adds selected directional pigment and sheen to the existing UVs. Its generated source is512px per view, not4K recovered detail. Main hair/crown use the new pigment while other hair material owners retain the396 cleanup treatment. Root specks, rough lock edges, braid/knot geometry and eye occlusion remain unresolved.

## Actual review

- `../integrated-review-wip-3/`: fresh source|c02|WIP3 in14 views plus6 UV/color/minimal-blink diagnostics. Same baseline/candidate cameras, lights, pose and display; comparison Freestyle OFF.
- `../production-preview-wip-3/`: three actual saved-camera renders with the saved skin contour pass. These are separate from the matched comparisons.
- `../live-wip-3/live-review.json`: actual Blender MCP open and five head/body/view/zoom captures; final head-centred ORTHO pivot(0,0,1.55), distance.63. Native hash unchanged. No origin, geometry or global preference change.

The selected-front body supplement in this initial review inherits an erroneous source shoulder landmark. It used Y350 rather than roughlyY290–295, yielding about6.7% excess source scale. Do not use this supplemental board for proportions. Original v06 four-view scale is unaffected by this branch, but its per-column lateral layout is not exact torso-axis registration. Both limitations are being corrected in the next body package. No drawing is treated as an exact orthographic anatomical blueprint.

## Replay and protection

`frozen-inputs.json` resolves from its own directory and defaults to a new sibling output; `exact-integration-recipe.py` and helper snapshots are preserved. Run Blender with `--python-exit-code 1`. Do not overwrite this frozen native.

The transfer preserves target body object/rig/modifiers/material route; remaps the face cap through old-to-new vertex IDs; verifies cap UV loops, weights, topology and polygon material indices before and after slot replay; and leaves unrelated face/hair geometry unchanged. Packed editable maps remain in the native. These checks do not establish art quality.

Code review also closed stale source-package reuse during diagnostics, composition of mismatched render bytes, body UV inspection after clay override, and overwriting a dirty live document. The two provenance rejection tests are in `../review-guard-tests/result.json`. Source art and native originals were not changed by those tests.
