import json
from collections import Counter, defaultdict
from pathlib import Path

import bpy
import numpy as np


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "proportion-p2" / "Mia_ReferenceFinish_WIP8_ProportionP2.blend"
SKIN = "MIA_V14_SculptedSkin"

bpy.ops.wm.open_mainfile(filepath=str(SOURCE), use_scripts=False)
skin = bpy.data.objects[SKIN]
for key in skin.data.shape_keys.key_blocks:
    key.value = 0.0
bpy.context.view_layer.update()
obj = skin.evaluated_get(bpy.context.evaluated_depsgraph_get())
mesh = obj.to_mesh()
points = np.array([tuple(vertex.co) for vertex in mesh.vertices])
faces = [tuple(poly.vertices) for poly in mesh.polygons]
obj.to_mesh_clear()
edges = Counter(tuple(sorted((face[i], face[(i + 1) % len(face)]))) for face in faces for i in range(len(face)))
boundary = defaultdict(list)
for (a, b), count in edges.items():
    if count == 1:
        boundary[a].append(b)
        boundary[b].append(a)
remaining = set(boundary)
loops = []
while remaining:
    start = min(remaining)
    stack, group = [start], set()
    while stack:
        vertex = stack.pop()
        if vertex in group:
            continue
        group.add(vertex)
        stack.extend(boundary[vertex])
    remaining -= group
    centre = points[list(group)].mean(axis=0)
    if len(group) > 40 and .01 < abs(centre[0]) < .06 and centre[1] > .035 and 1.525 < centre[2] < 1.555:
        inner = min(group, key=lambda item: abs(points[item, 0]))
        outer = max(group, key=lambda item: abs(points[item, 0]))
        branches = []
        for first in boundary[inner]:
            path = [inner, first]
            while path[-1] != outer:
                choices = [item for item in boundary[path[-1]] if item != path[-2]]
                if len(choices) != 1:
                    raise RuntimeError("non-simple eye boundary")
                path.append(choices[0])
            branches.append(path)
        branches.sort(key=lambda path: float(points[path, 2].mean()), reverse=True)
        loops.append({"side": int(np.sign(centre[0])), "upper": branches[0], "lower": branches[1], "centre": centre.tolist()})
assert len(loops) == 2, len(loops)
report = {
    "source": str(SOURCE),
    "method": "actual evaluated neutral boundary topology; upper/lower branch assigned by mean Z, not by object-name guess",
    "loops": loops,
    "owner_roles": {
        "skin_aperture": SKIN,
        "eye_surface": "MIA_V14_EyeSurface",
        "upper_lashes": ["MIA_V14_UpperLash_-1", "MIA_V14_UpperLash_1"],
        "outer_wings": ["MIA_V14_OuterWing_-1", "MIA_V14_OuterWing_1"],
        "lower_lid_cards": ["MIA_V12_FineLowerLid_-1", "MIA_V12_FineLowerLid_1"],
    },
    "limit": "This identifies the actual rim paths only. It does not assert a source-matched curve or modify any owner.",
}
(HERE / "proportion-p2" / "eye-rim-topology.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("P2_EYE_RIMS_DONE", [(item["side"], len(item["upper"]), len(item["lower"])) for item in loops])
