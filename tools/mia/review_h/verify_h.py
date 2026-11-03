"""Blender-CPU actual H collar/whole-mesh collision and source readback audit.

Only writes a compact JSON proof. Never opens/saves a native or changes a mesh.
Run with factory-startup background Blender; mathutils BVH is an accelerator,
and the existing exact-triangle SAT is the nonadjacent-pair narrow phase.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import sys
import time
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
REL = Path('asset/mia/blender/mia-fit-v003/body/surface-review12')
CACHE = ROOT/'.mia-cache/body-h/shape/assembly'


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ah(a): return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def load(name, p):
    s = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def edge_info(v, f):
    directed = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
    edges, inverse, counts = np.unique(np.sort(directed, axis=1), axis=0, return_inverse=True, return_counts=True)
    wind = np.bincount(inverse, weights=np.where(directed[:, 0] < directed[:, 1], 1, -1))
    physical_key = lambda e: tuple(sorted((v[e[0]].tobytes(), v[e[1]].tobytes())))
    problems = {physical_key(e): int(c) for e, c in zip(edges[counts != 2], counts[counts != 2])}
    badwind = {physical_key(e) for e, w, c in zip(edges, wind, counts) if c == 2 and w != 0}
    order = np.argsort(inverse, kind='stable'); owners = np.tile(np.arange(len(f)), 3)[order]
    starts = np.r_[0, np.cumsum(counts[:-1])]
    ids = np.flatnonzero(counts == 2)
    facepairs = np.column_stack([owners[starts[ids]], owners[starts[ids]+1]])
    return edges, counts, problems, badwind, ids, facepairs


def stats(x):
    x = np.asarray(x)
    return dict(count=len(x), median=float(np.median(x)) if len(x) else None,
                p95=float(np.percentile(x, 95)) if len(x) else None,
                maximum=float(x.max()) if len(x) else None)


def run(geometry, surface, output, canonical=ROOT, delta=None):
    root = Path(canonical); p = root/REL
    start = time.time()
    assert not Path(output).exists(), 'Never overwrite a recorded verification'
    capacity = load('h_verify_capacity', root/'asset/mia/blender/mia-fit-v003/integration/workspace-storage-20261103/storage_guard.py').inspect(2*1024**2)
    assert not capacity['violations'], capacity
    d = dict(np.load(geometry)); old = dict(np.load(p/'donor.npz'))
    v, f, part = d['world'], d['triangles'], d['source_part']
    assert np.isfinite(v).all()
    q = v[f].astype(float); facevec = np.cross(q[:, 1]-q[:, 0], q[:, 2]-q[:, 0])
    area = np.linalg.norm(facevec, axis=1)
    assert (area > 0).all(), ('Zero physical triangle', int((area <= 0).sum()))
    fn = facevec/area[:, None]
    print('H_VERIFY_EDGE_AUDIT', flush=True)
    edges, count, problems, badwind, edgeids, pairs = edge_info(v, f)
    _, oldcount, oldproblem, oldbadwind, _, _ = edge_info(old['world'], old['triangles'])
    newproblem = {key: c for key, c in problems.items() if oldproblem.get(key) != c}
    newwind = badwind-oldbadwind
    newfaces = np.flatnonzero(part == 3)
    # Live refinement also changes original guide faces near the shoulder cap.
    # Testing only generated collars would miss those newly edited surfaces.
    changed_ids = np.empty(0, dtype=np.int32)
    if delta is not None:
        live_delta = dict(np.load(delta))
        changed_ids = live_delta['vertex_ids']
        assert np.array_equal(v[changed_ids], live_delta['after']), 'Stale live delta'
        assert np.all(np.any(live_delta['before'] != live_delta['after'], axis=1))
    changed_faces = np.flatnonzero(np.isin(f, changed_ids).any(axis=1))
    tested_faces = np.union1d(newfaces, changed_faces)
    tree = BVHTree.FromPolygons([Vector(x) for x in v], f.tolist(), all_triangles=True)
    collar_tree = BVHTree.FromPolygons([Vector(x) for x in v], f[tested_faces].tolist(), all_triangles=True)
    narrow = load('h_triangle_narrow_phase', p.parent/'posterior-continuity08/geometry.py')
    seen = set(); intersections = []; tested = 0; shared = 0
    print('H_VERIFY_EDITED_SURFACE_BVH_READY', len(tested_faces), flush=True)
    for local, j in collar_tree.overlap(tree):
        i, j = int(tested_faces[local]), int(j)
        key = (min(i, j), max(i, j))
        if i == j or key in seen: continue
        seen.add(key)
        if any(int(a) == int(b) for a in f[i] for b in f[j]):
            shared += 1; continue
        tested += 1
        if narrow.triangle_intersects(q[i], q[j]): intersections.append(key)
    print('H_VERIFY_COLLAR_SAT_DONE', tested, len(intersections), flush=True)
    # Keep all results even when the gate fails, so no missing proof hides failure.
    dot = np.einsum('ij,ij->i', fn[pairs[:, 0]], fn[pairs[:, 1]])
    angles = np.degrees(np.arccos(np.clip(dot, -1, 1)))
    lengths = np.linalg.norm(v[edges[edgeids, 1]]-v[edges[edgeids, 0]], axis=1)
    touching = (part[pairs[:, 0]] == 3)|(part[pairs[:, 1]] == 3)
    seam = (part[pairs[:, 0]] == 3)^(part[pairs[:, 1]] == 3)
    ordinary = (lengths > .002)&(lengths < .006)&(area[pairs[:, 0]] > 1e-10)&(area[pairs[:, 1]] > 1e-10)
    assembly = json.loads((Path(geometry).parent/'assembly.json').read_text())
    seam_groups = {}
    for name, (lo, hi) in assembly['collar_triangle_ranges'].items():
        region = ((pairs[:, 0] >= lo)&(pairs[:, 0] < hi))|((pairs[:, 1] >= lo)&(pairs[:, 1] < hi))
        seam_groups[name] = dict(all_touching_dihedral_degrees=stats(angles[region]),
                                 endpoint_seam_dihedral_degrees=stats(angles[region&seam]),
                                 ordinary_edge_dihedral_degrees=stats(angles[region&ordinary]))
    identity = np.all(d['source_corner_bary'] == np.eye(3, dtype=np.float32)[None], axis=(1, 2))
    head = (part == 1)&identity; sf = d['source_face'][head]
    uv = np.stack([old['uv_0'], old['uv_1'], old['uv_2']], axis=2)
    head_uv = bool(np.array_equal(d['old_loop_uv'][head], uv[sf]))
    source_capture = json.loads((root/'.mia-cache/body-h/baseline4/capture.json').read_text())
    matrix = np.array(source_capture['geometry']['object_matrix'])[:3, :3]
    expected_n = np.einsum('tci,ij->tcj', old['corner_normals'].astype(float), np.linalg.inv(matrix))
    expected_n /= np.linalg.norm(expected_n, axis=2)[:, :, None]; expected_n = expected_n.astype(np.float32)
    head_n = bool(np.array_equal(d['source_corner_normals'][head], expected_n[sf]))
    lookup = {x.tobytes() for x in v}
    headids = np.flatnonzero(old['world'][:, 2] >= 1.469)
    lowerids = np.flatnonzero(old['world'][:, 2] <= 1.005)
    headcoords = all(old['world'][i].tobytes() in lookup for i in headids)
    lowercoords = all(old['world'][i].tobytes() in lookup for i in lowerids)
    s = dict(np.load(surface)); uvbody = s['loop_uv'].astype(float)
    dua, dub = uvbody[:, 1]-uvbody[:, 0], uvbody[:, 2]-uvbody[:, 0]
    uvarea = abs(dua[:, 0]*dub[:, 1]-dua[:, 1]*dub[:, 0])
    surface_world = bool(np.array_equal(s['world'], v))
    surface_faces = bool(np.array_equal(s['triangles'], f[s['meshfaceid']]))
    body_uv_nonzero = bool((uvarea > 0).all())
    errors = []
    for ok, label in [(not newproblem, 'new boundary/nonmanifold'), (not newwind, 'new winding'),
                      (not intersections, 'nonadjacent collar/edited-surface intersection'),
                      (head_uv, 'old head UV'), (head_n, 'old head WORLD normal'),
                      (headcoords, 'protected donor head coordinates'), (lowercoords, 'donor lower coordinates'),
                      (surface_world and surface_faces, 'surface/geometry binding'), (body_uv_nonzero, 'nonzero body UV')]:
        if not ok: errors.append(label)
    worst = np.flatnonzero(touching)[np.argmax(angles[touching])]
    report = dict(status='CPU gate PASS; actual gray/source/ART not evaluated' if not errors else 'CPU gate FAIL',
                  errors=errors, seconds=time.time()-start, geometry_path=str(geometry), geometry_sha256=sha(geometry),
                  surface_path=str(surface), surface_sha256=sha(surface), world_sha256=ah(v), triangles_sha256=ah(f),
                  vertices=len(v), triangles=len(f), new_collar_faces=len(newfaces),
                  changed_vertices=len(changed_ids), changed_faces=len(changed_faces), collision_faces=len(tested_faces),
                  live_delta=dict(path=str(delta), sha256=sha(delta)) if delta else None,
                  inherited_boundary_edges=int((count == 1).sum()), inherited_nonmanifold_edges=int((count > 2).sum()),
                  original_boundary_edges=int((oldcount == 1).sum()), original_nonmanifold_edges=int((oldcount > 2).sum()),
                  new_problem_edge_count=len(newproblem), new_winding_edge_count=len(newwind),
                  new_nonadjacent_collar_intersections=[list(pair) for pair in intersections], narrow_phase_pairs=tested,
                  graph_neighbor_pairs_excluded=shared,
                  collision_scope='Every actual collar and explicitly edited live surface triangle against entire actual joined mesh. Shared-vertex graph neighbors excluded; unchanged donor/guide-only collisions are outside this test. This is not whole-mesh SI or an art test.',
                  minimum_double_area_m2=float(area.min()), collar_dihedral=seam_groups,
                  worst_collar_edge=dict(angle_degrees=float(angles[worst]), edge=edges[edgeids[worst]].tolist(),
                                         world=v[edges[edgeids[worst]]].tolist(), faces=pairs[worst].tolist()),
                  unclipped_head_triangles=int(head.sum()), original_head_UV_exact=head_uv,
                  original_head_WORLD_normals_exact=head_n, original_head_vertices_exact=headcoords,
                  protected_head_vertices=len(headids), original_lower_vertices_exact=lowercoords,
                  protected_lower_vertices=len(lowerids), actual_surface_binding=surface_world and surface_faces,
                  actual_body_UV_nonzero=body_uv_nonzero, body_triangles=len(uvbody),
                  native_saved=False, GPU_used=False, mesh_modified=False, capacity=capacity)
    out = Path(output).resolve(); allowed = (root/'.mia-cache/body-h/shape/assembly').resolve()
    assert out.parent == allowed or allowed in out.parents, 'Verification output must stay in canonical assembly cache'
    out.write_text(json.dumps(report, indent=2)+'\n', encoding='utf8', newline='\n')
    print('H_VERIFY_FINISHED', json.dumps(dict(status=report['status'], errors=errors, intersections=len(intersections), seconds=report['seconds'])), flush=True)
    if errors: raise RuntimeError('H CPU verification failed: '+', '.join(errors))
    return report


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument('--geometry', type=Path, default=CACHE/'geometry.npz')
    parser.add_argument('--surface', type=Path, default=CACHE/'atlas/surface.npz')
    parser.add_argument('--output', type=Path, default=CACHE/'verify.json')
    parser.add_argument('--delta', type=Path)
    a = parser.parse_args(args)
    run(a.geometry, a.surface, a.output, delta=a.delta)
