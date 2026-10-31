# v17 review and v18 reopening

This records actual reviewer findings, not final-character approval.

## v17d review

Input: `uv-refined/Mia_HeadHair_v17d.blend`, SHA256 `41e198b13c75fe1fe4f6883b08df4fbbb6b3ccc141c0df934709fe1c8c047d82`.

- AC1: technical preservation passed for the scoped hair-UV integration.
- AC2: failed. Broad/blunt rear ends, simplified half-up knot and small detached remnants remained.
- AC3: unverified. Static geometry and rendered views do not establish final reference fit or contact under deformation.
- AC4: earlier static approval **reopened** following the user's oblique-face feedback. v18 clay and live MCP views confirm an orbital-to-cheek geometry defect. No current art PASS.
- AC5: failed for hair appearance: too dark and low-contrast against the reaffirmed portrait. Face fixed-UV and hair UV transfer checks are separate technical results.
- AC6: scoped static ownership only. Crown/fringe/rear groups in the main Pixal object are spatial regions, not cleanly separated lock topology or final weights.

## v18 measured diagnosis

Source native unchanged. Face has 728 control vertices / 1342 triangles, evaluated to 16,338 vertices / 16,104 faces with Subdivision level 2. There are 47 shape keys, smooth polygons and no custom-normal attribute.

At x = +55 mm, the orbital/upper-cheek sampled surface normal turns about 50.23 degrees over z = 1.542 to 1.532 m, with approximately 8.82 mm recession over the following sampled 20 mm span. The ledge persists in clay. More global subdivision is not a demonstrated remedy.

Bare crown z = 1.64521 m, eye opening center about 1.5393 m, chin about 1.46656 m: crown-to-eye is about 106 mm and eye-to-chin about 73 mm. This does not prove the crown must be raised. Broad/flat shape and the hair frame require separate inspection.

Evidence is in the face producer's `mia-face-head-diagnostic-v18` directory and root `live-face-v18` MCP captures. Additional upper-oblique concept art can reduce ambiguous depth choices, but is not a prerequisite to correcting the observed surface defect. Generated views derived from the model would not independently validate it.

## Evidence exclusions

- `uv-refined/live-mcp/` is a rejected open attempt: its captures show the earlier v17c scene. The evidence JSON explicitly marks this stale. It is not v17d proof.
- `uv-refined/live-mcp-confirmed/` successfully opened v17d after the user authorized discarding test-only view state.
- Paint-source imagegen images are painting inputs, not 3D renders.
- `tone-study/` is rejected for excessive brightness/pinkness, not the selected hair appearance.

New face/hair candidates require fresh integrated review. Technical hash preservation, render completion, and region labels alone cannot change an art criterion to PASS.

## v18 integration and v19 registered review

The integrated v18 native is SHA256 `87334607c76f6c0e876807f10ff407e8ce60fc7055265ae3591257893ba7b88d`. Live MCP integration preserved140 non-hair mesh records, then a fresh reopen produced44 actual views with the native hash unchanged. These are technical results only.

The user rejected the sufficiency of partial ratio checks and requested proper corresponding-view comparison, camera/light control and renewed body validation. The resulting front S/R/T registration, four-view art comparison, controlled body clay and lookdev diagnostic rig are documented in `../mia-reference-validation-v19/README.ko.md`. Overall art remains FAIL. The earlier unregistered review's “chin too long” direction is withdrawn: under the specified visible-pupil metric the model's mouth-to-chin ratio is smaller. This is not an instruction to change it from one image alone.

Body breast/pelvis/neck transition issues are explicitly open. The face and hair update cannot inherit or imply a body art PASS. Task entry rules now point to `asset/mia/WORKING_PROTOCOL.md` and `CURRENT_STATE.json` after compaction/handoff.
