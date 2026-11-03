# H appearance binding

Source-only adapter. No H bake, Blender material assignment, native save or GPU
render ran in this worker. The optional brief world correction stays unselected.

`h_surface.py prepare` reads the actual H assembly/atlas directly from canonical
`.mia-cache/body-h/shape/assembly`. It requires payload `H`, verifies the NPZ,
WORLD/triangle/UV arrays against metadata and actual assembly/atlas, and checks
the current shared head/body interface against the original slot10 pigment.
It writes only small JSON receipts under the canonical ignored appearance cache.

The prepared metadata references the **same surface NPZ**. Original NPZ/JSON and
geometry are not modified, linked, or copied. It adds the previously observed
source graphic support Z1.37778 as an explicit clavicle anchor rather than
reusing the E neck-ring-height fallback. Its 3D XY position is not invented.
The source graphic must still seat successfully on the actual H surface and
pass actual source/material comparison.

The root may explicitly select the orientation-corrected candidate by writing
canonical `.mia-cache/body-h/selected-candidate.json`. The helper only reads it;
it never selects/promotes a candidate. Optional `--selection <absolute file>`
can choose another root-authored selection inside the same H cache. Every
selected input path must be absolute, inside the assembly cache and hash-current:

```json
{
  "geometry": {"path": "absolute winding-fixed/geometry.npz", "sha256": "actual SHA"},
  "surface": {"path": "absolute winding-fixed/atlas/surface.npz", "sha256": "actual SHA"},
  "atlas": {"path": "absolute winding-fixed/atlas/atlas.npz", "sha256": "actual SHA"}
}
```

Metadata is read beside the selected surface NPZ and `assembly.json` beside its
geometry. The selection file itself is hash-bound into the preparation receipt.
When no default/explicit selection exists, original H paths remain the backward
compatible default. Selection is not a gray/ART approval. Original `prepared-H`
is stale for the corrected candidate and remains preserved. Use a separate output:

```powershell
python tools/mia/body_surface_h/h_surface.py prepare --output D:/MiaWorkCache/mia-reference-work/win-overlay/.mia-cache/body-h/appearance/prepared-H-oriented
```

For that candidate's later authorized bake, pass
`--prepared D:/MiaWorkCache/mia-reference-work/win-overlay/.mia-cache/body-h/appearance/prepared-H-oriented`
and a new map output such as `--output D:/MiaWorkCache/mia-reference-work/win-overlay/.mia-cache/body-h/appearance/maps-H-oriented`.
Use the same optional `--selection` in prepare and bake if not using the default
selection file. Original arrays and metadata are still never copied or modified.
Selection guard fixtures verified default compatibility, explicit path/hash
binding, rejection of stale hashes, relative/out-of-cache inputs and out-of-cache
selection files. A read-only actual original-H binding also passed. No actual
oriented candidate selection or preparation was written by this worker; the root
chooses it and invokes the new preparation separately.

```powershell
C:/Users/antio/miniconda3/python.exe -X utf8 tools/mia/body_surface_h/h_surface.py prepare
```

Default output is canonical `.mia-cache/body-h/appearance/prepared-H/`:
`surface-prepared.json`, `config.json`, `neck-inputs.json`,
`neck-interface-check.json`, `prepare-report.json`.
Idempotent reuse requires unchanged input/code/source-path hashes. A changed H
candidate needs a new explicitly selected cache output, not receipt overwrite.

Before baking, the root must inspect the real six-view gray/source package and
write a separate decision inside canonical `.mia-cache/body-h/`, for example:

```json
{
  "decision": "APPROVED_FOR_APPEARANCE_PREFLIGHT",
  "geometry_sha256": "actual geometry.npz SHA",
  "surface_sha256": "actual surface.npz SHA",
  "gray_capture": {"path": "absolute actual capture.json path", "sha256": "actual SHA"},
  "scope": "Root's bounded actual gray decision; final material/native/orbit still open"
}
```

This helper never creates that decision. It checks its exact H binding, capture
hash, actual H front/profile/back/oblique/high/low coverage and current image
hashes before the separately authorized heavy write. Root still serializes heavy
writers; the capacity estimate is not an atomic lock.

```powershell
C:/Users/antio/miniconda3/python.exe -X utf8 tools/mia/body_surface_h/h_surface.py bake --root-gray-decision D:/MiaWorkCache/mia-reference-work/win-overlay/.mia-cache/body-h/gray/appearance-decision.json
```

Default maps go to `.mia-cache/body-h/appearance/maps-H/`; a nonempty bake output
is never overwritten. Size is fixed4096, freshly rasterized with the existing
analytic bilinear-support code, not an upscale. The adapter orchestrates the
existing recipe, fresh TargetAuthor seating/full-body visibility, Cartesian
brief field, C1 fair paths, neck pigment, paint and padding functions. It does not
monkeypatch them or duplicate image/mesh inputs. It records the separate metadata
actually used rather than falsely crediting the unchanged original JSON.

Five shader assets: SkinBaseColor/UnderwearBaseColor(sRGB), UnderwearCoverage,
ClavicleInk and ClavicleShade(Non-Color), plus the diagnostic valid mask. Skin is
the existing R3b common color with actual interface-alpha continuation; thin
clavicle ink uses sigma0.65mm. The existing install_material API supplies the
actual diffuse-to-toon and limited specular route. No unused generic PBR maps are
invented. Native/material connection, light/toggle probes, cloth seating/look,
packing and final source/rotation review remain root tasks.

Actual worker checks: Python AST/import; actual E control surface derives the
new explicit-anchor config without a legacy landmark lookup; original metadata
unchanged; legacy non-H metadata, noncache output and bake without root decision
are rejected. The newly available actual H target also completed `prepare` in
1.13seconds: geometry SHA`1270428c…`, surface SHA`3d1c390a…`, atlas SHA`ee6b021f…`.
The full fingerprints are in the cache receipt. Actual slot10 interface check
covered123shared vertices, alpha0.048623..0.375056,6378neck-domain vertices and
367lower-boundary vertices with no inconsistent corner alpha. Five JSON files
total55,470bytes were written; arrays and original metadata remained unchanged.
These are H binding/interface/configuration checks only. No H seating/raster
bake/material/native/render or artistic acceptance was executed here.
Engram reminder/activity tools were unavailable.
