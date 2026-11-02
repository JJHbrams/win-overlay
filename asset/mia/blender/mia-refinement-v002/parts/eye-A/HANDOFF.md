# Bounded source12 and small-mouth candidate A

Apply to the current integrated R2 scene. No native scene is opened or saved by the helper. No full-scene snapshot was created. GPU is released.

Input native SHA256: `eed408b82e9a6160377e92e97fe94ce9619a51393e1ec1d4c928f4a4fd498d82`.

```python
import importlib.util
from pathlib import Path
entry = Path("C:/Users/antio/.codex/worktrees/mia-v002-face/win-overlay/asset/mia/blender/mia-expression-refine-v003/portable_expression_refine.py")
spec = importlib.util.spec_from_file_location("mia_expression_v003", entry)
delta = importlib.util.module_from_spec(spec)
spec.loader.exec_module(delta)
report = delta.apply_to_current_scene()
```

Only three small files are required. Preserve their relative layout.

- `portable_expression_refine.py`
- `payload/surprise-A.json`
- `payload/surprise-A.npz`

Hashes are in `handoff-manifest.json`. The helper and payload are frozen at the versions actually rendered.

## Actual cause and chosen scope

The original Surprise key raises the true rim only modestly. The upper lashes follow it. The first-hit audit disproved an inert separate upper-cap explanation. The opaque upper-lash material uses Emission. The visible opening closely follows the skin rim.

The inherited Surprise key also shrinks the iris mesh by about 20% at 0.8. A adds no open-iris or sclera scaling. The inherited radius response remains an explicit residual. Iris and sclera receive only a matching-side closure cancellation key.

The approximate source12 true-opening trace uses the confirmed red/green semantic distinction. It excludes the outer lash silhouette. Source canthus-frame central gap ratios are about 0.40 and 0.36, with at least one original pixel and pose uncertainty. A's actual P12 ratios increase from 0.346/0.337 to 0.419/0.416. This is a bounded surprise improvement, not a precise source proportion fit.

The new local skin field starts from the actual 24-vertex eye-hole boundaries. It extends through skin mesh edges with a 12.5 mm geodesic limit. Boundary depth follows the actual sclera shell. Wall and lash stations move in the corresponding evaluated skin frames. Original keys, raw coordinates, UV, weights and maps remain unchanged.

New key names are `Mia.v003.SourceSurprise.Aperture.{side}` and `Mia.v003.SourceSurprise.CloseGate.{side}`. Sides are world −1 and +1. The correction reads the existing `EYE_Surprised` value. It fades under global or matching unilateral Close/Joy. A separate counter key cancels the inherited Surprise contribution on that same side at full closure. The other eye remains active during a wink.

The small-mouth audit found real upper-crown visibility in P03/P06/P12. The new `ManualSmallMouthDentalHide` defaults to zero. Automatic contributions come only from existing P03/P06/P12, normalized by `PresetTotal` and multiplied by `Strength`. The existing MIA grin smoothly overrides hide. Manual I/E phonemes are unforced. The clean new enamel material mixes its original shader with Transparent BSDF. It exposes the existing cavity without moving teeth or painting the crowns dark.

Reset names beginning with `Manual`, or explicitly reset `ManualSmallMouthDentalHide`. The older `Manual_` reset pattern misses this requested property name.

## Allowed existing owners

- `MIA_V27_SharedHeadBody`: four additive keys and their drivers.
- `V28G_InnerLid_-1/1`: aperture and closure-gate keys.
- `V30_UpperLashes_-1/1` and `V30_LowerLashes_-1/1`: aperture and closure-gate keys.
- `V28G_Iris_-1/1` and `V28G_Sclera_-1/1`: closure-gate keys only.
- `Mia_FacialControls_v002`: the manual/effective dental-display properties, its driver and two provenance tags.
- `MIA_v002_UpperDentalCrowns` and `MIA_v002_LowerDentalCrowns`: material slot0 only.
- `MIA_v002_Enamel_ActualToon`: archive fake-user flag only. Its graph stays exact.

The new material is `MIA_v003_Enamel_DentalDisplay`. Existing clean cavity/collar palette, teeth geometry, jaw rig, MIA grin, FaceD2 paint, brows, body, hair, cameras and lights are untouched by the helper. Unrelated added keys are accepted by name. Root's Angry brow delta can coexist. Surprise brow support stayed positive, so no Surprise brow key was added.

## Evidence

`audit/CPU-guards-A.json` contains 208 passing checks across 37 states. Original keys and protected data stay exact. Neutral evaluated eye geometry is bit-exact. Matching closed endpoint differences stay below 0.00001 mm numerically. The maximum tested wall-root distance is 0.000478 mm. These floating-point comparisons do not certify clinical anatomy.

P12 brow support has 768 opaque interior samples per side. Minimum camera-order margins remain 0.08157/0.09154 mm, versus R2's 0.08158/0.09154 mm. No new buried sample was found in that test.

`review/A-quick10/render-records.json` records ten actual Blender frames. All camera clips are 0.1..10 m. All archived lights are hidden. Exactly three reference lights are active. The new enamel graph stays stable across each render. No native is saved.

The producer inspected all ten actual images. P12 opens visibly. The oblique retains ocular depth without an exposed temporal background slit in the inspected view. P03/P12 mouths read dark. Full close and the unilateral wink show no ocular sliver. The other eye remains open.

Neutral before/after RGB is bit-exact. P03 full transparency is also RGB bit-exact to physically hiding both dental objects. The tested endpoint has no residual tooth shadow or bright transparency fringe. Actual material settings are DITHERED, transparent shadows enabled, transparency overlap disabled and backface culling enabled.

Source boards and pixel evidence:

- `review/A-quick10/paired/P12-source-baseline-A.png`
- `review/A-quick10/paired/P03-source-baseline-A.png`
- `review/A-quick10/paired/closure-wink-depth.png`
- `review/A-quick10/paired/actual-diagnostics.json`

Original source aspect and actual native 512 images are preserved. No feature warp or source pose-fit claim is made.

## Review limits

Root owns selection and the final integrated 16-expression, source, critical, head-follow and intermediate review. The quick package is not a completed four-view face ART gate or full16 acceptance. Source eye curvature, upper-band finish and broader likeness remain open. Partial dental transparency intermediates were not rendered. Arbitrary simultaneous global/unilateral key combinations are not certified.

Posterior-row Y overlap includes hidden stations. Its negative minimum already existed in R2 (about −0.88 mm) and becomes about −0.90 mm in A. Both have zero missing sclera ray hits in the compared open states. This scalar is not an exposed-gap verdict. `audit/posterior-baseline-candidate.json` retains the limitation.

The first CPU log contains a JSON serialization failure. A later harness correction resets the new manual property correctly and samples brow contact using skin normals rather than double-sided ink normals. The final CPU report and actual quick proof use the corrected harness. Frozen FaceD2 and Mouth C files remain unchanged.
