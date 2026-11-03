# Profile AP registration audit — solve1 stopped

Root stopped the one bounded five-shape RAM attempt. Its24-iteration budget
had finished before process termination; final envelope/protection verification
was interrupted. No mesh, native, render, bake or model displacement was saved.
The terminal parameters are an **unselected failed diagnostic**, not a source
fit or anatomical impossibility result. Do not restart from them automatically.

The initial full-profile edge constraints showed39–57mm placement errors beyond
the2px bands on the front edge and22–25mm on the rear edge. Width-only fitting
would hide this. Shared profile pitch reached its allowed bound, RY shift60mm
and fan scale.8 reached bounds; the final coarse worst violation remained
36.201mm. No AP translation or source SRT/pose widening was applied. All39
curve boxes/78 inequalities, initial and terminal seeds and incomplete-proof
flags are preserved in ignored canonical cache `shape/solve1-stopped.json`.

## Where568 came from

All paths below are relative to canonical
`D:/MiaWorkCache/mia-reference-work/win-overlay/asset/mia/blender/mia-fit-v003/`.

1. `body/compose_current_source4.py:8` declares literal
   `centers=dict(front=239,profile=568,back=935,oblique=1317)`.
   Line16 describes horizontal pelvis centering but performs no pelvis,
   ankle, silhouette or bbox landmark calculation deriving568. The profile
   crop440..750 has midpoint595, so568 is not a proved bbox midpoint either.
2. That script computes only common scale and vertical translation from the
   front alpha crown/sole: source54/950 and current49/943 give
   `s=896/894=1.0022371365`, `dy=4.8903803132`.
3. `underwear-fit/run_blender_check.py:33–40` reads this horizontal reference
   center and emits `renderX=(sourceX-568)/s+400`. Forward scale is
   `.9977678571`, Xtranslation`-166.7321428571`, Ytranslation`-4.8794642857`.
   Registration is explicitly **PROVISIONAL**, not a calibrated body axis.
4. `body/render_current_source4.py:19` uses profile yaw90, target
   `(0,-.018,.86)`, camera`(4,-.018,.86)`, ORTHO1.85,800x1000, clip.1..10.
   Thus sourceX568 corresponds to worldY-.018; worldY0 maps to sourceX577.7515.
5. `body/surface-review12/export_atlas.py:71` copies the complete
   `underwear-fit/baseline-inputs.json` dictionary into `source_context`.
   E/v10 inherit that context unchanged. `current-body-limit.npz` has geometry,
   UV and weight arrays, no measured registration landmarks.
6. The original mapping names main confirmedv06 SHA
   `6d88d1bc6b579d1ac53436d9f1fa50f903117ac244e307b8e08a9d1e270080e1`.
   The G/H skin traces instead name the tied-hair visibility guide SHA
   `3cb29ca55df903ec5248e59ff10ac6c5b607e01bb4baf894d6bb41437e46614f`.
   `body/shoulder11/source-rails.json:19` assumes common canvas/body panels;
   no lower-body landmark transfer validating568 for the second image was found.

This chain was independently traced read-only by
`/root/v003_pose_space_helper/h_profile_registration_trace`. No replacement
axis was proposed. Root must audit unchanged lower-body anchors in actual R3b
and source before authorizing any corrected uniform panel registration. Such a
correction must apply equally to baseline and candidate and must not be fitted
to the neck. The existing conditional fan-floor proof remains mathematics on
its declared SRT; it does not independently validate that SRT's source binding.

## Durable receipts and scope

Canonical ignored raw receipt:
`D:/MiaWorkCache/mia-reference-work/win-overlay/.mia-cache/body-h/shape/solve1-stopped.json`
(20292bytes, SHA256
`5b27ddbc012b9e40ce51bc115ae01ad949eaa368241e6f28aab019d33ea168ac`).
It contains all constraints and the exact original profile fixture. It is not
promised present after a fresh clone; no raw cache was copied into Git.

`field_numpy.py` and `test_field_numpy.py` implement only the approved field
math: corrected1-Lipschitz hinge, same original component/union definitions,
one bilateral fan scale, Fold+Wnew*(FH-Fold), Z<=1.34 identity. Numeric versus
frozen-expression checks, nesting and derivative tests pass. `diagnostics.py`
contains the required physical/root analysis functions; those final candidate
checks did not complete before root stop. `ram_fit.py` has a stopped-run
preflight, small progress recovery receipt and a root stop-marker check for
future authorized use; no second solve is permitted by this checkpoint.
