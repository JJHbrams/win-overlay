"""One ray-localized posterior shoulder transition edit in live Blender."""
from pathlib import Path
import hashlib
import json
import sys
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'tools/mia/review_h'))
import assemble
import live_relax

ob = bpy.data.objects['MIA_Review12_H_LiveRepair']; ns = bpy.app.driver_namespace
if ob.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
v = np.array([p.co[:] for p in ob.data.vertices], np.float32)
d = dict(np.load(ROOT/'.mia-cache/body-h/shape/assembly/live-D/geometry.npz'))
f = d['triangles']; phase = globals().get('MIA_EDIT_PHASE', 'select')
smooth = lambda t: (t := np.clip(t, 0., 1.))**3*(10-15*t+6*t*t)
if phase == 'select':
    assert np.array_equal(v, d['world'])
    normals = assemble._normals(v, f)
    u, w = (abs(v[:, 0])-.160)/.020, (v[:, 2]-1.3375)/.025
    r = np.sqrt(u*u+w*w)
    c = [.041435307493, -.008618768402, -.007809874147, -.004621225907, -.007113765077, -.007049277220]
    target = c[0]+c[1]*u+c[2]*w+c[3]*u*u+c[4]*u*w+c[5]*w*w
    # Strength is the analytic XZ footprint only. Weighting by the old vertex
    # normal amplified its irregularities into a new displacement ripple.
    weight = smooth((1.5-r)/.5)
    guide = np.zeros(len(v), bool); guide[np.unique(f[d['source_part'] == 2])] = True
    ownership = guide & (r < 2.1) & (v[:, 1] > .005)
    for ids in ns['MIA_Live_H_Rows'].values(): ownership[np.asarray(ids).ravel()] = False
    tree = BVHTree.FromPolygons([Vector(p) for p in v], f.tolist(), all_triangles=True)
    first_sheet = np.zeros(len(v), bool)
    for i in np.flatnonzero(ownership):
        hit, _, _, _ = tree.ray_cast(Vector((float(v[i, 0]), .5, float(v[i, 2]))), Vector((0., -1., 0.)), 1.)
        first_sheet[i] = hit is not None and abs(hit.y-float(v[i, 1])) < .00025
    # A positive-Y normal alone also selected occluded folds. Only the actual
    # posterior first-hit sheet belongs to this local height chart.
    branch_fade, _ = live_relax.mask(v, f, first_sheet)
    weight *= branch_fade
    q = v.copy(); q[:, 1] += weight*np.clip(target-v[:, 1], -.006, .006)
    assert np.array_equal(q[:, [0, 2]], v[:, [0, 2]])
    assert np.array_equal(q[weight == 0], v[weight == 0])
    a = np.cross(v[f[:, 1]]-v[f[:, 0]], v[f[:, 2]]-v[f[:, 0]])
    b = np.cross(q[f[:, 1]]-q[f[:, 0]], q[f[:, 2]]-q[f[:, 0]])
    active = np.any(weight[f] > 0, axis=1)
    cosine = np.sum(a*b, axis=1)/np.maximum(np.linalg.norm(a, axis=1)*np.linalg.norm(b, axis=1), 1e-30)
    worst = int(np.flatnonzero(active)[np.argmin(cosine[active])])
    diagnostic = dict(selected=int((weight > 0).sum()), posterior_first_hit_vertices=int(first_sheet.sum()),
        minimum_old_new_normal_cosine=float(cosine[active].min()),
        XZ_projected_double_area_exact=bool(np.array_equal(a[:, 1], b[:, 1])),
        worst_face=worst, original_triangle=v[f[worst]].tolist(), proposed_triangle=q[f[worst]].tolist(),
        original_area_vector=a[worst].tolist(), proposed_area_vector=b[worst].tolist(),
        worst_weights=weight[f[worst]].tolist(),
        maximum_move_m=float(np.linalg.norm(q-v, axis=1).max()), model_mutated=False)
    (ROOT/'.mia-cache/body-h/live/posterior-selection-precheck.json').write_text(json.dumps(diagnostic, indent=2)+'\n', encoding='utf8')
    assert cosine[active].min() > 0, 'Reject overturn before applying the edit'
    ns['MIA_Live_Posterior_Before'] = v.copy(); ns['MIA_Live_Posterior_After'] = q
    ns['MIA_Live_Posterior_Report'] = dict(operation='One native-ray-localized posterior leaf/groove XZ-to-Y correction',
        source='Surrounding posterior annulus1<r<1.5,620points, robustquadric cond9.75/MAD1.066mm',
        selected_vertices=int((weight > 0).sum()), maximum_displacement_m=float(np.linalg.norm(q-v, axis=1).max()),
        posterior_first_hit_vertices=int(first_sheet.sum()), branch_feather='12mm geodesic C2 fade inside actual first-hit sheet',
        outside_coordinates_exact=int((weight == 0).sum()), all_X_Z_exact=True,
        changed_face_max_normal_turn_degrees=float(np.degrees(np.arccos(np.clip(cosine[active], -1, 1))).max()),
        landmarks=[dict(vertex_id=i, before=v[i].tolist(), after=q[i].tolist(), weight=float(weight[i])) for i in [99152, 99155, 99064, 99046]],
        before_sha256=hashlib.sha256(v.tobytes()).hexdigest(), after_sha256=hashlib.sha256(q.tobytes()).hexdigest(),
        limitation='Posterior leaf only; separate upward-facing trough remains. Not anatomical/source/art approval.', native_saved=False, adopted=False)
    for poly in ob.data.polygons: poly.select = False
    for e in ob.data.edges: e.select = False
    for vert in ob.data.vertices: vert.select = bool(weight[vert.index] > 0)
    bpy.context.tool_settings.mesh_select_mode = (True, False, False)
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D': area.spaces.active.overlay.show_overlays = True
    bpy.ops.object.mode_set(mode='EDIT')
    print(json.dumps(ns['MIA_Live_Posterior_Report']))
else:
    assert phase == 'apply' and np.array_equal(v, ns['MIA_Live_Posterior_Before'])
    q = ns['MIA_Live_Posterior_After']
    ob.data.vertices.foreach_set('co', q.ravel()); ob.data.update(); bpy.context.view_layer.update()
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D': area.spaces.active.overlay.show_overlays = False
    report = ns['MIA_Live_Posterior_Report']
    path = ROOT/'.mia-cache/body-h/live/posterior-leaf-operation.json'
    assert not path.exists()
    path.write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    print(json.dumps(report))
