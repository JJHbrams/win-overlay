# R: Side_Nape coherent base-pigment challenger

**Actual result:** on both reviewed sides, R removes much of the dirty broad side/nape guide signal and leaves restrained warm-ash color variation. It is a cleaner base, **not finished source-faithful fine ink**. Root owns selection; no canonical/live/native/Git changes were made here.

Read `profile-production-gray-board.png` and `opposite018-production-gray-board.png` first. Each is exact R2 production / R production / actual constant-gray geometry reference. Corresponding `*-pigment-comparison.png` directly displays Main's K-graded pigment without its light/normal response. Original actual PNGs remain unmodified under `review/` and `review-corrected/`.

## Exact actual proof

Input: `Mia_v0.0.2_Review_R2.blend`, SHA256 `eed408b82e9a6160377e92e97fe94ce9619a51393e1ec1d4c928f4a4fd498d82`. Root says its hair/geometry matches OP69bb; only oral palette differs.

Ten valid512px frames: two sides × baseline/candidate production, baseline/candidate Main-pigment-only, and one geometry-gray reference. Profile uses the source profile-wide orientation/position with uniform ortho inspection scale0.50; opposite uses exact orbit018 orientation/position/scale0.36. Both use actual Key60/Fill15/Rim8 only, captured and asserted immediately before every render, with identical world/color management and neutral head/gaze/expression controls. `valid-render-records.json` enumerates exact paths/hashes/settings.

The initial candidate shader exceeded EEVEE's vertex-attribute limit. Its four candidate PNGs are **rejected**, even though files/counts exist. Six baseline/gray frames were valid and retained. The SAME envelope was packed into ONE FLOAT_COLOR stream; a fresh deep guard and four corrected actual candidate renders then passed. Corrected log has zero actual shader compile errors. `rejected-first-compile.json` records the failure. Do not treat the first run's candidate images as appearance evidence.

Scope proof is deliberately exact rather than overstated:

- Opposite018 production **and** pigment pairs: zero changed pixels outside the actual Side_Nape first-hit mask expanded3pixels for AA.
- Profile production **and** pigment: **one** outside pixel `[325,437]` differs by maximum1/255,6pixels from the nearest center-hit semantic sample. Therefore strict profile outside pixel equality is **false**, not a PASS. It is a raw, unmodified comparison; no broader mask or image compositing was used to erase the discrepancy. Cause of that1LSB is not proven. A later same-batch integrated review may clarify it.
- Main coordinates/topology/all6UVs/weights/shape data/corner normals/all original POINT fields, all original maps/material graphs, other actors, rig/world/scene remain exact in `fresh-guards.json`. Gray references expose existing geometric faults; R changes no geometry.

`pixel-difference-report.json` contains full counts and RGB quantiles. In-scope production medians change profile `[77,69,69]→[88,79,79]`, opposite `[91,85,87]→[101,90,91]`. This is a scope/base-paint improvement, not proof of full source color matching across unmatched lighting/poses.

## What R actually does

`prepare_surface_R.py` samples the EXISTING four627² guide PNGs (9guarded samples/view,4pixel radius), with same-owner/depth/warm/bright safety and current center/rest-view confidence. No raster is generated, repainted, upscaled, or replaced. Numeric low-frequency color is attached to the real rest vertices. Luminance is compressed to a bounded ash envelope, preserving local hue/color variation; a restrained source warm-ash chroma reference keeps the clean fallback from reading purple slate. Existing K grade, actual geometric diffuse/toon response, opacity and normals stay connected.

Only exact Main `Side_Nape` weights select the envelope. The SINGLE new POINT FLOAT_COLOR `MIA_R_SourceAshAndScope` stores RGB pigment and semantic alpha, avoiding EEVEE's hardware input limit. Outside alpha0, the old pigment feeds the original K/light graph. Original maps and graph remain archived and intact.

Fine-mark correspondence was tested, not assumed: a bounded quadratic fit to coherent physical-manifold interior points detects narrow anisotropic concavity; boundary/nonmanifold areas and2rings are excluded. Existing guide darkness must persist along the local least-curvature strand direction and recover across it. Only1rawpoint exceeded weak0.1confidence, none0.5. That provides no continuous reliable fine-line support, so R withholds those projected fine marks instead of labeling them valid. Existing physical hair detail and outside-scope marks remain. **Fine source linework is OPEN.**

## What remains visibly open

- The largest upper-crown slate plate in orbit018 lies ABOVE Side_Nape. `scope-overlay-opposite018.png` shows that it is untouched. Upper Crown/Fringe and lowest Rear_Waves scuff remain outside R.
- Nape boundary flakes, blunt/flat inner layers and some sharp strand folds persist in the actual gray views. Pigment cleanup cannot fix them.
- New clean regions can read too simple beside still-scuffed unmodified hair. No whole-hair ART PASS, final atlas bake, new full native, or finished line-paint claim follows.

## Portable API

Copy `apply_surface_R.py`, `manifest.json`, `pigment-envelope.npz` together, then:

```python
import apply_surface_R
apply_surface_R.apply(folder)
```

Apply once after current MN+L→O→P integration. Main100383vertices/120915polygons and raw float32 coordinate SHA `16d192576cd8ecc1905f4eba96b4686c038e8c94a56e6eec7dee552e6eee0b2c` are required. No baseline scene/library replay occurs. This folder's manifest lists exact core hashes/sizes. GPU was released immediately after the corrected4frames; no more variant/render is queued.
