"""Apply/select the prepared top-neck delta in actual live Blender only."""
from pathlib import Path
import hashlib
import json
import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
ob = bpy.data.objects['MIA_Review12_H_LiveRepair']
if ob.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
v = np.array([p.co[:] for p in ob.data.vertices], np.float32)
proposal = dict(np.load(ROOT/'.mia-cache/body-h/live/cut-tangent-proposal.npz'))
ids = proposal['vertex_ids']
phase = globals().get('MIA_EDIT_PHASE', 'select')
ns = bpy.app.driver_namespace
if phase == 'select':
    assert np.array_equal(v[ids], proposal['before'])
    ns['MIA_Live_CutTangent_Before'] = v.copy()
    for p in ob.data.polygons: p.select = False
    for e in ob.data.edges: e.select = False
    mask = np.zeros(len(v), bool); mask[ids] = True
    for p in ob.data.vertices: p.select = bool(mask[p.index])
    bpy.context.tool_settings.mesh_select_mode = (True, False, False)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D': area.spaces.active.overlay.show_overlays = True
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    print(json.dumps(dict(phase='TOP NECK SELECT ONLY', selected=len(ids), geometry_changed=False)))
else:
    assert phase == 'apply' and np.array_equal(v, ns['MIA_Live_CutTangent_Before'])
    q = v.copy(); q[ids] = proposal['after']
    outside = np.ones(len(v), bool); outside[ids] = False
    assert np.array_equal(q[outside], v[outside]) and np.array_equal(q[:, 2], v[:, 2])
    ob.data.vertices.foreach_set('co', q.ravel()); ob.data.update(); bpy.context.view_layer.update()
    ns['MIA_Live_CutTangent_After'] = q.copy()
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D': area.spaces.active.overlay.show_overlays = False
    report = dict(operation='Three upper-neck rings match actual one-step donor secant with held lower anchor/cut',
        selected_vertices=len(ids), maximum_displacement_m=float(np.linalg.norm(q-v, axis=1).max()),
        outside_coordinates_exact=int(outside.sum()), all_Z_exact=True,
        before_sha256=hashlib.sha256(v.tobytes()).hexdigest(), after_sha256=hashlib.sha256(q.tobytes()).hexdigest(),
        native_saved=False, adopted=False)
    path = ROOT/'.mia-cache/body-h/live/cut-tangent-operation.json'
    assert not path.exists()
    path.write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    print(json.dumps(report))
