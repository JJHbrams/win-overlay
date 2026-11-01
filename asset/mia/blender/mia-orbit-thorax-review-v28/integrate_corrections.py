"""Apply a frozen Body-prefix handoff to a frozen, reviewed eye native.

blender -b --python integrate_corrections.py -- EYE BODY_HANDOFF OUTPUT
The eye producer owns appended face indices; the body producer owns original
Body indices. This script checks actual coordinates and named keys rather than
trusting either producer's completion status. It never overwrites an input.
"""
import hashlib
import json
from pathlib import Path
import sys

import bpy
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def coordinates(mesh):
    return np.asarray([[v.co[:] for v in key.data]
                       for key in mesh.shape_keys.key_blocks], dtype=np.float64)


def topology(mesh):
    return [list(p.vertices) for p in mesh.polygons]


args = sys.argv[sys.argv.index('--') + 1:]
assert len(args) == 3, 'EYE BODY_HANDOFF OUTPUT required'
eye, handoff, output = map(Path, args)
assert not output.exists(), 'Use a fresh output; reviewed natives are immutable'
assert output.resolve() not in (eye.resolve(), handoff.resolve())
input_sha = sha(eye)
patch = np.load(handoff, allow_pickle=False)
indices = patch['indices'].astype(np.int64)
assert len(indices) == len(set(indices.tolist()))
assert indices.min() >= 0 and indices.max() < 3957
assert np.isfinite(patch['target_selected42']).all()
bpy.ops.wm.open_mainfile(filepath=str(eye), use_scripts=False)
skin = bpy.data.objects['MIA_V27_SharedHeadBody']
mesh = skin.data
keys = mesh.shape_keys.key_blocks
names = [key.name for key in keys]
assert names == patch['key_names'].tolist()
assert len(keys) == 42 and len(mesh.vertices) == 4647
before = coordinates(mesh)
assert np.array_equal(before[:, indices], patch['baseline_selected42']), (
    'Eye native already changes the body handoff region or wrong baseline')
uv_before = {uv.name: np.array([v.uv[:] for v in uv.data]) for uv in mesh.uv_layers}
weights_before = [[(skin.vertex_groups[g.group].name, g.weight) for g in v.groups]
                  for v in mesh.vertices]
topology_before = topology(mesh)
other_before = {obj.name: coordinates(obj.data)
                if obj.data.shape_keys else np.array([v.co[:] for v in obj.data.vertices])
                for obj in bpy.data.objects if obj.type == 'MESH' and obj != skin}
for key, target in zip(keys, patch['target_selected42']):
    for index, point in zip(indices, target):
        key.data[int(index)].co = point
for v, point in zip(mesh.vertices, keys[0].data):
    v.co = point.co
after = coordinates(mesh)
assert np.array_equal(after[:, indices], patch['target_selected42'])
protected = np.ones(len(mesh.vertices), dtype=bool)
protected[indices] = False
assert np.array_equal(before[:, protected], after[:, protected])
assert topology_before == topology(mesh)
assert all(np.array_equal(old, np.array([v.uv[:] for v in mesh.uv_layers[name].data]))
           for name, old in uv_before.items())
assert weights_before == [[(skin.vertex_groups[g.group].name, g.weight) for g in v.groups]
                          for v in mesh.vertices]
assert all(np.array_equal(old, coordinates(bpy.data.objects[name].data)
                          if bpy.data.objects[name].data.shape_keys else
                          np.array([v.co[:] for v in bpy.data.objects[name].data.vertices]))
           for name, old in other_before.items())
master = bpy.data.objects['MIA_V27_Foundation_Face']
for key in master.data.shape_keys.key_blocks:
    key.value = 0
skin['MIA_V28_Integration'] = 'Reviewed eye reconstruction + disjoint original Body-prefix correction; full ART approval not implied'
bpy.context.view_layer.update()
output.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(output))
assert sha(eye) == input_sha
record = {
    'input_eye': {'path': str(eye), 'sha256': input_sha},
    'body_handoff': {'path': str(handoff), 'sha256': sha(handoff)},
    'output': {'path': str(output), 'sha256': sha(output)},
    'changed_body_indices': indices.tolist(),
    'key_names': names,
    'body_target_all42_exact': True,
    'protected_skin_all42_exact': True,
    'topology_uv_named_weights_exact': True,
    'all_other_mesh_coordinates_exact': True,
    'input_native_unchanged': True,
    'art_acceptance': 'NOT_INFERRED',
}
output.with_suffix('.integration.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps({'saved': str(output), 'sha256': record['output']['sha256'],
                  'body_vertices': len(indices), 'guards': 'PASS', 'art': 'NOT_EVALUATED'}))
