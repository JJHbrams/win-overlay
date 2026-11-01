"""WIP8 lower-face proportion correction with the mouth-height anchor retained."""
import bpy
import hashlib
import json
from pathlib import Path

import numpy as np
from mathutils import Vector


HERE = Path(__file__).resolve().parent
SOURCE = Path(r"C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v22/integration-wip-8-review/Mia_ReferenceFinish_v22.blend")
SOURCE_SHA = "ff2b61b2b2146fc4f73119cf10534571609dff75f6333fbec34d0926068b8bb4"
OUT = HERE / "proportion-p2"
NATIVE = OUT / "Mia_ReferenceFinish_WIP8_ProportionP2.blend"
SKIN = "MIA_V14_SculptedSkin"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def smoothstep(lo, hi, value):
    t = np.clip((value - lo) / (hi - lo), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def bell(value, centre, width):
    return np.exp(-((value - centre) / width) ** 2)


def lower_face_delta(point):
    """Keep the mouth anchor, lengthen and round only the lower facial carrier."""
    x, y, z = point
    ax = abs(x)
    front = smoothstep(-0.010, 0.016, y)
    # The actual hidden legacy mouth seam lies around Z 1.496.  This starts
    # below it so eye-to-mouth placement is not moved by this pass.
    under_mouth = 1.0 - smoothstep(1.496, 1.503, z)
    lower_side = bell(z, 1.488, 0.014) * smoothstep(0.022, 0.036, ax) * (1.0 - smoothstep(0.064, 0.080, ax))
    chin_band = bell(z, 1.475, 0.012) * smoothstep(0.008, 0.022, ax) * (1.0 - smoothstep(0.050, 0.068, ax))
    jaw_fade = smoothstep(1.463, 1.470, z)

    # Four millimetres at the lower carrier, smoothly anchored at the mouth.
    dz = -front * under_mouth * jaw_fade * 0.0040
    # The lower sides open before the chin, retaining a rounded terminal
    # region instead of solving vertical proportion with a sharper V.
    dx = np.sign(x) * front * (0.0030 * lower_side + 0.0009 * chin_band)
    dy = front * (0.00035 * lower_side)
    return np.array((dx, dy, dz), dtype=float)


def snapshot(obj):
    return {
        "coords": np.array([tuple(vertex.co) for vertex in obj.data.vertices]),
        "uvs": [[tuple(loop.uv) for loop in layer.data] for layer in obj.data.uv_layers],
        "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
        "polygons": [tuple(poly.vertices) for poly in obj.data.polygons],
        "key_names": [key.name for key in obj.data.shape_keys.key_blocks] if obj.data.shape_keys else [],
    }


assert sha(SOURCE) == SOURCE_SHA, "baseline hash drift"
OUT.mkdir(parents=True, exist_ok=True)
assert not NATIVE.exists(), "existing P2 evidence must not be overwritten"
bpy.ops.wm.open_mainfile(filepath=str(SOURCE), use_scripts=False)
skin = bpy.data.objects[SKIN]
before = {obj.name: snapshot(obj) for obj in bpy.data.objects if obj.type == "MESH"}
keys = skin.data.shape_keys.key_blocks
basis = keys[0]
delta = np.array([lower_face_delta(np.array(point.co, dtype=float)) for point in basis.data])
changed = np.where(np.linalg.norm(delta, axis=1) > 1e-9)[0]
assert len(changed) > 0
for key in keys:
    for index in changed:
        key.data[int(index)].co += Vector(delta[int(index)].tolist())
bpy.context.view_layer.update()

errors = []
for name, old in before.items():
    obj = bpy.data.objects[name]
    now = snapshot(obj)
    if name != SKIN and not np.array_equal(old["coords"], now["coords"]):
        errors.append("non_skin_coordinate_change:" + name)
    if old["uvs"] != now["uvs"] or old["materials"] != now["materials"] or old["polygons"] != now["polygons"] or old["key_names"] != now["key_names"]:
        errors.append("surface_structure_change:" + name)
assert not errors, errors
bpy.ops.wm.save_as_mainfile(filepath=str(NATIVE))

report = {
    "status": "WORKING CANDIDATE / ART UNAPPROVED",
    "baseline": {"path": str(SOURCE), "sha256": SOURCE_SHA},
    "native": {"path": str(NATIVE), "sha256": sha(NATIVE)},
    "pass": "whole-face-primary-proportion P2 lower-face anchor correction",
    "coordinate_space": "skin Basis local space; skin local +Y is the facial anterior axis",
    "method": "Fresh WIP8 pass. Mouth-height region is held by a Z 1.496-1.503 taper; lower face moves down a maximum 4mm and jaw sides open before the chin. No eye, lid, lash, UV, pigment, global-scale or image-fit change.",
    "skin": {"changed_vertices": int(len(changed)), "max_delta_m": float(np.linalg.norm(delta, axis=1).max())},
    "guards": {"all_non_skin_mesh_coordinates_exact": True, "all_mesh_uv_material_topology_key_names_exact": True, "all_skin_shape_keys_receive_basis_delta": True, "errors": errors},
    "landmark_hypothesis": {"eye_to_mouth": "retain WIP8 approximately; source and WIP8 were already near under manual IPD-normalized observation", "mouth_to_chin": "increase modestly; initial visual test uses about 4mm lower-carrier displacement, not a fixed source measurement"},
    "limits": ["P2 does not solve the midface wedge or eyelid curvature; those require subsequent isolated passes.", "Actual source/baseline/candidate fixed-camera review and limited deformation probes remain required before selection."],
}
(OUT / "manifest.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("PROPORTION_P2_DONE", len(changed), float(np.linalg.norm(delta, axis=1).max()))
