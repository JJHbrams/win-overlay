import bpy
import json
from pathlib import Path

from mathutils import Vector


HERE = Path(__file__).resolve().parent
SOURCE = Path(r"C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v22/integration-wip-8-review/Mia_ReferenceFinish_v22.blend")
NAMES = (
    "MIA_V14_SculptedSkin",
    "MIA_V14_MouthSeam",
    "MIA_V13_FaceOutline",
    "MIA_V17_RootLining_MIA_V14_SculptedSkin",
    "MIA_V14_EyeSurface",
    "MIA_V14_UpperLash_-1",
    "MIA_V14_UpperLash_1",
)


def bounds(points):
    return [[min(point[i] for point in points), max(point[i] for point in points)] for i in range(3)]


bpy.ops.wm.open_mainfile(filepath=str(SOURCE), use_scripts=False)
rows = []
for name in NAMES:
    obj = bpy.data.objects.get(name)
    assert obj and obj.type == "MESH", name
    local = [Vector(vertex.co) for vertex in obj.data.vertices]
    world = [obj.matrix_world @ point for point in local]
    rows.append({
        "name": name,
        "hide_render": obj.hide_render,
        "hide_viewport": obj.hide_get(),
        "collections": [collection.name for collection in obj.users_collection],
        "parent": obj.parent.name if obj.parent else None,
        "matrix_world": [[float(value) for value in row] for row in obj.matrix_world],
        "local_bounds": bounds(local),
        "world_bounds": bounds(world),
        "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
        "shape_keys": [key.name for key in obj.data.shape_keys.key_blocks] if obj.data.shape_keys else [],
    })
(HERE / "owner-coordinate-diagnosis.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
print("OWNER_COORDINATE_DIAGNOSIS_DONE", len(rows))
