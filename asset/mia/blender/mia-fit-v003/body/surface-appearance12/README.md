# Body surface appearance12

This worker owns only body texture authoring and CPU/material API checks. Root/integrator own geometry, native scenes, actual captures, source comparison and final acceptance. No face/head/hair pigment or UV, protected source native, rig, settings or GPU work is performed here.

## Current selection and limits

`maps-E-AA/` is the checked **4096px analytic/filter-support candidate** on E-v10. Root/producer's two actual AA recaptures confirm the peach cup punctures are gone. Strap outlines still show path waviness/steps. Clavicle stroke style and rear brief coverage need source comparison; F shoulder/lower-neck proportions are authorized separately. This is component evidence, not a final native or whole-Mia ART pass. E geometry and all previous variants remain frozen.

| Version | Evidence status |
| --- | --- |
| B/C/D3 | Actual geometry seam gates failed; frozen inputs/maps/proofs preserved |
| D2 | CPU component evidence, unselected without actual frames |
| Initial D09c353 | Held before receipt/bake; never adopted here |
| E-v9 | Physical receipt only; wrong hand/pelvis semantics rejected before paint |
| E-v10 / `maps-E` | Correct branches/new atlas; 2K centre-only raster produced actual cup punctures |
| `maps-E-AA` | Fresh 4K analytic support bake; puncture regression fixed in actuals; strap/style/proportion work remains |
| F | Await authorized actual F surface and anatomical anchors before final seating/bake |

The E-v9 NPZ is retained only as a wrong-semantic guard regression input; no map was baked from it. B/C/D2/D3 snapshots/proofs were not removed or rewritten.

## E input contract

| Input | SHA256 |
| --- | --- |
| E-v10 body NPZ | `e8d4d505e661a752ca3c1f9f7841d2109add1835b9e5ea333ac047a6fb759130` |
| World float32 | `9f48277cddd5d9173f4c138eec4aebbfec8b376815c99404399a353c03b3a7d8` |
| Body triangles | `7c34d1ca14482a387fad61f7d85533c32fd285510e234e2eb8552699bb7fb270` |
| New corner UV | `1423a2b49abf807947927ae32b30630336acf4ea34d11ee296164c1d920e17b0` |
| Branch ownership | `a050e19536f944bb05353ecf4d4d4ffedc09529713322581c51f157c1a64ac55` |

E legitimately changes topology: 139,005 world vertices / 240,195 body triangles. The body-only export excludes accepted head faces; `meshfaceid` refers to full joined polygons. `MIA_Review12UV` is the actual newly packed body atlas, not a dummy/proposed cylinder layout. Original head UV routes are separate.

`receive_expanded.py` uses complete physical correspondence, not D's same-ID assumption: 111,861 strict retained vertices plus 200 obsolete artificial forearm cut points cover all 112,061 required outside-band points. The latter have `source_vertex=-1`, old split Z1.035 and arm ownership; they are represented on the SAME original source_face using actual new triangles and source barycentrics. Maximum physical rounding residual is 3.65e-8m, source barycentric residual2.89e-8, largest-area fragment normal difference0.0067deg. This is representation-only, not permission to move original donor geometry. All 37,457 ordered head triangles/three old UVs/material/source-corner data and 2,992 D3 neck rows are exact. The 14,784 replaced old points must lie within authorized section/branch bounds; head/neck/core are protected. Full joined inputs are read-only and fingerprinted. Native POINT reconstruction/active UVs still require producer checks.

E-v9 incorrectly labelled lateral hands as pelvis. This worker rejected it. E-v10 inherits validated D3 donor arm labels via the SAME source_part/source_face; an independent check confirms all41,011 matching retained donor faces with no mismatch. This is not a global X/Z correction. Positional hand extents are diagnostic only.

Two tiny E UV faces were restored by the producer with root-approved one-ULP changes: four scalar components across two faces. Read-only `UV-numeric-restoration-proof.json` verifies raw/corrected arrays and exact export binding. No zero determinants remain; minimum positive double-area1.11e-16 is explicitly tiny/subtexel. The loader tests nonzero determinants in float64 rather than mislabelling every area<1e-12 as degenerate. This worker never edited UVs.

## Raster defect and common correction

`E-material-pixel-diagnosis.json` traces exact recorded clavicle-on camera pixels to actual E triangles. Three peach defects hit torso region1 with analytic coverage1.0 but PNG bilinear coverage0.0. The triangles are3.5–4.2mm in world yet less than one pixel wide in the2K atlas: centre-only rasterization supplied no seed, so zero coverage survived padding. Geometry/specular/semantics did not cause these holes.

`complete_filter_support` now supplies every actual UV triangle's bilinear neighbours using nearest-UV-edge barycentrics and real world points, preserving existing interior texels. This fills filter support, not geometry or per-view overlays. Padding remains4px. `maps-E-AA` is newly evaluated at4096, not upscaled from2K. The three defect lookups become1.0. A new independent deep-interior check finds37 failing cloth triangles in old2K versus zero among25,911 deep-cloth triangle centroids in the candidate, minimum coverage1.0. Original output-ancestry/ownership checks alone were insufficient and are not presented as interior-coverage proof.

The4K raster has5,224,691 actual centre texels plus179,178 filter-support texels, zero different-world overlaps at the declared2mm check tolerance, and4,108 triangles without a centre texel. Tiny faces remain a review-atlas limitation, not production-UV approval. Actual AA recapture is the visual evidence for the puncture fix. Remaining strap waviness requires a source-endpoint-preserving surface-constrained fair path, not another resolution claim.

## Five actual shader channels

| PNG | Color space | Actual use |
| --- | --- | --- |
| SkinBaseColor | sRGB | New body skin; all old underwear paint excluded |
| UnderwearBaseColor | sRGB | Illustrated matte charcoal and restrained band seam pigment |
| UnderwearCoverage | Non-Color | Material mixing plus actual roughness/specular control |
| ClavicleInk | Non-Color | Independent warm line weight |
| ClavicleShade | Non-Color | Separate authored soft pigment |

No unused normal/displacement/specular PNG is labelled finished. The actual EEVEE graph is white Diffuse roughness0 → ShaderToRGB → luminance/4 → saved-R3b-compatible EASE ramp → pigment/Emission, plus restrained actual specular. Skin uses common linear[.92,.69,.60] encoded[246,216,203]. Source illustration RGBs are authored appearance, not recovered physical albedo. The same supported body geometry is used for skin/underwear; texture clothing adds no thickness/compression or invented nipple/genital detail.

```python
import sys
from pathlib import Path
p = Path('/absolute/path/to/surface-appearance12')
sys.path.insert(0, str(p))
import install_material
mat = install_material.create_material(p/'maps-E-AA', variant='skin')
# Producer assigns ONLY actual body faces; original head materials are retained.
install_material.set_controls(mat, variant='underwear', clavicle_strength=1)
install_material.pack_material_images(mat, relative_prefix='//MIA_Review12Maps/')
proof = install_material.audit_material(mat)
```

Each call owns independent nodes/controls. Two scenes need two body Object instances sharing ONE Mesh, each with body slot12 OBJECT-linked to its own material. One Object shared across scenes would share its override. Other head slots remain untouched. Packing verifies original PNG byte hashes, is idempotent, and never saves native. Producer must save/freshly reopen to prove portability.

The body graph explicitly names `MIA_Review12UV`; do not switch the global active/render-active UV if retained head nodes use implicit UV inputs. Preserve original head UV routing, then check actual color-only/clavicleOFF neck continuity. Do not repaint the face to hide a body seam.

Fresh reviewer inspection establishes an actual small neck pigment residual: source cutslot10 mixes common[.92,.69,.60] with head[.82,.63,.55] by POINT `V27_HeadMaterialBlend`, near-cut alpha.0486–.3751, followed by the same actual-light ramp. Source UV pigment is neutral there. Constant commonRGB alone is therefore not a boundary-match proof. F needs body-only continuation from exact boundary alpha, fading C1 by actual neck-surface distance; no fixed-light bake or face edit. Slot10 has no specular while the new body has specular; any remaining lit residual needs a shared-unlit/common-ramp probe before changing controls. BODYColorOnly with a still-lit head is not that probe.

## Source authoring and pending style

Original body-v06 source SHA`6d88d1bc6b579d1ac53436d9f1fa50f903117ac244e307b8e08a9d1e270080e1`; tied-hair guide SHA`3cb29ca55df903ec5248e59ff10ac6c5b607e01bb4baf894d6bb41437e46614f`. Original-pixel source paths and ten illustrated color samples are in `underwear-source/`. Guide back scoop/band fragments have approximately2–4px manual uncertainty. Source images were never warped or edited.

Coverage uses declared source-relative anatomical chart fitting with original source-camera height calibration. Front/back brief paths remain distinct; hidden closure/gusset/continuous strap route are inferred. No global nearest-body projection across axillary sheets is used. All four current boundaries have128 newly seated actual-surface points each; straps are actual semantic upper-surface paths. These are authoring bindings, not art approval.

The original clavicle implementation was a five-point C0 polyline. Local contrast measurements are confounded but indicate source deficit≈.49 versus actual≈.22, so blind opacity reduction is unsupported. Root accepted a separate source-anchor-preserving C1/reseated curve and sigma.85→.65mm finer-stroke candidate, keeping gain.55 initially. Final curve/strap/style maps wait for actual F geometry and anatomical root anchors: E's1.445 guide-root/1.409 graphic height must not be blindly carried into F. Rear brief coverage also needs an original-aspect frozen-SRT source comparison, not ownership-only approval.

`material-route-proof.json` verifies actual Blender5.2.3 image paths/colorspaces, output ancestry, independent controls and original-byte packing without GPU/native. `footprint-proof.json` additionally includes deep interior coverage. No receipt/ray count/map count alone marks anatomy, native assignment, rigging or Mia ART PASS. Engram tools were unavailable; these are repository records, not claimed Wiki synchronization.

Reproduce the current CPU candidate without overwriting a running capture:

```text
python receive_expanded.py inputs/c5c5177af0cb.npz /immutable/E-v10.npz /producer/expanded-E-protection-proof.json inputs
python bake_surface.py inputs/e8d4d505e661.npz --output maps-E-AA --size 4096
python verify_surface_maps.py inputs/e8d4d505e661.npz maps-E-AA
blender -b --python-exit-code 2 --python verify_material.py -- /absolute/path/to/maps-E-AA
```
