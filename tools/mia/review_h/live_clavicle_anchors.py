"""Read-only actual D shoulder/neck surface stations; not inferred bone positions."""
from pathlib import Path
import hashlib
import json
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path('D:/MiaWorkCache/mia-reference-work/win-overlay')
ob = bpy.data.objects['MIA_Review12_H_LiveRepair']
v = np.array([p.co[:] for p in ob.data.vertices], np.float32)
before = hashlib.sha256(v.tobytes()).hexdigest()
assert before == '69d4d4f0ea907da2474bc74f4b55312971d137f0911bdf9089fc02509a6bf25a'
f = np.array([p.vertices[:] for p in ob.data.polygons], np.int32)
tree = BVHTree.FromPolygons([Vector(p) for p in v], f.tolist(), all_triangles=True)
rows = []
for x, z in [(0., 1.405), (0., 1.385), (.025, 1.405), (.05, 1.39),
             (.08, 1.385), (.11, 1.38), (.14, 1.375), (.16, 1.38),
             (.175, 1.35), (.15, 1.335)]:
    for side in ([1] if x == 0 else [-1, 1]):
        hit, normal, index, distance = tree.ray_cast(Vector((side*x, -1., z)), Vector((0., 1., 0.)), 2.)
        rows.append(dict(station=[side*x, z], surface_hit=list(hit) if hit else None,
                         normal=list(normal) if normal else None, triangle=index,
                         vertex_ids=f[index].tolist() if index is not None else []))
out = ROOT/'.mia-cache/body-h/live/clavicle-surface-stations.json'
assert not out.exists()
report = dict(scope='Current D exterior stations for anatomical edit planning; coordinates are not source bone landmarks',
              before_sha256=before, actual_live_geometry=True, geometry_modified=False,
              stations=rows, native_saved=False)
assert hashlib.sha256(np.array([p.co[:] for p in ob.data.vertices], np.float32).tobytes()).hexdigest() == before
out.write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
print(json.dumps(report))
