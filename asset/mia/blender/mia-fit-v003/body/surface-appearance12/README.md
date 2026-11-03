# Body surface appearance12

This folder supplies the **body-only static review material** for root's Review12 assembly. It does not change body geometry, head/face/hair materials, original UV channels, production rigging or protected R3b/upper11 files. The integration producer owns native assembly, actual EEVEE review, source comparisons and orbit captures.

## Adopted input and output

Use `maps-B/`. `maps-A/` and the d4bb41 diagnostic files are rejected earlier seating evidence, not alternate final maps. The old d4bb41 NPZ copy was removed to avoid retaining a redundant 3.9 MB intermediate; its receipt/metadata and failure data remain. The final immutable target snapshot is `inputs/21f67202861b.npz`, received from `surface-review12/surface-v3-branch-regions.npz`.

| Input | SHA256 |
| --- | --- |
| Final NPZ / semantic v3 | `21f67202861be45105fb9e977e052b8e69b6c867243d385078da5294922bc9e5` |
| World float32 coordinates | `523d4d820501abea38d4ade94fe7578b526b80ad8fc61cc616fdefb7409aa631` |
| Ordered body triangles | `fd0096040df4b4f6b8685399d87ed63ec87e5bbada1ee8bed57a6f91c6d5575d` |
| Actual per-corner body atlas | `8dbcb1c99355d086c3b63a6c5aca24033982830442484e6cca7bd0072d85c0a7` |
| Final face-region ownership | `16096617671a58577cee9ef0b1a66e62e9b85460f33d174642a36d394f1cf624` |

The final input has 126,845 joined vertices and 215,875 **body-only** triangles. Its atlas is the producer's real packed `MIA_Review12UV`, not the initial proposed cylinder rectangles. Accepted face/head triangles are excluded. `meshfaceid` maps body triangles to the producer's full joined mesh polygons.

`maps-B/bake-report.json` contains all five 2048² PNG hashes. Actual shader channels:

| PNG | Color space | Actual use |
| --- | --- | --- |
| SkinBaseColor | sRGB | New body skin pigment; old body underwear paint entirely excluded |
| UnderwearBaseColor | sRGB | Illustrated charcoal pigment and subtle band seam tint |
| UnderwearCoverage | Non-Color | Skin/underwear pigment mixing and restrained roughness/specular control |
| ClavicleInk | Non-Color | Thin warm graphic line with independent strength |
| ClavicleShade | Non-Color | Separate soft authored pigment below the line |

There is no unused normal/displacement/specular PNG presented as a completed map. Actual specular and roughness are shader controls derived from coverage. The maps have 4-pixel island padding and fixed-world edge smoothing. Tiny/subtexel triangles remain a reported review-atlas limitation.

## Installer API

Run inside **EEVEE**, after the producer has assigned the exact final body UV atlas:

```python
import sys
from pathlib import Path
p = Path('/absolute/path/to/surface-appearance12')
sys.path.insert(0, str(p))
import install_material
material = install_material.create_material(
    p / 'maps-B', uv_layer='MIA_Review12UV', variant='skin',
    clavicle_strength=1.0)
# The integration producer assigns this new material ONLY to its body faces.
# Preserve original head/face/hair materials and their existing UV routes.
install_material.set_controls(material, variant='underwear')
install_material.set_controls(material, clavicle_strength=0, color_only=True)
proof = install_material.audit_material(material)
```

The API creates a new material; it does not assign it or mutate any existing material. `variant='skin'` zeroes the underwear coverage factor; `variant='underwear'` enables it on the **same geometry and UVs**. Separate named materials or two scenes may share one body mesh. The integration producer must store the actual runtime mode and assignments in the native/manifest.

The active light route matches the saved R3b common skin response: white Diffuse roughness0 → ShaderToRGB → luminance /4 → matching EASE ramp → authored pigment → Emission. A black-base BSDF adds a restrained actual-light specular lobe. `ColorOnly` bypasses light/specular; `ClavicleStrength` bypasses authored ink and soft shade. The skin PNG encodes R3b common linear RGB `[.92,.69,.60]` as byte RGB `[246,216,203]`; this avoids treating the source illustration's lit skin pixel as measured albedo. A real hair-hidden color-only neck seam review is still required. Face pigment is never changed to conceal a body color mismatch.

## Source observations and inference

The original 1536×1024 body-v06 source is SHA `6d88d1bc6b579d1ac53436d9f1fa50f903117ac244e307b8e08a9d1e270080e1`; original-pixel paths and the ten illustrated RGB sample records are in `underwear-source/`. The tied-hair visibility guide is SHA `3cb29ca55df903ec5248e59ff10ac6c5b607e01bb4baf894d6bb41437e46614f`. Its visible back bra scoop/band were manually observed with approximately 2–4 source-pixel uncertainty, recorded in `tied-guide-paths.json`. Original source images were neither warped nor edited.

The selected source pack paths feed independent front scoop/band, profile side return/band, back scoop/band, distinct front/back brief waist and leg curves. They produce a source-relative anatomical angular chart with recorded source-camera Z calibration. **This is a declared artist fit, not exact source-pixel projection or reconstructed hidden garment dimensions.** The source chart width/side interpolation and continuous strap route are inferred. The source pose/form differs from this assembly, so exact source ray hits were not substituted with global nearest-surface picks.

All four final closed boundaries were newly seated with 128 actual anatomical-submesh first hits each. No wrong physical sheet is skipped; arm-occluded torso paths use an explicitly scoped torso authoring chart. Two shoulder straps are constrained shortest paths along actual torso/shoulder edges. Their width/hidden continuation is inferred. The two visible source clavicle lines were seated on the actual neck-front surface after a common anatomical-anchor translation, with separate soft pigment underneath. The common translation is explicit in `seated-boundaries.json`; it is not a warped source comparison. Other neck-shadow fragments are palette/context evidence, not a claim that all source lighting was physically recovered.

Brief lower openings are fitted to the actual central crotch bridge while retaining independent front/back and side-opening intent. Hidden gusset/closure construction is inferred. Underwear is texture coverage on supported skin geometry: it adds no cloth thickness, compression, cleavage bridge, nipple/genital detail or new unsupported-breast sculpt. Both material modes retain the same supported shape.

## Verification and unresolved actual review

`maps-B/footprint-proof.json`: final PNG SHA/size checks; 215,875 triangle-centroid UV footprint samples; zero underwear on arm/low-leg ownership; zero clavicle outside allowed front/neck regions; all 512 seated boundary barycentrics reconstruct exactly. This is an ownership/route test, not a continuous texture filtering or anatomy certificate.

`maps-B/material-route-proof.json`: actual Blender 5.2.3 loads the five **final** PNGs, verifies connected UV/Image/output ancestry, color spaces and material mode/clavicle/color-only toggles without loading/saving the source native or rendering. The older `material-api-smoke.json` only tests synthetic images and is not used as final-map proof.

The UV raster reports 1,321,288 occupied texels, 5 coincident shared-edge co-hits, zero different-world overlaps at the explicitly declared 2 mm check tolerance, and 14,464 triangles without a texel center. This is not a production UV approval. Body material assignment, actual neck continuity, source-underwear resemblance, strap continuity/filtering, moved-light/clavicle toggles and orbit appearance **remain for the producer's saved-native review**. None of these CPU checks mark Mia or body anatomy ART PASS.

Rejected earlier evidence is retained: the first producer atlas contained zero-UV triangles and was refused; the next corrected atlas needed world-normal/collar correction; then eight bra-side rays revealed inner-arm faces in a broad torso label. The producer's semantic v3 corrected 3,085 ownership labels using actual component fields; geometry and UV did not change. Final maps use only that v3 snapshot.

Engram knowledge/activity MCP tools were unavailable to this worker; these records are repository evidence only, not a claimed Wiki sync. No paid tool, install, settings change, model upload, GPU render or protected-source modification was performed.

Reproduce CPU bake and final checks from this worktree:

```text
python bake_surface.py inputs/21f67202861b.npz --output maps-B --size 2048
python verify_surface_maps.py inputs/21f67202861b.npz maps-B
blender -b --python-exit-code 2 --python verify_material.py -- /absolute/path/to/maps-B
```

Coordinate with the producer before regenerating a map folder currently in use; preserve target fingerprints and do not overwrite a running capture's inputs.
