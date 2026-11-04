"""Root-only live selection/application of the finite central-six groom.

select() reads actual actors and builds a RAM forecast; it does not edit a mesh.
apply(selection_sha256) needs that exact successful selection, then makes one
private Mesh.copy per existing target actor. No materials, UV, rigs, settings,
camera, light, rendered frames, or native files are changed. restore() is LIFO.
Imports are inert; no bpy call occurs until one of these explicit functions.
"""
from pathlib import Path
from datetime import datetime, timezone
from types import SimpleNamespace
import json
import runpy

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
KEY = 'MIA_RearGroom01'
SELECT = KEY+'_Selection'
BODY = 'MIA_Review12_H_LiveRepair'
BODY_SHA = '695dbbd825ce444fd04f0e390ccd64d31265d7cb14b027a08bf2ced82b4a7215'
NATIVE_SHA = '0d62eff09b4e95809a9f852d3e68654c1bb5a9e35fe70c065a939bc433e017ed'


def helpers(root):
    folder = Path(root)/'tools/mia/face_surface_live'
    return (runpy.run_path(str(folder/'rear_groom01.py')),
            runpy.run_path(str(folder/'v29_pigment_current.py')))


def _receipt(root, phase, report):
    folder = Path(root)/'.mia-cache/face-live/live/rear-groom01'
    folder.mkdir(parents=True, exist_ok=True)
    assert sum(p.stat().st_size for p in folder.iterdir() if p.is_file()) < 15*1024**2
    path = folder/(phase+'-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json')
    text = json.dumps(report, indent=2)+'\n'; assert len(text.encode()) < 1024**2
    with path.open('x', encoding='utf8') as stream: stream.write(text)
    return str(path)


def _actual_geometry(ob):
    import bpy
    depsgraph = bpy.context.evaluated_depsgraph_get(); evaluated = ob.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
    try:
        assert all(len(p.vertices) == 3 for p in mesh.polygons)
        q = np.asarray([v.co[:] for v in mesh.vertices], np.float64)
        matrix = np.asarray(evaluated.matrix_world, np.float64)
        q = q@matrix[:3, :3].T+matrix[:3, 3]
        return q, np.asarray([p.vertices[:] for p in mesh.polygons], np.int32)
    finally: evaluated.to_mesh_clear()


def _context(root, guard):
    """Bind evaluated contact inputs omitted by the raw-mesh fingerprint."""
    import bpy
    _, objects = guard['_watched'](root)
    armatures = {}
    for ob in bpy.data.objects:
        if ob.type == 'ARMATURE':
            armatures[ob.name] = dict(world=guard['digest'](np.asarray(ob.matrix_world, np.float32)),
                bones={b.name:(guard['digest'](np.asarray(b.matrix_basis, np.float32)),
                               guard['digest'](np.asarray(b.matrix, np.float32))) for b in ob.pose.bones})
    return dict(frame=bpy.context.scene.frame_current, armatures=armatures,
                modifiers={name:guard['_modifiers'](ob) for name,ob in objects.items()},
                keys={name:[(k.name,k.value,bool(k.mute)) for k in ob.data.shape_keys.key_blocks]
                      for name,ob in objects.items() if ob.data.shape_keys})


def _intersection_count(tree_a, tree_b, faces=None):
    pairs = np.asarray(tree_a.overlap(tree_b), np.int32).reshape(-1, 2)
    if faces is not None and len(pairs):
        pairs = pairs[pairs[:, 0] < pairs[:, 1]]
        shared = np.any(faces[pairs[:, 0], :, None] == faces[pairs[:, 1], None, :], axis=(1, 2))
        pairs = pairs[~shared]
    return len(pairs)


def _contacts(root, objects, targets, after):
    from mathutils.bvhtree import BVHTree
    before, candidate, faces, actual, moved_world = {}, {}, {}, {}, {}
    for name, ob in objects.items():
        q, f = _actual_geometry(ob); faces[name] = f
        actual[name] = (q, f)
        before[name] = BVHTree.FromPolygons(q.tolist(), f.tolist(), all_triangles=True, epsilon=0)
        if name in targets:
            matrix = np.asarray(ob.matrix_world, np.float64)
            moved = after[name].astype(float)@matrix[:3, :3].T+matrix[:3, 3]
            moved_world[name] = moved
            candidate[name] = BVHTree.FromPolygons(moved.tolist(), f.tolist(), all_triangles=True, epsilon=0)
        else: candidate[name] = before[name]
    rows = []; failed = []
    names = sorted(objects)
    for i, a in enumerate(names):
        for b in names[i:]:
            if a not in targets and b not in targets: continue
            f = faces[a] if a == b else None
            old = _intersection_count(before[a], before[b], f)
            new = _intersection_count(candidate[a], candidate[b], f)
            if old or new:
                row = dict(a=a, b=b, before=old, candidate=new)
                rows.append(row)
                if new > old: failed.append(row)
    sat = runpy.run_path(str(Path(root)/'tools/mia/face_surface_live/rear_groom01_contact.py'))['check'](
        root, actual, moved_world)
    return dict(method='Actual evaluated triangle BVH quick reject + bounded conservative AABB/SAT',
                affected_pairs=rows, increased_pairs=failed, gate_passed=not failed,
                SAT=sat, physical_status='FAIL' if failed or sat['status'] == 'FAIL' else sat['status'],
                limit='BVH alone is not collision PASS; SAT UNVERIFIED may preview, never KEEP; no continuous-motion/ART claim')


def _order_spans(rows, moved):
    result = []
    for front, back, low, high in [('CenterTurnLeft', 'CenterTurnRight', 1.400, 1.430),
                                    ('MidLeftInner', 'LongCenter', 1.310, 1.350)]:
        report = dict(front=front, behind=back, world_Z=[low, high], depth_inferred=True)
        for label, data in [('before', {n:r['co'] for n,r in rows.items()}), ('candidate', moved)]:
            a = data[front][:-2].reshape(-1, 32, 3); b = data[back][:-2].reshape(-1, 32, 3)
            ca, cb = a.mean(1), b.mean(1); measurements = []
            for z in np.linspace(low, high, 31):
                x = a[np.argmin(abs(ca[:, 2]-z))]; y = b[np.argmin(abs(cb[:, 2]-z))]
                overlap = min(x[:, 0].max(), y[:, 0].max())-max(x[:, 0].min(), y[:, 0].min())
                if overlap > 0: measurements.append((overlap*1000, (x[:, 1].min()-y[:, 1].max())*1000))
            report[label] = dict(projected_overlap_samples=len(measurements))
            if measurements:
                values = np.asarray(measurements)
                report[label].update(projected_X_overlap_mm=[float(values[:, 0].min()), float(values[:, 0].max())],
                                     conservative_section_Y_gap_mm=[float(values[:, 1].min()), float(values[:, 1].max())])
        result.append(report)
    return result


def select(root=ROOT):
    """Read-only scene selection plus bounded RAM/receipt ownership."""
    import bpy
    root = Path(root).resolve(); assert bpy.context.mode == 'OBJECT'
    assert KEY not in bpy.app.driver_namespace and SELECT not in bpy.app.driver_namespace
    plan, guard = helpers(root); rows = plan['cached'](root)
    current = json.loads((root/'asset/mia/CURRENT_STATE.json').read_text(encoding='utf8'))
    native = (root/current['active_live_checkpoint']['path']).resolve()
    assert Path(bpy.data.filepath).resolve() == native and plan['file_sha'](native) == NATIVE_SHA
    before = guard['_snapshot'](root); graphs = guard['materials_signature'](); context = _context(root, guard)
    assert before[BODY]['fingerprint']['coordinates'] == BODY_SHA
    target_names = [plan['PREFIX']+name for name in plan['NAMES']]
    _, objects = guard['_watched'](root)
    # The hidden authoritative raw Main is not a physical contact surface.
    physical = {name:ob for name,ob in objects.items() if name != 'MIA_V17_PIXAL_DetailedHair'}
    moved, payloads, originals, proofs, normal_status = {}, {}, {}, [], {}
    for short, row in rows.items():
        name = plan['PREFIX']+short; ob = objects[name]; mesh = ob.data
        assert before[name]['fingerprint'] == row['fingerprint'], 'Selected lock differs from retained cache: '+name
        assert len(ob.modifiers) == 0 and mesh.shape_keys is None
        owners = [o.name for o in bpy.data.objects if o.type == 'MESH' and o.data == mesh]
        assert owners == [name] and mesh.users == 1, 'Unexpected shared mesh: '+name
        normal_status[name] = dict(has_custom_normals=bool(mesh.has_custom_normals),
                                   encoded_attribute='custom_normal' in mesh.attributes)
        assert not mesh.has_custom_normals and 'custom_normal' not in mesh.attributes, (
            'Encoded normals require an explicit transport review; do not skip/rebuild them: '+name)
        out, proof, _ = plan['candidate'](short, row)
        assert proof['reversed_relative_to_baseline'] == 0 and proof['minimum_actual_area2'] > 1e-13
        assert proof['max_section_shape_error_um'] < .2 and .94 < proof['volume_ratio'] < 1.06
        assert np.linalg.norm(proof['tip_translation_mm']) < 8.01
        moved[name] = out; proofs.append(proof); originals[name] = mesh
        payloads[name] = guard['_mesh_payload'](mesh)
    spans = _order_spans(rows, {short:moved[plan['PREFIX']+short] for short in rows})
    assert all(span['candidate']['projected_overlap_samples'] == 31 and
               span['candidate']['conservative_section_Y_gap_mm'][0] > 1.5 for span in spans)
    contacts = _contacts(root, physical, target_names, moved)
    preview_ready = contacts['gate_passed'] and contacts['SAT']['status'] != 'FAIL'
    token = plan['sha'](np.frombuffer(guard['canonical'](dict(before=before, proofs=proofs, graphs=graphs, context=context)).encode(), np.uint8))
    report = dict(scope='Central-six finite path/order selection; not M2 ART', selection_sha256=token,
                  targets=target_names, body_sha256=BODY_SHA, shape_forecast=proofs,
                  normal_status=normal_status, order_spans=spans, contacts=contacts,
                  preview_ready=preview_ready, KEEP_allowed=False,
                  width_depth_scaling=False, added_twist=False,
                  root_join_rows_exact=True, UV_materials_held=True, inferred_depth=True,
                  native_saved=False, ART=False, source='v22 back/profile qualitative flow; no per-strand correspondence claim')
    report['receipt'] = _receipt(root, 'select', report)
    if preview_ready:
        bpy.app.driver_namespace[SELECT] = dict(root=str(root), token=token, before=before, graphs=graphs,
            originals=originals, payloads=payloads, moved=moved, report=report, native=str(native), context=context)
    return report


def apply(selection_sha256, root=ROOT):
    import bpy
    root = Path(root).resolve(); state = bpy.app.driver_namespace[SELECT]
    assert KEY not in bpy.app.driver_namespace and state['root'] == str(root)
    assert state['token'] == selection_sha256 and bpy.context.mode == 'OBJECT'
    _, guard = helpers(root)
    assert guard['_snapshot'](root) == state['before'] and guard['materials_signature']() == state['graphs']
    assert _context(root, guard) == state['context'], 'Modifier/pose/frame/key context changed after selection'
    state['owned'] = {}; bpy.app.driver_namespace[KEY] = state
    try:
        for name, out in state['moved'].items():
            ob = bpy.data.objects[name]; mesh = ob.data.copy(); state['owned'][name] = mesh
            mesh.name = name+'_Groom01_RAM_WIP'
            mesh.vertices.foreach_set('co', out.ravel()); mesh.update()
            ob.data = mesh
            assert guard['digest'](np.asarray([v.co[:] for v in mesh.vertices], np.float32)) == guard['digest'](out)
            after_payload = guard['_mesh_payload'](mesh)
            old_payload = dict(state['payloads'][name], attributes=dict(state['payloads'][name]['attributes']))
            after_payload['attributes'].pop('position'); old_payload['attributes'].pop('position')
            assert after_payload == old_payload, 'Non-position storage changed: '+name
        bpy.context.view_layer.update(); after = guard['_snapshot'](root)
        for name, old in state['before'].items():
            if name not in state['moved']: assert after[name] == old
            else:
                assert after[name]['slots'] == old['slots']
                assert {k:v for k,v in after[name]['fingerprint'].items() if k not in ('coordinates', 'corner_normals')} == {
                    k:v for k,v in old['fingerprint'].items() if k not in ('coordinates', 'corner_normals')}
        assert guard['materials_signature']() == state['graphs']
        assert _context(root, guard) == state['context']
        state['after'] = after
        del bpy.app.driver_namespace[SELECT]
        report = dict(status='APPLIED_CENTRAL_SIX_GROOM_WIP', selection_sha256=selection_sha256,
                      targets=list(state['owned']), original_data_pointers_retained=True,
                      original_UV_materials_other_actors_body_exact=True,
                      normals='Source locks have no custom-normal storage; actual smooth normals follow new geometry',
                      native_saved=False, ART=False, review_required='Actual source/back/both rear angles/high/low; restore before older root/look stages')
        report['receipt'] = _receipt(root, 'apply', report)
        return report
    except BaseException:
        for name, original in state['originals'].items(): bpy.data.objects[name].data = original
        for name, mesh in list(state['owned'].items()):
            assert mesh.users == 0; bpy.data.meshes.remove(mesh, do_unlink=False); del state['owned'][name]
        bpy.context.view_layer.update()
        assert guard['_snapshot'](root) == state['before'] and guard['materials_signature']() == state['graphs']
        bpy.app.driver_namespace.pop(KEY, None)
        raise


def restore(root=None):
    import bpy
    state = bpy.app.driver_namespace[KEY]; root = Path(state['root'] if root is None else root).resolve()
    assert state['root'] == str(root) and bpy.context.mode == 'OBJECT'
    _, guard = helpers(root)
    assert guard['_snapshot'](root) == state['after'] and guard['materials_signature']() == state['graphs']
    assert _context(root, guard) == state['context'], 'Restore later modifier/pose/frame/key edits first'
    for name, mesh in state['owned'].items():
        assert bpy.data.objects[name].data == mesh and mesh.users == 1
        original = state['originals'][name]
        proxy = SimpleNamespace(data=original, matrix_world=bpy.data.objects[name].matrix_world)
        h = guard['_helpers'](root)
        assert h['fingerprint'](proxy) == state['before'][name]['fingerprint']
        assert guard['_mesh_payload'](original) == state['payloads'][name]
    for name, original in state['originals'].items(): bpy.data.objects[name].data = original
    bpy.context.view_layer.update()
    assert guard['_snapshot'](root) == state['before']
    for name, mesh in list(state['owned'].items()):
        assert mesh.users == 0; bpy.data.meshes.remove(mesh, do_unlink=False); del state['owned'][name]
    assert guard['materials_signature']() == state['graphs']
    del bpy.app.driver_namespace[KEY]
    report = dict(status='RESTORED_EXACT_CENTRAL_SIX_ORIGINAL_POINTERS', native_saved=False, ART=False)
    report['receipt'] = _receipt(root, 'restore', report)
    return report
