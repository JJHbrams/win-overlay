"""Bounded manual R25 apex/attachment redistribution, with mass retained."""
import bpy, ast, json, hashlib
import numpy as np
from pathlib import Path
from collections import Counter
from mathutils import Vector
OUT = Path(__file__).resolve().parent
R25 = OUT.parent
H = R25.parent
SOURCE = R25 / 'refinement-r26/Mia_FaceFinish7_MalarTransitionR26_v22.blend'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
ah = lambda p: hashlib.sha256(np.asarray(p).tobytes()).hexdigest()
tree = ast.parse((H.parent / 'finish-6/dependencies/legacy_snapshot_apply_interp.py').read_text(encoding='utf-8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ['snapshots', 'apply']], type_ignores=[]), 'frozen-guards', 'exec'))
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
source_sha = sha(SOURCE)
skin = bpy.data.objects['MIA_V14_SculptedSkin']
P = np.array([tuple(v.co) for v in skin.data.shape_keys.key_blocks[0].data])
before = snapshots()
faces = np.array([list(p.vertices[:3]) for p in skin.data.polygons])
delta = np.zeros_like(P)
regions = {'continuous_outer_orbital_outflow': {i: (np.array(target) - 1000 * P[i]).tolist() for i, target in {335: [48.3, 55.7, 1537.7], 247: [48.6, 56.4, 1535.7], 243: [51.6, 53.3, 1537.7], 246: [51.2, 53.35, 1539.3], 245: [53.45, 51.7, 1541.5], 244: [54.0, 51.2, 1540.8], 248: [44.8, 59.1, 1533.8], 333: [44.1, 58.8, 1535.3], 232: [54.1, 48.0, 1536.9], 242: [48.1, 57.1, 1530.9]}.items()}}
mapping = {}
semantic = {}
used = set()
for region, values in regions.items():
    for i, offset in values.items():
        assert P[i, 0] > 0 and i not in used
        used.add(i)
        reflected = P[i] * np.array([-1, 1, 1])
        negative = np.where(P[:, 0] < 0)[0]
        j = {335: 527, 247: 54, 243: 52, 246: 530, 245: 532, 244: 53, 248: 55, 333: 524, 232: 43, 242: 51}[i]
        assert j not in used and np.linalg.norm(P[j] - reflected) < 0.002
        used.add(j)
        mapping[i] = j
        delta[i] = np.array(offset) / 1000
        delta[j] = delta[i] * np.array([-1, 1, 1])
        semantic[i] = semantic[j] = region
edge_counts = Counter((tuple(sorted((int(f[i]), int(f[(i + 1) % 3])))) for f in faces for i in range(3)))
boundary = {i for edge, n in edge_counts.items() if n == 1 for i in edge}
assert np.max(np.linalg.norm(delta[list(boundary)], axis=1)) == 0 and np.max(abs(delta[588:])) == 0

def normals(points):
    n = np.cross(points[faces[:, 1]] - points[faces[:, 0]], points[faces[:, 2]] - points[faces[:, 0]])
    return n / np.maximum(np.linalg.norm(n, axis=1)[:, None], 1e-20)
dots = np.sum(normals(P) * normals(P + delta), axis=1)
assert dots.min() > 0.35, float(dots.min())

def eye_boundary():
    bpy.context.view_layer.update()
    o = skin.evaluated_get(bpy.context.evaluated_depsgraph_get())
    m = o.to_mesh()
    p = np.array([tuple(v.co) for v in m.vertices])
    f = [list(q.vertices) for q in m.polygons]
    ec = Counter((tuple(sorted((v[k], v[(k + 1) % len(v)]))) for v in f for k in range(len(v))))
    ids = sorted({i for edge, n in ec.items() if n == 1 for i in edge if 0.01 < abs(p[i, 0]) < 0.061 and p[i, 1] > 0.035 and (1.525 < p[i, 2] < 1.558)})
    o.to_mesh_clear()
    return (ids, p[ids])
eye_ids, eye_before = eye_boundary()
errors = apply(skin, delta)
ids, eye_after = eye_boundary()
assert ids == eye_ids and np.array_equal(eye_before, eye_after)
after = snapshots()
for name in before:
    if name != skin.name:
        assert before[name] == after[name], name
    else:
        for field in ['uv', 'topology', 'weights', 'materials', 'matrix', 'modifiers']:
            assert before[name][field] == after[name][field], field
assert max(errors.values()) < 2e-07
native = OUT / 'Mia_FaceFinish7_OrbitalTransitionR27_v22.blend'
assert not native.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(native))
native_sha = sha(native)
bpy.ops.wm.open_mainfile(filepath=str(native))
assert snapshots() == after and sha(SOURCE) == source_sha
rows = [{'owner': 'MIA_V14_SculptedSkin', 'id': i, 'region': semantic[i], 'before': P[i].tolist(), 'after': (P[i] + delta[i]).tolist(), 'delta': delta[i].tolist()} for i in sorted(semantic)]
report = {'source': {'path': str(SOURCE), 'sha256': source_sha}, 'native': {'path': str(native), 'sha256': native_sha}, 'recipe': {'path': str(Path(__file__).resolve()), 'sha256': sha(__file__)}, 'semantic_offsets_mm': regions, 'actual_mirror_mapping': mapping, 'changed_vertices': len(rows), 'max_delta_m': float(np.linalg.norm(delta, axis=1).max()), 'minimum_old_new_normal_dot': float(dots.min()), 'all_non_skin_owners_exact': True, 'actual_evaluated_eye_boundary_exact': True, 'relative_key_errors': errors, 'limits': ['Manual final-position correction of measured outer lower-orbital depth backtrack; no fit or smoothing.', 'R26 broad apex and buccal mass unchanged. Only two outer lower-orbital support rows changed; exact targets are embedded in this recipe.', 'No whole-art PASS; requires actual low/level/high-angle review and limited blink recheck.']}
(OUT / 'manifest.json').write_text(json.dumps(report, indent=2))
(OUT / 'vertex-deltas-from-r26.json').write_text(json.dumps(rows, indent=2))
(OUT / 'exact-recipe.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps(report, indent=2))