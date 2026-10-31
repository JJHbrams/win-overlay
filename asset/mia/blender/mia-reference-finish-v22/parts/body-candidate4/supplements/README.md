# V22 candidate 4: continuous anterior thorax, frozen for independent review

Native: Mia_BodyContinuous_v22_candidate4.blend
SHA256: e9fef86d16f3020d3dff513a1306acad6d6c218d25ff40c1822e64645349159a
Source c02 SHA256: c02b8ad73b86b278f2768e61eff019be223a8828bd92df62ce0ab7cb60f56936
Status: UNSELECTED, pending independent source-art review. Technical preservation PASS is not art PASS. Candidates 1/2/3 remain archived and rejected, with separate evidence packages.

## Actual construction
The anterior thorax is a continuous replacement patch, not two attached breast islands. 379 old faces / 337 old interior vertices were removed; 3569 retained vertices map exactly by source_to_new_preserved_vertices in patch-provenance.json. There are 388 new vertices, 365 quad and 98 triangle faces. The 54 original boundary edges remain shared, each incidence 2. No new body holes. Original mesh datablock remains archived with fake user.

The height-field controls in surface-control-net.json use a source-sternum-informed thorax base and bilateral smooth asymmetric fullness. Exact boundary and one exterior source ring fit a thin-plate residual surface, with zero correction interior anchors. This replaces the candidate 3 local original-triangle collar interpolation that retained upper crescents/lower scallops. The exported boundary controls and exact recipe are included. These authored dimensions are a visual hypothesis, not precise measurements inferred through clothing.

## Source comparisons and limits
reference-review.json has mandatory front/profile/back/oblique plus selected-front anchor. Every view supplies SOURCE ART | c02 BASELINE | CANDIDATE 4, exact paths/hashes/crops and identical model camera/light/pose. Only uniform registration and translation are used. comparison_close_* magnifies the same panel crop without per-part warping. The v06 turnaround is a reference candidate; selected front is a clothed anchor, not approval of exact bare anatomy. Illustrated camera, arm abduction, pelvis tilt, clothing compression/support and hair occlusion remain uncertain.

Actual profile and 3Q show a much more continuous upper ramp and lower return, and no complete closed pad rim. Lower outline remains more tapered than the supported reference bra silhouette. Front reads softer and less laterally full than the clothed source; the actual x=.06 section shows greater forward depth than baseline, so soft shading must not be confused with reduced forward projection. Exact chest silhouette/volume acceptance remains with independent review.

## Whole-body residuals (not corrected by this patch)
Back, pelvis, thighs and neck are unchanged. Source back suggests fuller hip/upper-thigh and calf silhouettes than the current model, but illustrated pose and clothing vary. Existing front high-hip/crotch-to-thigh transitions remain abrupt; profile pelvis/glute contour and high-hip plane still need coherent review. Neck/back are largely hair-occluded in source; unchanged neck thickness and shoulder transition are not validated by this chest result. Hair/skull discrepancy in review panels is intentional hair hiding for body evaluation, not a head modeling claim.

## Verification and integration
protected-owner-audit.json: no errors. All 3569 retained control positions exact, all 183 headcap source IDs retained and exact; 2714 evaluated cap positions equal at 1e-6 rounding. Outside faces/UV/material slots/weights exact. Nonbody meshes, shape keys, weights, transforms; material nodes/defaults/links; packed image hashes unchanged. Body groups and object/rig relation retained. Source native hash unchanged. Source material/image fake-user retention is the only intentional datablock bookkeeping difference.

actual-sections.json/png: real control/evaluated intersections at x=.06 and z=1.28/1.32/1.36; outlines excluded, inherited body deformation/subdivision retained. Curves are evidence, not acceptance criteria.

Integrate by replacing only body meshdata and copied vertex weights/group names on the destination body object. Retain destination object transform, parent, rig relation and modifier stack. For independent face headcap edits, map every old vertex ID through source_to_new_preserved_vertices and transfer only approved headcap coordinates. New patch vertices have nearest source triangle + barycentric UV/weight provenance. Original outer-face UVs/weights are exact; reconstructed patch UV/weights are approximate and require texture/deformation review. Do not transfer this native's nonbody data over the face owner's changes. Root handles common body shader after selection; this candidate introduces no material-content edits.

## Educational provenance
Proko official public lesson notes: https://www.proko.com/course-lesson/how-to-draw-breasts-form-and-motion/
Access: public written Lesson Notes only; no premium/video content accessed. General reference for ribcage attachment and soft pec/axilla flow, not a character-specific measurement or endorsement.
