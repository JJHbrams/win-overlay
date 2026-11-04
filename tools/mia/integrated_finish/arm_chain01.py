"""Retired arm-chain forecast, retained for diagnosis; no live application.

This preserves transverse arm sections initially, changes longitudinal reach and
orientation, and rigidly transports the complete distal hand including nails.
Actual c9 source review rejected its thorax/breast/lat deformation. The live
select/apply entry points are retired; do not reuse this as an editing recipe.
"""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np

BASE_SHA = '695dbbd825ce444fd04f0e390ccd64d31265d7cb14b027a08bf2ced82b4a7215'
TARGETS = np.array([[.132, .051, 1.330], [.185, .039, 1.100],
                    [.294, .012, .895]], dtype=np.float64)
TIP_IDS = {1: 42692, -1: 42572}


def sha(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def smooth(a):
    a = np.clip(a, 0., 1.)
    return a*a*a*(10.+a*(-15.+6.*a))


def ramp(a, lo, hi):
    return smooth((a-lo)/(hi-lo))


def rotation(a, b):
    a = np.asarray(a, float); a = a/np.linalg.norm(a)
    b = np.asarray(b, float); b = b/np.linalg.norm(b)
    v = np.cross(a, b); c = float(np.dot(a, b))
    assert c > -.999999, 'Antiparallel frame unsupported'
    k = np.array([[0., -v[2], v[1]], [v[2], 0., -v[0]],
                  [-v[1], v[0], 0.]])
    return np.eye(3)+k+k@k/(1.+c)


def axial_map(a, b, aa, bb):
    u = b-a; old_length = np.linalg.norm(u); u = u/old_length
    new = bb-aa; scale = np.linalg.norm(new)/old_length
    return rotation(u, new)@(np.eye(3)+(scale-1.)*np.outer(u, u))


def setup(co, rows):
    frames = {}
    for side, row_name in ((1, 'armR'), (-1, 'armL')):
        # Actual section centres, not old bone positions. E is the current
        # visible bend / transition; W is the measured wrist constriction.
        s = np.array([side*.146, .008, 1.361])
        e = co[rows[row_name][12]].astype(float).mean(axis=0)
        w = np.array([side*.298892, -.026790, 1.000017])
        target = TARGETS.copy(); target[:, 0] *= side
        ss, ee, ww = target
        upper = axial_map(s, e, ss, ee)
        lower = axial_map(e, w, ee, ww)
        old_tip = co[TIP_IDS[side]].astype(float)
        tip_axis = np.array([side*.025, -.013, -.155])
        hand = rotation(old_tip-w, tip_axis)
        u = (w-e)/np.linalg.norm(w-e)
        frames[side] = dict(s=s, e=e, w=w, target=target,
                            upper=upper, lower=lower, hand=hand,
                            lower_axis=u, old_tip=old_tip)
    return frames


def support(q, charts=False):
    """Two material charts: broad torso carrier plus isolated arm residual.

    The first two rejected forecasts slid a narrow support threshold through
    merged tissue. Here the torso lateral coordinate is fixed: .04→.16 m,
    carried continuously from the actual lower waist (Z1.005) to Z1.25. The
    separate arm chart is identified by measured arm/torso gaps below merge.
    Its forearm/hand residual is never applied to ribcage points. The two
    transforms compose as carrier + residual, not two absolute arm transforms.
    """
    x = np.abs(q[:, 0]); z = q[:, 2]
    t = ramp(z, 1.140, 1.250)
    arm = ramp(x, .190+(.145-.190)*t, .210+(.158-.210)*t)
    upper = ramp(z, 1.250, 1.350)
    carrier = ramp(x, .040+(.075-.040)*upper, .160)*ramp(z, 1.005, 1.250)
    top = 1.-ramp(z, 1.375, 1.440)
    combined = (1.-(1.-carrier)*(1.-arm))*top
    return (combined, arm*top) if charts else combined


def deform(q, frames):
    q = np.asarray(q, np.float64)
    result = q.copy(); weight, arm_weight = support(q, charts=True)
    for side in (-1, 1):
        ids = np.flatnonzero((q[:, 0]*side > 0.) & (weight > 0.))
        p = q[ids]; f = frames[side]
        s, e, w = (f[k] for k in ('s', 'e', 'w'))
        ss, ee, ww = f['target']
        a = (p-s)@f['upper'].T+ss
        b = (p-e)@f['lower'].T+ee
        # This row band is transported, never held at old world positions.
        elbow = 1.-ramp(p[:, 2], 1.0862, 1.1839)
        linked = a+(b-a)*elbow[:, None]
        # Blend ends on the wrist plane. Every distal point is one rigid map,
        # not a hand scale or a blend through the palm and fingers.
        reach = (p-w)@f['lower_axis']
        wrist = ramp(reach, -.045, 0.)
        hand = (p-w)@f['hand'].T+ww
        linked += (hand-linked)*wrist[:, None]
        result[ids] += (a-p)*weight[ids, None]+(linked-a)*arm_weight[ids, None]
    return result


def numeric_jacobian(points, frames, step=1.e-5):
    jac = np.empty((len(points), 3, 3))
    for k in range(3):
        delta = np.eye(3)[k]*step
        jac[:, :, k] = (deform(points+delta, frames)-deform(points-delta, frames))/(2.*step)
    return jac


def summary(values):
    a = np.asarray(values)
    if not a.size: return dict(count=0)
    return dict(count=int(a.size), min=float(a.min()), max=float(a.max()),
                median=float(np.median(a)), p01=float(np.quantile(a, .01)),
                p99=float(np.quantile(a, .99)))


def adjacent_angles(co, candidate, faces, affected):
    """Actual mesh continuity witness, independent of the sampled Jacobian."""
    directed = np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    _, inverse, count = np.unique(np.sort(directed, axis=1), axis=0,
                                  return_inverse=True, return_counts=True)
    order = np.argsort(inverse, kind='stable')
    owners = np.tile(np.arange(len(faces)), 3)[order]
    starts = np.r_[0, np.cumsum(count[:-1])]
    paired = np.flatnonzero(count == 2)
    pairs = np.c_[owners[starts[paired]], owners[starts[paired]+1]]
    pairs = pairs[affected[pairs].any(axis=1)]
    angles = []
    for q in (co, candidate):
        triangles = q[faces].astype(float)
        n = np.cross(triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0])
        n /= np.linalg.norm(n, axis=1)[:, None]
        left, right = n[pairs[:, 0]], n[pairs[:, 1]]
        angles.append(np.degrees(np.arctan2(np.linalg.norm(np.cross(left, right), axis=1),
                                           np.sum(left*right, axis=1))))
    increase = angles[1]-angles[0]
    witness = int(np.argmax(increase))
    point = co[faces[pairs[witness]]].astype(float).mean(axis=(0, 1))
    return dict(affected_adjacent_pairs=len(pairs), before_deg=summary(angles[0]),
                after_deg=summary(angles[1]), increase_deg=summary(increase),
                largest_increase_witness=dict(faces=pairs[witness].tolist(),
                    original_center_m=point.tolist(), before_deg=float(angles[0][witness]),
                    after_deg=float(angles[1][witness])))


def forecast(root):
    root = Path(root)
    with np.load(root/'.mia-cache/body-h/live/integrated01/current-geometry.npz') as inp:
        co = inp['co']; faces = inp['faces']
    assert sha(co) == BASE_SHA, ('Stale current body', sha(co))
    with np.load(root/'.mia-cache/migration-to-C/row-ownership.npz') as inp:
        rows = {k: inp[k] for k in inp.files}
    with np.load(root/'.mia-cache/body-h/shape/assembly/live-D/geometry.npz') as inp:
        source_part = inp['source_part']
        assert np.array_equal(inp['triangles'], faces)
    frames = setup(co, rows)
    candidate = deform(co, frames).astype(np.float32)
    delta = candidate.astype(float)-co.astype(float)
    distance = np.linalg.norm(delta, axis=1)
    changed = distance > 0.
    head_ids = np.unique(faces[source_part == 1])
    low_core = (co[:, 2] <= 1.005) & (np.abs(co[:, 0]) < .190)
    medial_neck = (co[:, 2] >= 1.355) & (np.abs(co[:, 0]) <= .075)
    core = (co[:, 2] >= 1.14) & (co[:, 2] <= 1.355) & (np.abs(co[:, 0]) <= .075)
    # Lateral breast roots are intentionally part of the girdle transition.
    lateral_pec = ((co[:, 2] >= 1.250) & (co[:, 2] <= 1.375) &
                   (np.abs(co[:, 0]) > .075) & (co[:, 1] < -.035))
    waist = np.unique(rows['waist'])
    anterior_gland = ((co[:, 2] >= 1.220) & (co[:, 2] <= 1.350) &
                      (np.abs(co[:, 0]) <= .140) & (co[:, 1] < -.090))
    posterior_wall = ((co[:, 2] >= 1.200) & (co[:, 2] <= 1.375) &
                      (np.abs(co[:, 0]) > .075) & (co[:, 1] > .015))
    mask = changed[faces].any(axis=1)
    old_edges = co[faces[mask]].astype(float)
    new_edges = candidate[faces[mask]].astype(float)
    n0 = np.cross(old_edges[:, 1]-old_edges[:, 0], old_edges[:, 2]-old_edges[:, 0])
    n1 = np.cross(new_edges[:, 1]-new_edges[:, 0], new_edges[:, 2]-new_edges[:, 0])
    area0 = np.linalg.norm(n0, axis=1); area1 = np.linalg.norm(n1, axis=1)
    dot = np.einsum('ij,ij->i', n0, n1)/(area0*area1)
    # This is an orientation/strain screen, not a self-contact or ART test.
    triangle_bad = (area1 < 1.e-15) | (dot <= 0.)
    jac_ids = np.flatnonzero(changed)
    jac = numeric_jacobian(co[jac_ids].astype(float), frames)
    determinant = np.linalg.det(jac)
    singular = np.linalg.svd(jac, compute_uv=False)
    hand_report = {}
    for side, f in frames.items():
        hand_mask = ((co[:, 0]*side > .20) &
                     ((co.astype(float)-f['w'])@f['lower_axis'] >= 0.))
        hand_ids = np.flatnonzero(hand_mask)
        expected = (co[hand_ids].astype(float)-f['w'])@f['hand'].T+f['target'][2]
        residual = np.linalg.norm(candidate[hand_ids].astype(float)-expected, axis=1)
        hand_report[str(side)] = dict(vertices=int(len(hand_ids)),
            max_rigid_transport_error_m=float(residual.max()),
            old_tip=co[TIP_IDS[side]].tolist(),
            candidate_tip=candidate[TIP_IDS[side]].tolist(),
            wrist=f['w'].tolist(), target_wrist=f['target'][2].tolist(),
            rotation=f['hand'].tolist())
    protected = dict(head_vertices=int(len(head_ids)),
        head_max_move_m=float(distance[head_ids].max()),
        lower_body_core_vertices=int(low_core.sum()), lower_body_core_max_move_m=float(distance[low_core].max()),
        medial_neck_vertices=int(medial_neck.sum()), medial_neck_max_move_m=float(distance[medial_neck].max()),
        medial_chest_vertices=int(core.sum()), medial_chest_max_move_m=float(distance[core].max()),
        waist_row_move_m=summary(distance[waist]),
        anterior_gland_move_m=summary(distance[anterior_gland]),
        posterior_attachment_move_m=summary(distance[posterior_wall]),
        lateral_pectoral_transition_vertices=int(lateral_pec.sum()),
        lateral_pectoral_transition_move_m=summary(distance[lateral_pec]))
    success = (not triangle_bad.any() and (determinant > 0.).all() and
               all(protected[k] == 0. for k in ('head_max_move_m', 'lower_body_core_max_move_m',
                  'medial_neck_max_move_m')) and
               all(v['max_rigid_transport_error_m'] < 2.e-7 for v in hand_report.values()))
    report = dict(status='TECHNICAL_FORECAST_PASS' if success else 'FORECAST_REJECT',
        source_art_status='UNREVIEWED', collisions='UNVERIFIED',
        input_sha256=sha(co), candidate_sha256=sha(candidate),
        changed_vertices=int(changed.sum()), total_vertices=len(co),
        moved_bounds=[co[changed].min(0).tolist(), co[changed].max(0).tolist()],
        distance_m=summary(distance[changed]), support_weight=summary(support(co)[changed]),
        protected=protected, hands=hand_report,
        triangles=dict(affected=int(mask.sum()), nonpositive_or_degenerate=int(triangle_bad.sum()),
            orientation_cos=summary(dot), area_ratio=summary(area1/area0),
            bad_face_indices=np.flatnonzero(mask)[triangle_bad][:32].tolist()),
        adjacent_surface_angles=adjacent_angles(co, candidate, faces, mask),
        local_jacobian=dict(samples=len(jac_ids), determinant=summary(determinant),
            singular_min=summary(singular.min(1)), singular_max=summary(singular.max(1)),
            nonpositive=int((determinant <= 0.).sum()),
            bad_vertex_indices=jac_ids[determinant <= 0.][:32].tolist()),
        frames={str(k):{n:v.tolist() for n,v in f.items()} for k,f in frames.items()},
        limits=['Art centre intervals are not skeletal ground truth.',
                'First candidate preserves transverse girth; source width refinement is open.',
                'No final shading, collision, deformation, multi-view or ART acceptance.'])
    return candidate, changed, report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', required=True)
    p.add_argument('--output', required=True)
    a = p.parse_args()
    candidate, changed, report = forecast(a.root)
    out = Path(a.output).resolve(); root = Path(a.root).resolve()
    assert out.is_relative_to(root/'.mia-cache'), out
    out.mkdir(parents=True, exist_ok=True)
    assert sum(f.stat().st_size for f in out.rglob('*') if f.is_file()) < 30*1024**2
    (out/'forecast.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    np.savez_compressed(out/'candidate.npz', co=candidate, changed=changed)
    print(json.dumps({k:report[k] for k in ('status','candidate_sha256','changed_vertices',
                                          'protected','hands','triangles','local_jacobian')}, indent=2))


if __name__ == '__main__':
    main()
