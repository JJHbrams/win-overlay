"""One CPU upper-template03 construction, using actual original contours.

Retain current D below1.355 and its exact head. Reuse the original donor roof
above1.400, and transport only the lower boundary mismatch across45mm of the
donor's non-elliptical contour family. No nearest-point or Coons mapping.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
BASE_SHA = '69d4d4f0ea907da2474bc74f4b55312971d137f0911bdf9089fc02509a6bf25a'
DONOR_SHA = '21e66277e7df3fa9d78bc27d1cfc6799261cef95f3345af774f5270cb707e8cd'
LOW, HIGH, HEAD = 1.355, 1.400, 1.465
BANDS = 12
ATTR = 17  # UV6, WORLDnormal3, original bary3, baseline bary3, ReviewUV2


def ah(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(name, p):
    spec = importlib.util.spec_from_file_location(name, p)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def vertex_normals(v, f):
    q = v[f].astype(float)
    n = np.cross(q[:, 1]-q[:, 0], q[:, 2]-q[:, 0])
    out = np.zeros_like(v, dtype=float)
    for k in range(3): np.add.at(out, f[:, k], n)
    return out/np.maximum(np.linalg.norm(out, axis=1)[:, None], 1e-30)


def quadrant_order(points):
    """Keep cycle order; anchor cardinal anatomical planes, not moving extrema.

    The donor sternum/clavicular dimple means minY can jump from one side to the
    other between sections. That is not a stable material rail. Unique cardinal
    ray intersections through the common sagittal/coronal frame provide rails.
    Other contour parts may be non-star-shaped; they are never angle sorted.
    """
    p = np.asarray(points, float)
    order = np.arange(len(p))
    area = np.sum(p[:, 0]*np.roll(p[:, 1], -1)-p[:, 1]*np.roll(p[:, 0], -1))
    assert abs(area) > 1e-8, 'Degenerate contour'
    if area < 0: order = order[::-1]
    q = p[order]; ends = np.roll(q, -1, axis=0)
    lengths = np.linalg.norm(ends-q, axis=1); arc = np.r_[0., np.cumsum(lengths)]
    perimeter = arc[-1]; assert perimeter > 1e-5
    origin = np.array([0., .005]); a = q[:, :2]-origin; edge = ends[:, :2]-q[:, :2]
    cross = lambda x, y: x[..., 0]*y[..., 1]-x[..., 1]*y[..., 0]
    landmarks = []
    for ray in [np.array([1., 0.]), np.array([0., 1.]), np.array([-1., 0.]), np.array([0., -1.])]:
        den = cross(ray, edge)
        radius = np.divide(cross(a, edge), den, out=np.full(len(q), np.inf), where=abs(den) > 1e-14)
        position = np.divide(cross(a, ray), den, out=np.full(len(q), np.inf), where=abs(den) > 1e-14)
        hit = np.flatnonzero((abs(den) > 1e-14)&(radius > 0)&(position >= -1e-10)&(position <= 1+1e-10))
        distances = np.mod(arc[hit]+np.clip(position[hit], 0, 1)*lengths[hit], perimeter)
        distances = np.sort(distances)
        unique = []
        for value in distances:
            if not any(min(abs(value-old), perimeter-abs(value-old)) < 1e-7 for old in unique): unique.append(float(value))
        assert len(unique) == 1, ('Ambiguous anatomical cardinal rail', ray.tolist(), unique)
        landmarks.append(unique[0])
    anchors = np.r_[np.mod(np.asarray(landmarks)-landmarks[0], perimeter), perimeter]
    assert np.all(np.diff(anchors) > 1e-6), ('Cardinal rails not in cyclic anatomical order', anchors.tolist())
    distances = np.mod(arc[:-1]-landmarks[0], perimeter)
    rotate = np.argsort(distances); order = order[rotate]; distances = distances[rotate]
    u = np.interp(distances, anchors, np.arange(5)*np.pi/2)
    assert np.all(np.diff(u) > 0)
    return order, u


def sample_cycle(points, values):
    order, u = quadrant_order(points)
    p = np.asarray(points, float)[order]
    return np.column_stack([np.interp(values, np.r_[u[-1]-2*np.pi, u, u[0]+2*np.pi],
                                     np.r_[p[-1, k], p[:, k], p[0, k]]) for k in range(3)])


def section(source, z):
    """One actual principal closed contour, retaining its topological order."""
    v, edges = source.v, source.edges
    value = v[:, 2]-z
    crosses = value[edges[:, 0]]*value[edges[:, 1]] < 0
    eid = np.flatnonzero(crosses)
    t = value[edges[eid, 0]]/(value[edges[eid, 0]]-value[edges[eid, 1]])
    points = v[edges[eid, 0]]+t[:, None]*(v[edges[eid, 1]]-v[edges[eid, 0]])
    table = np.full(len(edges), -1, np.int32); table[eid] = np.arange(len(eid))
    hits = table[source.face_edges]; graph = {}
    for row in hits[(hits >= 0).sum(1) == 2]:
        a, b = row[row >= 0]; graph.setdefault(int(a), []).append(int(b)); graph.setdefault(int(b), []).append(int(a))
    assert graph and all(len(v) == 2 for v in graph.values()), ('Invalid plane graph', z)
    seen = set(); loops = []
    for seed in graph:
        if seed in seen: continue
        old = -1; cur = seed; loop = []
        while cur not in seen:
            seen.add(cur); loop.append(cur)
            nex = next(n for n in graph[cur] if n != old); old, cur = cur, nex
        assert cur == seed
        loops.append(loop)
    assert len(loops) == 1, ('Not a single principal upper-body contour', z, list(map(len, loops)))
    return points[loops[0]]


def crossing_pairs(poly):
    """Strict nonadjacent planar segment crossings, not a shape judgment."""
    p = np.asarray(poly, float)[:, :2]; q = np.roll(p, -1, axis=0)
    lo, hi = np.minimum(p, q), np.maximum(p, q)
    cross = lambda a, b: a[..., 0]*b[..., 1]-a[..., 1]*b[..., 0]
    bad = []
    for i in range(len(p)):
        ids = np.flatnonzero((lo[:, 0] <= hi[i, 0])&(hi[:, 0] >= lo[i, 0])&(lo[:, 1] <= hi[i, 1])&(hi[:, 1] >= lo[i, 1]))
        ids = ids[(ids > i+1)&~((i == 0)&(ids == len(p)-1))]
        if not len(ids): continue
        a = cross(q[i]-p[i], p[ids]-p[i]); b = cross(q[i]-p[i], q[ids]-p[i])
        c = cross(q[ids]-p[ids], p[i]-p[ids]); d = cross(q[ids]-p[ids], q[i]-p[ids])
        for j in ids[(a*b < -1e-22)&(c*d < -1e-22)]: bad.append([i, int(j)])
    return bad


def stats(a):
    a = np.asarray(a)
    return dict(maximum=float(a.max()), p95=float(np.percentile(a, 95)), median=float(np.median(a)))


def angle(a, b):
    a = a/np.maximum(np.linalg.norm(a, axis=1)[:, None], 1e-30)
    b = b/np.maximum(np.linalg.norm(b, axis=1)[:, None], 1e-30)
    return np.degrees(np.arctan2(np.linalg.norm(np.cross(a, b), axis=1), np.sum(a*b, axis=1)))


def source_edge_key(data, fi, corner, donor_faces):
    vi = int(data['triangles'][fi, corner]); known = int(data['source_vertex'][vi])
    if known >= 0: return ('vertex', known)
    sf = int(data['source_face'][fi]); bary = data['source_corner_bary'][fi, corner]
    active = donor_faces[sf][np.abs(bary) > 1e-7]
    assert len(active) == 2, ('Head boundary not an original source edge', vi, sf, bary.tolist())
    return ('edge', *sorted(map(int, active)))


def build(root):
    start = time.time(); root = Path(root).resolve()
    component = root/'asset/mia/blender/mia-fit-v003/body/surface-review12'
    ops = load('upper03_mesh_ops', component/'mesh_ops.py')
    assembly_api = load('upper03_assembly_api', root/'tools/mia/review_h/assemble.py')
    d = dict(np.load(root/'.mia-cache/body-h/shape/assembly/live-D/geometry.npz'))
    original = dict(np.load(component/'donor.npz'))
    assert ah(d['world']) == BASE_SHA and ah(original['world']) == DONOR_SHA
    rows = dict(np.load(root/'.mia-cache/migration-to-C/row-ownership.npz'))
    for name in ['waist', 'armR', 'armL']: assert d['world'][rows[name], 2].max() < LOW
    atlas = np.load(root/'.mia-cache/body-h/shape/assembly/winding-fixed/atlas/atlas.npz')['loop_uv']
    assert atlas.shape == (len(d['triangles']), 3, 2)
    matrix = np.asarray(json.loads((root/'.mia-cache/body-h/baseline4/capture.json').read_text())['geometry']['object_matrix'])[:3, :3]
    on = np.einsum('tci,ij->tcj', original['corner_normals'].astype(float), np.linalg.inv(matrix))
    on /= np.maximum(np.linalg.norm(on, axis=2)[:, :, None], 1e-30)
    original_weights = np.column_stack([original[k] for k in ['armR', 'armL', 'legR', 'legL']])
    offset = len(d['world'])

    class WorkMesh(ops.Mesh):
        def oriented(self, face, center, axis, mat, part):
            q = np.asarray([self.xyz[i] for i in face]); radial = q.mean(0)-center; radial -= axis*np.dot(radial, axis)
            if np.dot(np.cross(q[1]-q[0], q[2]-q[0]), radial) < 0: face = [face[0], face[2], face[1]]
            self.add(face, np.zeros((3, ATTR)), mat, part, -1)

    world = np.vstack([d['world'], original['world']])
    mesh = WorkMesh(world, np.vstack([d['vertex_limb_weights'], original_weights]),
                    np.vstack([vertex_normals(d['world'], d['triangles']), vertex_normals(original['world'], original['triangles'])]))
    all_edges, counts = np.unique(np.sort(np.concatenate([d['triangles'][:, [0, 1]], d['triangles'][:, [1, 2]], d['triangles'][:, [2, 0]]]), axis=1), axis=0, return_counts=True)
    mesh.inherited_boundary = {tuple(map(int, e)) for e in all_edges[counts == 1]}
    mesh.inherited_nonmanifold = {tuple(map(int, e)): int(n) for e, n in zip(all_edges[counts > 2], counts[counts > 2])}
    da = np.concatenate([d['old_loop_uv'].reshape(-1, 3, 6), d['source_corner_normals'], d['source_corner_bary'],
                         np.broadcast_to(np.eye(3), (len(d['triangles']), 3, 3)), atlas], axis=2)
    source_ranges = []; baseline_faces = []
    for part in np.unique(d['source_part']):
        if part == 1: continue
        selected = np.flatnonzero(d['source_part'] == part); begin = len(mesh.faces)
        mesh.clipped(d['triangles'][selected], da[selected], d['triangle_materials'][selected], int(part),
                     [('D_lower', np.array([0., 0., -1.]), LOW, None)])
        local = np.asarray(mesh.sourceface[begin:], int)
        baseline_faces.extend(selected[local].tolist())
        mesh.sourceface[begin:] = d['source_face'][selected[local]].tolist()
        source_ranges.append((begin, len(mesh.faces), 'D'))
    head_faces = np.flatnonzero(d['source_part'] == 1); head_begin = len(mesh.faces)
    for fi in head_faces:
        mesh.add(d['triangles'][fi].tolist(), da[fi].copy(), int(d['triangle_materials'][fi]), 1, int(d['source_face'][fi]))
        baseline_faces.append(int(fi))
    source_ranges.append((head_begin, len(mesh.faces), 'D'))
    print('UPPER03_RETAINED_D', len(mesh.faces), flush=True)
    oa = np.concatenate([original['uv_0'], original['uv_1'], original['uv_2'], on,
                         np.broadcast_to(np.eye(3), (len(original['triangles']), 3, 3)),
                         np.zeros((len(original['triangles']), 3, 5))], axis=2)
    template_begin = len(mesh.faces)
    # Top first: intersection cache retains true original-edge identities.
    mesh.clipped(original['triangles']+offset, oa, original['triangle_materials'], 4,
                 [('template_top', np.array([0., 0., -1.]), HEAD, None),
                  ('template_bottom', np.array([0., 0., 1.]), -HIGH, None)])
    baseline_faces.extend([-1]*(len(mesh.faces)-template_begin))
    source_ranges.append((template_begin, len(mesh.faces), 'original'))

    head_tokens = {}
    for fi in head_faces:
        for k, vi in enumerate(d['triangles'][fi]):
            if abs(float(d['world'][vi, 2])-HEAD) < 1e-7:
                token = source_edge_key(d, fi, k, original['triangles'])
                assert token not in head_tokens or head_tokens[token] == int(vi)
                head_tokens[token] = int(vi)
    assert head_tokens
    weld = {}; distances = []
    for (plane, a, b), vi in mesh.cache.items():
        if plane != 'template_top': continue
        token = ('edge', *sorted([a-offset, b-offset])); assert token in head_tokens, ('Missing exact source-edge head binding', token)
        target = head_tokens[token]; distances.append(float(np.linalg.norm(np.asarray(mesh.xyz[vi])-mesh.xyz[target])))
        weld[int(vi)] = target
    for vi in range(offset, offset+len(original['world'])):
        if abs(float(mesh.xyz[vi][2])-HEAD) < 1e-12:
            token = ('vertex', vi-offset)
            if token in head_tokens: weld[vi] = head_tokens[token]
    assert set(weld.values()) == set(head_tokens.values()), ('Head boundary cardinality mismatch', len(weld), len(head_tokens))
    assert max(distances, default=0.) < 2e-7, ('Source-edge mismatch, do not move head', max(distances))
    for fi in range(template_begin, len(mesh.faces)):
        mesh.faces[fi] = [weld.get(int(i), int(i)) for i in mesh.faces[fi]]
    print('UPPER03_SOURCE_EDGE_HEAD_WELD', len(weld), max(distances, default=0.), flush=True)
    loops, _ = mesh.boundary_loops()
    cut_loops = {}
    for key, z in [('lower', LOW), ('upper', HIGH)]:
        matches = [loop for loop in loops if np.max(np.abs(np.asarray(mesh.xyz)[loop, 2]-z)) < 1e-7]
        assert len(matches) == 1, ('Invalid principal cut loop', key, list(map(len, matches)))
        cut_loops[key] = matches[0]
    inherited_loops = len(loops)-2
    frames = {}
    for key, loop in cut_loops.items():
        order, u = quadrant_order(np.asarray(mesh.xyz)[loop]); ids = np.asarray(loop)[order]
        frames[key] = (ids, u)
    count = int(np.ceil(max(len(cut_loops['lower']), len(cut_loops['upper']), 96)/8)*8)
    u = np.arange(count)*2*np.pi/count
    p0 = sample_cycle(np.asarray(mesh.xyz)[cut_loops['lower']], u)
    p1 = sample_cycle(np.asarray(mesh.xyz)[cut_loops['upper']], u)
    donor_sections = ops.SectionSource(original['world'], original['triangles'])
    current_sections = ops.SectionSource(d['world'], d['triangles'])
    h = (HIGH-LOW)/BANDS
    original0 = sample_cycle(section(donor_sections, LOW), u)
    original_minus = sample_cycle(section(donor_sections, LOW-h), u)
    current_minus = sample_cycle(section(current_sections, LOW-h), u)
    delta0 = p0-original0
    delta_slope = (delta0-(current_minus-original_minus))/h
    source_rows = np.asarray([sample_cycle(section(donor_sections, LOW+k*h), u) for k in range(BANDS+1)])
    qrows = source_rows.copy(); row_intersections = []
    for k in range(BANDS+1):
        t = k/BANDS
        h00 = 1-10*t**3+15*t**4-6*t**5
        h10 = t-6*t**3+8*t**4-3*t**5
        qrows[k] += h00*delta0+h10*(HIGH-LOW)*delta_slope
        qrows[k, :, 2] = LOW+k*h
        bad = crossing_pairs(qrows[k]); assert not bad, ('Collar section self crossing', k, bad[:8])
        row_intersections.append(len(bad))
    qrows[0] = p0; qrows[-1] = p1
    collar_begin = len(mesh.faces); all_row_ids = []; prior_ids, prior_u = frames['lower']
    for k in range(1, BANDS):
        ids = np.arange(len(mesh.xyz), len(mesh.xyz)+count, dtype=np.int32)
        mesh.xyz.extend(qrows[k]); mesh.weights.extend(np.zeros((count, 4))); mesh.normals.extend(np.zeros((count, 3)))
        mesh.zipper(prior_ids, prior_u, ids, u, np.array([0., .005, LOW+k*h]), np.array([0., 0., 1.]), 0, 6)
        prior_ids, prior_u = ids, u; all_row_ids.append(ids)
    mesh.zipper(prior_ids, prior_u, *frames['upper'], np.array([0., .005, HIGH]), np.array([0., 0., 1.]), 0, 6)
    baseline_faces.extend([-1]*(len(mesh.faces)-collar_begin))
    # New collar UVs are explicit provisional cylindrical coordinates only.
    provisional = 0
    mesh_world = np.asarray(mesh.xyz)
    for fi in range(collar_begin, len(mesh.faces)):
        face = mesh.faces[fi]; q = mesh_world[face]
        ru = np.mod(np.arctan2(q[:, 1]-.005, q[:, 0]), 2*np.pi)/(2*np.pi)
        if ru.max()-ru.min() > .5: ru[ru < .5] += 1
        uv = np.column_stack([ru, (q[:, 2]-LOW)/(HIGH-LOW)])
        for j in range(3): mesh.attrs[fi][:, j*2:j*2+2] = uv
        mesh.attrs[fi][:, 15:17] = uv; provisional += 1
    faces = np.asarray(mesh.faces, np.int32); attrs = np.asarray(mesh.attrs, np.float32)
    parts = np.asarray(mesh.part, np.int16)
    flips = assembly_api.collar_orientation_flips(faces, np.where(parts == 6, 3, 0))
    assert np.all(parts[flips] == 6)
    faces[flips] = faces[flips][:, [0, 2, 1]]; attrs[flips] = attrs[flips][:, [0, 2, 1]]
    after_loops, _ = mesh.boundary_loops()
    assert len(after_loops) == inherited_loops, ('New open boundary', len(after_loops), inherited_loops)
    all_world = np.asarray(mesh.xyz, np.float32); used = np.unique(faces)
    remap = np.full(len(all_world), -1, np.int32); remap[used] = np.arange(len(used))
    baseline_vertex = np.full(len(used), -1, np.int32); retained = used < len(d['world']); baseline_vertex[retained] = used[retained]
    source_vertex = np.full(len(used), -1, np.int32); source_vertex[retained] = d['source_vertex'][used[retained]]
    known_original = (used >= offset)&(used < offset+len(original['world'])); source_vertex[known_original] = used[known_original]-offset
    arrays = dict(world=all_world[used], triangles=remap[faces], old_loop_uv=attrs[:, :, :6].reshape(-1, 3, 3, 2),
                  source_corner_normals=attrs[:, :, 6:9], source_corner_bary=attrs[:, :, 9:12],
                  baseline_corner_bary=attrs[:, :, 12:15], review_loop_uv=attrs[:, :, 15:17],
                  triangle_materials=np.asarray(mesh.material, np.int16), source_part=parts,
                  source_face=np.asarray(mesh.sourceface, np.int32), source_vertex=source_vertex,
                  baseline_face=np.asarray(baseline_faces, np.int32), baseline_vertex=baseline_vertex,
                  vertex_limb_weights=np.asarray(mesh.weights, np.float32)[used])
    head_ids = np.unique(d['triangles'][d['source_part'] == 1]); lower_ids = np.flatnonzero(d['world'][:, 2] <= LOW)
    assert (remap[head_ids] >= 0).all() and (remap[lower_ids] >= 0).all()
    assert np.array_equal(arrays['world'][remap[head_ids]], d['world'][head_ids])
    assert np.array_equal(arrays['world'][remap[lower_ids]], d['world'][lower_ids])
    actual_head = np.flatnonzero(parts == 1)
    assert np.array_equal(arrays['triangles'][actual_head], remap[d['triangles'][head_faces]])
    for key in ['old_loop_uv', 'source_corner_normals', 'source_corner_bary']:
        assert np.array_equal(arrays[key][actual_head], d[key][head_faces]), key
    new_rows = {k: remap[rows[k]] for k in ['waist', 'armR', 'armL']}
    new_rows['upper_template_transition'] = remap[np.asarray(all_row_ids)]
    for key in ['waist', 'armR', 'armL']:
        assert np.array_equal(arrays['world'][new_rows[key]], d['world'][rows[key]])
    ff = arrays['triangles']; vv = arrays['world'].astype(float); tri = vv[ff]
    double_area = np.linalg.norm(np.cross(tri[:, 1]-tri[:, 0], tri[:, 2]-tri[:, 0]), axis=1)
    assert np.isfinite(vv).all() and (double_area > 0).all(), ('Collapsed triangle', int((double_area <= 0).sum()))
    lower_end_angle = angle(qrows[1]-qrows[0], p0-current_minus)
    donor_plus = sample_cycle(section(donor_sections, HIGH+h), u)
    upper_end_angle = angle(qrows[-1]-qrows[-2], donor_plus-p1)
    report = dict(status='CPU geometry constructed; NO live/source/ART acceptance',
                  operation='Retained D below1.355 + exact Dhead, actual original donor roof/neck1.400..1.465,45mm actual-contour annulus with lower offset/tangent-difference fade',
                  candidate_sha256=ah(arrays['world']), baseline_sha256=BASE_SHA,
                  vertices=len(vv), triangles=len(ff), new_template_faces=int((parts == 4).sum()), new_collar_faces=int((parts == 6).sum()),
                  cut_bounds=dict(lower=LOW, upper=HIGH, unchanged_head_cut=HEAD),
                  boundary_counts={k: len(v) for k, v in cut_loops.items()}, resample_count=count, bands=BANDS,
                  head_vertices_exact=len(head_ids), lower_vertices_exact=len(lower_ids),
                  retained_head_faces_exact=len(head_faces), retained_head_UV3_exact=True, supplied_head_WORLD_normals_exact=True,
                  Ewaist_arm_rows_exact=True, head_template_source_edge_welds=len(weld), template_only_head_snap_max_m=max(distances, default=0.),
                  no_new_open_loops=True, minimum_double_area_m2=float(double_area.min()),
                  contour_nonadjacent_crossings=row_intersections,
                  end_secants=dict(lower_angles_degrees=stats(lower_end_angle), upper_angles_degrees=stats(upper_end_angle),
                                   meaning='Measured finite-row secants, not claimed exact analytic G1; donor absolute contours never averaged into ellipses'),
                  maximum_lower_offset_m=float(np.linalg.norm(delta0, axis=1).max()),
                  maximum_template_correction_m=float(np.linalg.norm(qrows-source_rows, axis=2).max()),
                  provisional_loft_UV_faces=provisional, body_UV_final=False,
                  new_nonadjacent_intersections='UNVERIFIED until complete triangle narrow phase',
                  known_open='Original posterior leaf nearZ1.333 belowlowercut untouched; M1..M6/FB notpassed',
                  source_files=dict(D_geometry_sha256=sha(root/'.mia-cache/body-h/shape/assembly/live-D/geometry.npz'), donor_npz_sha256=sha(component/'donor.npz')),
                  native_saved=False, GPU_used=False, mesh_modified=False, seconds=time.time()-start)
    return arrays, new_rows, report


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args(); root = args.root.resolve()
    out = root/'.mia-cache/body-h/shape/assembly/template03'
    assert not out.exists(), 'Immutable ONE construction output already exists'
    guard = load('upper03_capacity', root/'asset/mia/blender/mia-fit-v003/integration/workspace-storage-20261103/storage_guard.py')
    capacity = guard.inspect(128*1024**2); assert not capacity['violations'], capacity
    arrays, rows, report = build(root)
    out.mkdir(parents=True)
    np.savez_compressed(out/'geometry.npz', **arrays)
    np.savez_compressed(out/'rows.npz', **rows)
    report.update(geometry_npz_sha256=sha(out/'geometry.npz'), capacity=capacity)
    (out/'build.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    total = sum(p.stat().st_size for p in out.iterdir() if p.is_file())
    assert total <= 128*1024**2
    print(json.dumps(dict(status=report['status'], world_sha256=report['candidate_sha256'], vertices=report['vertices'], triangles=report['triangles'], bytes=total, output=str(out))))


if __name__ == '__main__': main()
