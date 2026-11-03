"""One connected proportional sculpt from actual D stations; no target fitting.

Shallow collar depression/ridge and broad cap translation are one bounded study.
The source gives observed planes, not exact bone depth. Keep or restore only after
actual multi-angle/source review. This does not resolve the protected head cut.
"""
from pathlib import Path
import hashlib
import heapq
import json
import sys
import bpy
import numpy as np

ROOT = Path('D:/MiaWorkCache/mia-reference-work/win-overlay')
sys.path.insert(0, str(ROOT/'tools/mia/review_h'))
import assemble
import live_relax

ns = bpy.app.driver_namespace
key = 'MIA_CollarSculpt01'
phase = globals().get('MIA_EDIT_PHASE', 'select')
assert phase in ('select', 'apply', 'restore')
out = ROOT/'.mia-cache/body-h/live'
path = out/f'collar-sculpt01-{phase}.json'
assert not path.exists(), 'This immutable trial phase was already recorded'
ob = bpy.data.objects['MIA_Review12_H_LiveRepair']
assert ob.mode == 'OBJECT'
v = np.array([p.co[:] for p in ob.data.vertices], np.float32)
d = dict(np.load(ROOT/'.mia-cache/body-h/shape/assembly/live-D/geometry.npz'))
f = d['triangles']
sha = lambda q: hashlib.sha256(np.asarray(q, np.float32).tobytes()).hexdigest()

if phase == 'select':
    assert key not in ns and sha(v) == '69d4d4f0ea907da2474bc74f4b55312971d137f0911bdf9089fc02509a6bf25a'
    x, y, z = abs(v[:, 0]), v[:, 1], v[:, 2]
    eligible = ((z > 1.355) & (z < 1.455) & (x < .195)) | ((x > .13) & (x < .19) & (y > .015) & (z > 1.31) & (z < 1.39))
    head = np.unique(f[d['source_part'] == 1]); eligible[head] = False
    for ids in ns['MIA_Live_H_Rows'].values(): eligible[np.asarray(ids).ravel()] = False
    boundary_weight, edges = live_relax.mask(v, f, eligible, fade=.012)
    graph = [[] for _ in v]
    for a, b in edges[eligible[edges].all(1)]:
        length = float(np.linalg.norm(v[a].astype(float)-v[b]))
        graph[a].append((int(b), length)); graph[b].append((int(a), length))
    normal = assemble._normals(v, f)
    def influence(position, radius):
        candidates = np.flatnonzero(eligible)
        seed = int(candidates[np.argmin(np.linalg.norm(v[candidates]-position, axis=1))])
        dist = np.full(len(v), np.inf); dist[seed] = 0.; queue = [(0., seed)]
        while queue:
            length, i = heapq.heappop(queue)
            if length != dist[i] or length >= radius: continue
            for j, edge in graph[i]:
                value = length+edge
                if value < radius and value < dist[j]: dist[j] = value; heapq.heappush(queue, (value, j))
        t = np.minimum(dist/radius, 1.)
        return (1-t)**4*(4*t+1), seed
    depression = np.zeros(len(v)); depression_weight = np.zeros(len(v))
    delta = np.zeros((len(v), 3)); handles = []
    def add(label, position, radius, motion=None, ridge=None, depth=None):
        weight, seed = influence(np.asarray(position), radius)
        if depth is not None:
            depression[:] += weight*depth; depression_weight[:] += weight
            vector = [0., depth, 0.]
        else:
            vector = normal[seed]*ridge if ridge is not None else np.asarray(motion, float)
            delta[:] += weight[:, None]*vector
        handles.append(dict(label=label, vertex_id=seed, position=v[seed].tolist(), radius_m=radius,
                            motion_m=np.asarray(vector).tolist(), surface_normal=normal[seed].tolist()))
    add('shallow central notch', [0., -.070, 1.395], .035, depth=.003)
    for side in [-1, 1]:
        add('collar fossa', [side*.045, -.054, 1.405], .037, depth=.0018)
        for a, b, c, radius, height in [(.025, -.071, 1.385, .028, .0007), (.065, -.052, 1.38, .037, .0008), (.12, -.016, 1.375, .036, .0006)]:
            add('broad low clavicle ridge', [side*a, b, c], radius, ridge=height)
        add('upper cap plane', [side*.15, .01, 1.37], .05, motion=[-side*.0015, .0005, -.002])
        add('posterior cap transition', [side*.16, .045, 1.34], .055, motion=[-side*.001, -.0025, -.0015])
    # Overlapping collar wells form one bounded shallow depression, not three
    # independently accumulated holes. Ridges are broad actual-anchor normals.
    delta[:, 1] += depression/np.maximum(1., depression_weight)
    q = (v.astype(float)+boundary_weight[:, None]*delta).astype(np.float32)
    changed = np.linalg.norm(q-v, axis=1) > 0
    before_tri = np.cross(v[f[:, 1]]-v[f[:, 0]], v[f[:, 2]]-v[f[:, 0]])
    after_tri = np.cross(q[f[:, 1]]-q[f[:, 0]], q[f[:, 2]]-q[f[:, 0]])
    active_faces = changed[f].any(1)
    denom = np.linalg.norm(before_tri, axis=1)*np.linalg.norm(after_tri, axis=1)
    cos = np.sum(before_tri*after_tri, axis=1)/np.maximum(denom, 1e-30)
    assert cos[active_faces].min() > .8, 'Reject strained local surface before actual mutation'
    assert np.array_equal(q[~eligible], v[~eligible]) and np.array_equal(q[head], v[head])
    report = dict(operation='ONE actual-surface geodesic proportional collar/cap sculpt; not Coons, quadric fit or new topology',
                  before_sha256=sha(v), after_sha256=sha(q), changed_vertices=int(changed.sum()),
                  maximum_displacement_m=float(np.linalg.norm(q-v, axis=1).max()),
                  maximum_triangle_turn_degrees=float(np.degrees(np.arccos(np.clip(cos[active_faces].min(), -1, 1)))),
                  handles=handles, protected='All head; upper10mm cervical collar; E joins; anterior breast/root below1.355; inferior axillary passage',
                  source_depth='Inferred shallow artist construction; source graphic ink Z is not a bone coordinate',
                  native_saved=False, art_accepted=False, head_cut_fixed=False)
    ns[key] = dict(before=v.copy(), after=q, report=report)
elif phase in ('apply', 'restore'):
    state = ns[key]
    expected = state['before'] if phase == 'apply' else state['after']
    assert np.array_equal(v, expected), 'Do not overwrite an unrelated live edit'
    target = state['after'] if phase == 'apply' else state['before']
    ob.data.vertices.foreach_set('co', target.ravel()); ob.data.update(); bpy.context.view_layer.update()
    assert sha(np.array([p.co[:] for p in ob.data.vertices], np.float32)) == sha(target)
    report = dict(state['report'], phase=phase, actual_live_geometry=True,
                  retained_as_working_sculpt=False, geometry_world_sha256=sha(target))
    if phase == 'restore': del ns[key]
else:
    raise ValueError(phase)
path.write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
print(json.dumps(report))
