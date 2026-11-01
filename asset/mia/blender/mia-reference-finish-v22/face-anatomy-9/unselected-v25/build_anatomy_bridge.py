"""Bounded primary-form trial for the orbital–malar–maxillary transition.

This deliberately starts from the reviewed F2 face.  It moves only the face
skin keys as a relative delta; hair, body, eyes, UVs and materials are guards.
The target is a broad under-orbit to anterior-cheek bridge, not a lower-cheek
inflation or an image-space fit.
"""
import bpy
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np
from mathutils import Vector

HERE = Path(__file__).resolve().parent
SOURCE = Path(r"C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v22/parts/face-finish8-f2-review/native/6d0672ae12ea-Mia_FaceFinish8_ConnectedBuccalF2.blend")
OUT = HERE / "candidate-a1"
OUT.mkdir(parents=True, exist_ok=True)
NATIVE = OUT / "Mia_FaceAnatomy25_OrbitalMalarBridgeA1.blend"
SKIN_NAME = "MIA_V14_SculptedSkin"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def snapshot_all():
    result = {}
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        mesh = obj.data
        result[obj.name] = {
            "vertices": np.array([tuple(v.co) for v in mesh.vertices]),
            "uv": [
                np.array([tuple(loop.uv) for loop in layer.data])
                for layer in mesh.uv_layers
            ],
            "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
            "keys": {
                key.name: np.array([tuple(point.co) for point in key.data])
                for key in mesh.shape_keys.key_blocks
            } if mesh.shape_keys else {},
        }
    return result


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
assert not NATIVE.exists(), "candidate already exists; retain the frozen trial"
skin = bpy.data.objects[SKIN_NAME]
for key in skin.data.shape_keys.key_blocks:
    key.value = 0.0
bpy.context.view_layer.update()
before = snapshot_all()
points = np.array([tuple(point.co) for point in skin.data.shape_keys.key_blocks[0].data])
faces = [list(poly.vertices) for poly in skin.data.polygons]
edge_counts = Counter(
    tuple(sorted((face[i], face[(i + 1) % len(face)])))
    for face in faces for i in range(len(face))
)
boundary = {vertex for edge, count in edge_counts.items() if count == 1 for vertex in edge}

# The F2 lower-aperture protection is retained.  Its mirrored ids are included,
# but the next few interior rings are intentionally not blanket-frozen: that
# would preserve the defect we are trying to diagnose.
protected = {236, 242, 247, 248, 249, 250, 251, 252, 253}
negative = np.where(points[:, 0] < 0)[0]
for index in list(protected):
    counterpart = negative[np.argmin(np.linalg.norm(points[negative] - points[index] * [-1, 1, 1], axis=1))]
    protected.add(int(counterpart))

delta = np.zeros_like(points)
targets = []
for index, (x, y, z) in enumerate(points):
    ax = abs(x)
    if index in boundary or index in protected:
        continue
    # Exclude nasal bridge/wing, eye rim, lower mouth/chin and outer face seam.
    if not (0.018 < ax < 0.071 and 1.503 < z < 1.545 and y > -0.006):
        continue
    # Broad upper front-cheek mass: it begins under the orbit, spreads laterally
    # onto the malar support and fades into the F2 lower-cheek volume.
    lateral = smooth(0.018, 0.030, ax) * (1.0 - smooth(0.061, 0.071, ax))
    vertical = smooth(1.503, 1.512, z) * (1.0 - smooth(1.536, 1.545, z))
    anterior_gate = smooth(-0.006, 0.018, y)
    # The malar apex is lateral and slightly lower than the lower lid.  It is
    # intentionally an asymmetric-in-depth ridge across a *wide* patch, not a
    # spherical cheek mound or a narrow nasolabial groove.
    zygoma = np.exp(-((ax - 0.048) / 0.017) ** 2 - ((z - 1.523) / 0.014) ** 2)
    maxilla = np.exp(-((ax - 0.030) / 0.013) ** 2 - ((z - 1.516) / 0.014) ** 2)
    weight = lateral * vertical * anterior_gate
    forward = weight * (0.0017 + 0.0032 * zygoma + 0.0020 * maxilla)
    # A small outward/downward component prevents a single depth-only trench
    # and carries the mass around the cheek instead of pushing it toward nose.
    delta[index, 0] = np.sign(x) * weight * (0.00035 * zygoma + 0.00018 * maxilla)
    delta[index, 1] = forward
    delta[index, 2] = -weight * (0.00028 * zygoma) + weight * (0.00012 * maxilla)
    if np.linalg.norm(delta[index]) > 1e-8:
        targets.append({"id": int(index), "weight": float(weight), "delta": delta[index].tolist(), "position": points[index].tolist()})

# Apply the same coordinate delta to every key block.  Therefore every relative
# expression deformation remains exactly the same; only its neutral carrier
# surface moves.  This is a guard, not a claim that all expressions are art-fit.
for key in skin.data.shape_keys.key_blocks:
    for index in np.where(np.linalg.norm(delta, axis=1) > 1e-10)[0]:
        key.data[int(index)].co += Vector(delta[int(index)].tolist())
bpy.context.view_layer.update()
after = snapshot_all()

# All non-skin mesh data and every skin relative deformation must be unchanged.
guard_errors = []
for name, old in before.items():
    new = after[name]
    if name != SKIN_NAME:
        for field in ("vertices", "uv", "materials", "keys"):
            if field == "uv":
                same = len(old[field]) == len(new[field]) and all(np.array_equal(a, b) for a, b in zip(old[field], new[field]))
            elif field == "keys":
                same = old[field].keys() == new[field].keys() and all(np.array_equal(old[field][key], new[field][key]) for key in old[field])
            else:
                same = np.array_equal(old[field], new[field]) if field == "vertices" else old[field] == new[field]
            if not same:
                guard_errors.append(f"non_skin_changed:{name}:{field}")
    else:
        if old["materials"] != new["materials"] or len(old["uv"]) != len(new["uv"]) or any(not np.array_equal(a, b) for a, b in zip(old["uv"], new["uv"])):
            guard_errors.append("skin_uv_or_material_changed")
        for key in old["keys"]:
            expected = old["keys"][key] + delta
            if not np.allclose(new["keys"][key], expected, atol=1e-10):
                guard_errors.append(f"skin_relative_delta_failed:{key}")
assert not guard_errors, guard_errors

bpy.ops.wm.save_as_mainfile(filepath=str(NATIVE))
assert sha(SOURCE) == "6d0672ae12eaa0c8a4386a42291e2bb39cf9b70921d5183929500df2fa63eef9"
(OUT / "vertex-deltas.json").write_text(json.dumps(targets, indent=2), encoding="utf-8")
(OUT / "manifest.json").write_text(json.dumps({
    "status": "WORKING CANDIDATE / ART UNAPPROVED",
    "baseline": {"path": str(SOURCE), "sha256": sha(SOURCE)},
    "native": {"path": str(NATIVE), "sha256": sha(NATIVE)},
    "owner": SKIN_NAME,
    "changed_vertices": len(targets),
    "max_delta_m": float(np.linalg.norm(delta, axis=1).max()),
    "guard_errors": guard_errors,
    "method": "one broad orbital-malar-maxillary bridge patch; same delta replayed to every relative face key",
    "limits": [
        "Candidate only. Visual continuity and source likeness require actual review.",
        "No topology change, no global smoothing, no body/hair/eye geometry edit.",
        "Aperture boundary vertices remain exact; adjacent rings intentionally remain editable."
    ]
}, indent=2), encoding="utf-8")
print("ANATOMY_A1_DONE", len(targets), float(np.linalg.norm(delta, axis=1).max()))
