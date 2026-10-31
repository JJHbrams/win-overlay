# Hair correction v20 — editable static candidate

Source is frozen BodyCorrection8e262, itself derived from immutable canonical873. Full hashes and all owners are in manifest.json. Geometry build, fresh-reopen preservation, clay and final-five-view commands exit0. No source native saved. No face/body/eye/rig/material/shape-key changes in this hair pass.

## Actual changes

- Seven old puck/core/wrap objects moved into hidden child collection MIA_V20_REJECTED_KNOT_ARCHIVE beneath MIA_V17_PIXAL_HAIR. Their original mesh data remains unchanged. Preserve both collection and object hide_render/hide_viewport flags during append; never force every object visible.
- Three independent tapered flattened C/S folded locks replace the puck. Width/depth/twist vary, roots/endpoints are ray-fitted under nearby original crown. Knot is smaller and less protruding, but its internal shape/strata still simplified relative to concept. It is not a finished art-approved knot.
- The previous smooth procedural crown pills were rejected. MIA_V20_Crown_PixalDonorLock duplicates adjacent original Pixal strand surface and both original UV/4096paintUV coordinates, shifts it14mm alongY and feathers boundary depth under neighbors. Actual source material/atlas retained. This is donor reconstruction, NOT recovery of missing original polygons.
- The complete unfiltered SOURCE_SINGLE_RAW was tested after original uniform fit: all3 diagnosed rays hit the opposite sideX<0. Thus this particular hole also exists in raw source, independently of prior extraction filters. raw-crown-inspection.json records actual raw source polygon hits. The new donor owns the3 near-side ray hitsX+.0566..+.0619.
- Original main Pixal122129faces and bothUV layers preserved. Lower rear19439vertices get bounded submillimeter positional noise polish; coarse source sheets, some jagged/torn ends and broader wave design remain unresolved. No blanket decimation, remesh or source paint edits.

## Ownership and limitations

Actual independent new owners: HalfUp_Fold_Left, HalfUp_Fold_Right, HalfUp_Binder, Crown_PixalDonorLock (all prefixed MIA_V20_). They are in the production hair collection with explicit owner properties; new knot UV is longitudinal. Original main Pixal is still one mesh with spatial vertex groups. Its giant connected surface crosses fringe/crown/side/rear; this pass does not claim a clean lock-based semantic split or future deformation readiness. Cutting the current groups would cut locks; further face-boundary ownership requires explicit seam correspondence and duplicated boundary vertices preserving source IDs/UVs/normals.

141 nonhair meshes/UV/keys remain byte-exact, including Body8e262.59 packed source images remain byte-exact. Original atlas and4096paintatlas unchanged. New procedural knot material only; source hair shader unchanged. Body lower oval breast border/high-hip concerns remain BODY ART FAIL; this hair pass does not close them. No animation or rig claims.

## Evidence

final-five-view-evidence.json ties all before/after front/profile/back/both45deg images to their actual saved hashes. Same ortho.52,targetZ1.475,1000square,Standard/None,exposure0,gamma1. Original emission toon beauty is not physical diffuse. before/after_clay_profile/back use18%diffuse override, neutral white camera-relative review lights and fixed settings. Diagnostic rendering never resaves native. Final native remains colored beauty with front camera.
