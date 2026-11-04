"""One source-guided, explicit-ID waist-width proposal; no Blender mutation.

Retains existing sections and Y/Z. A smooth lateral cage correction narrows the
natural waist and releases to exact held rib/hip boundaries. This is not a
replacement torso, a loft, an anatomy pass, or an automatically approved edit.
"""
from pathlib import Path
import argparse
import hashlib
import json
import runpy
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
BASE = '183402301d4e38d46e63a9de64665dcf042491e6d0bbe3eb95f081b0fc4fb709'
CONTROL_Z = np.array([1.005, 1.04, 1.08, 1.12, 1.135, 1.155, 1.175, 1.195])
CONTROL_DELTA = np.array([0., -.006, -.0095, -.0235, -.0239, -.020, -.010, 0.])


def sha(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def tangents(x, y):
    """Shape-preserving Hermite slopes, with exact held endpoint tangents."""
    h = np.diff(x); d = np.diff(y)/h; m = np.zeros_like(y)
    for i in range(1, len(y)-1):
        if d[i-1]*d[i] > 0:
            w1, w2 = 2*h[i]+h[i-1], h[i]+2*h[i-1]
            m[i] = (w1+w2)/(w1/d[i-1]+w2/d[i])
    return m


def curve(z, x=CONTROL_Z, y=CONTROL_DELTA):
    z = np.asarray(z, float); m = tangents(x, y)
    i = np.clip(np.searchsorted(x, z, side='right')-1, 0, len(x)-2)
    h = x[i+1]-x[i]; t = np.clip((z-x[i])/h, 0., 1.)
    value = ((2*t**3-3*t**2+1)*y[i] + (t**3-2*t**2+t)*h*m[i]
             + (-2*t**3+3*t**2)*y[i+1] + (t**3-t**2)*h*m[i+1])
    return np.where((z > x[0]) & (z < x[-1]), value, 0.)


def sections(q, faces, levels):
    edges = np.unique(np.sort(np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]]), axis=1), axis=0)
    a, b = q[edges[:, 0]].astype(float), q[edges[:, 1]].astype(float)
    output = []
    for z in levels:
        hit = (a[:, 2]-z)*(b[:, 2]-z) < 0
        aa, bb = a[hit], b[hit]
        points = aa+(bb-aa)*((z-aa[:, 2])/(bb[:, 2]-aa[:, 2]))[:, None]
        assert len(points), ('No actual section', z)
        output.append(dict(z=float(z), radius=float((points[:, 0].max()-points[:, 0].min())/2),
                           center_x=float((points[:, 0].max()+points[:, 0].min())/2),
                           ymin=float(points[:, 1].min()), ymax=float(points[:, 1].max())))
    return output


def stats(a):
    return dict(min=float(a.min()), median=float(np.median(a)), p99=float(np.quantile(a, .99)), max=float(a.max()))


def continuity(before, after, faces, affected):
    directed = np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    _, inverse, count = np.unique(np.sort(directed, axis=1), axis=0, return_inverse=True, return_counts=True)
    order = np.argsort(inverse, kind='stable'); owners = np.tile(np.arange(len(faces)), 3)[order]
    starts = np.r_[0, np.cumsum(count[:-1])]; pairs = np.flatnonzero(count == 2)
    pairs = np.c_[owners[starts[pairs]], owners[starts[pairs]+1]]
    pairs = pairs[affected[pairs].any(1)]
    angles = []
    for q in (before, after):
        tri = q[faces].astype(float); n = np.cross(tri[:, 1]-tri[:, 0], tri[:, 2]-tri[:, 0])
        n /= np.linalg.norm(n, axis=1)[:, None]; a, b = n[pairs[:, 0]], n[pairs[:, 1]]
        angles.append(np.degrees(np.arctan2(np.linalg.norm(np.cross(a, b), axis=1), np.sum(a*b, axis=1))))
    delta = angles[1]-angles[0]; witness = int(np.argmax(delta))
    return dict(before_degrees=stats(angles[0]), after_degrees=stats(angles[1]), increase_degrees=stats(delta),
                witness=dict(faces=pairs[witness].tolist(), before=float(angles[0][witness]),
                             after=float(angles[1][witness]), original_center=before[faces[pairs[witness]]].mean((0, 1)).tolist()))


def prepare(root=ROOT):
    root = Path(root).resolve(); folder = root/'.mia-cache/body-h/live/waist01'
    output = folder/'proposal'; assert not output.exists(), 'Do not overwrite a frozen proposal'
    with np.load(folder/'current-geometry.npz') as archive:
        q, faces = archive['co'], archive['faces'].astype(np.int32)
    assert sha(q) == BASE
    with np.load(root/'.mia-cache/body-h/shape/assembly/live-D/geometry.npz') as archive:
        parts = archive['source_part']; assert np.array_equal(archive['triangles'], faces)
    with np.load(root/'.mia-cache/migration-to-C/row-ownership.npz') as archive:
        waist = archive['waist'].ravel()
    guide = np.unique(faces[parts == 2]); semantic = np.unique(np.r_[waist, guide])
    eligible = semantic[(q[semantic, 2] > CONTROL_Z[0]) & (q[semantic, 2] < CONTROL_Z[-1])]
    edges = np.unique(np.sort(np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]]), axis=1), axis=0)
    components = runpy.run_path(str(root/'tools/mia/integrated_finish/arm_length02.py'))['components']
    labels = components(eligible, edges, len(q))
    seed = int(waist[len(waist)//2]); label = labels[np.flatnonzero(eligible == seed)[0]]
    ids = eligible[labels == label]
    assert np.abs(q[ids, 0]).max() < .16 and ids.size > 17000
    levels = np.linspace(CONTROL_Z[0]-1e-5, CONTROL_Z[-1]+1e-5, 192)
    # Measurement window only; edit ownership is the connected semantic domain
    # above. Actual arms lie outside this window at these waist heights.
    trunk = faces[(np.abs(q[faces, 0]) < .17).all(1)]
    old_sections = sections(q, trunk, levels)
    radii = np.array([row['radius'] for row in old_sections])
    centers = np.array([row['center_x'] for row in old_sections])
    z = q[ids, 2].astype(float); radius = np.interp(z, levels, radii); center = np.interp(z, levels, centers)
    delta = curve(z); scale = 1+delta/radius; assert scale.min() > .7 and scale.max() <= 1
    candidate = q.copy(); candidate[ids, 0] = (center+(q[ids, 0]-center)*scale).astype(np.float32)
    assert np.array_equal(candidate[:, 1:].view(np.uint32), q[:, 1:].view(np.uint32))
    editable = ids[(z >= 1.04) & (z <= 1.165)].astype(np.int32)
    transition = np.setdiff1d(ids, editable).astype(np.int32)
    fixed = np.setdiff1d(np.arange(len(q), dtype=np.int32), ids); head = np.unique(faces[parts == 1])
    guard = runpy.run_path(str(root/'tools/mia/integrated_finish/scoped_mesh_edit.py'))
    proof = guard['validate_delta'](q, candidate, faces, editable, transition,
        dict(head=head, retained_chest_lats_pelvis_limbs=fixed), expected_before_sha256=BASE)
    changed = (q.view(np.uint32) != candidate.view(np.uint32)).any(1); affected = changed[faces].any(1)
    a, b = q[faces[affected]].astype(float), candidate[faces[affected]].astype(float)
    n0, n1 = np.cross(a[:, 1]-a[:, 0], a[:, 2]-a[:, 0]), np.cross(b[:, 1]-b[:, 0], b[:, 2]-b[:, 0])
    area0, area1 = np.linalg.norm(n0, axis=1), np.linalg.norm(n1, axis=1)
    cosine = np.sum(n0*n1, axis=1)/(area0*area1)
    assert (area1 > 1e-15).all() and (cosine > 0).all()
    after_sections = sections(candidate, trunk, levels)
    hand_ids = np.load(root/'.mia-cache/body-h/live/integrated01/arm-length02/proposal.npz')['editable_ids']
    assert np.array_equal(q[hand_ids], candidate[hand_ids])
    report = dict(proof, status='ONE_SCOPED_WAIST_FORECAST_NOT_APPLIED',
        domain='Actual E waist row IDs plus actual guidepart2 lower-wall IDs,1.005<Z<1.195; all complement fixed',
        operation='Positive X-only masked section-preserving cage correction; no new sections/topology/loft',
        controls=[dict(z=float(z), delta_radius=float(d)) for z, d in zip(CONTROL_Z, CONTROL_DELTA)],
        endpoint_delta_tangents=tangents(CONTROL_Z, CONTROL_DELTA)[[0, -1]].tolist(),
        before_sections=old_sections, after_sections=after_sections,
        maximum_lateral_move_m=float(np.abs(candidate[:, 0]-q[:, 0]).max()), scale=stats(scale),
        minimum_x_jacobian=float(scale.min()), Y_Z_bit_exact=True, arm_reach_ids_exact=len(hand_ids),
        triangles=dict(affected=int(affected.sum()), minimum_orientation_cos=float(cosine.min()), area_ratio=stats(area1/area0)),
        continuity=continuity(q, candidate, faces, affected),
        source='Original v06+visibility waist contour widths:90–92pixels aroundZ1.12–1.14 at frozenMPP.001845870535714286; uncertain±3–5pixels/pose',
        source_limit='Upper transition cannot exactly fit source while chest fixed; radius minimum target≈.086m. No depth or vertical proportion change.',
        limits='Scope/strain only. Actual source/neutral/toon, collision and anatomy/ART require root live review.', ART=False)
    output.mkdir()
    np.savez_compressed(output/'proposal.npz', candidate=candidate, faces=faces, editable_ids=editable,
                        transition_ids=transition, protected_head=head, protected_retained=fixed)
    (output/'forecast.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    assert sum(p.stat().st_size for p in output.iterdir()) < 10*1024**2
    print(json.dumps(dict(output=str(output), candidate_sha256=proof['candidate_sha256'],
                          changed_vertices=proof['changed_vertices'], protected_vertices=len(fixed),
                          min_radius_m=min(row['radius'] for row in after_sections), ART=False)))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--root', type=Path, default=ROOT)
    prepare(parser.parse_args().root)
