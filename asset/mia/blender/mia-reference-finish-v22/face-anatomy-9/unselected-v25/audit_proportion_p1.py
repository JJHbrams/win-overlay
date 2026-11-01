import json
from pathlib import Path

import bpy
import numpy as np


HERE = Path(__file__).resolve().parent
BASELINE = Path(r"C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v22/integration-wip-8-review/Mia_ReferenceFinish_v22.blend")
CANDIDATE = HERE / "proportion-p1" / "Mia_ReferenceFinish_WIP8_ProportionP1.blend"
SKIN = "MIA_V14_SculptedSkin"


def mesh_snapshot(obj):
    return {
        "coords": np.array([tuple(vertex.co) for vertex in obj.data.vertices]),
        "uvs": [[tuple(loop.uv) for loop in layer.data] for layer in obj.data.uv_layers],
        "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
        "polygons": [tuple(poly.vertices) for poly in obj.data.polygons],
        "keys": {
            key.name: np.array([tuple(point.co) for point in key.data])
            for key in obj.data.shape_keys.key_blocks
        } if obj.data.shape_keys else {},
    }


def scene_snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path), use_scripts=False)
    return {obj.name: mesh_snapshot(obj) for obj in bpy.data.objects if obj.type == "MESH"}


before = scene_snapshot(BASELINE)
after = scene_snapshot(CANDIDATE)
assert before.keys() == after.keys(), "mesh owner set changed"
rows = {}
failures = []
for name in sorted(before):
    old, new = before[name], after[name]
    base_equal = bool(np.array_equal(old["coords"], new["coords"]))
    uvs_equal = old["uvs"] == new["uvs"]
    materials_equal = old["materials"] == new["materials"]
    topology_equal = old["polygons"] == new["polygons"]
    key_names_equal = old["keys"].keys() == new["keys"].keys()
    row = {
        "base_coordinates_equal": base_equal,
        "uvs_equal": uvs_equal,
        "materials_equal": materials_equal,
        "topology_equal": topology_equal,
        "shape_key_names_equal": key_names_equal,
    }
    if name == SKIN:
        basis_delta = new["keys"]["Basis"] - old["keys"]["Basis"]
        residuals = {
            key: float(np.abs((new_points - old["keys"][key]) - basis_delta).max())
            for key, new_points in new["keys"].items()
        }
        row["basis_changed_vertices"] = int(np.sum(np.linalg.norm(basis_delta, axis=1) > 1e-10))
        row["basis_max_delta_m"] = float(np.linalg.norm(basis_delta, axis=1).max())
        row["relative_key_delta_residual_max_m"] = max(residuals.values(), default=0.0)
        row["relative_key_delta_residuals_m"] = residuals
        if row["relative_key_delta_residual_max_m"] > 2e-7:
            failures.append("skin_relative_key_delta_mismatch")
    elif not base_equal:
        failures.append("non_skin_coordinate_change:" + name)
    if not (uvs_equal and materials_equal and topology_equal and key_names_equal):
        failures.append("surface_structure_change:" + name)
    rows[name] = row

report = {
    "status": "TECHNICAL AUDIT ONLY / ART UNAPPROVED",
    "baseline": str(BASELINE),
    "candidate": str(CANDIDATE),
    "skin_owner": SKIN,
    "owners": rows,
    "failures": failures,
    "result": "PASS" if not failures else "FAIL",
    "limits": [
        "This checks saved mesh/UV/material/topology/key data, not artistic source match.",
        "Blink and mouth probes are visual evidence only; they do not prove every expression.",
    ],
}
(HERE / "proportion-p1" / "technical-audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
assert not failures, failures
print("PROPORTION_P1_AUDIT_PASS", rows[SKIN]["basis_changed_vertices"], rows[SKIN]["basis_max_delta_m"])
