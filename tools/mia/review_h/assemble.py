"""Bounded, CPU-only H assembly. Importing never exports or touches Blender.

The original E waist/arm construction is retained. A fresh cervical collar is
an explicit construction hypothesis, not an inferred anatomical scan. The
caller must select and inspect the actual guide cut before exporting anything.
"""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import numpy as np

sys.dont_write_bytecode = True
CANONICAL = Path('D:/MiaWorkCache/mia-reference-work/win-overlay')
BODY = Path('asset/mia/blender/mia-fit-v003/body')


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ah(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@dataclass(frozen=True)
class CutSpec:
    # No default for the critical cut: 1.37 can remove a cap, not just a neck.
    guide_neck_z: float
    donor_neck_z: float = 1.465
    waist_guide_z: float = 1.145
    waist_donor_z: float = 1.005
    maximum_row_spacing_m: float = .004
    medial_neck_halfwidth_limit_m: float = .085


@dataclass(frozen=True)
class NeckGuide:
    z: float
    center_y: float
    radius_x: float
    radius_y: float
    uncertainty_m: float
    source: str


def observed_neck_guides(canonical=CANONICAL):
    """Shared midpoints of the recorded intervals; ellipse is our hypothesis.

    row215 includes trapezius and a bra strap. It is intentionally not turned
    into a separate cylindrical neck station. The caller sees omitted guides.
    """
    record = json.loads((Path(canonical)/'.mia-cache/body-h/head-audit/source-neck-continuity-audit.json').read_text(encoding='utf8'))
    mpp = record['source_mapping']['mpp']
    z0 = record['source_mapping']['z0']
    result = []
    for row in [195, 205]:
        p = record['guide_profile_manual_silhouette_estimates'][str(row)]
        w = record['guide_front_back_manual_outline_estimates'][str(row)]
        interval = w['shared_width_interval_allowing_per_boundary_2px_uncertainty_mm']
        result.append(NeckGuide((z0-row)*mpp, p['centerY_mm']/1000.,
                               np.mean(interval)/2000., p['AP_mm']/2000.,
                               max(2*mpp, (interval[1]-interval[0])/2000.),
                               'tied-hair guide visible outlines; main profile hair-occluded; row'+str(row)))
    return result


def _normals(v, f):
    q = v[f].astype(float)
    n = np.cross(q[:, 1]-q[:, 0], q[:, 2]-q[:, 0])
    out = np.zeros_like(v, dtype=float)
    for k in range(3):
        np.add.at(out, f[:, k], n)
    out /= np.maximum(np.linalg.norm(out, axis=1)[:, None], 1e-20)
    return out


def _angular_delta(points, delta, sigma):
    lengths = np.linalg.norm(np.roll(points, -1, axis=0)-points, axis=1)
    arc = np.r_[0., np.cumsum(lengths[:-1])]
    distance = abs(arc[:, None]-arc[None, :])
    distance = np.minimum(distance, lengths.sum()-distance)
    w = np.exp(-.5*(distance/sigma)**2)
    w[distance > 3*sigma] = 0
    w /= w.sum(1)[:, None]
    return w@delta


def _extrapolate(endpoint, first, second, sample_h, exterior_h):
    """Quadratic at the actual sample spacing, evaluated outside the cut."""
    d1 = (4*first-second-3*endpoint)/(2*sample_h)
    d2 = (second-2*first+endpoint)/(sample_h*sample_h)
    return endpoint-exterior_h*d1+.5*exterior_h*exterior_h*d2


def cervical_rows(mesh, sections_guide, sections_donor, a, b, angles,
                  p0, p1, bands, guides, maximum_row_spacing_m):
    height = float(b[2][2]-a[2][2])
    spacing = height/bands
    assert height > 0 and spacing <= maximum_row_spacing_m+1e-12
    # At the donor cut 1.473 already contains jaw/face branches. Sample +2/+4mm
    # (or closer if original facets demand it), never a whole-head bbox.
    hg = min(sections_guide.row_step(a), .002)
    hd = min(sections_donor.row_step(b), .002)
    g1 = sections_guide.sample(a, -hg, angles)
    g2 = sections_guide.sample(a, -2*hg, angles)
    d1 = sections_donor.sample(b, hd, angles)
    d2 = sections_donor.sample(b, 2*hd, angles)
    q = np.zeros((bands+1, len(angles), 3), float)
    q[0], q[-1] = p0, p1
    q[1] = _extrapolate(p0, g1, g2, hg, spacing)
    q[-2] = _extrapolate(p1, d1, d2, hd, spacing)
    chord0 = np.linalg.norm(np.roll(p0, -1, axis=0)-p0, axis=1)
    chord1 = np.linalg.norm(np.roll(p1, -1, axis=0)-p1, axis=1)
    sigma = 2*max(np.percentile(chord0, 75), np.percentile(chord1, 75))
    q[1] = p0+_angular_delta(p0, q[1]-p0, sigma)
    q[-2] = p1+_angular_delta(p1, q[-2]-p1, sigma)
    fixed = np.array([0, 1, bands-1, bands])
    free = np.setdiff1d(np.arange(bands+1), fixed)
    D = np.zeros((bands-1, bands+1))
    for j in range(bands-1):
        D[j, j:j+3] = [1., -2., 1.]
    matrices = [D]
    targets = [np.zeros((len(D), len(angles), 3))]
    used, omitted = [], []
    for guide in guides:
        t = (guide.z-a[2][2])/spacing
        if not 1.5 < t < bands-1.5:
            omitted.append(dict(z=guide.z, source=guide.source,
                                reason='Outside free cervical collar; must not claim this station fitted'))
            continue
        j = int(np.floor(t)); s = t-j
        row = np.zeros((1, bands+1)); row[0, j:j+2] = [1-s, s]
        target = np.column_stack([guide.radius_x*np.cos(angles),
                                  guide.center_y+guide.radius_y*np.sin(angles),
                                  np.full(len(angles), guide.z)])
        # One fixed uncertainty-scaled data term, no handle/strength sweeps.
        strength = spacing/max(guide.uncertainty_m, spacing)
        matrices.append(strength*row); targets.append(strength*target[None])
        used.append(dict(z=guide.z, center_y=guide.center_y,
                         radius_x=guide.radius_x, radius_y=guide.radius_y,
                         uncertainty_m=guide.uncertainty_m, source=guide.source,
                         normalized_strength=strength))
    A = np.concatenate(matrices)
    target = np.concatenate(targets).reshape(len(A), -1)
    rhs = target-A[:, fixed]@q[fixed].reshape(len(fixed), -1)
    q[free] = np.linalg.solve(A[:, free].T@A[:, free], A[:, free].T@rhs).reshape(len(free), len(angles), 3)
    for k in range(1, bands):
        q[k, :, 2] = a[2][2]+k*spacing
    centers = q.mean(1)
    min_radius = np.min(np.linalg.norm(q[:, :, :2]-centers[:, None, :2], axis=2))
    assert np.isfinite(q).all() and min_radius > .005, 'Collapsed cervical row'
    residuals = []
    for item in used:
        t = (item['z']-a[2][2])/spacing; j = int(np.floor(t)); s = t-j
        station = (1-s)*q[j]+s*q[j+1]
        bounds = [station.min(0), station.max(0)]
        residuals.append(dict(source=item['source'], z=item['z'],
                              achieved_center_y=float((bounds[0][1]+bounds[1][1])/2),
                              achieved_width_x_m=float(bounds[1][0]-bounds[0][0]),
                              achieved_depth_y_m=float(bounds[1][1]-bounds[0][1]),
                              center_y_error_m=float((bounds[0][1]+bounds[1][1])/2-item['center_y']),
                              meaning='Numerical row interpolation only; not a rendered contour'))
    return q, dict(method='Single constrained minimum row-bending solve with uncertain observed elliptical guides',
                   construction_limit='Elliptical stations are an artist construction, not recovered anatomy; actual six-view review mandatory.',
                   row_spacing_m=spacing, bands=bands, fixed_rows=fixed.tolist(),
                   endpoint_sample_m=dict(guide=hg, donor=hd),
                   angular_delta_sigma_m=float(sigma), used_guides=used, omitted_guides=omitted,
                   guide_row_residuals=residuals,
                   minimum_row_radius_m=float(min_radius),
                   maximum_centerline_slope=float(np.max(np.linalg.norm(np.diff(centers[:, :2], axis=0), axis=1)/spacing)))


def _old_collar_loops(Mesh, e, triangle_range, axis):
    v, f = e['world'], e['triangles'][slice(*triangle_range)]
    edges, counts = np.unique(np.sort(np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]), axis=1), axis=0, return_counts=True)
    adj = {}
    for x, y in edges[counts == 1]:
        adj.setdefault(int(x), []).append(int(y)); adj.setdefault(int(y), []).append(int(x))
    assert all(len(xs) == 2 for xs in adj.values())
    seen, loops = set(), []
    for seed in adj:
        if seed in seen: continue
        cur, old, loop = seed, None, []
        while cur not in seen:
            seen.add(cur); loop.append(cur)
            nxt = next(i for i in adj[cur] if i != old)
            old, cur = cur, nxt
        assert cur == seed
        loops.append(loop)
    assert len(loops) == 2
    temp = Mesh(v, np.zeros((len(v), 4)), np.zeros_like(v))
    frames = [temp.ordered(loop, axis) for loop in loops]
    return temp, sorted(frames, key=lambda fr: fr[2]@axis)


def _row_reuse_provider(Mesh, kind, axis, e, erows, emeta):
    oldmesh, oldframes = _old_collar_loops(Mesh, e, emeta['collar_triangle_ranges'][kind], axis)
    # E waist travels downwards; all other collar axes travel upwards.
    if kind == 'waist': oldframes.reverse()
    def provider(a, b, angles, p0, p1, bands):
        old0, _ = oldmesh.resample(oldframes[0], angles)
        old1, _ = oldmesh.resample(oldframes[1], angles)
        delta = max(float(abs(old0-p0).max()), float(abs(old1-p1).max()))
        assert delta < 2e-7, (kind, 'E cut/frame mismatch; cannot reuse rows', delta)
        ids = erows[kind]
        assert ids.shape == (bands-1, len(angles)), (kind, ids.shape, bands, len(angles))
        rows = np.concatenate([p0[None], e['world'][ids].astype(float), p1[None]])
        return rows, dict(method='Reuse E waist/arm interior rows exactly after actual endpoint/frame comparison',
                          interior_rows_float32_exact=True, endpoint_resample_max_packing_delta_m=delta,
                          endpoint_comparison_tolerance_m=2e-7,
                          no_false_bitexact_endpoint_claim=True)
    return provider


def assemble(guide_path, *, cuts, canonical=CANONICAL, donor_path=None,
             neck_guides=None, headneck_delta=None, protected_donor_vertices=None):
    """Return arrays/report in RAM. No writes, mesher, bpy, save, or render.

    headneck_delta(points) must return (world_delta[N,3], Jacobian[N,3,3]).
    If supplied, explicit protected donor IDs are mandatory and remain exact.
    The callback is a caller-approved cervical edit, never automatic head move.
    """
    root = Path(canonical); p = root/BODY/'surface-review12'
    ops = load_module('h_assembly_mesh_ops', p/'mesh_ops.py')
    d = dict(np.load(donor_path or p/'donor.npz'))
    gd = dict(np.load(guide_path))
    v0, f0 = d['world'].copy(), d['triangles']
    vg, fg = gd['world'], gd['triangles']; offset = len(v0)
    baseline = json.loads((root/'.mia-cache/body-h/baseline4/capture.json').read_text())
    matrix = np.array(baseline['geometry']['object_matrix'])
    n = np.einsum('tci,ij->tcj', d['corner_normals'].astype(float), np.linalg.inv(matrix[:3, :3]))
    n /= np.maximum(np.linalg.norm(n, axis=2)[:, :, None], 1e-20)
    edit = dict(applied=False, changed_vertices=0)
    if headneck_delta is not None:
        assert protected_donor_vertices is not None, 'Explicit protected face donor IDs required'
        dv, J = headneck_delta(v0.astype(float))
        assert dv.shape == v0.shape and J.shape == (len(v0), 3, 3)
        assert np.isfinite(dv).all() and np.linalg.det(J).min() > .25
        assert np.array_equal(dv[protected_donor_vertices], np.zeros_like(dv[protected_donor_vertices]))
        # Unretained cervical samples may move to give the retained cut a true
        # neighborhood/Jacobian. Distal retained body is still byte-exact.
        assert np.array_equal(dv[v0[:, 2] <= 1.34], np.zeros_like(dv[v0[:, 2] <= 1.34]))
        assert abs(dv[:, 2]).max() < 1e-12, 'This planar-cut API permits cervical AP/lateral edits only'
        changed = np.linalg.norm(dv, axis=1) > 0
        v0 = (v0+dv).astype(np.float32)
        invJ = np.linalg.inv(J)
        n = np.einsum('tci,tcij->tcj', n, invJ[f0])
        n /= np.maximum(np.linalg.norm(n, axis=2)[:, :, None], 1e-20)
        edit = dict(applied=True, changed_vertices=int(changed.sum()),
                    protected_donor_vertices_exact=len(protected_donor_vertices),
                    maximum_delta_m=float(np.linalg.norm(dv, axis=1).max()),
                    positive_J_min=float(np.linalg.det(J).min()))
    n = n.astype(np.float32)
    W = np.column_stack([d[k] for k in ['armR', 'armL', 'legR', 'legL']])
    vn = np.zeros_like(v0, dtype=float)
    for k in range(3): np.add.at(vn, f0[:, k], n[:, k])
    vn /= np.maximum(np.linalg.norm(vn, axis=1)[:, None], 1e-20)
    gn = _normals(vg, fg)
    mesh = ops.Mesh(np.vstack([v0, vg]), np.vstack([W, np.zeros((len(vg), 4))]), np.vstack([vn, gn]))
    edges, counts = np.unique(np.sort(np.concatenate([f0[:, [0, 1]], f0[:, [1, 2]], f0[:, [2, 0]]]), axis=1), axis=0, return_counts=True)
    mesh.inherited_boundary = {tuple(map(int, e)) for e in edges[counts == 1]}
    mesh.inherited_nonmanifold = {tuple(map(int, e)): int(c) for e, c in zip(edges[counts > 2], counts[counts > 2])}
    uv = np.concatenate([d['uv_0'], d['uv_1'], d['uv_2'], n, np.broadcast_to(np.eye(3), (len(f0), 3, 3))], axis=2)
    ga = np.zeros((len(fg), 3, 12)); ga[:, :, 6:9] = gn[fg]
    meta = json.loads((p/'donor.json').read_text()); mat = len(meta['material_slots'])
    Z = np.array([0., 0., 1.]); R = np.array([np.sin(np.deg2rad(25)), 0., -np.cos(np.deg2rad(25))]); L = R*np.array([-1, 1, 1])
    cGR = np.array([.236, 0., 1.17])-.020*R
    cDR = np.array([.25, 0., 1.13])+.045*R
    frames = {'armR': (R, cGR, cDR), 'armL': (L, cGR*np.array([-1, 1, 1]), cDR*np.array([-1, 1, 1]))}
    plane = lambda name, axis, c: (name, np.asarray(axis, float), float(c), None)
    mesh.clipped(f0, uv, np.full(len(f0), mat), 0, [plane('donor_waist', -Z, cuts.waist_donor_z)])
    mesh.clipped(f0, uv, d['triangle_materials'], 1, [plane('donor_neck', Z, -cuts.donor_neck_z)])
    for kind, semantic in [('armR', 1), ('armL', 0)]:
        axis, cg, cd = frames[kind]
        mesh.clipped(f0, uv, np.full(len(f0), mat), 0, [plane('donor_waist', Z, -cuts.waist_donor_z),
                     ('donor_'+kind+'_semantic', None, .5, semantic), plane('donor_'+kind, axis, -axis@cd)])
    mesh.clipped(fg+offset, ga, np.full(len(fg), mat), 2,
                 [plane('guide_waist', Z, -cuts.waist_guide_z), plane('guide_neck', -Z, cuts.guide_neck_z)]
                 +[plane('guide_'+kind, -axis, axis@cg) for kind, (axis, cg, cd) in frames.items()], source_offset=-len(f0))
    loops, _ = mesh.boundary_loops(); classified = {}; inherited = []
    tests = {'donor_waist': lambda q: abs(q[:, 2]-cuts.waist_donor_z).max() < 1e-7 and abs(q[:, 0].mean()) < .08,
             'guide_waist': lambda q: abs(q[:, 2]-cuts.waist_guide_z).max() < 1e-7,
             'donor_neck': lambda q: abs(q[:, 2]-cuts.donor_neck_z).max() < 1e-7,
             'guide_neck': lambda q: abs(q[:, 2]-cuts.guide_neck_z).max() < 1e-7}
    for kind, (axis, cg, cd) in frames.items():
        sign = 1 if kind == 'armR' else -1
        for prefix, c in [('donor', cd), ('guide', cg)]:
            tests[prefix+'_'+kind] = lambda q, axis=axis, c=c, sign=sign: abs((q-c)@axis).max() < 1e-7 and sign*q[:, 0].mean() > .15
    records = []
    for loop in loops:
        q = np.array(mesh.xyz)[loop]; labels = [name for name, test in tests.items() if test(q)]
        name = labels[0] if len(labels) == 1 else None
        if name:
            assert name not in classified, ('Multiple cut loops', name)
            classified[name] = loop
        else: inherited.append(loop)
        records.append(dict(name=name or 'inherited', count=len(loop), bounds=[q.min(0).tolist(), q.max(0).tolist()]))
    assert set(classified) == set(tests), ('Missing cuts', set(tests)-set(classified))
    neck = np.array(mesh.xyz)[classified['guide_neck']]
    assert abs(neck[:, 0]).max() <= cuts.medial_neck_halfwidth_limit_m, ('Guide cut crosses cap/shoulder; choose true medial neck opening', neck.min(0), neck.max(0))
    removed_cap = (abs(vg[:, 0]) > cuts.medial_neck_halfwidth_limit_m)&(vg[:, 2] > cuts.guide_neck_z+1e-7)
    assert not removed_cap.any(), ('Guide plane would amputate cap roof', int(removed_cap.sum()))
    e = dict(np.load(p/'joined-expanded-E.npz')); erows = dict(np.load(p/'collar-rows-E.npz'))
    emeta = json.loads((p/'assembly-E.json').read_text())
    sg, sd = ops.SectionSource(vg, fg), ops.SectionSource(v0, f0)
    collars = {}; ranges = {}; all_guides = neck_guides if neck_guides is not None else observed_neck_guides(root)
    for kind, axis in [('neck', Z), ('waist', Z), ('armR', R), ('armL', L)]:
        a = mesh.ordered(classified['guide_'+kind], axis)
        b = mesh.ordered(classified['donor_'+kind], axis)
        bands = max(8, int(np.ceil(abs((b[2]-a[2])@axis)/cuts.maximum_row_spacing_m-1e-8)))
        if kind == 'neck':
            def provider(a, b, angles, p0, p1, bands):
                return cervical_rows(mesh, sg, sd, a, b, angles, p0, p1, bands, all_guides, cuts.maximum_row_spacing_m)
        else: provider = _row_reuse_provider(ops.Mesh, kind, axis, e, erows, emeta)
        start = len(mesh.faces)
        collars[kind] = mesh.collar(classified['guide_'+kind], classified['donor_'+kind], axis, mat, 3,
                                    bands=bands, discrete_provider=provider)
        ranges[kind] = [start, len(mesh.faces)]
    after, _ = mesh.boundary_loops(); assert len(after) == len(inherited), 'New open seam'
    faces = np.asarray(mesh.faces, np.int32); attrs = np.asarray(mesh.attrs, np.float32)
    world = np.asarray(mesh.xyz, np.float32); used = np.unique(faces)
    remap = np.full(len(world), -1, np.int32); remap[used] = np.arange(len(used))
    source_vertex = np.full(len(used), -1, np.int32)
    known = used < len(v0); source_vertex[known] = used[known]
    guide_vertex = np.full(len(used), -1, np.int32)
    known = (used >= offset)&(used < offset+len(vg)); guide_vertex[known] = used[known]-offset
    arrays = dict(world=world[used], triangles=remap[faces], old_loop_uv=attrs[:, :, :6].reshape(-1, 3, 3, 2),
                  source_corner_normals=attrs[:, :, 6:9], source_corner_bary=attrs[:, :, 9:12],
                  triangle_materials=np.asarray(mesh.material, np.int16), source_part=np.asarray(mesh.part, np.int16),
                  source_face=np.asarray(mesh.sourceface, np.int32), source_vertex=source_vertex, guide_vertex=guide_vertex,
                  vertex_limb_weights=np.asarray(mesh.weights, np.float32)[used])
    row_arrays = {k: remap[np.asarray(info.pop('row_vertex_ids'), np.int32)] for k, info in collars.items()}
    report = dict(status='RAM assembly only; not exported, installed, rendered or accepted',
                  guide_path=str(guide_path), guide_sha256=sha(guide_path), donor_sha256=sha(donor_path or p/'donor.npz'),
                  world_sha256=ah(arrays['world']), triangles_sha256=ah(arrays['triangles']),
                  vertices=len(arrays['world']), triangles=len(arrays['triangles']), cuts=cuts.__dict__,
                  cut_loops=records, collars=collars, collar_triangle_ranges=ranges,
                  cervical_donor_edit=edit, inherited_boundary_edges=len(mesh.inherited_boundary),
                  inherited_nonmanifold_edges=len(mesh.inherited_nonmanifold), new_open_seams=0,
                  old_UV_layers=meta['uv_layers'], GPU_used=False, native_saved=False)
    return arrays, row_arrays, report


def export_assembly(arrays, rows, report, output_dir, *, canonical=CANONICAL):
    """Explicit root-authorized writer; never called automatically by assemble."""
    root = Path(canonical).resolve(); out = Path(output_dir).resolve()
    allowed = (root/'.mia-cache/body-h/shape/assembly').resolve()
    assert out == allowed or allowed in out.parents, 'Output must stay in canonical ignored H assembly cache'
    guard = load_module('h_assembly_capacity', root/'asset/mia/blender/mia-fit-v003/integration/workspace-storage-20261103/storage_guard.py')
    budget = guard.inspect(40*1024**2); assert not budget['violations'], budget
    out.mkdir(parents=True, exist_ok=True)
    assert not (out/'geometry.npz').exists(), 'Do not overwrite a frozen candidate'
    np.savez_compressed(out/'geometry.npz', **arrays)
    np.savez_compressed(out/'collar-rows.npz', **rows)
    final = dict(report, assembly_geometry_sha256=sha(out/'geometry.npz'), capacity=budget,
                 status='CPU assembled payload; actual gray/source review still required')
    (out/'assembly.json').write_text(json.dumps(final, indent=2)+'\n', encoding='utf8', newline='\n')
    return final
