"""Pure-NumPy triangle narrow phase and seam audit; never modifies geometry."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import itertools
import json
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[3]


def digest(a): return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def stats(a):
    return dict(count=len(a), maximum=float(np.max(a)) if len(a) else None,
                p95=float(np.percentile(a, 95)) if len(a) else None,
                median=float(np.median(a)) if len(a) else None)


def audit(root):
    start = time.time(); root = Path(root)
    out = root/'.mia-cache/body-h/shape/assembly/template03'
    d = np.load(out/'geometry.npz'); v = d['world']; f = d['triangles']; part = d['source_part']
    q = v[f].astype(float); vector = np.cross(q[:, 1]-q[:, 0], q[:, 2]-q[:, 0])
    area = np.linalg.norm(vector, axis=1); assert (area > 0).all()
    normal = vector/area[:, None]
    directed = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
    edges, inverse, counts = np.unique(np.sort(directed, axis=1), axis=0, return_inverse=True, return_counts=True)
    winding = np.bincount(inverse, weights=np.where(directed[:, 0] < directed[:, 1], 1, -1))
    order = np.argsort(inverse, kind='stable'); owners = np.tile(np.arange(len(f)), 3)[order]
    starts = np.r_[0, np.cumsum(counts[:-1])]; ix = np.flatnonzero(counts == 2)
    pairs = np.column_stack([owners[starts[ix]], owners[starts[ix]+1]])
    seam = (part[pairs[:, 0]] == 6)^(part[pairs[:, 1]] == 6)
    seams = {}
    for name, mask in [('upper', seam&(part[pairs] == 4).any(1)),
                       ('lower', seam&~(part[pairs] == 4).any(1))]:
        pick = pairs[mask]
        a = np.degrees(np.arccos(np.clip(np.sum(normal[pick[:, 0]]*normal[pick[:, 1]], axis=1), -1, 1)))
        seams[name] = dict(dihedral_degrees=stats(a), over45=int((a > 45).sum()), over90=int((a > 90).sum()))
        if len(a):
            worst = int(np.argmax(a)); edge_index = ix[np.flatnonzero(mask)[worst]]
            seams[name]['worst'] = dict(faces=pick[worst].tolist(), world_edge=v[edges[edge_index]].tolist())
    changed = np.flatnonzero((part == 4)|(part == 6))
    lo, hi = q.min(1), q.max(1)
    region_min, region_max = lo[changed].min(0)-1e-6, hi[changed].max(0)+1e-6
    relevant = np.flatnonzero((lo <= region_max).all(1)&(hi >= region_min).all(1))
    cell = .006

    def cells(i):
        a = np.floor((lo[i]-1e-9)/cell).astype(int); b = np.floor((hi[i]+1e-9)/cell).astype(int)
        return itertools.product(*(range(int(x), int(y)+1) for x, y in zip(a, b)))

    bins = {}
    for i in relevant:
        for key in cells(i): bins.setdefault(key, []).append(int(i))
    print('UPPER03_SI_BINS', len(changed), len(relevant), len(bins), flush=True)
    p = root/'asset/mia/blender/mia-fit-v003/body/posterior-continuity08/geometry.py'
    spec = importlib.util.spec_from_file_location('upper03_triangle_sat', p)
    narrow = importlib.util.module_from_spec(spec); spec.loader.exec_module(narrow)
    seen = set(); intersections = []; tested = 0; adjacent = 0
    for index, i in enumerate(changed):
        candidates = set()
        for key in cells(i): candidates.update(bins.get(key, ()))
        for j in candidates:
            if i == j: continue
            pair = (min(int(i), j), max(int(i), j))
            if pair in seen: continue
            seen.add(pair)
            if (lo[i] > hi[j]+1e-12).any() or (lo[j] > hi[i]+1e-12).any(): continue
            if np.intersect1d(f[i], f[j], assume_unique=True).size:
                adjacent += 1; continue
            tested += 1
            if narrow.triangle_intersects(q[i], q[j]): intersections.append(list(pair))
        if index and index % 5000 == 0: print('UPPER03_SI_PROGRESS', index, tested, len(intersections), flush=True)
    errors = []
    if intersections: errors.append('new upper-template/annulus nonadjacent triangle intersection')
    if seams['upper']['over90'] or seams['lower']['over90']: errors.append('reverse upper/lower seam turn over90deg')
    # Edge winding/topology must be compared with inherited hand/face defects.
    baseline = np.load(root/'.mia-cache/body-h/shape/assembly/live-D/geometry.npz')

    def problems(vv, ff):
        directed = np.concatenate([ff[:, [0, 1]], ff[:, [1, 2]], ff[:, [2, 0]]])
        e, inv, n = np.unique(np.sort(directed, axis=1), axis=0, return_inverse=True, return_counts=True)
        w = np.bincount(inv, weights=np.where(directed[:, 0] < directed[:, 1], 1, -1))
        key = lambda edge: tuple(sorted([vv[edge[0]].tobytes(), vv[edge[1]].tobytes()]))
        return ({key(edge): int(count) for edge, count in zip(e[n != 2], n[n != 2])},
                {key(edge) for edge, count, sign in zip(e, n, w) if count == 2 and sign != 0})

    old_problems, old_wind = problems(baseline['world'], baseline['triangles'])
    new_problems, new_wind = problems(v, f)
    extra = [key for key, value in new_problems.items() if old_problems.get(key) != value]
    extra_wind = new_wind-old_wind
    if extra: errors.append('new boundary/nonmanifold edge')
    if extra_wind: errors.append('new inconsistent edge winding')
    orphan = len(v)-len(np.unique(f))
    if orphan: errors.append('unused vertices')
    report = dict(status='CPU technical PASS; live/source/ART unverified' if not errors else 'CPU technical FAIL',
                  errors=errors, candidate_sha256=digest(v), vertices=len(v), triangles=len(f),
                  unused_vertices=orphan, seam=seams, new_problem_edges=len(extra), new_winding_edges=len(extra_wind),
                  tested_new_faces=len(changed), broadphase_relevant_faces=len(relevant),
                  narrow_phase_pairs=tested, graph_neighbor_pairs_excluded=adjacent,
                  new_nonadjacent_intersections=intersections,
                  collision_scope='Every new donor-roof and annulus triangle versus entire candidate through conservative AABB grid; shared-vertex graph neighbors excluded. Preserved-only inherited collisions are not reevaluated.',
                  source_registration_or_ART_evaluated=False, seconds=time.time()-start)
    path = out/'verification.json'; assert not path.exists()
    path.write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    print(json.dumps(dict(status=report['status'], errors=errors, intersections=len(intersections), seams=seams, seconds=report['seconds'])))
    if errors: raise RuntimeError('Upper-template CPU gate failed: '+', '.join(errors))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--root', type=Path, default=ROOT)
    audit(parser.parse_args().root.resolve())
