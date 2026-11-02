# Empirical frame-1 Armature control-space mapping

Bounded CPU helper for `MIA_V27_SharedHeadBody` in immutable
`Mia_v0.0.2_Review_R3b.blend`, SHA256
`4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1`.
This is a technical coordinate-space result. No body shaping, rig retarget,
native save, render, source-art acceptance, upload, install, or settings change.

The saved frame 1 is a low-A pose; raw local mesh coordinates are near a T pose.
The owner also has a world rotation of approximately 180 degrees about Z.
The map measures the actual current Blender result, including those transforms.

## API and scope

```python
import sys
sys.path.insert(0, r'C:/Users/antio/.codex/worktrees/mia-v002-face/win-overlay/asset/mia/blender/mia-fit-v003/pose-space')
from pose_space import build_mapping, target_world_to_local_delta, save_mapping

mapping = build_mapping(bpy.data.objects['MIA_V27_SharedHeadBody'])
delta_local = target_world_to_local_delta(mapping, target_world)  # (4647, 3)
# This is an ADDITIVE pre-Armature local offset, not an absolute local position.
save_mapping(mapping, '/absolute/path/map-stem')  # NPZ + JSON only
```

`build_mapping(current_object)` never opens or saves a scene. It copies the object
and mesh, checks that its shape-key data are private, inserts a GN Set Position
offset from a private FLOAT_VECTOR/POINT attribute immediately before the
Armature, and disables post-Armature modifiers on the copy. It evaluates zero and
central +/-10 mm local-axis probes. Original mesh/key data, weights, modifiers,
rig pose/rest and scene settings are untouched. Finally it removes only its own
copy, mesh, keys, attribute (with mesh), and node group.

The map is **original current shape keys + Armature only**, before Weld, Subsurf,
Smooth and outlines, in original raw vertex order. Enabled pre-Armature modifiers
and multiple/multi Armatures are rejected. Rebuild for a different pose, weights,
shape-key state or transform; never use subdivided indices. Actual envelope and
preserve-volume flags are recorded. This implementation does not assume LBS or
manually invert bone matrices. A finite field check cannot prove affine response
for every possible field or every future pose.

Array convention:

| NPZ array | Shape | Meaning |
|---|---|---|
| `q0_world` | N,3 | Actual posed world cage at zero added offset |
| `q0_local` | N,3 | Actual Armature-only posed cage in owner-local axes |
| `J_world_from_local` | N,3,3 | [vertex, world axis, local offset axis] |
| `local_from_world` | N,3,3 | Inverse [vertex, local offset axis, world axis] |
| `matrix_world` | 4,4 | Owner world matrix at build time |
| `control_local` | N,3 | Original raw mesh coordinates; not posed coordinates |
| `condition`, `singular_values` | N / N,3 | Conditioning evidence |
| `test_*` | N,3 | Independent field and actual evaluated roundtrip evidence |

```python
import json
import numpy as np
a = np.load('mapping-frame1.npz', allow_pickle=False)
meta = json.load(open('mapping-frame1.json', encoding='utf-8'))
assert meta['status'] == 'PASS'
delta_local = np.einsum('nij,nj->ni', a['local_from_world'], target_world - a['q0_world'])
```

JSON contains the NPZ SHA256 and pose SHA256. `pose_signature(obj, armature_mod)`
can guard the complete pose/weights/key state before using a saved map. The pose
hash includes rig rest matrices, evaluated pose matrices, pose bases, owner/rig
transforms, deform/envelope settings, weights, original key coordinates/values,
raw coordinates, frame and control settings.

## Acceptance contract and actual results

| ID | Required runtime outcome | Verification/evidence | Result |
|---|---|---|---|
| AC1 | Actual world/local map for 4647 original vertices, original 47 keys, frame 1 before post modifiers | Fresh Blender `run_verifier.py`; NPZ/JSON | PASS |
| AC2 | Independent meaningful nonuniform smooth 20-40 mm field actually re-evaluates after inversion | `test_*` arrays and JSON measured forward/inverse/roundtrip errors | PASS |
| AC3 | Original keys, UV, materials, weights, rig rest+pose, all original scene owners/envelope and native hash preserved; own temporaries removed | Before/after read-only signatures in `verification.json` | PASS |
| AC4 | CPU/background execution, no render or full native generated | Command/log and implementation; only small NPZ/JSON proof | PASS |

The exact baseline contains **620** objects, including the earlier 618 owners.
All 620 before/after owner signatures, mesh/key/UV data, materials/node groups,
weights, rig state, ID inventory and scene envelope signatures match exactly.
No `_MIA_POSE_SPACE_` temporary ID remains. Original native SHA256 is unchanged.

- Armature: `MIA_V06_RIG`; preserve volume/DQ **false**, vertex groups **true**,
  bone envelopes **false**, multi modifier **false**.
- Jacobian condition max **1.165902764**, minimum singular value **0.857704322**.
- Independent smooth field magnitude **23.0617-40.0000 mm**.
- Forward prediction error max **0.000569653 mm**.
- World-to-local recovery error max **0.000584579 mm**.
- Actual re-evaluated world roundtrip max **0.000558446 mm**, RMS **0.000109720 mm**.
- Acceptance tolerance **0.020 mm**; zero-offset GN versus no GN **exactly 0**.
- Source-art, final post-modifier body fitting, arbitrary future poses: **UNVERIFIED**.

## Reproduce

Only this separate verifier process opens the baseline (through Blender's CLI);
the helper itself never does. No GPU/render invocation is made.

```powershell
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' `
  --background 'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-refinement-v002/integrated/Mia_v0.0.2_Review_R3b.blend' `
  --python-exit-code 2 `
  --python 'C:/Users/antio/.codex/worktrees/mia-v002-face/win-overlay/asset/mia/blender/mia-fit-v003/pose-space/run_verifier.py' `
  *> 'C:/Users/antio/.codex/worktrees/mia-v002-face/win-overlay/asset/mia/blender/mia-fit-v003/pose-space/verification.log'
```

Engram KG/activity tools were unavailable; no KG or activity synchronization is claimed.
