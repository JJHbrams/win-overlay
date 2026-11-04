"""Retired c9 live trial: select/apply reject; restore remains available.

Explicit API: select(root), apply(selection_sha256), restore(), cancel().
Imports are inert. Historical code is retained to explain the rejected trial
and restore interrupted old sessions. Private payload/context helpers are also
reused by scoped_mesh_edit.py; do not remove them as unused trial code.
"""
from pathlib import Path
from datetime import datetime, timezone
from types import SimpleNamespace
import hashlib
import json
import runpy
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
KEY = 'MIA_ArmChain01'
SELECT = KEY+'_Selection'
BODY = 'MIA_Review12_H_LiveRepair'
RETIRED_REASON = ('Arm-chain c9 is retired: actual matched views showed distortion of retained '
                  'thorax/breast roots/lats and shoulder ledges. Use an explicitly scoped edit; '
                  'do not replay or coefficient-retune this carrier. Existing restore remains usable.')


def helpers(root):
    root = Path(root)
    return (runpy.run_path(str(root/'tools/mia/integrated_finish/arm_chain01.py')),
            runpy.run_path(str(root/'tools/mia/face_surface_live/v29_pigment_current.py')))


def file_sha(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(4*1024**2): value.update(block)
    return value.hexdigest()


def _read(collection, field, width=1, dtype=np.float32):
    out = np.empty((len(collection), width), dtype)
    collection.foreach_get(field, out.ravel())
    return out[:, 0] if width == 1 else out


def _coordinates(mesh): return _read(mesh.vertices, 'co', 3)


def _normals(mesh): return _read(mesh.corner_normals, 'vector', 3)


def _receipt(root, phase, report):
    folder = Path(root)/'.mia-cache/body-h/live/integrated01/arm-chain01'
    folder.mkdir(parents=True, exist_ok=True)
    assert sum(p.stat().st_size for p in folder.rglob('*') if p.is_file()) < 30*1024**2
    output = folder/(phase+'-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json')
    value = json.dumps(report, indent=2, allow_nan=False)+'\n'
    assert len(value.encode('utf8')) < 1024**2
    with output.open('x', encoding='utf8') as stream: stream.write(value)
    return str(output)


def _sources(root):
    paths = ['tools/mia/integrated_finish/arm_chain01.py',
             'tools/mia/integrated_finish/arm_chain01_live.py',
             'tools/mia/face_surface_live/v29_pigment_current.py',
             '.mia-cache/body-h/live/integrated01/current-geometry.npz',
             '.mia-cache/body-h/shape/assembly/live-D/geometry.npz',
             '.mia-cache/migration-to-C/row-ownership.npz']
    return {p: file_sha(Path(root)/p) for p in paths}


def _context(root, guard, exclude=()):
    """Raw-mesh fingerprints do not cover pose, modifiers or scene actors."""
    import bpy
    objects = {}
    poses = {}
    for ob in bpy.context.scene.objects:
        if ob.name in exclude: continue
        objects[ob.name] = dict(type=ob.type,
            data=int(ob.data.as_pointer()) if ob.data else None,
            matrix=guard['digest'](np.asarray(ob.matrix_world, np.float64)),
            hidden=bool(ob.hide_get()), hide_render=bool(ob.hide_render),
            modifiers=guard['_modifiers'](ob),
            keys=[(k.name, k.value, bool(k.mute)) for k in ob.data.shape_keys.key_blocks]
                 if ob.type == 'MESH' and ob.data.shape_keys else [],
            optical=guard['_rna'](ob.data) if ob.type in ('CAMERA', 'LIGHT') else None)
        if ob.type == 'ARMATURE':
            poses[ob.name] = {b.name:(guard['digest'](np.asarray(b.matrix_basis)),
                                    guard['digest'](np.asarray(b.matrix))) for b in ob.pose.bones}
    return dict(objects=objects, poses=poses, frame=bpy.context.scene.frame_current,
                camera=bpy.context.scene.camera.name if bpy.context.scene.camera else None,
                native=str(Path(bpy.data.filepath).resolve()))


def _groups(ob):
    return [(g.index, g.name, bool(g.lock_weight)) for g in ob.vertex_groups]


def _uv_flags(mesh):
    return dict(active=mesh.uv_layers.active_index,
        layers=[(u.name, bool(u.active_render), bool(u.active_clone)) for u in mesh.uv_layers])


def _without_position(payload):
    result = dict(payload, attributes=dict(payload['attributes']))
    result['attributes'].pop('position', None)
    return result


def _ui():
    import bpy
    return dict(selected=list(bpy.context.selected_objects), active=bpy.context.view_layer.objects.active)


def _restore_ui(saved):
    import bpy
    for ob in bpy.context.view_layer.objects: ob.select_set(ob in saved['selected'])
    bpy.context.view_layer.objects.active = saved['active']


def _remove_overlay(state):
    import bpy
    ob = state.get('overlay')
    if ob is not None:
        try: ob.as_pointer()
        except ReferenceError: pass  # Already removed during interrupted cleanup.
        else: bpy.data.objects.remove(ob, do_unlink=True)
        state['overlay'] = None
    mesh = state.get('overlay_mesh')
    if mesh is not None:
        try: users = mesh.users
        except ReferenceError: pass
        else:
            assert users == 0
            bpy.data.meshes.remove(mesh, do_unlink=False)
        state['overlay_mesh'] = None


def select(root=ROOT):
    raise RuntimeError(RETIRED_REASON)
    # Kept below for forensic provenance of the failed recipe, never dispatched.
    import bpy
    root = Path(root).resolve()
    assert bpy.context.mode == 'OBJECT'
    assert KEY not in bpy.app.driver_namespace and SELECT not in bpy.app.driver_namespace
    plan, guard = helpers(root)
    body = bpy.data.objects[BODY]
    assert body.mode == 'OBJECT' and not body.modifiers and body.data.shape_keys is None
    assert np.array_equal(np.asarray(body.matrix_world), np.eye(4))
    original = body.data; before_co = _coordinates(original)
    assert plan['sha'](before_co) == plan['BASE_SHA']
    candidate, changed, proof = plan['forecast'](root)
    assert proof['status'] == 'TECHNICAL_FORECAST_PASS', proof['status']
    with np.load(root/'.mia-cache/body-h/live/integrated01/current-geometry.npz') as archive:
        faces = archive['faces']
    assert np.array_equal(_read(original.loops, 'vertex_index', dtype=np.int32).reshape(-1, 3), faces)
    before = guard['_snapshot'](root); graphs = guard['materials_signature']()
    payload = guard['_mesh_payload'](original)
    assert payload['attributes']['custom_normal'][1] == 'INT16_2D'
    with np.load(root/'.mia-cache/body-h/shape/assembly/live-D/geometry.npz') as archive:
        head_ids = np.unique(faces[archive['source_part'] == 1])
    head_loops = np.flatnonzero(np.isin(_read(original.loops, 'vertex_index', dtype=np.int32), head_ids))
    context = _context(root, guard); sources = _sources(root)
    token = hashlib.sha256(guard['canonical'](dict(before=before, graphs=graphs,
        context=context, sources=sources, candidate=proof['candidate_sha256'])).encode()).hexdigest()
    state = dict(root=str(root), token=token, original=original, before=before,
        graphs=graphs, payload=payload, context=context, sources=sources,
        uv_flags=_uv_flags(original), groups=_groups(body), candidate=candidate,
        original_normal_sha=plan['sha'](_normals(original)),
        head_loops=head_loops, head_normals=_normals(original)[head_loops],
        ui=_ui(), overlay=None, overlay_mesh=None, owned=None, proof=proof,
        native_sha=file_sha(Path(bpy.data.filepath)))
    bpy.app.driver_namespace[SELECT] = state
    try:
        selected_faces = faces[changed[faces].any(axis=1)]
        used = np.unique(selected_faces); remap = np.full(len(before_co), -1, np.int32)
        remap[used] = np.arange(len(used))
        mesh = bpy.data.meshes.new('MIA_ArmChain01_SupportMesh')
        state['overlay_mesh'] = mesh
        overlay = bpy.data.objects.new('MIA_ArmChain01_Support', mesh)
        state['overlay'] = overlay
        mesh.from_pydata(before_co[used].tolist(), [], remap[selected_faces].tolist()); mesh.update()
        bpy.context.scene.collection.objects.link(overlay)
        overlay.hide_render = True; overlay.display_type = 'WIRE'
        overlay.show_in_front = True; overlay.color = (1., .35, .015, 1.)
        for ob in bpy.context.view_layer.objects: ob.select_set(ob == overlay)
        bpy.context.view_layer.objects.active = overlay
        assert guard['_snapshot'](root) == before
        report = dict(status='SUPPORT_SELECTION_ONLY', selection_sha256=token,
            overlay_object=overlay.name, forecast=proof, original_body_unchanged=True,
            preview_ready=True, KEEP_allowed=False, collision_status='UNVERIFIED',
            native_saved=False, ART=False,
            scope='Connected torso carrier plus separate arm chain, rigid hands and nails; no width fitting',
            normals='Encoded storage will be copied untouched; derived normal transport requires actual readback')
        report['receipt'] = _receipt(root, 'select', report)
        return report
    except BaseException:
        _remove_overlay(state); _restore_ui(state['ui'])
        bpy.app.driver_namespace.pop(SELECT, None)
        raise


def apply(selection_sha256):
    raise RuntimeError(RETIRED_REASON)
    # Existing pending preview can still be reverted with restore().
    import bpy
    state = bpy.app.driver_namespace[SELECT]; root = Path(state['root'])
    assert bpy.context.mode == 'OBJECT' and KEY not in bpy.app.driver_namespace
    assert selection_sha256 == state['token']
    plan, guard = helpers(root)
    assert _sources(root) == state['sources'], 'Source recipe or geometry input changed'
    assert guard['_snapshot'](root) == state['before']
    assert guard['materials_signature']() == state['graphs']
    assert guard['_mesh_payload'](state['original']) == state['payload']
    assert _context(root, guard, exclude=[state['overlay'].name]) == state['context']
    assert file_sha(Path(bpy.data.filepath)) == state['native_sha']
    body = bpy.data.objects[BODY]; assert body.data == state['original']
    _remove_overlay(state); _restore_ui(state['ui'])
    bpy.app.driver_namespace[KEY] = state
    try:
        mesh = state['original'].copy(); state['owned'] = mesh
        mesh.name = 'MIA_ArmChain01_TwoChart_RAM_WIP'
        body.data = mesh
        mesh.vertices.foreach_set('co', state['candidate'].ravel()); mesh.update()
        bpy.context.view_layer.update()
        assert np.array_equal(_coordinates(mesh), state['candidate'])
        assert _without_position(guard['_mesh_payload'](mesh)) == _without_position(state['payload'])
        assert _uv_flags(mesh) == state['uv_flags'] and _groups(body) == state['groups']
        original_head = state['head_normals'].astype(float)
        candidate_head = _normals(mesh)[state['head_loops']].astype(float)
        angle = np.degrees(np.arctan2(np.linalg.norm(np.cross(original_head, candidate_head), axis=1),
                                     np.sum(original_head*candidate_head, axis=1)))
        assert angle.max() < .05, 'Protected head corner normals changed'
        assert plan['sha'](_normals(state['original'])) == state['original_normal_sha']
        assert guard['_mesh_payload'](state['original']) == state['payload']
        after = guard['_snapshot'](root)
        for name, row in state['before'].items():
            if name != BODY: assert after[name] == row, name
            else:
                assert after[name]['slots'] == row['slots']
                assert {k:v for k,v in after[name]['fingerprint'].items() if k not in ('coordinates','corner_normals')} == {
                    k:v for k,v in row['fingerprint'].items() if k not in ('coordinates','corner_normals')}
        assert guard['materials_signature']() == state['graphs']
        current_context = _context(root, guard)
        expected_context = json.loads(json.dumps(state['context']))
        expected_context['objects'][BODY]['data'] = int(mesh.as_pointer())
        # JSON coercion is used on both sides only to normalize tuple RNA values.
        assert guard['canonical'](current_context) == guard['canonical'](expected_context)
        state['after'] = after; state['after_context'] = current_context
        del bpy.app.driver_namespace[SELECT]
        report = dict(status='APPLIED_ARM_CHAIN_PREVIEW_WIP', candidate_sha256=plan['sha'](_coordinates(mesh)),
            original_body_pointer_retained=True, head_corner_normal_max_angle_deg=float(angle.max()),
            non_position_payload_UV_groups_exact=True, other_watched_actors_exact=True,
            encoded_custom_normal_storage_exact=True,
            normals='Original encoded storage retained; local decoded normals follow geometry, no global normal setter',
            native_saved=False, ART=False, KEEP_allowed=False, collisions='UNVERIFIED',
            review_required='Frozen source/front/profile/back/both oblique/high/low, root/gland/waist strain and contacts')
        report['receipt'] = _receipt(root, 'apply', report)
        return report
    except BaseException:
        # Leave a resumable exact-baseline cleanup state if update/removal fails.
        # The namespace is released only after all cleanup guards succeed.
        body.data = state['original']; state['restore_pending'] = True
        bpy.context.view_layer.update()
        if state['owned'] is not None:
            assert state['owned'].users == 0
            bpy.data.meshes.remove(state['owned'], do_unlink=False); state['owned'] = None
        assert guard['_snapshot'](root) == state['before']
        bpy.app.driver_namespace.pop(KEY, None)
        bpy.app.driver_namespace.pop(SELECT, None)
        raise


def cancel():
    import bpy
    state = bpy.app.driver_namespace[SELECT]; root = Path(state['root'])
    _, guard = helpers(root)
    assert bpy.context.mode == 'OBJECT'
    assert guard['_snapshot'](root) == state['before']
    assert guard['_mesh_payload'](state['original']) == state['payload']
    _remove_overlay(state); _restore_ui(state['ui'])
    del bpy.app.driver_namespace[SELECT]
    return dict(status='CANCELLED_SUPPORT_ONLY', original_body_unchanged=True, native_saved=False, ART=False)


def restore():
    import bpy
    state = bpy.app.driver_namespace[KEY]; root = Path(state['root'])
    plan, guard = helpers(root); body = bpy.data.objects[BODY]
    assert bpy.context.mode == 'OBJECT'
    if not state.get('restore_pending', False):
        assert body.data == state['owned'] and state['owned'].users == 1
        assert guard['_snapshot'](root) == state['after']
        assert guard['materials_signature']() == state['graphs']
        assert _context(root, guard) == state['after_context']
        assert _without_position(guard['_mesh_payload'](body.data)) == _without_position(state['payload'])
        assert _uv_flags(body.data) == state['uv_flags'] and _groups(body) == state['groups']
    assert guard['_mesh_payload'](state['original']) == state['payload']
    assert plan['sha'](_normals(state['original'])) == state['original_normal_sha']
    helper = guard['_helpers'](root)
    proxy = SimpleNamespace(data=state['original'], matrix_world=body.matrix_world)
    assert helper['fingerprint'](proxy) == state['before'][BODY]['fingerprint']
    assert body.data in (state['original'], state['owned']), 'Do not overwrite an unrelated later mesh binding'
    body.data = state['original']; state['restore_pending'] = True
    bpy.context.view_layer.update()
    assert guard['_snapshot'](root) == state['before']
    assert _context(root, guard) == state['context']
    assert guard['materials_signature']() == state['graphs']
    assert _uv_flags(body.data) == state['uv_flags'] and _groups(body) == state['groups']
    mesh = state['owned']
    if mesh is not None:
        assert mesh.users == 0
        bpy.data.meshes.remove(mesh, do_unlink=False); state['owned'] = None
    del bpy.app.driver_namespace[KEY]
    bpy.app.driver_namespace.pop(SELECT, None)
    report = dict(status='RESTORED_EXACT_ARM_CHAIN_BASELINE_POINTER',
                  body_sha256=plan['sha'](_coordinates(body.data)), native_saved=False, ART=False)
    report['receipt'] = _receipt(root, 'restore', report)
    return report
