# WIP9 combined face material audit

This is a read-only diagnostic of the saved Q9 + E2 + M4 native. It adds no material variant, raster texture, UV edit, geometry edit, native save, or model acceptance. WIP9 remains an intermediate candidate.

## Inputs and reproducibility

- Baseline, relative to the v22 root: `integration-wip-8-review/Mia_ReferenceFinish_v22.blend`; SHA256 `ff2b61b2b2146fc4f73119cf10534571609dff75f6333fbec34d0926068b8bb4`.
- Candidate: `../Mia_FaceReview_v22_WIP9.blend`; SHA256 `fb85468a623e1befc590176a24636548b944491ce4ae19decaece625304945b2`.
- Reference package: v22 `parts/face-finish8-f2-review/reference-review.json`. Its source image hashes, cameras and inherited uniform registrations were verified and retained. Source art is the reaffirmed face portrait and expression-sheet panel 04.
- `inspect_combined_material.py` audits actual material-output connectivity, packed images and evaluated UVs. `packed-map-uv-audit.json` is its complete result.
- `render_combined_material.py` opens each source without saving and renders eight actual EEVEE frames: WIP8/WIP9 x front/left oblique x lit/skin-color-only. All inputs and output paths were absolute. The renderer AST-loads the existing frozen rig functions from v22 `render_integrated_review.py`.
- `compose_material_audit.py` only lays out original source and actual Blender renders. No image generation, repainting, local warping, feature fit or texture-image modification occurs. `actual-review/comparison-boards.json` records exact uniform registrations and pose uncertainty.
- Blender 5.2.3 LTS. Both native hashes remained unchanged. Render metadata, hashes and camera/light/display conditions are in `actual-review/render-records.json` and `actual-review/manifest.json`.

## Technical result

All these bounded checks passed:

1. Evaluated neutral UVs are exact between WIP8's evaluated mesh and WIP9's baked dense mesh.
2. `FINISH8_BasePigment`, `FINISH8_FatigueMask`, and `FINISH8_FineLineMask` consume the same original packed image bytes, names, dimensions and color spaces in both natives. These maps were already connected in WIP8; they were not newly painted here.
3. M4's `IDENTITY9_MeasuredLowerLidUVCurve` and `IDENTITY9_SecondaryFoldPigment` reach the actual face output. The obsolete shifted-mask node remains unused and was not counted as a consumed map.
4. Baseline and candidate have identical camera, light and display records for each matched diagnostic.

Technical connectivity does not prove source likeness. A UV hash does not independently prove ideal pigment placement after shape changes.

## Actual visual findings

All four source/WIP8/WIP9 boards were opened and inspected: lit front, lit left oblique, color-only front, color-only left oblique.

- WIP9 has a visibly stronger and broader muted mauve/brown under-eye mass than WIP8. A short, faint outer lower fold is present; the rejected M3 long dark closed arc has not returned.
- The pigment follows the lower eye aperture on the integrated geometry in these two views. No obvious UV slide, detached pigment island or gross stretching is visible. This is a two-view visual observation, not a distortion metric or animation guarantee.
- The source's upper-eyelid crease and short layered brown linework above the black lash remain largely absent. Changing the lower fatigue shader cannot supply this missing layer.
- The source separates the dark under-eye mass, a brighter lower boundary and broken fine contours. WIP9 still reads as a smoother, more uniform dark eye-bag band. More color density alone is not sufficient to reproduce the reference drawing.
- Source nose/eyelid/cheek marks have stronger local line and light/dark separation. The current shader remains soft and smooth. This audit does not treat a geometry-induced shadow as painted makeup or claim new normal/specular/roughness maps.
- The source/model difference remains substantial in face proportions, eyebrow/eye impression, hair silhouette and line treatment. These boards must not be described as full source match or ART PASS. The geometry review and any subsequent jaw candidate are separate from this material isolation.

## Comparison limits

- Lit renders keep native hair. Color-only renders hide hair and bypass only skin's controlled-light multiplication; eye and accessory shaders remain native. They are pigment diagnostics, not finished portraits.
- The source panel has different gaze/expression and uncertain yaw/pitch/roll. Existing baseline SRT was copied exactly to the candidate. Its eye-to-chin normalization cannot validate vertical proportions; this is explicitly labelled on the boards.
- No extra material variants or native saves were made. Only neutral front/left-oblique appearance was reviewed here. Blink/expression mixtures and other views need their own evidence; the parent deformation audit is not replaced by this material audit.

Disposition: retain M4 as an auxiliary appearance candidate; source identity and final texture completion remain unaccepted.
