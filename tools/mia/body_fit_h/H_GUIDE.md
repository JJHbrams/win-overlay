# H roof guide checkpoint

The single H guide is CPU-ready for static assembly and remains **ART UNVERIFIED**.
There has been one native Geometry Nodes VolumeCube/VolumeToMesh evaluation,
no GPU work, no native save, no input copies, and no neck AP/RY or head transform.
Root owns subsequent neck construction, source-view review and adoption.

The roof-only fit starts from the neutral five-parameter seed, with one shared
camera estimate per source panel. It meets 27/33 observed roof intervals; six
remain outside, with maximum excess 5.828 mm. This is neither a complete source
fit nor a profile fit. The stopped profile-constrained attempt is preserved.
The field gate, nesting proof, radii and physical diagnostics are in the ignored
`roof-fit.json`; the compact parameters are in `roof_candidate.json`. That
configuration records the RAM phase at its creation, before meshing.

## One mesh and explicit lower-boundary constraint

`build_mesh.py` emitted `H-guide-raw.npz` and correctly stopped: ten lower
vertices moved by up to 33.2594 micrometres despite pointwise field identity.
The VDB grid cell straddles the Z=1.34 boundary. This is real stencil influence,
**not roundoff**. The raw mesh and original STOP report remain unchanged.

Root then explicitly authorized `finalize_guide.py` to restore exactly those
ten Z coordinates to their unique source11 counterparts, without another
meshing run. X/Y were already exact; every other coordinate is held. The
adjacent-face geometric normal changes by at most 0.276029 degrees and local
edge-turn change by at most 0.344660 degrees. Restored coordinates do not
change implicit-field inside/outside membership at any of the ten points;
the restored H and source11 field values agree exactly there. Field values
are not geometric distances, and the repaired mesh is explicitly a constrained
boundary discretization of the field, not a second field fit.

Final physical retention is complete: 49,658 lower source vertices and 98,928
oriented lower triangles are exact after spatial correspondence. The final
mesh has 65,362 vertices and 130,720 triangles, one closed consistently oriented
component, no zero-area faces and no nonadjacent self-intersections. The
whole-guide BVH has zero nonadjacent overlap candidates; shared-vertex pairs
are treated as adjacent. This floating-point BVH/SAT check uses a 1e-9 m
intersection tolerance and does not prove adjacent-fan or curvature quality.
The one-ring change figures come from the hashed RAM halo diagnostic on the
same restored coordinates. An independent read-only code/proof review found
no material scope mismatch; it did not grant ART acceptance.
Signed upper-guide volume changes by -855.893 mL
from source11; that includes the temporary neck stub and is not a wholebody
or medical volume.

Actual triangle surface outside |X|>=0.085 reaches Z=1.397294489. The planar
Z=1.400 cut has one closed 367-point intersection loop, with X bounds
[-0.071203598, 0.071188552] and Y bounds [-0.068020387, 0.053898558].
Additional measured sections at 1.397, 1.415, 1.420 and 1.434 are recorded.
Waist and arm endpoint loops below the held boundary retain their complete
physical triangles; other loops on the same planes are not relabelled as arms.

## Local artifacts and commands

All raw artifacts are ignored local files under
`D:/MiaWorkCache/mia-reference-work/win-overlay/.mia-cache/body-h/shape/`.
`guide_artifact_receipt.json` records exact paths, byte sizes and SHA256 values.
These raw files are not contained in a Git clone. No cache deletion is authorized.

The final assembly input is `H-guide.npz` (world float32 coordinates and int32
triangles), SHA256 `098b13d96c880a701218f003b92c0c13254979639b5a8b9d1bea318dc891ac04`.
`H-lower-correspondence.npz` maps source11 IDs to final H IDs.

The executed commands used Blender 5.2.3 in factory-empty background mode:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:TEMP='D:/MiaWorkCache/mia-reference-work/runtime-temp'
$env:TMP=$env:TEMP
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' --background --factory-startup --python-exit-code 2 --python 'D:/MiaWorkCache/mia-reference-work/shape-h-author/tools/mia/body_fit_h/build_mesh.py'
# The initial STOP was followed by the authorized RAM halo diagnostic:
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' --background --factory-startup --python-exit-code 2 --python 'D:/MiaWorkCache/mia-reference-work/shape-h-author/tools/mia/body_fit_h/diagnose_halo.py'
# Only this finalizer exported the final guide; it does not run the mesher:
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' --background --factory-startup --python-exit-code 2 --python 'D:/MiaWorkCache/mia-reference-work/shape-h-author/tools/mia/body_fit_h/finalize_guide.py'
```

Each writer invokes the canonical storage capacity guard. The scripts refuse
to overwrite their frozen outputs; do not rerun the one-mesh build in the
current cache. No second guide, amplitude sweep, render, bake or native export
is authorized by this checkpoint. Source4/high-low form, fresh neck joins,
head/body proportions and final material/GIF delivery remain open.
