"""Exact original-cage ownership for one broad connected static design edit."""
from pathlib import Path
from collections import deque
import hashlib
import json
import numpy as np

ROOT = Path('D:/MiaWorkCache/mia-reference-work/win-overlay')
BODY = ROOT/'asset/mia/blender/mia-fit-v003/body'
CACHE = ROOT/'.mia-cache/body-connected'


def load_scope():
    mapping = dict(np.load(BODY/'inputs/mapping-frame1.npz'))
    top = dict(np.load(BODY/'posed-target/control-topology.npz'))
    q = mapping['q0_world']; count = len(q)
    offset = np.r_[0, np.cumsum(top['polygon_sizes'])]
    faces = [top['loop_vertices'][offset[i]:offset[i+1]].tolist() for i in range(len(offset)-1)]
    edges = set()
    for face in faces:
        edges.update(tuple(sorted((a, b))) for a, b in zip(face, face[1:]+face[:1]))
    adjacency = [set() for _ in q]
    for a, b in edges: adjacency[a].add(b); adjacency[b].add(a)
    arm = [459,464,466,492,496,499,501,556,555,542,540,457]
    center = -.0004777
    reflected = q[arm].copy(); reflected[:, 0] = 2*center-reflected[:, 0]
    other = np.argmin(np.sum((reflected[:, None]-q[None])**2, axis=2), axis=1).tolist()
    assert len(set(other)) == len(arm)
    assert max(np.linalg.norm(reflected-q[other], axis=1)) < .002
    for loop in [arm, other]:
        assert all(tuple(sorted((a, b))) in edges for a, b in zip(loop, loop[1:]+loop[:1]))
    skin = np.zeros(count, bool)
    skin[np.unique(top['triangles'][top['triangle_materials'] == 1])] = True
    lower_neck = (~skin)&(np.arange(count)<3957)&(q[:, 2]>1.40)&(q[:, 2]<1.469)&(abs(q[:, 0])<.045)
    head = set(np.flatnonzero((np.arange(count)>=3957)|(q[:, 2]>=1.469)).tolist())
    protected = set(head)
    frontier = set(head)
    for _ in range(2):
        frontier = {v for u in frontier for v in adjacency[u]}-protected
        protected.update(frontier)
    allowed = (skin|lower_neck)&(q[:, 2]>1.11)
    allowed[list(protected)] = False
    allowed[arm+other] = False
    seed = min(np.flatnonzero(allowed), key=lambda i: np.linalg.norm(q[i]-[0., -.04, 1.36]))
    selected = {int(seed)}; queue = deque(selected)
    while queue:
        for v in adjacency[queue.popleft()]:
            if allowed[v] and v not in selected:
                selected.add(v); queue.append(v)
    selected = np.array(sorted(selected), np.int32)
    assert not set(selected)&protected
    assert not set(selected)&set(arm+other)
    # The certified arm rings are graph barriers; distal branches cannot be
    # reached by a torso flood without crossing them.
    assert abs(q[selected, 0]).max() < .20, 'Distal arm leaked into the design domain'
    boundary = {int(i) for i in selected if any(j not in set(selected) for j in adjacency[i])}
    support = set(boundary)
    for _ in range(1): support |= {j for i in list(support) for j in adjacency[i] if j in set(selected)}
    return dict(mapping=mapping, topology=top, q=q, faces=faces,
                edges=np.array(sorted(edges), np.int32), adjacency=adjacency,
                selected=selected, protected=np.array(sorted(protected), np.int32),
                boundary=np.array(sorted(boundary), np.int32), support=np.array(sorted(support), np.int32),
                arm=np.array(arm, np.int32), other_arm=np.array(other, np.int32), lower_neck=lower_neck)


def prepare():
    s = load_scope(); CACHE.mkdir(parents=True, exist_ok=True)
    out = CACHE/'scope.npz'
    arrays = {k:s[k] for k in ['selected','protected','boundary','support','arm','other_arm']}
    arrays['q0_world'] = s['q']; arrays['q0_local'] = s['mapping']['q0_local']
    np.savez_compressed(out, **arrays)
    report = dict(scope='ONE broad connected original static design cage; no geometry edit yet',
        controls=len(s['q']), selected_controls=len(s['selected']),
        selected_bounds=[s['q'][s['selected']].min(0).tolist(),s['q'][s['selected']].max(0).tolist()],
        lower_neck_selected=int(s['lower_neck'][s['selected']].sum()),
        true_head_and_two_ring_support=len(s['protected']), boundary_controls=len(s['boundary']),
        two_row_transition_support=len(s['support']), arm_cycles=[s['arm'].tolist(),s['other_arm'].tolist()],
        raw_face690_excluded=True, body_prefix_alone_not_head_guard=True,
        source_native_sha256='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1',
        mapping_sha256=hashlib.sha256((BODY/'inputs/mapping-frame1.npz').read_bytes()).hexdigest(),
        scope_npz_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),
        source_modified=False, live_installed=False, ART=False)
    (CACHE/'scope.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report))


if __name__ == '__main__': prepare()
