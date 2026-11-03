"""Read/apply a reversible neck-only normal-continuity diagnostic.

Geometry remains D. This cannot certify its physical cut tangent or anatomy.
"""
from pathlib import Path
import hashlib
import json
import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
ob = bpy.data.objects['MIA_Review12_H_LiveRepair']; me = ob.data
assert ob.mode == 'OBJECT'
d = dict(np.load(ROOT/'.mia-cache/body-h/shape/assembly/live-D/geometry.npz'))
v = np.array([p.co[:] for p in me.vertices], np.float32)
assert np.array_equal(v, d['world'])
f, part = d['triangles'], d['source_part']
before = np.array([n.vector[:] for n in me.corner_normals], np.float32).reshape(-1, 3, 3)
head = part == 1
cut_ids = np.unique(f[head][abs(v[f[head], 2]-1.465) < 1e-7])
assert len(cut_ids) == 123
desired = np.zeros((len(v), 3)); auto = np.zeros_like(desired)
hc = np.zeros(len(v)); bc = np.zeros(len(v))
for k in range(3):
    np.add.at(desired, f[head, k], before[head, k]); np.add.at(hc, f[head, k], 1)
    body = ~head
    np.add.at(auto, f[body, k], before[body, k]); np.add.at(bc, f[body, k], 1)
desired /= np.maximum(np.linalg.norm(desired, axis=1)[:, None], 1e-20)
auto /= np.maximum(np.linalg.norm(auto, axis=1)[:, None], 1e-20)
assert (hc[cut_ids] > 0).all() and (bc[cut_ids] > 0).all()
center = v[cut_ids, :2].mean(0)
theta = np.mod(np.arctan2(v[cut_ids, 1]-center[1], v[cut_ids, 0]-center[0]), 2*np.pi)
order = np.argsort(theta); theta = theta[order]; cut_ids = cut_ids[order]
delta = desired[cut_ids]-auto[cut_ids]
custom = np.zeros_like(before); custom[head] = d['source_corner_normals'][head]
collar = np.zeros(len(f), bool); collar[209484:221750] = True
q = v[f]
t = np.clip((q[:, :, 2]-1.44972)/(1.465-1.44972), 0., 1.)
t = t*t*t*(10-15*t+6*t*t)
affected = collar[:, None] & (t > 0)
angle = np.mod(np.arctan2(q[:, :, 1]-center[1], q[:, :, 0]-center[0]), 2*np.pi)
tt = np.r_[theta[-1]-2*np.pi, theta, theta[0]+2*np.pi]
dd = np.vstack([delta[-1], delta, delta[0]])
correction = np.stack([np.interp(angle, tt, dd[:, k]) for k in range(3)], axis=2)
target = before.astype(float)+t[:, :, None]*correction
target /= np.maximum(np.linalg.norm(target, axis=2)[:, :, None], 1e-20)
custom[affected] = target[affected]
ns = bpy.app.driver_namespace
assert 'MIA_Live_CutShade_Input' not in ns, 'Do not accumulate normal corrections'
ns['MIA_Live_CutShade_Input'] = custom.copy()
old_input = np.zeros_like(custom); old_input[head] = d['source_corner_normals'][head]
ns['MIA_Live_CutShade_BeforeInput'] = old_input
me.normals_split_custom_set(custom.reshape(-1, 3).tolist()); me.update(); bpy.context.view_layer.update()
after = np.array([n.vector[:] for n in me.corner_normals], np.float32).reshape(-1, 3, 3)
assert np.array_equal(v, np.array([p.co[:] for p in me.vertices], np.float32))
protected = head & np.all(v[f, 2] >= 1.469, axis=1)
dot = np.sum(before[protected]*after[protected], axis=2)
cross = np.linalg.norm(np.cross(before[protected], after[protected]), axis=2)
head_error = np.degrees(np.arctan2(cross, dot))
assert head_error.max() < .05
residual = []
for vid in cut_ids:
    hn = after[head][f[head] == vid]; bn = after[collar][f[collar] == vid]
    residual.extend(np.degrees(np.arccos(np.clip(bn@hn.T, -1, 1))).ravel().tolist())
report = dict(operation='Neck collar normal-continuity diagnostic, upper15.28mm quintic fade',
    geometry_world_sha256=hashlib.sha256(v.tobytes()).hexdigest(), geometry_changed=False,
    affected_body_corners=int(affected.sum()), protected_head_max_normal_repack_degrees=float(head_error.max()),
    cut_normal_jump_degrees=dict(median=float(np.median(residual)), p95=float(np.percentile(residual, 95)), maximum=float(max(residual))),
    actual_normals_sha256=hashlib.sha256(after.tobytes()).hexdigest(),
    physical_tangent_fixed=False, native_saved=False, adopted=False)
(ROOT/'.mia-cache/body-h/live/cut-shading-operation.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
print(json.dumps(report))
