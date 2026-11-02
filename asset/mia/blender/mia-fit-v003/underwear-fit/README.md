# Posed surface seating and barycentric underwear UV transfer

Portable CPU preparation for the 41 observed v06 source paths. It does not change
body geometry, keys, rigs, material nodes, UVs, live state or a native file, and
does not paint/bake a garment or neck map. Rejected target01 and unselected
target02 are not inputs to the diagnostics. The original R3b body is used solely
to exercise actual camera rays and UV correspondence.

## API

Inside Blender, `blender_capture.capture_surface(current_object)` reads the
actual evaluated posed mesh and **per-loop triangle corners** of
`MIA_V002_UnderwearUV`. It does not alter the modifier stack or original object.
All surface data are returned in memory; the capture helper never opens, saves
or renders a scene. `actual_camera_frame(record)` reconstructs recorded ORTHO
settings on temporary private IDs, obtains Blender's actual view frame and
removes those IDs. Supplying a final surface cache is also supported without
Blender: arrays are `world[V,3]`, `triangles[T,3]`, `triangle_uv[T,3,2]`.

```python
from surface_seating import seat_path, transfer_barycentric

path = dict(source_pack['paths'][0], source_sha256=source_pack['source']['sha256'])
result = seat_path(
    path, evaluated_surface, actual_camera, registered_view,
    cast_triangle_ids=visible_skin_body_triangles,
    allowed_triangle_ids=authored_torso_region_triangles,
    purpose='production', selection_status='SELECTED_BODY')
assert result['accepted']  # every supplied sample must seat without uncertainty
sample = transfer_barycentric(result['points'][0], result['surface_guards'], evaluated_surface)
```

The caller must supply an anatomical triangle-region policy appropriate to the
specific torso/strap/side-return, pelvis/leg/crotch or neck path. Stable triangle
IDs or bone/part-derived regions can supply this guard. A whole-body material
filter alone does not prove that a hit belongs to the intended anatomical part.
Policy correctness and scene hair/garment occlusion require root's later actual
source review. Explicit `cast_triangle_ids` define visibility scope. The baseline
check casts every actual evaluated owner triangle, including headblend materials
9/10; no material is guessed to be an outline and skipped.

The nearest supplied-body ray hit is retained. A wrong-region foreground hit is
**rejected**, never skipped to reach convenient geometry behind it. Missed rays,
grazing/back-facing surfaces, conflicting cohit UV seams and out-of-view points
also fail. An omitted anatomical region remains UNVERIFIED. There is no nearest
surface fallback, world-height mask, raw-T projection, mirrored hidden pattern
or triangular-cup approximation.

Each successful geometric sample records its triangle ID and barycentric
weights. UV transfer uses that triangle's three actual loop UVs, preserving
seams instead of averaging UVs per vertex. Geometry, ordered triangles, UV layer
and triangle-UV hashes guard reuse. Shape changes require fresh source seating;
changed tessellation/UV correspondence rejects transfer. Animation-only reuse
of a selected attachment can explicitly allow changed geometry while retaining
the exact topology/UV identity; that is not motion acceptance.

## Registration and source pattern scope

`baseline-inputs.json` captures the actual source front/profile/back/oblique
camera matrices, resolution, pixel aspect, clipping and Blender view frames.
Source points remain original1536x1024 pixels. Its inverse registration is the
existing **single** whole-height scale/vertical translation plus per-view pelvis
centering from `body/current-v06-boards.json`; no axis or feature normalization.
Conceptually, `render_x=400+(source_x-source_center_x)/scale` and
`render_y=(source_y-vertical_translation)/scale`. This uses the declared uniform
transform, not separately rounded raster resize dimensions.

Those illustration/camera correspondences remain PROVISIONAL. Production
seating refuses unselected geometry or an unreviewed registration. A selected
new body and its actual camera/framing must be supplied and reviewed; do not
promote this baseline diagnostic configuration by relabelling it.

The source pack keeps the true scoop, distinct upper cup/band transition and
lower band edge, visible strap/side fragments, dipped brief waist, separate
front/back leg coverage and tiny visible crotch turns. All remain separate path
constraints; no hidden back bra/gusset is filled. Neck/clavicle graphic/shadow
paths use the same final posed-surface/UV process after anatomy fitting. RGB
samples remain illustrated appearance, not physical albedo. Complete garment
interpolation, source4 appearance, active shader ancestry and final UV/color/
normal/roughness/runtime acceptance belong to root after shape selection.

## Verification and reproduction

```powershell
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' `
  --background 'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-refinement-v002/integrated/Mia_v0.0.2_Review_R3b.blend' `
  --python-exit-code 2 `
  --python 'C:/Users/antio/.codex/worktrees/mia-v002-face/win-overlay/asset/mia/blender/mia-fit-v003/underwear-fit/run_blender_check.py'
python asset/mia/blender/mia-fit-v003/underwear-fit/run_checks.py
```

`blender-check.json` records actual readback versus the existing checkpoint,
official Blender projection comparisons and original-data preservation.
`checks.json` records actual triangle-interior ray/barycentric/UV probes, source
fragment miss/uncertainty counts and intentional guard failures. Diagnostics
export no final seated garment paths or maps. Their PASS is technical helper
evidence, not BODY_FORM, UNDERWEAR_FIT or ART acceptance. Engram KG/activity tools
were unavailable; no synchronization is claimed.

Actual bounded results:

| Criterion | Runtime evidence | Result |
|---|---|---|
| Current evaluated posed UV/topology correspondence | 80771 vertices/161184 triangles, world/indices/corner UV/materials bit-exact to checkpoint | PASS |
| Actual camera frame/ray calibration | All4 cameras versus Blender's official projection; max0.0000663px | PASS |
| Triangle/barycentric/UV transfer |16 actual triangle-interior probes across4views; max9.61e-9m world /6.54e-9UV error | PASS |
| Unsafe seating rejected | Wrong region, missed ray, conflicting UV seam, changed UV, anisotropic registration, unselected production | PASS |
| Original preservation |620 owners, scene envelope/ID inventory/native hash exact; temporary IDs removed | PASS |
| Final source pattern fitting |123 baseline source samples:40misses,83region-unverified,0accepted pattern points | UNVERIFIED |
| Final UV/shader/source4/garment appearance | Selected body and authoritative region/registration review remain pending | UNVERIFIED |
