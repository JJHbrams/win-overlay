# WIP9 combined face review — not final likeness

## Current actual editor: M5 look added

Current native is `Mia_FaceReview_v22_WIP9_M5.blend`, SHA256 `c04f81985330eace7ba06142cb99419f7c043f680f8fcfbefefff237ece56778`. It is the byte-identical adopted copy of the inspected placement-corrected M5 candidate. It retains WIP9 geometry, UV, all keys and original packed map bytes; only the skin material slot7 changes. `m5-adoption.json` links the provenance. Actual MCP opened it from clean WIP9 and returned five fresh captures in `../live-wip-9-m5-review`; root inspected the head zoom. No native was saved by viewport review.

M5 adds a thin warm upper crease and a faint lower bright edge from measured eyelid UV curves. The first placement was hidden by the upper lash and is unselected. Actual lash clearance was measured before correcting the placement, with no contrast sweep. Root and independent reviewer inspected corrected lit/color-only front/oblique and blink evidence. The fold is a small visible improvement; it is still less shaped than the concept and does not solve the generic lower rim or broad under-eye pigment band. No new raster map is claimed.

Fresh final-native source comparisons are in `source-review-m5/face`; root inspected both obliques/profile and the front look. `eye-spacing-wip9-m5.png` retains height visibility. The M5 producer's `placement-corrected-review` contains actual paired half/full blink. Geometry is exactly WIP9, so its matte findings still apply.

| Requested outcome | Actual final state |
|---|---|
| Face proportions | Lower-face height improved in approximate eye-spacing calibration; overall width/shape not accepted. |
| Continuous cheek-to-jaw contour | **Unresolved.** Q10/Q11 rejected; WIP9 notch and profile wedge remain. |
| Source eye character | Upper/lower rim curves changed; tired gaze closer, source outer/lower finesse still incomplete. |
| Makeup/fatigue identity | Existing pigment strengthened and upper-fold layer added; source paint character not complete. |
| Technical preservation/deformation | Native reopened, scoped data preserved; limited actual blink checks only, not full animation validation. |

Overall art acceptance remains **FAIL / unfinished**. There are no further geometry or material producers running. Do not resume small coordinate-field trials as if the failed jaw task were solved.

## Earlier WIP9 / M4 checkpoint

Actual saved native: `Mia_FaceReview_v22_WIP9.blend`, SHA256 `fb85468a623e1befc590176a24636548b944491ce4ae19decaece625304945b2`.

This is a review checkpoint combining Q9 geometry, E2 eyelid contours and M4 material. It is now open in actual Blender through MCP; `../live-wip-9-review/live-review.json` records five real viewport captures and the unchanged native hash. Root viewed front/left-oblique captures. It does not complete Mia, the face art gate, texture authoring or expression validation.

## Actual changes and correction of prior reporting

- P2 had moved the actual mouth boundary down approximately 4 mm despite the earlier statement that the mouth was fixed. Q9 restores that measured displacement. Code intent was incorrectly substituted for a coordinate check; the earlier claim is retracted. Q9 also makes a separate bounded 1.2 mm cheek-width change; that is an artistic hypothesis, not an exact source measurement.
- Q7 replaces the cramped cage response with a dense rest-space bake and a connected anterior surface correction. All stored keys, UV and weights were carried through the bake. The old low-density native remains preserved. This improves the fragmented front-cheek plane locally but does not cure the whole jaw or muzzle.
- E2 changes the actual upper/lower eye boundaries and their lash followers. It removes the former single high upper bow and retains a shallow central arc with an outer change in curvature. Full-close geometry is retained; limited neutral/half/full renders are available. This is not all-expression or collision approval.
- M4 strengthens the existing under-eye pigment response and adds a short procedural UV fold. The three existing packed maps are preserved. No new raster maps, normal map or specular map are claimed.

## Root visual inspection

Read `source-review/face` source/baseline/candidate boards together with `eye-spacing-wip9.png`. The former keeps the historical uniform registrations and cannot validate a dimension normalized away; the latter uses approximate pupil-spacing anchors so the disputed eye-to-chin height remains visible. Neither method is a numerical art-acceptance score.

Actual combined front, both oblique and profile views were rendered using identical frozen cameras, light and display settings. Root inspected front, left oblique, profile and the eye-spacing board, plus actual bare matte front/left oblique and full blink. Independent review of the four source boards agrees that mouth position and lowered upper lid are local gains, while the major source gaps remain.

Remaining visible failures: lower cheek still forms a corner/notch before the small chin; mouth/chin is a forward wedge in profile; the nose-side vertical fold and outer orbital diagonal remain in matte; the outer upper eyeliner is too graphic and lower-lid curvature lacks the concept's character. The pigment is smoother and less articulated than the source. The broad-face impression is not declared solved.

The combined full blink has no new visible white leak in the inspected front render. This is limited visual evidence, not a collision solver. Body, hair and garments inherit WIP8 limitations.

## Evidence validity is separate from art

`source-review/evidence-validation.json` confirms artifacts, hashes, four-view coverage and declared equal camera/light settings. It explicitly returns `art_acceptance: NOT_EVALUATED`. `integration-manifest.json` records save/reopen and scope guards. Neither grants ART PASS.

`deformation-review-absolute` is the valid combined deformation/matte batch. The first `deformation-review` attempt used a relative render output path that Blender interpreted relative to the opened native; it failed before completing the manifest. Its log is retained as a failed run and must not be used as complete evidence.

## Next structural correction

Q10 and Q11 are REJECTED. Q10 section-envelope/depth blending introduced a new lower-cheek hollow and wrinkles. Q11 global X-only mapping softened the front outline but created conspicuous horizontal lower-cheek grooves and a crumpled mouth-corner patch. Producer and a separate actual-image reviewer both rejected it after paired front, oblique and profile matte/material inspection. Keeping Y unchanged and a positive Jacobian is insufficient to preserve acceptable surface-normal curvature. The exact recipes, deltas, audits and selected actual comparisons are archived in `../parts/face-anatomy9-jaw-rejected`. WIP9 geometry is retained; the jaw task remains unsolved. No further geometry candidates are running.

`material-audit` separately verifies actual evaluated UV and consumed packed maps against WIP8, and renders lit/color-only front/oblique. Root inspected the color-only front board: lower pigment is stronger, but the original upper crease and irregular fine/light contours remain absent. M4 is auxiliary look work, not finished makeup.
