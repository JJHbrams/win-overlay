"""REJECTED CPU-only source-gap transverse bend; NO live apply operation.

Import is inert. There is deliberately no select/apply/restore implementation.
One forecast gained a front gap but hid the entire left brow at -35 degrees,
and produced new intersections with unowned Main side/backing components.
Do not retune this into an automatic variant grid. The source
art is unchanged; its existing manually interpreted gap is an uncertain design
guide, not artist spline recovery or a guarantee of physical brow visibility.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import runpy

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
KEY = 'MIA_FringeCoherentBend01'
OUT = '.mia-cache/face-live/live/fringe-bend01'
TARGET = 'MIA_Hair_CurvedRear03Base_RemainingMain'
BASE = '16d192576cd8ecc1905f4eba96b4686c038e8c94a56e6eec7dee552e6eee0b2c'
FAMILIES = {'Outer': [34013, 37707, 39972, 42926, 46927, 35163],
            'Fine': [47790, 47982, 48443], 'Inner': [48868, 48535, 41036, 49058, 48600]}
REJECTION = dict(
    status='FORECAST_REJECTED_NOT_LIVE_APPLYABLE',
    left_brow_clear_sample_indices={
        'front': dict(before=[44, 45, 46, 47], after=[31, 32, 33, 34, 35]),
        'minus35': dict(before=[49, 50, 51, 52], after=[]),
        'plus35': dict(before=[], after=[22])},
    right_brow_clear_sets_unchanged=True,
    sampled_before_matches_actual_probe=True,
    new_intersection_witnesses=[dict(faces=[32734, 34983], roots=[31817, 35163]),
                                dict(faces=[32734, 34985], roots=[31817, 35163]),
                                dict(faces=[29977, 35168], roots=[29178, 35163])],
    collision_limit='Stopped after5 new SAT witnesses/338 tested pairs; not a complete count or collision PASS',
    geometry_or_material_changed=False, native_saved=False)


def digest(a): return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def file_sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def smooth(t):
    t = np.clip(t, 0, 1)
    return t**3*(10+t*(-15+6*t))


def smooth_derivative(t):
    t = np.asarray(t)
    return np.where((t > 0)&(t < 1), 30*t*t*(1-t)**2, 0.)


def profile(s, bounds):
    lo, left, right, hi = bounds
    assert lo < left < right < hi
    a, b = (s-lo)/(left-lo), (hi-s)/(hi-right)
    w = smooth(a)*smooth(b)
    dw = smooth_derivative(a)/(left-lo)*smooth(b)-smooth(a)*smooth_derivative(b)/(hi-right)
    return w, dw


def catmull(points, t):
    p = np.asarray(points, float); value = t*(len(p)-1)
    i = min(int(value), len(p)-2); f = value-i
    a, b, c, d = p[max(i-1, 0)], p[i], p[i+1], p[min(i+2, len(p)-1)]
    return .5*(2*b+(-a+c)*f+(2*a-5*b+4*c-d)*f*f+(-a+3*b-3*c+d)*f*f*f)


def ray_hits(q, point, direction):
    origin = point-direction*2
    lower, upper = q.min(1), q.max(1)
    relevant = np.flatnonzero((lower <= np.maximum(origin, point)+1e-10).all(1)&
                             (upper >= np.minimum(origin, point)-1e-10).all(1))
    p = q[relevant]; e1, e2 = p[:, 1]-p[:, 0], p[:, 2]-p[:, 0]
    h = np.cross(np.broadcast_to(direction, e2.shape), e2); det = np.sum(e1*h, axis=1)
    good = abs(det) > 1e-15; s = origin-p[:, 0]
    u = np.divide(np.sum(s*h, axis=1), det, out=np.zeros(len(det)), where=good)
    cross = np.cross(s, e1)
    v = np.divide(np.sum(cross*direction, axis=1), det, out=np.zeros(len(det)), where=good)
    distance = np.divide(np.sum(cross*e2, axis=1), det, out=np.zeros(len(det)), where=good)
    mask = good&(u >= -1e-7)&(v >= -1e-7)&(u+v <= 1+1e-7)&(distance >= 0)&(distance < 2-2e-5)
    return relevant[mask], distance[mask]


def design(root=ROOT):
    root = Path(root)
    with np.load(root/'.mia-cache/face-live/source-audit/analysis.npz') as archive:
        raw, world, faces = [archive[k].copy() for k in ('main_raw', 'main_world', 'main_triangles')]
    with np.load(root/'.mia-cache/face-live/source-audit/components.npz') as archive: roots = archive['face_root'].copy()
    assert digest(raw) == BASE
    probe_path = root/'.mia-cache/face-live/live/fringe-probe01/probe.json'
    probe = json.loads(probe_path.read_text())
    goal_path = root/'tools/mia/face_surface_live/fringe_terminal_goal.json'
    goal = json.loads(goal_path.read_text()); source = root/goal['source']
    assert file_sha(source) == goal['source_sha256']
    matrix = np.array(probe['ray_views'][0]['matrix'])
    r = matrix[:3, 0].copy(); r /= np.linalg.norm(r)
    up = matrix[:3, 1]-r*(matrix[:3, 1]@r); up /= np.linalg.norm(up)
    direction = -matrix[:3, 2]; direction /= np.linalg.norm(direction)
    origin = np.array([0., 0., 1.58])
    curves = {name: np.array([s['world_candidates'][0] for s in curve['samples']])
              for name, curve in probe['current_evaluated_brow_curves'].items()}
    assert all(len(s['world_candidates']) == 1 for c in probe['current_evaluated_brow_curves'].values() for s in c['samples'])
    def brow(side, u):
        values = curves['V31_SourceBrow_'+str(side)]
        return np.array([np.interp(u, np.linspace(0, 1, len(values)), values[:, i]) for i in range(3)])
    pp = np.array([[v['pixel'][0], -v['pixel'][1]] for v in goal['source_brow_anchors']], float)
    qq = np.array([[(brow(v['side'], v['u'])-origin)@r, (brow(v['side'], v['u'])-origin)@up]
                   for v in goal['source_brow_anchors']])
    p0, q0 = pp.mean(0), qq.mean(0)
    z = pp[:, 0]-p0[0]+1j*(pp[:, 1]-p0[1]); w = qq[:, 0]-q0[0]+1j*(qq[:, 1]-q0[1])
    similarity = np.vdot(z, w)/np.vdot(z, z)
    def mapped(pixel):
        return complex(pixel[0]-p0[0], -pixel[1]-p0[1])*similarity+complex(*q0)
    def source_edge(leaf, sign):
        lo, hi = .5, .85
        for _ in range(45):
            t = (lo+hi)/2; p = catmull(leaf['pixels'], t)
            x = p[0]+sign*float(catmull(leaf['full_width_pixels'], t))/2
            by = 276+(x-410)*(272-276)/45
            if p[1] < by: lo = t
            else: hi = t
        p = catmull(leaf['pixels'], (lo+hi)/2)
        return [float(p[0]+sign*catmull(leaf['full_width_pixels'], (lo+hi)/2)/2), float(p[1])]
    source_left = source_edge(goal['leaves'][0], 1); source_right = source_edge(goal['leaves'][1], -1)
    left, right = mapped(source_left), mapped(source_right)
    gap = right.real-left.real; center_height = (left.imag+right.imag)/2
    assert .002 < gap < .006, 'Manual source gap outside bounded hypothesis'
    ids = {name: np.flatnonzero(np.isin(roots, values)) for name, values in FAMILIES.items()}
    points = {name: np.unique(faces[values]) for name, values in ids.items()}
    selected = np.unique(np.concatenate(list(points.values())))
    selected_faces = np.unique(np.concatenate(list(ids.values())))
    assert len(selected) == 741 and len(selected_faces) == 951
    bank_faces = np.r_[ids['Outer'], ids['Fine']]
    def edge_u(face_ids, lo, hi, starts_hit):
        triangles = world[faces[face_ids]].astype(float)
        assert bool(len(ray_hits(triangles, brow(-1, lo), direction)[0])) == starts_hit
        assert bool(len(ray_hits(triangles, brow(-1, hi), direction)[0])) != starts_hit
        for _ in range(35):
            mid = (lo+hi)/2
            if bool(len(ray_hits(triangles, brow(-1, mid), direction)[0])) == starts_hit: lo = mid
            else: hi = mid
        return (lo+hi)/2
    ul, ur = edge_u(bank_faces, .45, .55, True), edge_u(ids['Inner'], .3, .5, False)
    old_left, old_right = (brow(-1, ul)-origin)@r, (brow(-1, ur)-origin)@r
    amplitudes = {'Outer': left.real-old_left, 'Fine': left.real-old_left, 'Inner': right.real-old_right}
    assert -.008 < amplitudes['Fine'] < 0 < amplitudes['Inner'] < .008
    after = raw.copy(); slope = np.zeros(len(raw)); profile_records = {}
    for name, selected_points in points.items():
        s = (raw[selected_points].astype(float)-origin)@up
        # One source-gap-wide plateau; true family-level roots/hooks stay held.
        # Internal laminate caps are not mistaken for anatomical root anchors.
        bounds = [float(s.min()+2*gap), center_height-gap/2, center_height+gap/2, float(s.max()-2*gap)]
        value, derivative = profile(s, bounds)
        after[selected_points] = raw[selected_points].astype(float)+amplitudes[name]*value[:, None]*r
        slope[selected_points] = amplitudes[name]*derivative
        profile_records[name] = dict(amplitude_mm=amplitudes[name]*1000, height_bounds_m=bounds,
            selected_points=len(selected_points), unchanged_root_hook_points=int((value == 0).sum()),
            changed_points=int((value > 0).sum()), maximum_shear=float(abs(amplitudes[name]*derivative).max()))
    changed = np.flatnonzero(np.any(after != raw, axis=1))
    affected_faces = np.flatnonzero(np.any(np.isin(faces, changed), axis=1))
    assert np.isin(affected_faces, selected_faces).all()
    tri_before, tri_after = raw[faces[affected_faces]].astype(float), after[faces[affected_faces]].astype(float)
    n0 = np.cross(tri_before[:, 1]-tri_before[:, 0], tri_before[:, 2]-tri_before[:, 0])
    n1 = np.cross(tri_after[:, 1]-tri_after[:, 0], tri_after[:, 2]-tri_after[:, 0])
    norm0, norm1 = np.linalg.norm(n0, axis=1), np.linalg.norm(n1, axis=1)
    angles = np.degrees(np.arccos(np.clip(np.sum(n0*n1, axis=1)/(norm0*norm1), -1, 1)))
    assert (norm1 > 1e-13).all() and float(angles.max()) < 70, 'Collapsed or excessive triangle turn'
    assert np.array_equal(raw[np.setdiff1d(np.arange(len(raw)), selected)], after[np.setdiff1d(np.arange(len(raw)), selected)])
    report = dict(status=REJECTION['status'], rejection=REJECTION,
        operation='Source-gap-derived C2 coherent shear bend, no width multiplier or new leaf meshes',
        source=str(source.relative_to(root)), source_sha256=goal['source_sha256'],
        source_gap_pixels=[source_left, source_right], source_gap_mm=gap*1000,
        source_similarity_scale=float(abs(similarity)), source_similarity_rotation_degrees=float(np.angle(similarity)*180/np.pi),
        source_anchor_residual_mm=(abs(z*similarity+complex(*q0)-(qq[:, 0]+1j*qq[:, 1]))*1000).tolist(),
        current_bank_edge_u=[ul, ur], current_bank_overlap_mm=float((old_left-old_right)*1000),
        profiles=profile_records, selected_points=741, selected_faces=951, changed_points=len(changed),
        affected_faces=len(affected_faces), maximum_move_mm=float(np.linalg.norm(after-raw, axis=1).max()*1000),
        maximum_geometric_normal_turn_degrees=float(angles.max()), p95_geometric_normal_turn_degrees=float(np.percentile(angles, 95)),
        no_triangle_flips=True, continuous_shear_Jacobian_determinant=1,
        original_depth_along_front_axis_held=True, source_root_lower_hook_profiles_held=True,
        source_curve_limit='Existing manually interpreted Fine/Middle edge guide; not recovered artist spline or all-view visibility proof',
        source_probe_sha256=file_sha(probe_path), hypothesis_only=True, ART=False)
    return dict(before=raw, after=after, world=world, faces=faces, roots=roots, point_ids=points,
                family_faces=ids, changed=changed, affected_faces=affected_faces, slope=slope,
                right=r, up=up, probe=probe, report=report)
