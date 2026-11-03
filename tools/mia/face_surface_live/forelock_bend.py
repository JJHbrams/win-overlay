"""One live right-diagonal forelock bend, preserving thickness and root attachment.

Unlike rejected C, this does not narrow terminal bundles into needles. A small
smooth lateral bend opens a real medial brow slit. Live images decide retention.
"""
from pathlib import Path
import hashlib
import json
import bpy
import numpy as np

ROOT = Path('D:/MiaWorkCache/mia-reference-work/win-overlay')
OUT = ROOT/'.mia-cache/face-live/live'
ns = bpy.app.driver_namespace
review = ns['MIA_HairReviewState']
body = bpy.data.objects['MIA_Review12_H_LiveRepair']
assert hashlib.sha256(np.array([v.co[:] for v in body.data.vertices], np.float32).tobytes()).hexdigest() == review['body_sha256']
ob = bpy.data.objects['MIA_V17_PIXAL_DetailedHair']
if bpy.context.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
raw = np.array([v.co[:] for v in ob.data.vertices], np.float32)
assert hashlib.sha256(raw.tobytes()).hexdigest() == '16d192576cd8ecc1905f4eba96b4686c038e8c94a56e6eec7dee552e6eee0b2c'
faces = np.array([p.vertices[:] for p in ob.data.polygons], np.int32)
assert hashlib.sha256(faces.tobytes()).hexdigest() == 'ef2c4f25af6eb18e77fb891974054ec37f39bae30d6358a5a2d3cf4ac84804a9'
phase = globals().get('MIA_EDIT_PHASE', 'select')
if phase == 'select':
    assert not ob.data.shape_keys, 'This first operation expects the actual unkeyed R3b Main'
    roots = np.load(ROOT/'.mia-cache/face-live/source-audit/components.npz')['face_root']
    islands = [60079,56676,59915,59480,60595,60217,60696,61608,60299]
    owned_faces = np.flatnonzero(np.isin(roots, islands))
    ids = np.unique(faces[owned_faces])
    q = raw[ids].astype(float)
    u = (q[:,2].max()-q[:,2])/np.ptp(q[:,2])
    t = np.clip((u-.20)/.80, 0, 1)
    gain = t*t*(3-2*t)
    delta = np.zeros_like(q)
    delta[:,0] = .006*gain
    # A pure X(Z) bend keeps the entire cross section, including opaque backing,
    # coherent. Existing tip width/depth and Z are deliberately not flattened.
    lock = np.load(ROOT/'.mia-cache/face-live/source-audit/analysis.npz')['main_weight_Roots_Locked'][ids] > .5
    delta[lock] = 0
    assert np.max(np.linalg.norm(delta,axis=1)) <= .006000001
    before = raw[faces[owned_faces]].astype(float)
    whole_delta = np.zeros_like(raw); whole_delta[ids] = delta.astype(np.float32)
    after = (raw+whole_delta)[faces[owned_faces]].astype(float)
    n0 = np.cross(before[:,1]-before[:,0], before[:,2]-before[:,0])
    n1 = np.cross(after[:,1]-after[:,0], after[:,2]-after[:,0])
    assert (np.einsum('ij,ij->i',n0,n1) > 0).all(), 'Reject triangle reversal'
    ns['MIA_HairForelockBend01'] = dict(ids=ids, delta=whole_delta, before=raw,
                                      owned_faces=owned_faces, created_basis=False,
                                      vertex_selection=np.array([v.select for v in ob.data.vertices]))
    for o in bpy.context.selected_objects: o.select_set(False)
    ob.hide_set(False); ob.select_set(True); bpy.context.view_layer.objects.active = ob
    for p in ob.data.polygons: p.select = False
    for e in ob.data.edges: e.select = False
    for v in ob.data.vertices: v.select = False
    for i in ids: ob.data.vertices[int(i)].select = True
    bpy.context.tool_settings.mesh_select_mode = (True, False, False)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D': area.spaces.active.overlay.show_overlays = True
    bpy.ops.object.mode_set(mode='EDIT')
    report = dict(phase=phase, scope='Right diagonal forelock complete nine-island skin/backing family only',
                  selected_vertices=len(ids), selected_faces=len(owned_faces), root_points_held=int(lock.sum()),
                  max_move_mm=float(np.linalg.norm(delta,axis=1).max()*1000),
                  minimum_oriented_normal_dot=float(np.einsum('ij,ij->i',n0,n1).min()),
                  no_width_depth_or_vertical_taper=True, body_preserved=True, ART=False)
else:
    edit = ns['MIA_HairForelockBend01']
    assert not ob.data.shape_keys, 'Do not replay a completed bend'
    ob.shape_key_add(name='Basis'); edit['created_basis'] = True
    key = ob.shape_key_add(name='Mia.Live.ForelockBend01')
    key.data.foreach_set('co', (edit['before']+edit['delta']).ravel())
    key.value = 1.
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D': area.spaces.active.overlay.show_overlays = False
    bpy.context.view_layer.update()
    report = dict(phase=phase, key=key.name, current_value=key.value,
                  actual_changed_points=int(np.count_nonzero(np.linalg.norm(edit['delta'],axis=1)>0)),
                  protected_raw_basis_exact=bool(np.array_equal(raw,edit['before'])),
                  max_move_mm=float(np.linalg.norm(edit['delta'],axis=1).max()*1000),
                  body_preserved=True, native_saved=False, ART=False)
(OUT/('forelock-bend01-'+phase+'.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(report))
