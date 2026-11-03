"""Prepare one bounded top-neck delta from an actual donor section, no bpy."""
from pathlib import Path
import hashlib
import json
import numpy as np
import assemble

ROOT = Path(__file__).resolve().parents[3]


def prepare():
    base = ROOT/'.mia-cache/body-h/shape/assembly/live-D'
    d = dict(np.load(base/'geometry.npz'))
    v, f = d['world'], d['triangles']
    rows = np.load(ROOT/'.mia-cache/body-h/shape/assembly/collar-rows.npz')['neck']
    ops = assemble.load_module('cut_neighbor_ops', ROOT/'asset/mia/blender/mia-fit-v003/body/surface-review12/mesh_ops.py')
    mesh, frames = assemble._old_collar_loops(ops.Mesh, d, [209484, 221750], np.array([0., 0., 1.]))
    cut = frames[1]
    angles = np.arange(rows.shape[1])*2*np.pi/rows.shape[1]
    endpoint, _ = mesh.resample(cut, angles)
    donor = dict(np.load(ROOT/'asset/mia/blender/mia-fit-v003/body/surface-review12/donor.npz'))
    sections = ops.SectionSource(donor['world'], donor['triangles'])
    step = min(sections.row_step(cut), .002)
    neighbor = sections.sample(cut, step, angles)
    zcut = float(endpoint[:, 2].mean())
    h = zcut-float(v[rows[-1], 2].mean())
    target_last = endpoint[:, :2]-h*(neighbor[:, :2]-endpoint[:, :2])/step
    displacement = target_last-v[rows[-1], :2]
    anchor_z = float(v[rows[-4], 2].mean())
    L = zcut-anchor_z
    tlast = 1-h/L
    ids, before, after = [], [], []
    for row in rows[-3:]:
        z = float(v[row, 2].mean())
        t = (z-anchor_z)/L
        # Zero value and slope at the held lower row, zero at the held cut;
        # its sampled last row matches the actual one-step donor secant.
        weight = t*t*(1-t)/(tlast*tlast*(1-tlast))
        q = v[row].copy(); q[:, :2] += weight*displacement
        ids.extend(row.tolist()); before.extend(v[row]); after.extend(q)
    ids = np.array(ids, np.int32); before = np.array(before, np.float32); after = np.array(after, np.float32)
    movement = np.linalg.norm(after-before, axis=1)
    assert movement.max() < .004, ('Reject oversized top-neck correction', movement.max())
    out = ROOT/'.mia-cache/body-h/live/cut-tangent-proposal.npz'
    assert not out.exists()
    np.savez_compressed(out, vertex_ids=ids, before=before, after=after)
    report = dict(scope='UNAPPLIED three top-neck rings, actual finite donor secant',
        world_sha256=hashlib.sha256(v.tobytes()).hexdigest(), vertices=len(ids),
        maximum_proposed_displacement_m=float(movement.max()), donor_sample_step_m=step,
        held_lower_anchor_z=anchor_z, held_head_cut_z=zcut,
        protections='All original head, cut loop, lower neck, cap, breast, axilla, E joins; all Z exact',
        native_saved=False, live_applied=False, art_approved=False,
        delta_path=str(out), delta_sha256=hashlib.sha256(out.read_bytes()).hexdigest())
    out.with_suffix('.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    print(json.dumps(report))


if __name__ == '__main__': prepare()
