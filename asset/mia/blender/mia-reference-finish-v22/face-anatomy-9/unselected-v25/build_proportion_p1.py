"""Whole-face primary proportion trial from the immutable integrated WIP8."""
import bpy
import hashlib
import json
from pathlib import Path

import numpy as np
from mathutils import Vector


HERE = Path(__file__).resolve().parent
SOURCE = Path(r"C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v22/integration-wip-8-review/Mia_ReferenceFinish_v22.blend")
EXPECTED_SOURCE_SHA = "ff2b61b2b2146fc4f73119cf10534571609dff75f6333fbec34d0926068b8bb4"
OUT = HERE / "proportion-p1"
NATIVE = OUT / "Mia_ReferenceFinish_WIP8_ProportionP1.blend"
SKIN = "MIA_V14_SculptedSkin"
CONTINUITY_OWNERS = (
    "MIA_V14_MouthSeam",
    "MIA_V13_FaceOutline",
    "MIA_V17_RootLining_MIA_V14_SculptedSkin",
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def smoothstep(lo, hi, value):
    t = np.clip((value - lo) / (hi - lo), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def bell(value, centre, width):
    return np.exp(-((value - centre) / width) ** 2)


def carrier_delta(point):
    """A coordinated lower-face carrier, expressed in skin local space.

    The field deliberately starts below the eyelid line.  It lengthens the
    mouth-to-chin carrier and broadens the mandibular side before the chin,
    rather than pulling the chin into a longer V.  A weak upper-cheek fade
    avoids treating the old cheek width as a fixed boundary.
    """
    x, y, z = point
    ax = abs(x)
    front = smoothstep(-0.010, 0.018, y)
    below_eye = 1.0 - smoothstep(1.523, 1.540, z)
    lower = 1.0 - smoothstep(1.486, 1.518, z)
    chin = bell(z, 1.477, 0.013)
    mandible = bell(z, 1.493, 0.018) * smoothstep(0.020, 0.036, ax) * (1.0 - smoothstep(0.064, 0.078, ax))
    upper_cheek = bell(z, 1.519, 0.010) * smoothstep(0.024, 0.040, ax)
    side = smoothstep(0.012, 0.026, y)

    # A vertical carrier elongation, increasing continuously from the lower
    # orbit through the mouth mass to the chin.  The chin is not singled out.
    dz = -front * (0.0010 * below_eye + 0.0045 * lower + 0.0015 * chin)

    # The jaw turns gradually from cheek into a rounded lower width.  The
    # terminal central chin remains nearly fixed in X, preventing a V taper.
    dx = np.sign(x) * front * (
        0.0038 * mandible
        + 0.0010 * lower * smoothstep(0.032, 0.050, ax)
        - 0.00075 * upper_cheek
    )
    dy = front * side * (0.00045 * mandible - 0.00018 * upper_cheek)
    return np.array((dx, dy, dz), dtype=float)


def local_delta_for_owner(skin, owner, point):
    skin_local = skin.matrix_world.inverted() @ owner.matrix_world @ point.co
    delta_skin = carrier_delta(np.array(skin_local, dtype=float))
    before_world = skin.matrix_world @ skin_local
    after_world = skin.matrix_world @ (skin_local + Vector(delta_skin.tolist()))
    return owner.matrix_world.inverted().to_3x3() @ (after_world - before_world)


def snapshot_surface(obj):
    return {
        "coords": [tuple(v.co) for v in obj.data.vertices],
        "uvs": [[tuple(loop.uv) for loop in layer.data] for layer in obj.data.uv_layers],
        "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
        "polygons": [tuple(poly.vertices) for poly in obj.data.polygons],
    }


def assert_unchanged(label, obj, before, errors):
    after = snapshot_surface(obj)
    if after["coords"] != before["coords"]:
        errors.append("unexpected_coordinate_change:" + label)
    if after["uvs"] != before["uvs"]:
        errors.append("unexpected_uv_change:" + label)
    if after["materials"] != before["materials"]:
        errors.append("unexpected_material_change:" + label)
    if after["polygons"] != before["polygons"]:
        errors.append("unexpected_topology_change:" + label)


assert sha(SOURCE) == EXPECTED_SOURCE_SHA, "baseline hash drift"
OUT.mkdir(parents=True, exist_ok=True)
assert not NATIVE.exists(), "candidate already exists; use a new pass, do not overwrite evidence"
bpy.ops.wm.open_mainfile(filepath=str(SOURCE), use_scripts=False)
skin = bpy.data.objects[SKIN]
assert skin.type == "MESH" and skin.data.shape_keys, "missing face carrier keys"
owners = [bpy.data.objects[name] for name in CONTINUITY_OWNERS]
assert all(owner and owner.type == "MESH" for owner in owners), "continuity owner missing"

all_meshes = {obj.name: snapshot_surface(obj) for obj in bpy.data.objects if obj.type == "MESH"}
skin_basis = skin.data.shape_keys.key_blocks[0]
skin_delta = np.array([carrier_delta(np.array(point.co, dtype=float)) for point in skin_basis.data])
changed = np.where(np.linalg.norm(skin_delta, axis=1) > 1e-9)[0]
assert len(changed) > 0

# Shape-key coordinates receive the same carrier-space delta based on Basis,
# retaining each key's existing relative facial deformation.
for key in skin.data.shape_keys.key_blocks:
    for index in changed:
        key.data[int(index)].co += Vector(skin_delta[int(index)].tolist())

owner_reports = {}
for owner in owners:
    if owner.data.shape_keys:
        basis = owner.data.shape_keys.key_blocks[0]
        deltas = [local_delta_for_owner(skin, owner, point) for point in basis.data]
        for key in owner.data.shape_keys.key_blocks:
            for index, delta in enumerate(deltas):
                if delta.length > 1e-10:
                    key.data[index].co += delta
    else:
        deltas = [local_delta_for_owner(skin, owner, point) for point in owner.data.vertices]
        for index, delta in enumerate(deltas):
            if delta.length > 1e-10:
                owner.data.vertices[index].co += delta
    owner_reports[owner.name] = {
        "changed_vertices": sum(delta.length > 1e-10 for delta in deltas),
        "max_delta_m": max((delta.length for delta in deltas), default=0.0),
    }

bpy.context.view_layer.update()
errors = []
for name, before in all_meshes.items():
    if name in (SKIN, *CONTINUITY_OWNERS):
        continue
    assert_unchanged(name, bpy.data.objects[name], before, errors)
assert not errors, errors

bpy.ops.wm.save_as_mainfile(filepath=str(NATIVE))
landmarks = {
    "source_manual_px": {
        "left_pupil": [450, 324], "right_pupil": [582, 310],
        "mouth": [518, 412], "chin": [520, 463],
    },
    "wip8_raw_render_manual_px": {
        "left_pupil": [383, 539], "right_pupil": [614, 513],
        "mouth": [522, 688], "chin": [525, 765],
    },
    "limit": "Manual landmarks are approximate and include source roll, hair and pose uncertainty. They guide review; no exact percentage was imposed.",
}
report = {
    "status": "WORKING CANDIDATE / ART UNAPPROVED",
    "baseline": {"path": str(SOURCE), "sha256": EXPECTED_SOURCE_SHA},
    "native": {"path": str(NATIVE), "sha256": sha(NATIVE)},
    "pass": "whole-face-primary-proportion P1",
    "coordinate_space": "carrier is evaluated in skin local space; each continuity owner maps world -> skin local -> owner local",
    "method": "Low-frequency lower-orbit-to-chin carrier: continuous vertical extension plus broad mandibular side width, with a small upper-cheek fade. No source image fit, global smooth, UV edit, or pigment change.",
    "skin": {"changed_vertices": int(len(changed)), "max_delta_m": float(np.linalg.norm(skin_delta, axis=1).max())},
    "continuity_owners": owner_reports,
    "guards": {"source_hash": EXPECTED_SOURCE_SHA, "non_target_meshes_exact": True, "uv_material_topology_unchanged": True, "skin_keys_shifted_equally": True, "errors": errors},
    "landmark_record": landmarks,
    "limits": ["P1 is only the primary proportion/jaw pass. Eyelid geometry and pigment are intentionally untouched.", "Requires frozen-camera front/profile/both-oblique review and blink/mouth probes before any selection."],
}
(OUT / "manifest.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
(OUT / "landmark-record.json").write_text(json.dumps(landmarks, indent=2), encoding="utf-8")
print("PROPORTION_P1_DONE", len(changed), float(np.linalg.norm(skin_delta, axis=1).max()), owner_reports)
