"""Bounded conservative changed-triangle AABB/SAT check; no bpy/mutation."""
from pathlib import Path
import itertools
import runpy
import time

import numpy as np


def check(root, before, moved, max_pairs=4000, max_seconds=25):
    started = time.monotonic()
    narrow = runpy.run_path(str(Path(root)/'asset/mia/blender/mia-fit-v003/body/posterior-continuity08/geometry.py'))
    intersects = narrow['triangle_intersects']
    a = np.asarray([(0,0,0),(.001,0,0),(0,.001,0)], float)
    witnesses = dict(crossing=np.asarray([(.0002,.0002,-.0005),(.0002,.0002,.0005),(.0008,.0002,0)]),
                    coplanar=np.asarray([(.0001,.0001,0),(.0008,.0001,0),(.0001,.0008,0)]),
                    separated=np.asarray([(.0002,.0002,.001),(.0002,.0002,.002),(.0008,.0002,.0015)]))
    verified = {key:bool(intersects(a, value)) for key,value in witnesses.items()}
    assert verified == dict(crossing=True, coplanar=True, separated=False)
    def expired(phase, changed_count=0):
        return dict(status='UNVERIFIED', complete=False, tested_pairs=0, changed_faces=changed_count,
                    new_intersection_witnesses=[], inherited_intersections_tested=0,
                    controlled_witnesses=verified, stopped_phase=phase,
                    method='Conservative AABB grid + existing triangle SAT including coplanar axes',
                    limit='Time budget exhausted before complete check; preview only, never KEEP')
    points0, points1, faces, owner, local_face = [], [], [], [], []
    names = sorted(before); offset = 0
    for index, name in enumerate(names):
        q, f = before[name]; q = np.asarray(q, float)
        out = np.asarray(moved.get(name, q), float); assert out.shape == q.shape
        points0.append(q); points1.append(out); faces.append(f+offset)
        owner.extend([index]*len(f)); local_face.extend(range(len(f))); offset += len(q)
    q0, q1 = np.concatenate(points0), np.concatenate(points1); f = np.concatenate(faces)
    owner, local_face = np.asarray(owner), np.asarray(local_face)
    changed = np.any(q0 != q1, axis=1); changed_faces = np.flatnonzero(changed[f].any(1))
    tri, old_tri = q1[f], q0[f]; lo, hi = tri.min(1), tri.max(1)
    minimum, maximum = lo[changed_faces].min(0)-1e-9, hi[changed_faces].max(0)+1e-9
    relevant = np.flatnonzero((lo <= maximum).all(1)&(hi >= minimum).all(1))
    cell = .006
    def cells(i):
        first, last = np.floor((lo[i]-1e-9)/cell).astype(int), np.floor((hi[i]+1e-9)/cell).astype(int)
        return itertools.product(*(range(int(x), int(y)+1) for x,y in zip(first,last)))
    bins = {}
    for i in relevant:
        if time.monotonic()-started >= max_seconds: return expired('grid', len(changed_faces))
        for key in cells(i):
            bins.setdefault(key, []).append(int(i))
            if time.monotonic()-started >= max_seconds: return expired('grid cells', len(changed_faces))
    seen = set(); hits = []; inherited = 0; tested = 0; complete = True
    for i in changed_faces:
        if time.monotonic()-started >= max_seconds: complete = False; break
        candidates = set()
        for key in cells(i):
            candidates.update(bins.get(key, ()))
            if time.monotonic()-started >= max_seconds: complete = False; break
        if not complete: break
        for j in sorted(candidates):
            if time.monotonic()-started >= max_seconds: complete = False; break
            pair = (min(int(i), j), max(int(i), j))
            if i == j or pair in seen: continue
            seen.add(pair)
            if (lo[i] > hi[j]+1e-9).any() or (lo[j] > hi[i]+1e-9).any(): continue
            if np.intersect1d(f[i], f[j], assume_unique=True).size: continue
            tested += 1
            if intersects(tri[i], tri[j]):
                if intersects(old_tri[i], old_tri[j]): inherited += 1
                else: hits.append(dict(a=names[owner[i]], face_a=int(local_face[i]),
                                       b=names[owner[j]], face_b=int(local_face[j])))
            if len(hits) >= 3 or tested >= max_pairs or time.monotonic()-started >= max_seconds:
                complete = False; break
        if not complete: break
    status = 'FAIL' if hits else ('PASS' if complete else 'UNVERIFIED')
    return dict(status=status, complete=complete, tested_pairs=tested, changed_faces=len(changed_faces),
                new_intersection_witnesses=hits, inherited_intersections_tested=inherited,
                controlled_witnesses=verified, method='Conservative AABB grid + existing triangle SAT including coplanar axes',
                limit='Bounded discrete changed-face check; UNVERIFIED may preview, never KEEP; no ART/continuous-motion claim')
