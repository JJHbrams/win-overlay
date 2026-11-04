"""ONE continuous C1 AP profile warp of intact D; root invokes via live MCP.

This is a bounded design deformation, not ARAP, native elastic solving, physical
anatomy, or per-ring coordinate replacement. Original Mesh remains the exact
checkpoint; only one in-RAM Mesh.copy on the same actor receives coordinates.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import bpy
import numpy as np
from numpy.polynomial import Polynomial as P

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'.mia-cache/body-h/live/ap-profile01'
KEY = 'MIA_APProfile01'
BODY = 'MIA_Review12_H_LiveRepair'
BASE = '69d4d4f0ea907da2474bc74f4b55312971d137f0911bdf9089fc02509a6bf25a'
EXPECTED = '695dbbd825ce444fd04f0e390ccd64d31265d7cb14b027a08bf2ced82b4a7215'
LOW, BACK, XCORE, XEND, OFFSET = 1.355, .005, .035, .13, .025
_spec = importlib.util.spec_from_file_location('mia_ap_profile01_diagnostics', ROOT/'tools/mia/upper_template_live/diagnostic_weights.py')
diag = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(diag)

def sha(a): return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def read(collection, prop, width=1, dtype=np.float32):
    a = np.empty((len(collection), width), dtype); collection.foreach_get(prop, a.ravel())
    return a if width != 1 else a.ravel()


def xyz(mesh): return read(mesh.vertices, 'co', 3)


def topology(mesh):
    return {key: sha(read(collection, prop, width, dtype))
            for key, collection, prop, width, dtype in [
                ('edges', mesh.edges, 'vertices', 2, np.int32),
                ('corner_vertex', mesh.loops, 'vertex_index', 1, np.int32),
                ('corner_edge', mesh.loops, 'edge_index', 1, np.int32),
                ('face_start', mesh.polygons, 'loop_start', 1, np.int32),
                ('face_size', mesh.polygons, 'loop_total', 1, np.int32),
                ('material_index', mesh.polygons, 'material_index', 1, np.int32),
                ('smooth', mesh.polygons, 'use_smooth', 1, bool)]}


def uv(mesh):
    return dict(values={u.name: read(u.data, 'uv', 2) for u in mesh.uv_layers},
                active=mesh.uv_layers.active.name if mesh.uv_layers.active else None,
                render=[u.name for u in mesh.uv_layers if u.active_render])


def flags(mesh):
    return {(name, prop): read(getattr(mesh, name), prop, dtype=bool)
            for name in ('vertices', 'edges', 'polygons') for prop in ('select', 'hide')}


def head_attributes(mesh, head):
    meta = json.loads((ROOT/'asset/mia/blender/mia-fit-v003/body/surface-review12/head-attributes.json').read_text())
    result = {}
    for rec in meta['attributes']:
        assert rec['domain'] == 'POINT'
        attr = mesh.attributes.get(rec['name']); assert attr is not None, rec['name']
        sample = attr.data[0].bl_rna.properties[rec['property']]
        dtype = np.float32 if sample.type == 'FLOAT' else (bool if sample.type == 'BOOLEAN' else np.int32)
        result[rec['name']] = sha(read(attr.data, rec['property'], rec['dimension'], dtype)[head])
    return result


def normals(mesh): return np.asarray([n.vector[:] for n in mesh.corner_normals], np.float32)


def actors(body):
    return {ob.name: dict(data=int(ob.data.as_pointer()) if ob.data else None,
                         matrix=[list(row) for row in ob.matrix_world], hidden=bool(ob.hide_get()),
                         render_hidden=bool(ob.hide_render), selected=bool(ob.select_get()),
                         materials=[int(s.material.as_pointer()) if s.material else None for s in ob.material_slots]
                         if ob.type == 'MESH' else None)
            for ob in bpy.context.scene.objects if ob != body}


def context_snapshot():
    ts = bpy.context.tool_settings
    names = ('mesh_select_mode', 'use_proportional_edit', 'use_proportional_connected',
             'use_proportional_projected', 'proportional_edit_falloff', 'proportional_size')
    settings = {k: tuple(getattr(ts, k)) if k == 'mesh_select_mode' else getattr(ts, k)
                for k in names if hasattr(ts, k)}
    views = [(a.spaces.active, a.spaces.active.shading.type, a.spaces.active.shading.color_type,
              a.spaces.active.overlay.show_overlays)
             for screen in bpy.data.screens for a in screen.areas if a.type == 'VIEW_3D']
    return dict(active=bpy.context.view_layer.objects.active,
                selected=[ob for ob in bpy.context.view_layer.objects if ob.select_get()],
                tool=settings, views=views)


def restore_context(saved):
    for space, kind, color_type, overlays in saved['views']:
        space.shading.type = kind; space.shading.color_type = color_type; space.overlay.show_overlays = overlays
    for k, value in saved['tool'].items(): setattr(bpy.context.tool_settings, k, value)
    for ob in bpy.context.view_layer.objects: ob.select_set(ob in saved['selected'])
    bpy.context.view_layer.objects.active = saved['active']


def critical(poly):
    return [float(q.real) for q in poly.roots() if abs(q.imag) < 1e-7 and 0 < q.real < 1]


def profile(world, rows):
    """Actual front-row PCHIP prior, C1 Hermite target, exact polynomial bounds."""
    front = np.array([ids[np.argmin(world[ids, 1])] for ids in rows['neck']])
    z, y = world[front, 2].astype(float), world[front, 1].astype(float)
    h = np.diff(z); secant = np.diff(y)/h; slopes = np.empty(len(z))
    assert (h > 0).all() and (secant > 0).all()
    for i in range(1, len(z)-1):
        a, b = secant[i-1], secant[i]; w1, w2 = 2*h[i]+h[i-1], h[i]+2*h[i-1]
        slopes[i] = (w1+w2)/(w1/a+w2/b)
    def endpoint(h0, h1, a, b):
        value = ((2*h0+h1)*a-h0*b)/(h0+h1)
        return 0. if value*a <= 0 else (3*a if a*b < 0 and abs(value) > 3*abs(a) else value)
    slopes[0] = endpoint(h[0], h[1], secant[0], secant[1])
    slopes[-1] = endpoint(h[-1], h[-2], secant[-1], secant[-2])
    polys = [P([y[i], h[i]*slopes[i], 3*(y[i+1]-y[i])-h[i]*(2*slopes[i]+slopes[i+1]),
                2*(y[i]-y[i+1])+h[i]*(slopes[i]+slopes[i+1])]) for i in range(len(h))]
    def F(x, derivative=False):
        x = np.asarray(x); index = np.clip(np.searchsorted(z, x, side='right')-1, 0, len(h)-1)
        out = np.empty_like(x, dtype=float)
        for k in range(len(h)):
            mask = index == k; u = (x[mask]-z[k])/h[k]
            out[mask] = polys[k].deriv()(u)/h[k] if derivative else polys[k](u)
        low = x < z[0]
        out[low] = slopes[0] if derivative else y[0]+slopes[0]*(x[low]-z[0])
        return out
    cap = float(world[rows['neck'][12:].ravel(), 2].min()); z0 = z[0]; length = cap-z0
    y0, y1 = y[0]+OFFSET, float(F(np.array([cap]))[0])
    m0, m1 = slopes[0], float(F(np.array([cap]), True)[0])
    target = P([y0, length*m0, 3*(y1-y0)-length*(2*m0+m1), 2*(y0-y1)+length*(m0+m1)])
    target_min_slope = min(float(target.deriv()(u)/length) for u in [0., 1.]+critical(target.deriv(2)))
    assert target_min_slope > 0, 'Target front profile reverses; no automatic retune'
    # The lower-roof F continuation is linear, not constant: C1 at first row.
    pieces = [(LOW, z0, P([y[0]+m0*(LOW-z0), m0*(z0-LOW)]), OFFSET*P([0, 0, 0, 10, -15, 6]))]
    for i, poly in enumerate(polys):
        a, b = max(z0, z[i]), min(cap, z[i+1])
        if b <= a: continue
        fp = poly(P([(a-z[i])/h[i], (b-a)/h[i]]))
        tp = target(P([(a-z0)/length, (b-a)/length])); pieces.append((a, b, fp, tp-fp))
    ratios, amplitudes = [], []
    for a, b, fp, dp in pieces:
        denominator = P([BACK])-fp
        assert min(denominator(u) for u in [0., 1.]+critical(denominator.deriv())) > 0
        for u in [0., 1.]+critical(dp.deriv()*denominator+dp*fp.deriv()):
            ratios.append((float(dp(u)/denominator(u)), a+(b-a)*u))
        amplitudes.extend(float(dp(u)) for u in [0., 1.]+critical(dp.deriv()))
    # Tiny polynomial roundoff at zero endpoints is reported, never clamped into
    # a different field. Exact piecewise masks set outside regions to zero.
    assert min(amplitudes) >= -1e-12 and max(amplitudes) <= OFFSET+1e-12
    jacobian_bound = 1-1.5*max(ratios)[0]
    assert jacobian_bound > 0, 'Continuous AP map can fold'
    def d(x):
        x = np.asarray(x); out = np.zeros_like(x, dtype=float)
        roof = (x > LOW)&(x < z0); u = (x[roof]-LOW)/(z0-LOW)
        out[roof] = OFFSET*(10*u**3-15*u**4+6*u**5)
        neck = (x >= z0)&(x < cap)
        out[neck] = target((x[neck]-z0)/length)-F(x[neck])
        return out
    proof = dict(front_vertex_ids=front.tolist(), first_front_z_m=float(z0), cap_m=cap,
                 F='PCHIP of actual16 neck frontmost vertices; linear first-tangent continuation below first row',
                 target='One cubic Hermite; endpoint derivatives match F; lower roof quintic rise',
                 target_min_dY_dZ=target_min_slope, displacement_min_m=min(amplitudes),
                 displacement_max_m=max(amplitudes), maximum_offset_depth_ratio=max(ratios)[0],
                 analytic_global_min_Jacobian_bound=jacobian_bound,
                 C1='d and d-prime zero at support endpoints; d-prime zero at roof/neck join; X/depth weights C1')
    return F, d, cap, proof


def forecast(world, faces, rows, source_part):
    assert sha(world) == BASE
    v = world.astype(float); F, d, cap, proof = profile(world, rows)
    s = np.clip((abs(v[:, 0])-XCORE)/(XEND-XCORE), 0, 1); wx = 1-(3*s*s-2*s*s*s)
    t = np.clip((BACK-v[:, 1])/(BACK-F(v[:, 2])), 0, 1)
    dy = wx*d(v[:, 2])*(3*t*t-2*t*t*t)
    q = v.copy(); q[:, 1] += dy; q = q.astype(np.float32)
    assert sha(q) == EXPECTED, 'Chosen field differs from the exact float32 forecast; do not retune'
    changed = np.any(q != world, axis=1); delta = q.astype(float)-v
    anchors = (v[:, 2] <= LOW)|(v[:, 2] >= cap)|(abs(v[:, 0]) >= XEND)|(v[:, 1] >= BACK)
    head = np.unique(faces[source_part == 1]); anchors[head] = True
    for key in ('waist', 'armR', 'armL'): anchors[rows[key].ravel()] = True
    assert np.array_equal(q[anchors], world[anchors]) and np.array_equal(q[:, [0, 2]], world[:, [0, 2]])
    assert (delta[:, 1] >= 0).all() and int(changed.sum()) == 5873
    profile_rows = []; envelope = []
    for i, ids in enumerate(rows['neck']):
        fi = ids[np.argmin(world[ids, 1])]; qi = ids[np.argmin(q[ids, 1])]; envelope.append(float(q[qi, 1]))
        profile_rows.append(dict(row=i, front_Z_m=float(v[fi, 2]), before_front_Y_m=float(v[fi, 1]),
                                 after_front_Y_m=float(q[qi, 1]), after_front_X_m=float(q[qi, 0]),
                                 delta_at_original_front_m=float(delta[fi, 1])))
    assert (np.diff(envelope) > 0).all(), 'Discrete anterior neck envelope reverses'
    a, b = v[faces], q.astype(float)[faces]
    n = np.cross(a[:, 1]-a[:, 0], a[:, 2]-a[:, 0]); nn = np.cross(b[:, 1]-b[:, 0], b[:, 2]-b[:, 0])
    area, area_new = np.linalg.norm(n, axis=1), np.linalg.norm(nn, axis=1)
    assert (area_new > 0).all(); n /= area[:, None]; nn /= area_new[:, None]
    active = changed[faces].any(1)
    turn = np.degrees(np.arctan2(np.linalg.norm(np.cross(n[active], nn[active]), axis=1), np.sum(n[active]*nn[active], axis=1)))
    assert (np.sum(n[active]*nn[active], axis=1) > 0).all() and turn.max() < 45
    directed = np.concatenate((faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]))
    edges, inv, count = np.unique(np.sort(directed, axis=1), axis=0, return_inverse=True, return_counts=True)
    order = np.argsort(inv, kind='stable'); owners = np.tile(np.arange(len(faces)), 3)[order]
    starts = np.r_[0, np.cumsum(count[:-1])]; ix = np.flatnonzero(count == 2)
    pairs = np.c_[owners[starts[ix]], owners[starts[ix]+1]]; pairs = pairs[active[pairs].any(1)]
    angles = []
    for normals_array in (n, nn):
        left, right = normals_array[pairs[:, 0]], normals_array[pairs[:, 1]]
        angles.append(np.degrees(np.arctan2(np.linalg.norm(np.cross(left, right), axis=1), np.sum(left*right, axis=1))))
    assert angles[1].max() < 30
    gradient = abs(delta[edges[:, 0], 1]-delta[edges[:, 1], 1])/np.linalg.norm(v[edges[:, 0]]-v[edges[:, 1]], axis=1)
    proof.update(candidate_sha256=sha(q), changed_vertices=int(changed.sum()),
                 support_bounds_m=[v[changed].min(0).tolist(), v[changed].max(0).tolist()],
                 actual_max_displacement_m=float(delta[:, 1].max()), profile_rows=profile_rows,
                 minimum_discrete_front_row_step_m=float(np.diff(envelope).min()),
                 normal_turn_median_p95_max_deg=np.percentile(turn, [50, 95, 100]).tolist(),
                 reversed_faces=0, minimum_area_ratio=float((area_new[active]/area[active]).min()),
                 max_edge_displacement_gradient=float(gradient.max()),
                 dihedral_before_median_p95_max_deg=np.percentile(angles[0], [50, 95, 100]).tolist(),
                 dihedral_after_median_p95_max_deg=np.percentile(angles[1], [50, 95, 100]).tolist(),
                 dihedral_increase_p95_max_deg=np.percentile(angles[1]-angles[0], [95, 100]).tolist(),
                 collision_tested=False, source_ART_approved=False)
    return q, changed, anchors, head, proof


def remove_overlay(state):
    overlay = state.get('overlay')
    if overlay is not None:
        mesh = overlay.data; bpy.data.objects.remove(overlay, do_unlink=True)
        if mesh.users == 0: bpy.data.meshes.remove(mesh)
        state['overlay'] = None


def restore_checkpoint(state):
    body = state['body_object']; assert body.mode == 'OBJECT'
    remove_overlay(state); body.data = state['before_mesh']
    for slot, (link, material) in zip(body.material_slots, state['before_material_slots']):
        slot.link = link; slot.material = material
    restore_context(state['context']); bpy.context.view_layer.update()
    assert sha(xyz(body.data)) == BASE and topology(body.data) == state['topology']
    assert diag.metadata(body) == state['group_metadata'] and diag.digest(diag.entries(body.data)) == state['deform_sha256']
    assert sha(normals(body.data)) == state['original_corner_normals_sha256']
    actual_uv = uv(body.data); old_uv = state['uv']
    assert actual_uv['active'] == old_uv['active'] and actual_uv['render'] == old_uv['render']
    assert actual_uv['values'].keys() == old_uv['values'].keys()
    assert all(np.array_equal(actual_uv['values'][k], a) for k, a in old_uv['values'].items())
    assert head_attributes(body.data, state['head']) == state['named_head_attributes']
    actual_flags = flags(body.data); assert all(np.array_equal(actual_flags[k], a) for k, a in state['flags'].items())
    assert np.array_equal(np.asarray(body.matrix_world), state['matrix'])
    assert actors(body) == state['actors']
    if state.get('after_mesh') is not None and state['after_mesh'].users == 0: bpy.data.meshes.remove(state['after_mesh'])


def select():
    ns = bpy.app.driver_namespace; assert KEY not in ns and 'MIA_HairReviewState' not in ns
    body = bpy.data.objects[BODY]; assert body.mode == 'OBJECT' and not body.hide_get()
    assert not body.modifiers and not body.data.shape_keys and np.array_equal(np.asarray(body.matrix_world), np.eye(4))
    before = xyz(body.data); assert sha(before) == BASE
    d = np.load(ROOT/'.mia-cache/body-h/shape/assembly/live-D/geometry.npz'); assert sha(d['world']) == BASE
    rows = dict(np.load(ROOT/'.mia-cache/migration-to-C/row-ownership.npz')); faces = d['triangles']
    assert np.array_equal(read(body.data.loops, 'vertex_index', dtype=np.int32).reshape(-1, 3), faces)
    after, changed, anchors, head, proof = forecast(before, faces, rows, d['source_part'])
    OUT.mkdir(parents=True, exist_ok=True); assert not (OUT/'selection.json').exists()
    mesh = body.data; head_loops = np.flatnonzero(np.isin(read(mesh.loops, 'vertex_index', dtype=np.int32), head))
    state = dict(body_object=body, before_mesh=mesh, after_mesh=None, before=before, after=after,
        changed=changed, anchors=anchors, head=head, head_loops=head_loops, head_normals=normals(mesh)[head_loops],
        original_corner_normals_sha256=sha(normals(mesh)), topology=topology(mesh), uv=uv(mesh), flags=flags(mesh),
        named_head_attributes=head_attributes(mesh, head), group_metadata=diag.require_known(body),
        deform_sha256=diag.digest(diag.entries(mesh)), matrix=np.asarray(body.matrix_world).copy(),
        before_material_slots=[(s.link, s.material) for s in body.material_slots],
        actors=actors(body), context=context_snapshot(), overlay=None,
        report=dict(proof, status='Support selection only; body original Mesh untouched', before_sha256=BASE,
                    operation='ONE continuous C1 AP profile warp; not ARAP/native solver/physical tissue',
                    namespace_key=KEY, native_saved=False, art_accepted=False))
    ns[KEY] = state
    try:
        # Owned render-hidden wire overlay; no original-mesh attribute or flags edited.
        selected_faces = faces[changed[faces].any(1)]; used = np.unique(selected_faces)
        remap = np.full(len(before), -1, np.int32); remap[used] = np.arange(len(used))
        overlay_mesh = bpy.data.meshes.new('MIA_APProfile01_SupportMesh')
        overlay_mesh.from_pydata(before[used].tolist(), [], remap[selected_faces].tolist()); overlay_mesh.update()
        overlay = bpy.data.objects.new('MIA_APProfile01_Support', overlay_mesh); state['overlay'] = overlay
        bpy.context.scene.collection.objects.link(overlay); overlay.hide_render = True
        overlay.display_type = 'WIRE'; overlay.show_in_front = True; overlay.color = (1., .35, .015, 1.)
        for ob in bpy.context.view_layer.objects: ob.select_set(ob == overlay)
        bpy.context.view_layer.objects.active = overlay
        assert body.data == mesh and sha(xyz(mesh)) == BASE
        (OUT/'selection.json').write_text(json.dumps(state['report'], indent=2)+'\n', encoding='utf8')
        print(json.dumps(dict(state['report'], overlay_object=overlay.name)))
    except Exception:
        restore_checkpoint(state); ns.pop(KEY, None); raise


def apply():
    ns = bpy.app.driver_namespace; state = ns[KEY]; body = state['body_object']
    assert body.mode == 'OBJECT' and body.data == state['before_mesh'] and sha(xyz(body.data)) == BASE
    assert 'MIA_HairReviewState' not in ns and state['after_mesh'] is None
    assert not (OUT/'apply.json').exists() and not (OUT/'apply-failed.json').exists()
    try:
        remove_overlay(state); restore_context(state['context'])
        assert actors(body) == state['actors']
        mesh = state['before_mesh'].copy(); mesh.name = 'MIA_APProfile01_Unselected_Trial'; state['after_mesh'] = mesh
        body.data = mesh
        for slot, (link, material) in zip(body.material_slots, state['before_material_slots']): slot.link = link; slot.material = material
        mesh.vertices.foreach_set('co', state['after'].ravel()); mesh.update(); bpy.context.view_layer.update()
        actual = xyz(mesh); assert np.array_equal(actual, state['after'])
        assert np.array_equal(actual[state['anchors']], state['before'][state['anchors']])
        assert np.array_equal(actual[:, [0, 2]], state['before'][:, [0, 2]]) and topology(mesh) == state['topology']
        actual_uv = uv(mesh); expected_uv = state['uv']
        assert actual_uv['active'] == expected_uv['active'] and actual_uv['render'] == expected_uv['render']
        assert actual_uv['values'].keys() == expected_uv['values'].keys()
        assert all(np.array_equal(actual_uv['values'][k], a) for k, a in expected_uv['values'].items())
        assert head_attributes(mesh, state['head']) == state['named_head_attributes']
        assert diag.metadata(body) == state['group_metadata'] and diag.digest(diag.entries(mesh)) == state['deform_sha256']
        assert diag.metadata_for_mesh(bpy, state['before_mesh']) == state['group_metadata']
        assert diag.digest(diag.entries(state['before_mesh'])) == state['deform_sha256']
        old, current = state['head_normals'].astype(float), normals(mesh)[state['head_loops']].astype(float)
        angle = np.degrees(np.arctan2(np.linalg.norm(np.cross(old, current), axis=1), np.sum(old*current, axis=1)))
        assert angle.max() < .05, 'Meaningful protected-head normal readback change'
        assert sha(xyz(state['before_mesh'])) == BASE and sha(normals(state['before_mesh'])) == state['original_corner_normals_sha256']
        assert actors(body) == state['actors'] and np.array_equal(np.asarray(body.matrix_world), state['matrix'])
        actual_flags = flags(mesh); assert all(np.array_equal(actual_flags[k], a) for k, a in state['flags'].items())
        ids = np.flatnonzero(state['changed']); delta = (actual.astype(float)-state['before'])[ids].astype(np.float32)
        assert not (OUT/'actual-delta.npz').exists()
        np.savez_compressed(OUT/'actual-delta.npz', vertex_ids=ids.astype(np.int32), delta=delta)
        state['report'].update(status='Actual live unselected C1 AP profile warp; source/collision/ART pending',
            candidate_sha256=sha(actual), actual_delta_sha256=sha(delta), actual_coordinate_readback_exact=True,
            original_mesh_pointer_retained=True, one_in_RAM_Mesh_copy_same_actor=True,
            topology_UV_named_head_attributes_diagnostic_groups_exact=True, all_declared_anatomy_anchors_exact=True,
            actual_head_corner_normal_max_angle_deg=float(angle.max()),
            head_normal_readback_sha256=sha(current.astype(np.float32)), original_head_normal_sha256=sha(state['head_normals']),
            normal_meaning='Original input Mesh/custom-normal storage untouched; working body derived normals recomputed, no body packed-normal identity claim',
            selection_hide_context_restored=True, all_other_actor_properties_held=True)
        (OUT/'apply.json').write_text(json.dumps(state['report'], indent=2)+'\n', encoding='utf8')
        print(json.dumps(state['report']))
    except Exception as error:
        restore_checkpoint(state); ns.pop(KEY, None)
        (OUT/'apply-failed.json').write_text(json.dumps(dict(error=str(error), original_mesh_pointer_restored=True,
            world_sha256=BASE, native_saved=False), indent=2)+'\n', encoding='utf8')
        raise


if not globals().get('MIA_AP_PROFILE01_NO_MAIN', False):
    phase = globals().get('MIA_AP_PROFILE01_PHASE', 'select'); assert phase in ('select', 'apply')
    select() if phase == 'select' else apply()
