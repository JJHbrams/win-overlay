# Mia WIP4 — Face6 and Body14 local corrections

Editable native: **Mia_ReferenceFinish_v22.blend**. SHA256 `7377542702efb4b65b11011ad2bfee1321ef765730d834e518b042c4e2c02cee`.

This is the current local/editor WIP, not a finished or approved character. It combines independently recommended Face6 continuous lower-cheek shaping and Body14 thorax/breast primary form with existing hair0d. Hair3a8's folded tip and d195's detached smooth terminal/failed UV were rejected; neither is integrated.

Face6 moves the lower lateral cheek and matching headcap together, reducing the source-mismatched flare while preserving eyes, iris, nose, mouth and upper orbital rim. Source-relative width improvement is modest; upper temple/cheek planes and nose paint still differ. Forty-one headcap source IDs differ from c02 in the combined face input; the new Face6 increment touched24. Cap UV/weights/topology/material indices remain intact through the Body14 ID map.

Body14 restores rounded lower projection and a gradual upper thorax connection, removing the previous pointed/horizontal lower shelf. Front and oblique retain overly uniform ovoid lower/outer rims. The supported/covered source does not define exact unclothed underfold anatomy. Pelvis/groin and neck remain unfinished.

Actual checker review exposes enlarged cells across the breast masses and compression underneath compared with WIP3. No UV completion claim: the preserved UV layout still needs distortion/texel-density work after the primary form settles. Face UV and the limited Close0.5/Fun0.25 checks are local smoke evidence, not a completed expression rig.

## Actual evidence

- ../integrated-review-wip-4: fresh c02 versus73775427 source-paired14 views plus6 diagnostics. All three package validators report evidence_valid=true and art_acceptance=NOT_EVALUATED.
- ../production-preview-wip-4: saved-native camera/light/material renders at900px, including render-only contour.
- ../live-wip-4: actual Blender MCP front/profile/oblique/zoom/body captures. Head-centred ORTHO; source native SHA unchanged. No origin/preferences changes or native save during review.
- ../independent-wip4-review.md: actual-image review of combined face/headcap/neck/body/hair and residual failures.
- integration-manifest.json and frozen-inputs.json: exact input ownership/hashes, body mapping, all12 hair material routes, executable recipe and helper copies. No hair objects shared mesh datablocks in these inputs; the production integrator now isolates any shared mesh before DATA-linked material replay.

Body comparisons use the corrected selected-front scale and v06 per-panel torso-axis translation. Earlier WIP3 front_anchor was6.7% oversized and must not support proportion judgments. Uncertain artwork yaw/pose/support remains explicitly recorded.

The native keeps anatomy and hair as separate owners. Garments, final rig and event animation remain deferred. AC2/AC3/AC4 remain FAIL. Reproduction and review integrity do not override that assessment.
