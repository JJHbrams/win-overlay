"""One normal-directed cap lobe/trough correction, reviewed in live Blender."""
from pathlib import Path
import hashlib
import json
import sys
import bpy
import numpy as np

ROOT = Path('D:/MiaWorkCache/mia-reference-work/win-overlay')
sys.path.insert(0, str(ROOT/'tools/mia/review_h'))
import assemble
import live_relax

ob = bpy.data.objects['MIA_Review12_H_LiveRepair']
if ob.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
v = np.array([p.co[:] for p in ob.data.vertices], np.float32)
d = dict(np.load(ROOT/'.mia-cache/body-h/shape/assembly/live-D/geometry.npz'))
f = d['triangles']; ns = bpy.app.driver_namespace
phase = globals().get('MIA_EDIT_PHASE', 'select')
chart = globals().get('MIA_CAP_DIRECTION') == 'chart'
prefix = 'MIA_Live_CapChart' if chart else 'MIA_Live_CapForm'
if phase == 'select':
    normal = assemble._normals(v, f)
    p = v.astype(float).copy(); n = normal.copy()
    side = np.where(p[:, 0] < 0, -1., 1.)
    p[:, 0] *= side; n[:, 0] *= side
    C = np.array([.16455474, .00537421, 1.34930373])
    N = np.array([.72390198, .06313082, .68700832])
    U = np.array([-.04579187, .99800526, -.04345808])
    V = np.array([-.688381457, 0., .725348861])
    rx, ry = .0390447961772342, .04690998124481638
    c = np.array([.016864973605466866, .00040527291766227075, .0018421475735705805,
                  -.024593608561287627, -.002611279382076394, -.015622787827763003])
    u, w, h = (p-C)@U/rx, (p-C)@V/ry, (p-C)@N
    radius = np.sqrt(u*u+w*w)
    target = c[0]+c[1]*u+c[2]*w+c[3]*u*u+c[4]*u*w+c[5]*w*w
    residual = h-target
    du, dw, dh = n@U/rx, n@V/ry, n@N
    derivative = dh-(c[1]*du+c[2]*dw+2*c[3]*u*du+c[4]*(w*du+u*dw)+2*c[5]*w*dw)
    eligible = (p[:, 0] > .11)&(p[:, 0] < .205)&(p[:, 2] > 1.33)&(p[:, 2] < 1.405)&(radius < 1.35)&(dh > .4)&(derivative > .15)
    eligible[(p[:, 0] >= .18)&(p[:, 2] <= 1.35)] = False
    eligible[p[:, 0] >= .20] = False
    eligible[(p[:, 1] < -.035)&(p[:, 2] < 1.35)&(p[:, 0] < .16)] = False
    eligible[(p[:, 0] < .16)&(p[:, 2] < 1.335)] = False
    eligible[np.unique(f[d['source_part'] == 1])] = False
    for ids in ns['MIA_Live_H_Rows'].values(): eligible[np.asarray(ids).ravel()] = False
    weight, edges = live_relax.mask(v, f, eligible)
    step = np.zeros(len(v))
    if chart:
        # A common chart direction preserves both tangent coordinates and
        # their triangle order. Varying vertex-normal rays folded thin faces.
        direction = np.tile(N, (len(v), 1)); direction[:, 0] *= side
        step[eligible] = -np.clip(residual[eligible], -.0048, .0048)
    else:
        direction = normal
        step[eligible] = np.clip(-np.clip(residual[eligible], -.0048, .0048)/derivative[eligible], -.006, .006)
    q = (v.astype(float)+direction*(step*weight)[:, None]).astype(np.float32)
    assert np.array_equal(q[weight == 0], v[weight == 0])
    assert np.linalg.norm(q-v, axis=1).max() <= .006001
    if chart:
        displacement = q.astype(float)-v
        displacement[:, 0] *= side
        assert abs(displacement@U).max() < 2e-7 and abs(displacement@V).max() < 2e-7
        tri_before = np.cross(v[f[:, 1]]-v[f[:, 0]], v[f[:, 2]]-v[f[:, 0]])
        tri_after = np.cross(q[f[:, 1]]-q[f[:, 0]], q[f[:, 2]]-q[f[:, 0]])
        changed_faces = np.any(weight[f] > 0, axis=1)
        denom = np.linalg.norm(tri_before, axis=1)*np.linalg.norm(tri_after, axis=1)
        cosine = np.sum(tri_before*tri_after, axis=1)/np.maximum(denom, 1e-30)
        assert cosine[changed_faces].min() > 0, 'Reject triangle overturn before live mutation'
    ns[prefix+'_Before'] = v.copy(); ns[prefix+'_After'] = q
    ns[prefix+'_Weight'] = weight
    ns[prefix+'_Report'] = dict(operation='One cap broad-quadric height correction along fixed chart N' if chart else 'One cap normal-directed broad-quadric residual correction, no repeated Relax',
        fit='D right-cap outer annulus .65<r<1.15, outwardN>.4, robust quadric condition8.12; mirrored chart left',
        limitation='Broad cap construction reference, not recovered source skin or anatomical ground truth',
        selected_vertices=int((weight > 0).sum()), maximum_displacement_m=float(np.linalg.norm(q-v, axis=1).max()),
        outside_coordinates_exact=int((weight == 0).sum()),
        protections='Head, allneckrows, Earm/waistjoins, medial/inferioraxillarywalls, frontroot, lateralacromionsupport held',
        before_sha256=hashlib.sha256(v.tobytes()).hexdigest(), after_sha256=hashlib.sha256(q.tobytes()).hexdigest(),
        landmarks=[dict(vertex_id=i, before=v[i].tolist(), proposed=q[i].tolist(), weight=float(weight[i])) for i in [100158, 97184, 98050, 62197, 67364, 63554, 100128]],
        native_saved=False, adopted=False)
    for poly in ob.data.polygons: poly.select = False
    for e in ob.data.edges: e.select = False
    for vert in ob.data.vertices: vert.select = bool(weight[vert.index] > 0)
    bpy.context.tool_settings.mesh_select_mode = (True, False, False)
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D': area.spaces.active.overlay.show_overlays = True
    bpy.ops.object.mode_set(mode='EDIT')
    print(json.dumps(ns[prefix+'_Report']))
else:
    assert phase == 'apply' and np.array_equal(v, ns[prefix+'_Before'])
    q = ns[prefix+'_After']
    ob.data.vertices.foreach_set('co', q.ravel()); ob.data.update(); bpy.context.view_layer.update()
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D': area.spaces.active.overlay.show_overlays = False
    report = ns[prefix+'_Report']
    path = ROOT/'.mia-cache/body-h/live'/('cap-chart-operation.json' if chart else 'cap-form-operation.json')
    assert not path.exists()
    path.write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    print(json.dumps(report))
