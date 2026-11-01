# Mia face foundation v27 — frozen working candidate

Native: `face-shared-final/Mia_Foundation_v27.blend`

SHA256: `e9c8654121307b61fb75d73789c9b2443a3e42c53420dfdfada927d194b475d4`

This is a reviewed working improvement, not final source-art acceptance or full motion-rig acceptance. Do not substitute intermediate `face-shared-head` natives (8c971/7ae354): their Body group mapping was defective. The corrected file above uses explicit original group-name mapping, verified independently.

## What is in the candidate

- Clean original Face foundation with connected cheek support, neutral mouth, source-guided eye width/iris ratio and thin independently owned upper/lower ink. Original donor cards are hidden. All 42 facial keys retained.
- Actual shared control topology: original Body3957 prefix plus Face690 appended vertices, 38 exact corresponding boundary vertices, one original Body Armature/Weld/Subsurf2/Smooth stack. Internal seam is uncreased. Weld is restricted to original Body vertices, preventing blink/lip contact from being arbitrarily welded.
- Original Body3957 named weights exact; original per-corner UV layers exact. Outside the shared boundary, all42 keys have identical original Body control coordinates. Original Body and original historical face owners remain hidden and preserved.
- New visible skin owner: `MIA_V27_SharedHeadBody`. Facial key master: `MIA_V27_Foundation_Face`. Four visible `BoundaryRibbon...Dense` owners follow the master keys and the same rig Head hierarchy. Their neutral Armature difference is only 0.000119mm; ±12-degree head tests have the same numerical residual.
- Actual face-UV fatigue/upper fold and thin lip/nostril pigment are packed. Head/upper-neck material blend uses the original rest Head-weight attribute; lower Body materials remain assigned unchanged. All14 consumed visible-material images are packed. Unused archive-image paths are separately listed.

## Authoritative evidence

- `final-source-frozen/face/`: four source/baseline/candidate boards and `reference-review.json`; evidence validator passed, ART is not evaluated by that validator. Same camera/light/display and original uniform SRT retained.
- `final-diagnostics-frozen/`: actual matte front/profile/both obliques/lowfront, half/full blink front/left, face pigment-only and face UV checker. All reopen the frozen native. **Color-only overrides face material slot0 only; cap/neck stay lit. It is not whole-head albedo-equality evidence.** Head color continuity is assessed in native lit renders and by the explicit mask route.
- `final-rig-body-proof-matched/`: ±12-degree Head pose images/rig-follow errors, full-body baseline/candidate with Freestyle disabled for both. Earlier `final-rig-body-proof/` body images had unmatched Freestyle settings and are not the matched comparison.
- `face-shared-final/shared-correspondence-audit.json`: bidirectional evaluated Body correspondence. Below both Z1.35 and1.40, max position discrepancy0.000357628mm, vertex counts56927/60135 equal, corresponding evaluated corner UV difference0. Body changes above1µm occur only within world bbox `[-.076159,-.037081,1.460778]` to `[.075375,.052248,1.643094]`m. Whole head max nearest-vertex change7.64598mm. These are coordinate/UV checks, not artwork approval.
- `face-shared-final/body-weight-audit.json`, `shared-head-audit.json`, `integration-finish-audit.json`, `packed-image-audit.json`, `evaluated-contact-audit.json`.

## Portable reconstruction

`replay-package/` is the authoritative small reconstruction package. `face-owners.blend` contains only the six new visible owners and their new dependencies (~3.1MB compressed), not a duplicate full native. Original materials, rig and modifier references are restored from the immutable baseline by name.

Run Blender background with `replay-package/replay_face.py -- --source <exact c04 WIP9_M5 native> --output-dir <fresh directory>`. The script guards source SHA and package SHA, sets all new keys0, restores original visibility and scene color/Freestyle settings, and verifies all six owners' key-coordinate/topology/UV/weight/material/transform fingerprints before saving. A fresh real replay is recorded under `replay-verification-final/`; do not archive its giant duplicate native. Include its JSON audit records only.

Final fresh replay verification also matches all six **evaluated coordinate and loop-UV arrays byte-for-byte**, max evaluated UV error0.0. The earlier replay without restored scene render settings had a UV hash discrepancy and is superseded by this complete replay. Frozen native e9 was never changed for this check.

Construction recipes worth retaining for provenance: `build_shared_head.py`, `shared-boundary-map.json`, `finish_shared_integration.py`, `seat_shared_head-final.py`, `final_eye_proportions_r2.py`, `refine_ribbon_r3.py`, `paint_actual_uv_r3.py`. These document sculpt/integration steps and reference producer checkpoints; use the portable package for baseline-to-final reconstruction.

Evidence recipes: `render_diagnostics_frozen.py`, `render_rig_body_proof.py`, `audit_shared_correspondence-final.py`, `inspect_join_weights-final.py`, `audit_frozen_package.py`, `export_replay_package.py`. The source4 renderer/composer/validator are the existing canonical v22 helpers; their exact dependencies and hashes are recorded in the frozen review manifests.

## Remaining limits

Source drawing has stronger eye-underlining/blush, outer-tail definition and nose-plane information than this working candidate. Existing hair-card extraction/temple mismatch and lower-neck/body facets are retained outside this face task. Full-expression and whole-motion rig validation are not claimed. No further cheek hollowing is justified by the reviewed images. Original live/canonical/Git/Wiki were not modified by this producer.
