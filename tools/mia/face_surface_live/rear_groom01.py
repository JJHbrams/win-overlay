"""One source-v22 central-six PATH/ORDER groom forecast; no bpy on import.

Finite hand-chosen path guides, not random/sine phases. World +Y is posterior.
Depth is inferred. Existing root-emergence rows and two join rows stay exact.
Two short upturned tails follow by rigid translation, avoiding a pinned-tip
compression. Other tip rows stay exact. Each 32-point section follows a minimal
tangent rotation: no width/depth scaling, no new twist, texture, UV or topology.
This module currently forecasts only. No live selection/application is implied.
"""
from pathlib import Path
import hashlib
import json

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
PREFIX = 'MIA_Hair_CurvedRear03Base_'
# 9c953 is the visibility-corrected review copy; its 21 geometry/UV/material
# fingerprints are identical to the earlier 113a451a copy. No native is loaded.
CHECKPOINT_SHA = '9c953fb48bf3c55595ca69d28523197b43b924550d96b6ad91a0792f4fabedb7'
NAMES = ('DeepCenter', 'LongCenter', 'MidLeftInner', 'MidRightInner',
         'CenterTurnLeft', 'CenterTurnRight')
# (existing ring, target world X, target world Y); all original Zs are held.
# The under-layer loses matching left/right pulses; the middle layer crosses it.
# Upper left short overlays upper right; middle left overlays the long centre.
GUIDES = {
    'DeepCenter': [(48, -.004, .124), (62, -.002, .1215), (77, -.007, .1138), (88, -.016, .110)],
    'LongCenter': [(34, .015, .1473), (48, .004, .143), (62, -.006, .137), (77, .002, .1384)],
    'MidLeftInner': [(25, .026, .148), (36, .025, .1555), (47, .012, .159), (58, .041, .158)],
    # The middle-right layer passes behind the carried short curl. Original
    # coplanar Y0.155 caused actual SAT witnesses; this inferred depth is0.142.
    'MidRightInner': [(25, -.025, .1515), (36, -.040, .142), (47, -.013, .1575), (58, -.034, .155)],
    # Carry the left curl before its tight turn; do not pull a fixed tip back
    # through that turn. The inner upper diagonal still overlaps the right.
    'CenterTurnLeft': [(25, .008, .1682), (36, .005, .168), (47, -.007, .161), (53, -.0145, .1575)],
    'CenterTurnRight': [(31, -.009, .154), (42, -.004, .1505), (55, .0164, .148)],
}
RIGID_TAIL = {'CenterTurnLeft': 53, 'CenterTurnRight': 55}


def sha(array):
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def file_sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(4*1024*1024): result.update(block)
    return result.hexdigest()


def cached(root):
    """Reconstruct actual retained rings, never choose an assumed new six."""
    root = Path(root)
    checkpoint = json.loads((root/'.mia-cache/production-resume-20261104/checkpoint.json').read_text())
    assert checkpoint['sha256'] == CHECKPOINT_SHA
    folder = root/'.mia-cache/face-live/live/rear-root01'
    applied = json.loads((folder/'apply.json').read_text())
    assert file_sha(folder/'delta.npz') == applied['delta_sha256']
    actual_path = root/'.mia-cache/face-live/curved-rear03/actual-emergence/geometry.npz'
    assert file_sha(actual_path) == applied['actual_payload_sha256']
    result = {}
    with np.load(actual_path, allow_pickle=False) as actual, np.load(folder/'delta.npz', allow_pickle=False) as delta:
        for short in NAMES:
            name = PREFIX+short
            q = actual[name+'_world'].copy(); ids = delta[name+'_ids']
            assert np.array_equal(q[ids], delta[name+'_before'])
            q[ids] = delta[name+'_after']
            assert sha(q) == checkpoint['objects'][name]['fingerprint']['coordinates']
            assert (len(q)-2) % 32 == 0
            result[short] = dict(co=q, triangles=actual[name+'_triangles'].copy(),
                                 UV=actual[name+'_UV'].copy(),
                                 hold_through=applied['targets'][name]['support_last_changed_ring']+2,
                                 fingerprint=checkpoint['objects'][name]['fingerprint'])
    return result


def _hermite(x, y, query):
    slopes = np.zeros_like(y)
    slopes[1:-1] = (y[2:]-y[:-2])/(x[2:]-x[:-2])[:, None]
    i = np.clip(np.searchsorted(x, query, side='right')-1, 0, len(x)-2)
    dx = x[i+1]-x[i]; u = (query-x[i])/dx
    return ((2*u**3-3*u**2+1)[:, None]*y[i]
            +(u**3-2*u**2+u)[:, None]*dx[:, None]*slopes[i]
            +(-2*u**3+3*u**2)[:, None]*y[i+1]
            +(u**3-u**2)[:, None]*dx[:, None]*slopes[i+1])


def _tangent_rotation(old, new):
    a = np.gradient(old, axis=0); b = np.gradient(new, axis=0)
    a /= np.linalg.norm(a, axis=1)[:, None]; b /= np.linalg.norm(b, axis=1)[:, None]
    v = np.cross(a, b); dot = (a*b).sum(1)
    assert dot.min() > -.99, 'Ambiguous path-frame reversal'
    skew = np.zeros((len(v), 3, 3))
    skew[:, 0, 1], skew[:, 0, 2] = -v[:, 2], v[:, 1]
    skew[:, 1, 0], skew[:, 1, 2] = v[:, 2], -v[:, 0]
    skew[:, 2, 0], skew[:, 2, 1] = -v[:, 1], v[:, 0]
    rotation = np.eye(3)[None]+skew+np.einsum('nij,njk->nik', skew, skew)/(1+dot)[:, None, None]
    assert np.max(abs(np.linalg.det(rotation)-1)) < 1e-9
    return rotation


def candidate(short, row):
    q, faces = row['co'], row['triangles']
    rings = q[:-2].reshape(-1, 32, 3).astype(float); center = rings.mean(1)
    n = len(rings); start = row['hold_through']; end = RIGID_TAIL.get(short, n-3)
    # Longitudinal parameter comes from the existing body faces' LockParamUV.
    body_faces = faces[:(n-1)*64]
    body_v = row['UV'].reshape(-1, 3, 2)[:len(body_faces), :, 1]
    parameter = np.asarray([np.median(body_v[(body_faces//32) == i]) for i in range(n)])
    assert np.all(np.diff(parameter) > 0)
    guides = GUIDES[short]
    index = np.asarray([start]+[g[0] for g in guides]+([] if short in RIGID_TAIL else [end]))
    delta = np.asarray([[0., 0.]]+[[x-center[i, 0], y-center[i, 1]] for i,x,y in guides]
                       +([] if short in RIGID_TAIL else [[0., 0.]]))
    shift = _hermite(parameter[index], delta, np.clip(parameter, parameter[start], parameter[end]))
    shift[:start+1] = 0
    shift[end:] = delta[-1] if short in RIGID_TAIL else 0
    target = center.copy(); target[:, :2] += shift
    rotation = _tangent_rotation(center, target)
    rotation[:start+1] = np.eye(3); rotation[end:] = np.eye(3)
    offsets = rings-center[:, None, :]
    moved = target[:, None, :]+np.einsum('nij,nkj->nki', rotation, offsets)
    out = q.copy(); out[:-2] = moved.reshape(-1, 3).astype(np.float32)
    out[:(start+1)*32] = q[:(start+1)*32]
    if short in RIGID_TAIL:
        out[-1, :2] = (q[-1, :2].astype(float)+shift[-1]).astype(np.float32)
    else: out[end*32:] = q[end*32:]
    assert np.array_equal(out[:(start+1)*32], q[:(start+1)*32])
    if short not in RIGID_TAIL: assert np.array_equal(out[end*32:], q[end*32:])
    # Shape comparison removes rigid rotation, not a width normalization.
    actual_offsets = out[:-2].reshape(-1, 32, 3).astype(float)-target[:, None, :]
    returned = np.einsum('nji,nkj->nki', rotation, actual_offsets)
    t0 = q[faces].astype(float); t1 = out[faces].astype(float)
    n0 = np.cross(t0[:, 1]-t0[:, 0], t0[:, 2]-t0[:, 0])
    n1 = np.cross(t1[:, 1]-t1[:, 0], t1[:, 2]-t1[:, 0])
    a0, a1 = np.linalg.norm(n0, axis=1), np.linalg.norm(n1, axis=1)
    dot = (n0*n1).sum(1)/(a0*a1)
    volume = lambda t: float(np.einsum('ij,ij->i', t[:, 0], np.cross(t[:, 1], t[:, 2])).sum()/6)
    proof = dict(actor=PREFIX+short, hold_through_ring=start,
                 hold_tip_from_ring=None if short in RIGID_TAIL else end,
                 rigid_tail_from_ring=end if short in RIGID_TAIL else None,
                 tip_translation_mm=((out[-1]-q[-1])*1000).tolist(),
                 guide_ring_XY=guides, guide_UV_v=parameter[index].tolist(),
                 max_move_mm=float(np.linalg.norm(out-q, axis=1).max()*1000),
                 max_depth_move_mm=float(np.max(abs(out[:, 1]-q[:, 1]))*1000),
                 max_section_shape_error_um=float(np.max(abs(returned-offsets))*1e6),
                 minimum_area_ratio=float((a1/a0).min()), reversed_relative_to_baseline=int((dot <= 0).sum()),
                 minimum_actual_area2=float(a1.min()), volume_ratio=volume(t1)/volume(t0),
                 max_face_rotation_deg=float(np.degrees(np.arccos(np.clip(dot.min(), -1, 1)))))
    return out, proof, rotation


def forecast(root=ROOT):
    rows = cached(root); proofs = []
    for name in NAMES:
        _, proof, _ = candidate(name, rows[name]); proofs.append(proof)
    return dict(scope='One finite central-six path/order forecast only; no live change',
                actors=proofs, inferred_depth=True, native_saved=False, ART=False,
                contacts='Not yet actual BVH/matched-render validated')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args(); print(json.dumps(forecast(args.root), indent=2))
