# Current Mia v27 turntables and proportion comparisons

Native SHA `e9c8654121307b61fb75d73789c9b2443a3e42c53420dfdfada927d194b475d4` was confirmed as the actual open Blender document, without unsaved changes. Export did not change or save the native. These are real Blender renders and camera rotations, not generated intermediary pictures or character motion clips.

| Output | Contents |
|---|---|
| `mia-v27-head-360.gif` | 96 actual views, 360deg orthographic bust, elevation5deg, native materials |
| `mia-v27-bare-360.gif` | 72 actual views, hair hidden, diffuse skin diagnostic, elevation0deg, camera-relative lights |
| `mia-v27-body-360.gif` | 72 actual views, full body, elevation2deg, native materials, no clothes added |
| `face-multiview-comparison.png` | Source/current front, profile-like80deg, subtle25deg and opposite-10deg views from the same frozen native |
| `face-front-ipd-comparison.png` | Independent uniform eye-spacing registration, without fitting chin/mouth; manual projected ratios |
| `body-multiview-comparison.png` | v06 body-art candidate/current front, side, oblique and back, uniformly fitted display height |

Each GIF lasts6.76seconds, loops, and briefly holds the cardinal views. GIF encoding uses a common256-color palette. PNG frames remain locally at the path recorded in `export-manifest.json`; raw frames are not duplicated in Git. Three12-view contact sheets are also included. Actual camera matrices, native SHA, frame hashes and key values are recorded under `render-records/`.

## Interpretation

The front comparison uses manually located visible iris centers because lids partly hide the actual pupils. Eye spacing and eye-line roll are normalized uniformly; chin and mouth remain unfitted. Approximate projected ratios:

| Measure / eye spacing | Source | Current |
|---|---:|---:|
| Eye line to chin | 1.096 | 1.056 |
| Eye line to mouth | .713 | .667 |
| Mouth to chin | .383 | .389 |
| Lower-jaw section width at0.80 eye spacing below eye line | .98 | .99 |

Anchor uncertainty is about +/-3original pixels, plus source pitch/gaze uncertainty. The apparent3.7percent shorter projected eye-to-chin length is a diagnostic observation, not a prescribed3D correction. The jaw sample is not maximum cheek width. Raw coordinates and calculations are in `front-ratio-measurements.json`.

Other face views preserve the existing uniform source/baseline/current registration and actual frozen source-matched cameras. Their eye-to-chin normalization cannot independently validate face height. The small profile art is only80x72original pixels with yaw70–90deg uncertainty and partly hidden bridge. Opposite expression art is near-front with upward gaze/open mouth, not a confirmed opposite45deg drawing. These limitations are printed on the comparison.

The body comparison fits hair-top-to-sole display height uniformly; this is not a body-height or anatomy approval. v06 is a generated modeling-reference candidate; pose, hair height and underwear differ. Grid lines show fractions of display height, not anatomical landmark targets.

An independent read-only visual review confirmed registration, original-pixel landmarks, labels and stable turntable scale/framing. Root inspected the contact sheets and comparison images. Hair extraction edges/length, neck/body facets and source line/pigment differences remain visible model issues; this export does not change their acceptance state.

## Recipes

Run `render_turntables.py` through Blender background with `-- --native <native> --output <fresh frame folder> --preset head|bare|body --frames <count>`. Native SHA is guarded and checked again after rendering. Then run `encode_turntables.py --output <folder containing head/bare/body frame folders>` and `compose_comparisons.py --output <same folder> --body` with Pillow/NumPy Python. No extra dependency installation was needed.
