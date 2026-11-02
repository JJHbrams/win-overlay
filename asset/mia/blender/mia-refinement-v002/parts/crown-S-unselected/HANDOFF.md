# S hybrid Crown UV/paint experiment — NOT SELECTED FOR R3

Root reviewed the actual paired boards and rejected authored S for R3. Seed transport looks close and preserves front identity, but the formerly flat opposite Crown develops bunched/creased painted streaks. **R3 keeps adopted R only and its original six UVs.** Neither S UV/seed nor authored fill is active in the canonical/native model. No second imagegen, extra GPU or full native save is queued.

## Actual views first

- `front-bake-actual-comparison.png`, `opposite018-bake-actual-comparison.png`: original/R route versus numeric unique-UV seed transport.
- `front-fill-actual-comparison.png`, `opposite018-fill-actual-comparison.png`: S seed versus ONE masked authored fill.
- Raw actual images/settings/hashes: `review-bake/records.json`, `review-fill/records.json`. Each phase has four valid512px same-batch frames, actual Key60/Fill15/Rim8 asserted immediately before render, same neutral controls/cameras/world. Actual logs contain no shader compile errors. No native saved.

Transport inside active Crown is not pixel-exact: RGB MAE front2.054/opposite1.288per255. It looks close but does not establish exact high-frequency preservation. Both seed and authored comparisons have **zero changed pixels outside the active-face mask expanded3pixels for AA**, including zero changes on legacy exceptions outside that edge allowance. Seed and generated bitmap bytes are unchanged. See `actual-pair-metrics.json`.

## Frozen scope and limits

The all-around outer-sheet candidate has4,999 existing Main faces. The new unique-UV/material route covers4,759 well-resolved faces;240 peripheral/return exceptions retain the **entire original/R route**, preserving their existing detail. No geometry, normals, weights, oldUVs or original POINT data were edited. The phase is **not a complete UV migration/export-ready atlas**.

`crown-flow-frozen.npz` freezes exact actual/raw face IDs, UV corners and240exceptions. Every active new-UV triangle is positive at actual float32 precision; exact area-overlap test found0pairs. A per-face1texel threshold alone was too strong as a rejection rule: weighted review showed the240faces occupy2.005%of layer area, while the7float32 slivers occupy0.0368%, and neither set intersects the visible slate core. These facts justified the conservative hybrid, not new geometry. See `weighted-UV-impact.json` and `active-UV-hybrid-proposal.json`.

Uniqueness is **not** low distortion or correct grooming. Actual atlas-packed stretch anisotropy is median6.49/P9024.07 across active faces; slate core median2.69/P907.66/max41.52. Root/rim harmonic flow is an inferred geometric field, not a measured source strand map. Generated strokes and restoration of protected older paint can bunch across that variable parameterization. The unchanged gray geometry does not show the newly painted creases, so this rejected paint experiment does **not** prove Crown shape is collapsed or needs rebuilding. See `UV-distortion-and-limit.json`.

`boundary-six-view-proof.png` is explicitly mixed evidence: four hair-ON actual orbit RGB frames with CPU first-hit ownership overlays, and two **standalone CPU normal/ownership** high views. Earlier two high RGB overlays ignored the base frames' temporary hair-OFF state and are rejected under `REJECTED-hairOFF-overlay-*`; they must not be cited. This harness error is recorded, not hidden.

The approved v22 master has front/one profile/back/3/4, **no calibrated opposite270°profile**. Opposite-side interpretation remains inferred from the other views. Source crops preserve original pixels/aspect. No opposite-source ART alignment or whole-hair ART PASS is claimed.

## Paint data

`Crown_S_ExistingPigment_Bake.png` is a numeric2048²pre-K rebake of existing current F/H/N pigment, with12pixel color padding. It contains no newly drawn strokes, scene light or new cast-shadow bake. `Crown_S_ReconstructionConfidence_DATA.png` describes reconstruction confidence, **not artistic correctness**. Protected/missing masks and a4pixel inward feather are separate data; protected seed bitmap pixels were never edited.

Root ran exactly ONE built-in imagegen on the actual seed/flow/missing-mask/v22references. Its original output is **1254×1254**, SHA256 `5573374ef27c1485bdc30aab590ff0d528e5843588df417243676bab74082d38`, copied byte-exact to `art/Crown_S_AuthoredFill_1254.png`. Prompt is `art/imagegen-prompt.txt`. No crop, resize, upscaling or Python painting was performed.1254source detail is not claimed as2048detail.

The optional shader uses the same normalized UV for native1254art,2048seed and masks:

`Seed*(1-w)+Generated*w`, with `w=Closest(BinaryMissing>.5)*Linear(NumericFeather)`.

Thus sampled protected-mask0forces fill weight0. The copied material retains inherited K grade and actual deformed geometric normal/diffuse/toon route. One UV stream/four image samplers avoids the previous attribute ceiling. Geometry/routing on240exceptions remains intact. This is a rejected candidate, not an active replacement.

## Exact portable runtime

`RUNTIME_FILES.json` enumerates current exact byte counts and SHA256values. Four seed runtime files:

1. `apply_crown_S_uv.py`
2. `manifest.json`
3. `crown-flow-frozen.npz`
4. `Crown_S_ExistingPigment_Bake.png`

Call `apply_crown_S_uv.apply(folder)` only for an isolated review on fresh matching MN+L→O→P→R. It requires guarded Main geometry/topology/raw IDs and six original UV hashes, adds one new UV and separate clean material slot on4,759faces, preserves all original six UV flags/active index, and uses one UV/one seed texture. `fresh-UV-routing-guards.json` is the successful deep fresh replay proof. Root did not select this for R3.

Five optional authored-candidate files, used only after the seed route:

1. `apply_crown_S_fill.py`
2. `fill-runtime.json`
3. `art/Crown_S_AuthoredFill_1254.png`
4. `Crown_S_MissingPaintFill_MASK.png`
5. `Crown_S_MissingPaintFeather_DATA.png`

Call `apply_crown_S_fill.apply(folder)` for the rejected-candidate review only. No rig/camera/lights/world/full-scene replay is included. Review masks/flow/ownership data remain alongside the runtime. Original source maps, source native, R bundle and canonical/live/Git state were not changed by this child task.
