"""Read-only fresh native geometry check, executed by background Blender."""
import json
from pathlib import Path

import bpy
import numpy as np

root = Path(__file__).resolve().parents[5]
pack = root / 'asset/mia/blender/mia-fit-v003/body/shoulder11'
data = np.load(pack / 'shoulder11-canonical.npz')
meshes = [obj for obj in bpy.data.objects if obj.type == 'MESH']
assert len(meshes) == 1 and len(bpy.data.objects) == 14
obj = meshes[0]
vertices = np.asarray([v.co[:] for v in obj.data.vertices], np.float32)
triangles = np.asarray([p.vertices[:] for p in obj.data.polygons], np.int32)
assert np.array_equal(vertices, data['world'])
assert np.array_equal(triangles, data['triangles'])
assert np.array_equal(np.array(obj.matrix_world), np.eye(4))
assert not obj.data.shape_keys and not obj.data.uv_layers
assert not obj.vertex_groups and not obj.modifiers
assert Path(bpy.data.filepath).resolve() == (pack / 'native/Mia_Shoulder11_STATIC_ShapeGuide.blend').resolve()
print('CANONICAL_SHOULDER11_REOPEN_PASS', json.dumps(dict(
    vertices=len(vertices), triangles=len(triangles), saved_native_exact_FINAL=True,
    static_only=True, GPU_render_called=False, files_written=False)))
