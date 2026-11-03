"""One live, reversible neck-only operation; no source/model/native save.

Replace short-section quadratic extrapolation and forced posterior station
centres by monotone radial Hermite interpolation of the actual end sections.
"""
from pathlib import Path
import hashlib
import json
import sys
import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'tools/mia/review_h'))
import assemble


def edge_angles(world, faces, lo, hi):
    q = world[faces].astype(float)
    n = np.cross(q[:, 1]-q[:, 0], q[:, 2]-q[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1)[:, None], 1e-20)
    e = np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    owners = np.tile(np.arange(len(faces)), 3)
    order = np.lexsort(np.sort(e, axis=1).T[::-1]); e = np.sort(e, axis=1)[order]; owners = owners[order]
    same = np.all(e[1:] == e[:-1], axis=1)
    ids = np.flatnonzero(same)
    pairs = np.column_stack([owners[ids], owners[ids+1]])
    use = ((pairs >= lo)&(pairs < hi)).all(1)
    pairs = pairs[use]
    angles = np.degrees(np.arccos(np.clip((n[pairs[:, 0]]*n[pairs[:, 1]]).sum(1), -1, 1)))
    return dict(median=float(np.median(angles)), p95=float(np.percentile(angles, 95)), maximum=float(angles.max()), over45=int((angles>45).sum()))


def main():
    body = bpy.data.objects['MIA_Review12_H_LiveRepair']
    ns = bpy.app.driver_namespace
    before = np.array([v.co[:] for v in body.data.vertices], np.float32)
    assert np.array_equal(before, ns['MIA_Live_H_Baseline']), 'One operation from the reviewed baseline only'
    d = dict(np.load(Path(ns['MIA_Live_H_Payload'])/'geometry.npz'))
    rows = ns['MIA_Live_H_Rows']['neck']
    lo, hi = 209484, 221750
    ops = assemble.load_module('live_neck_meshops', ROOT/'asset/mia/blender/mia-fit-v003/body/surface-review12/mesh_ops.py')
    mesh, frames = assemble._old_collar_loops(ops.Mesh, d, [lo, hi], np.array([0., 0., 1.]))
    a, b = frames
    count = rows.shape[1]; angles = np.arange(count)*2*np.pi/count
    p0, _ = mesh.resample(a, angles); p1, _ = mesh.resample(b, angles)
    guide = dict(np.load(ROOT/'.mia-cache/body-h/shape/H-guide.npz'))
    donor = dict(np.load(ROOT/'asset/mia/blender/mia-fit-v003/body/surface-review12/donor.npz'))
    sg, sd = ops.SectionSource(guide['world'], guide['triangles']), ops.SectionSource(donor['world'], donor['triangles'])
    hg = min(sg.row_step(a), .002); hd = min(sd.row_step(b), .002)
    g1, d1 = sg.sample(a, -hg, angles), sd.sample(b, hd, angles)
    c0, c1, cg, cd = [p[:, :2].mean(0) for p in [p0, p1, g1, d1]]
    v0, v1 = p0[:, :2]-c0, p1[:, :2]-c1
    r0, r1 = np.linalg.norm(v0, axis=1), np.linalg.norm(v1, axis=1)
    rg, rd = np.linalg.norm(g1[:, :2]-cg, axis=1), np.linalg.norm(d1[:, :2]-cd, axis=1)
    H = float(b[2][2]-a[2][2]); m = (np.log(r1)-np.log(r0))/H
    assert np.all(m < 0), 'This operation requires the observed decreasing radii'
    slopes = [(np.log(r0)-np.log(rg))/hg, (np.log(rd)-np.log(r1))/hd]
    slopes = [assemble._angular_delta(p, slope[:, None], .006).ravel() for p, slope in zip([p0, p1], slopes)]
    alpha, beta = np.maximum(slopes[0]/m, 0), np.maximum(slopes[1]/m, 0)
    scale = np.minimum(1., 3./np.maximum(np.sqrt(alpha*alpha+beta*beta), 1e-20))
    s0, s1 = alpha*scale*m, beta*scale*m
    dc0, dc1 = (c0-cg)/hg, (cd-c1)/hd
    after = before.copy()
    for k, ids in enumerate(rows, start=1):
        t = k/(len(rows)+1)
        h00, h10, h01, h11 = 2*t**3-3*t*t+1, t**3-2*t*t+t, -2*t**3+3*t*t, t**3-t*t
        center = h00*c0+h10*H*dc0+h01*c1+h11*H*dc1
        radius = np.exp(h00*np.log(r0)+h10*H*s0+h01*np.log(r1)+h11*H*s1)
        direction = (1-t)*v0/r0[:, None]+t*v1/r1[:, None]
        direction /= np.linalg.norm(direction, axis=1)[:, None]
        after[ids, :2] = center+radius[:, None]*direction
    selected = np.unique(rows)
    protected = np.ones(len(before), bool); protected[selected] = False
    assert np.array_equal(before[protected], after[protected])
    assert np.array_equal(before[:, 2], after[:, 2])
    report = dict(operation='Live neck interior monotone radial Hermite; no forced posterior guide centre',
                  source='Actual one-step neighbor sections, physically smoothed6mm radial derivatives, monotone limiter',
                  selected_vertices=len(selected), outside_vertices_exact=int(protected.sum()),
                  endpoints_head_face_arms_waist_caps_held=True, all_Z_exact=True,
                  maximum_displacement_m=float(np.linalg.norm(after-before, axis=1).max()),
                  before_world_sha256=hashlib.sha256(before.tobytes()).hexdigest(),
                  after_world_sha256=hashlib.sha256(after.tobytes()).hexdigest(),
                  neck_dihedral_before=edge_angles(before, d['triangles'], lo, hi),
                  neck_dihedral_after=edge_angles(after, d['triangles'], lo, hi),
                  endpoint_centers=[c0.tolist(), c1.tolist()], actual_center_secants=[dc0.tolist(), dc1.tolist()],
                  source_uncertainty='Does not claim exact source neck stations; prior drawing midpoint constraints caused an anatomically implausible S bend. Actual source/neighbor-angle review required.',
                  native_saved=False, geometry_exported=False, adopted=False)
    ns['MIA_Live_Neck_Operation_Before'] = before.copy()
    body.data.vertices.foreach_set('co', after.ravel()); body.data.update(); bpy.context.view_layer.update()
    actual = np.array([v.co[:] for v in body.data.vertices], np.float32)
    assert np.array_equal(actual, after)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D': area.spaces.active.overlay.show_overlays = False
    (ROOT/'.mia-cache/body-h/live/neck-operation.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    print(json.dumps(report))


main()
