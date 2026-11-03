"""Read-only live cut/normal diagnostic; no geometry or shading assignments."""
from pathlib import Path
import hashlib
import json
import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
ob = bpy.data.objects['MIA_Review12_H_LiveRepair']
assert ob.mode == 'OBJECT'
d = dict(np.load(ROOT/'.mia-cache/body-h/shape/assembly/live-D/geometry.npz'))
v = np.array([p.co[:] for p in ob.data.vertices], np.float32)
f, part = d['triangles'], d['source_part']
assert np.array_equal(v, d['world']), 'Live scene changed since D export'
corners = np.array([n.vector[:] for n in ob.data.corner_normals], float).reshape(-1, 3, 3)
q = v[f].astype(float)
geo = np.cross(q[:, 1]-q[:, 0], q[:, 2]-q[:, 0])
geo /= np.linalg.norm(geo, axis=1)[:, None]
edges = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
unique, inverse, counts = np.unique(np.sort(edges, axis=1), axis=0, return_inverse=True, return_counts=True)
order = np.argsort(inverse, kind='stable')
owners = np.tile(np.arange(len(f)), 3)[order]
starts = np.r_[0, np.cumsum(counts[:-1])]
pairs = np.column_stack([owners[starts[counts == 2]], owners[starts[counts == 2]+1]])
shared = unique[counts == 2]
is_cut = ((part[pairs[:, 0]] == 1) & (part[pairs[:, 1]] == 3)) | ((part[pairs[:, 1]] == 1) & (part[pairs[:, 0]] == 3))
pairs, shared = pairs[is_cut], shared[is_cut]
angle = lambda a, b: np.degrees(np.arccos(np.clip(np.einsum('ij,ij->i', a, b), -1, 1)))
geometric = angle(geo[pairs[:, 0]], geo[pairs[:, 1]])
shading = []
for (a, b), edge in zip(pairs, shared):
    for point in edge:
        na = corners[a, np.flatnonzero(f[a] == point)[0]]
        nb = corners[b, np.flatnonzero(f[b] == point)[0]]
        shading.append(float(angle(na[None], nb[None])[0]))
stats = lambda x: dict(count=len(x), median=float(np.median(x)), p95=float(np.percentile(x, 95)), maximum=float(np.max(x)))
report = dict(scope='Read-only actual live head/body cut geometry and displayed split normals',
    object=ob.name, vertices=len(v), world_sha256=hashlib.sha256(v.tobytes()).hexdigest(),
    cut_edges=len(shared), cut_z_range=v[np.unique(shared), 2].tolist(),
    geometric_face_dihedral_degrees=stats(geometric), actual_split_normal_jump_degrees=stats(shading),
    geometry_changed=False, normals_changed=False, native_saved=False,
    limitation='A normal jump may explain a band but does not alone certify source shape or justify geometry inflation.')
path = ROOT/'.mia-cache/body-h/live/head-cut-probe.json'
assert not path.exists()
path.write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
print(json.dumps({k: val for k, val in report.items() if k != 'cut_z_range'}))
