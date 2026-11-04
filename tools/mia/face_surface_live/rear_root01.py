"""One reversible buried-to-visible emergence trial on six existing rear locks.

Restores the actual pre-follow stem, then monotonically fades its measured
outward displacement back to the unchanged hanging lock. No new meshes,
widths, UVs, shaders, rigs, or whole-scene checkpoints. Run through live MCP.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import runpy

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'.mia-cache/face-live/live/rear-root01'
KEY = 'MIA_RearRoot01'
PREFIX = 'MIA_Hair_CurvedRear03Base_'
NAMES = ('DeepCenter', 'LongCenter', 'MidLeftInner', 'MidRightInner',
         'CenterTurnLeft', 'CenterTurnRight')


def sha(array):
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def coordinates(ob):
    values = np.empty((len(ob.data.vertices), 3), np.float32)
    ob.data.vertices.foreach_get('co', values.ravel())
    return values


def bends(rings):
    edges = np.diff(rings.astype(float).mean(1), axis=0)
    return np.degrees(np.arccos(np.clip(np.einsum('ij,ij->i', edges[:-1], edges[1:])/
        (np.linalg.norm(edges[:-1], axis=1)*np.linalg.norm(edges[1:], axis=1)), -1, 1)))


def candidate(before, original, faces):
    """The support comes from the exact prior Y-only outward-follow delta."""
    assert before.dtype == original.dtype == np.float32 and before.shape == original.shape
    assert np.array_equal(before[:, [0, 2]], original[:, [0, 2]])
    count = (len(before)-2)//32
    assert count*32+2 == len(before)
    old = original[:-2].reshape(count, 32, 3)
    current = before[:-2].reshape(count, 32, 3)
    delta = current[:, :, 1]-old[:, :, 1]
    assert np.ptp(delta, axis=1).max() < 8e-8, 'Not the previous whole-section Y edit'
    dy = delta[:, 0]
    changed = np.flatnonzero(abs(dy) > 1e-7)
    assert len(changed) and changed[0] == 0
    end = int(changed[-1])+1
    assert end+1 < count and not np.any(abs(dy[end:]) > 1e-7)
    center = old.astype(float).mean(1)
    arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(center, axis=0), axis=1))]
    phase = np.clip(arc/arc[end], 0, 1)
    blend = phase**3*(10+phase*(-15+6*phase))
    after = before.copy()
    after[:-2].reshape(count, 32, 3)[:end, :, 1] = (
        old[:end, :, 1].astype(float)+dy[:end, None].astype(float)*blend[:end, None])
    after[-2] = original[-2]  # Original buried root-cap centre only; tip held.
    assert np.array_equal(after[:, [0, 2]], before[:, [0, 2]])
    assert np.array_equal(after[end*32:-2], before[end*32:-2])
    assert np.array_equal(after[-1], before[-1])
    t0, t1 = before[faces].astype(float), after[faces].astype(float)
    n0 = np.cross(t0[:, 1]-t0[:, 0], t0[:, 2]-t0[:, 0])
    n1 = np.cross(t1[:, 1]-t1[:, 0], t1[:, 2]-t1[:, 0])
    area0, area1 = np.linalg.norm(n0, axis=1), np.linalg.norm(n1, axis=1)
    dots = np.einsum('ij,ij->i', n0, n1)
    assert area1.min() > 1e-13 and (dots > 0).all(), 'New collapsed/reversed triangle'
    volume = float(np.einsum('ij,ij->i', t1[:, 0], np.cross(t1[:, 1], t1[:, 2])).sum()/6)
    assert volume > 0
    b0, b1 = bends(current), bends(after[:-2].reshape(count, 32, 3))
    assert float((b1[:end]-b0[:end]).max()) < 9, 'New sharp centreline bend'
    ids = np.flatnonzero(np.any(before != after, axis=1))
    proof = dict(ring_count=count, support_last_changed_ring=end-1, unchanged_join_ring=end,
                 support_arc_mm=float(arc[end]*1000), changed_vertices=len(ids),
                 max_move_mm=float(np.linalg.norm(after-before, axis=1).max()*1000),
                 minimum_triangle_area2=float(area1.min()), reversed_triangles=0,
                 maximum_face_normal_rotation_degrees=float(np.degrees(np.arccos(
                     np.clip(dots/(area0*area1), -1, 1))).max()), positive_volume_m3=volume,
                 support_max_bend_before_degrees=float(b0[:end].max()),
                 support_max_bend_after_degrees=float(b1[:end].max()),
                 maximum_bend_increase_degrees=float((b1[:end]-b0[:end]).max()),
                 inherited_DeepCenter_join_limit='Its approximately72.6deg join is retained, not fixed',
                 XZ_width_topology_and_hanging_lower_points_exact=True)
    return after, ids, proof


def helper():
    return runpy.run_path(str(Path(__file__).with_name('lock_look01.py')),
                         init_globals={'MIA_LOCK_LOOK01_LIBRARY_ONLY': True})


def actor_geometry(ob, deps):
    """Read actual evaluated retained Main, including its declared omission."""
    ev = ob.evaluated_get(deps)
    mesh = ev.to_mesh(preserve_all_data_layers=True, depsgraph=deps)
    try:
        mesh.calc_loop_triangles()
        verts = np.asarray([ev.matrix_world@v.co for v in mesh.vertices], float)
        faces = np.asarray([t.vertices[:] for t in mesh.loop_triangles], np.int32)
        return verts, faces
    finally:
        ev.to_mesh_clear()


def overlap(actor_names, records, proposed, all_parts):
    """Actual hair-layer occlusion diagnostic, not blanket collision approval."""
    import bpy
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    deps = bpy.context.evaluated_depsgraph_get()
    owned = {}
    for ob in all_parts:
        if ob.name in records:
            owned[ob.name] = (proposed.get(ob.name, records[ob.name]['before']).astype(float),
                              records[ob.name]['faces'])
        else:
            owned[ob.name] = actor_geometry(ob, deps)
    result = {}
    for name in actor_names:
        vertices, triangles, offset = [], [], 0
        for other, (verts, faces) in owned.items():
            if other == name: continue
            vertices.append(verts); triangles.append(faces+offset); offset += len(verts)
        tree = BVHTree.FromPolygons(np.concatenate(vertices).tolist(),
                                   np.concatenate(triangles).tolist(), all_triangles=True)
        rec = records[name]
        count, end = rec['proof']['ring_count'], rec['proof']['unchanged_join_ring']
        before = rec['before'][:-2].reshape(count, 32, 3)
        after = proposed.get(name, rec['before'])[:-2].reshape(count, 32, 3)
        angles = {}
        for angle in (0, -35, 35):
            direction = Vector((np.sin(np.radians(angle)), np.cos(np.radians(angle)), 0))
            values = []
            # Full sections in back; root and representative stem sections in
            # both rear obliques. Bounds are physical, not drawing cameras.
            sample = range(end+1) if angle == 0 else sorted(set((0, 2, end//3, 2*end//3, end)))
            for i in sample:
                gaps = []
                for point in after[i]:
                    origin = Vector(point)+direction*.7
                    hit = tree.ray_cast(origin, -direction, 1.4)[0]
                    if hit is not None: gaps.append(float((Vector(point)-hit).dot(direction)))
                exposed = sum(value > 0 for value in gaps)
                values.append(dict(ring=i, parent_hits=len(gaps),
                    exposed_fraction=exposed/len(gaps) if gaps else None,
                    minimum_gap_mm=min(gaps)*1000 if gaps else None,
                    maximum_gap_mm=max(gaps)*1000 if gaps else None,
                    section_X_span_mm=float(np.ptp(after[i, :, 0])*1000)))
            root = values[0]
            assert root['parent_hits'] == 32 and root['maximum_gap_mm'] < -1, (
                name, angle, 'Root not wholly buried beneath actual hair', root)
            meaningful = [v['ring'] for v in values if v['exposed_fraction'] is not None and v['exposed_fraction'] >= .25]
            first = meaningful[0] if meaningful else None
            empty_after = [v['ring'] for v in values if first is not None and v['ring'] > first and v['exposed_fraction'] == 0]
            angles[str(angle)] = dict(sections=values, first_quarter_exposed_ring=first,
                                      fully_hidden_sections_after_first_quarter=empty_after)
            # In obliques another unchanged layer may cover the whole lock;
            # that is occlusion, not a geometric gap. Inspect actual renders.
        result[name] = angles
    return result


def main():
    import bpy
    ns = bpy.app.driver_namespace
    assert KEY not in ns and bpy.context.mode == 'OBJECT'
    assert not (OUT/'apply.json').exists() and not (OUT/'delta.npz').exists(), 'Immutable trial exists'
    rear = ns['MIA_CurvedRear03Base']; assert rear['provisional_keep'] and len(rear['objects']) == 19
    assert 'MIA_HairLockLook01' in ns, 'Preserve the current retained look'
    original_dir = ROOT/'.mia-cache/face-live/curved-rear03'
    actual_dir = original_dir/'actual-emergence'
    cfg = json.loads((original_dir/'candidate.json').read_text(encoding='utf8'))
    capture = json.loads((actual_dir/'capture.json').read_text(encoding='utf8'))
    assert file_sha(original_dir/'curves.npz') == cfg['payload_sha256']
    assert file_sha(actual_dir/'geometry.npz') == capture['geometry_sha256']
    original, actual = np.load(original_dir/'curves.npz'), np.load(actual_dir/'geometry.npz')
    h = helper(); fingerprint = h['fingerprint']
    raw = bpy.data.objects['MIA_V17_PIXAL_DetailedHair']
    actors = list(rear['objects'])+[raw]
    before_fingerprints = {ob.name: fingerprint(ob) for ob in actors}
    before_slots = {ob.name: h['slots'](ob) for ob in actors}
    body = bpy.data.objects['MIA_Review12_H_LiveRepair']
    body_data, body_before = body.data, fingerprint(body)
    look = ns['MIA_HairLockLook01']['material']
    look_signature = h['shader_signature'](look)
    records, proposed = {}, {}
    for suffix in NAMES:
        name = PREFIX+suffix; ob = bpy.data.objects[name]
        assert ob in rear['objects'] and ob.type == 'MESH' and not ob.modifiers and not ob.data.shape_keys
        assert not ob.data.has_custom_normals, 'Do not overwrite authored normals'
        assert np.allclose(np.asarray(ob.matrix_world), np.eye(4), atol=1e-8)
        before = coordinates(ob)
        assert np.array_equal(before, actual[name+'_world']), 'Another geometry edit exists: '+name
        faces = np.asarray([p.vertices[:] for p in ob.data.polygons], np.int32)
        assert np.array_equal(faces, actual[name+'_triangles'])
        after, ids, proof = candidate(before, original[suffix+'_world'], faces)
        records[name] = dict(before=before, after=after, ids=ids, faces=faces, proof=proof)
        proposed[name] = after
    phase = globals().get('MIA_EDIT_PHASE', 'apply')
    assert phase in ('select', 'apply')
    support = {name: rec['proof'] for name, rec in records.items()}
    if phase == 'select':
        OUT.mkdir(parents=True, exist_ok=True)
        report = dict(status='PREPARED_SUPPORT_NOT_APPLIED', targets=support,
                      body_sha256=body_before['coordinates'], ART=False)
        with (OUT/'selection.json').open('x', encoding='utf8') as stream:
            stream.write(json.dumps(report, indent=2)+'\n')
        print(json.dumps(report)); return
    # Measure the proposed whole hair assembly before changing live coordinates.
    parent = overlap(list(records), records, proposed, rear['objects'])
    guard_path = ROOT/'asset/mia/blender/mia-fit-v003/integration/workspace-storage-20261103/storage_guard.py'
    spec = importlib.util.spec_from_file_location('mia_rear_capacity', guard_path)
    guard = importlib.util.module_from_spec(spec); spec.loader.exec_module(guard)
    assert not guard.inspect(4*1024**2)['violations']
    try:
        for name, rec in records.items():
            ob = bpy.data.objects[name]; ob.data.vertices.foreach_set('co', rec['after'].ravel()); ob.data.update()
        bpy.context.view_layer.update()
        after_fingerprints = {ob.name: fingerprint(ob) for ob in actors}
        for name, previous in before_fingerprints.items():
            current = after_fingerprints[name]
            if name in records:
                assert current['coordinates'] == sha(records[name]['after'])
                assert {k:v for k,v in current.items() if k not in ('coordinates', 'corner_normals')} == {
                    k:v for k,v in previous.items() if k not in ('coordinates', 'corner_normals')}
            else:
                assert current == previous, 'Another hair actor changed: '+name
        assert body.data == body_data and fingerprint(body) == body_before
        assert before_slots == {ob.name:h['slots'](ob) for ob in actors}
        assert h['shader_signature'](look) == look_signature
        OUT.mkdir(parents=True, exist_ok=True)
        delta = {}
        for name, rec in records.items():
            delta[name+'_ids'] = rec['ids']; delta[name+'_before'] = rec['before'][rec['ids']]
            delta[name+'_after'] = rec['after'][rec['ids']]
        np.savez_compressed(OUT/'delta.npz', **delta)
        report = dict(status='APPLIED_UNSELECTED_ROOT_EMERGENCE_WIP', targets=support,
            body_sha256=body_before['coordinates'], body_unchanged=True, other_14_hair_actors_exact=True,
            XZ_width_topology_UV_materials_and_authored_normal_inputs_held=True,
            affected_normals='Automatically derived normals legitimately update only with changed geometry',
            before=before_fingerprints, after=after_fingerprints, parent_occlusion=parent,
            delta_sha256=file_sha(OUT/'delta.npz'),
            source_payload_sha256=cfg['payload_sha256'], actual_payload_sha256=capture['geometry_sha256'],
            operation='Original buried root plus quintic arc fade to exact current hanging join',
            limits=['DeepCenter inherited72.6deg bend retained',
                    'CenterTurnRight face normal rotation reaches approximately55.46deg and needs oblique shading review',
                    'Retained-cape-only RAM rays showed small pre-emergence Right peeks; inspect full actual layers',
                    'Inter-layer intentional root overlap is not blanket collision clearance',
                    'Back/oblique ray occlusion is diagnostic, actual paired source renders still required',
                    'Regular S rhythm, widths/tips, Main artifacts, final maps and rig remain unresolved'],
            native_saved=False, ART=False)
        with (OUT/'apply.json').open('x', encoding='utf8') as stream:
            stream.write(json.dumps(report, indent=2)+'\n')
        ns[KEY] = dict(records=records, report=report, before_fingerprints=before_fingerprints,
                       after_fingerprints=after_fingerprints, before_slots=before_slots,
                       actor_names=[ob.name for ob in actors], look=look, look_signature=look_signature)
    except Exception:
        for name, rec in records.items():
            ob = bpy.data.objects[name]; ob.data.vertices.foreach_set('co', rec['before'].ravel()); ob.data.update()
        bpy.context.view_layer.update()
        assert before_fingerprints == {ob.name:fingerprint(ob) for ob in actors}, 'Rollback differs'
        raise
    print(json.dumps(dict(status=report['status'], actors=6,
        changed_vertices=sum(rec['proof']['changed_vertices'] for rec in records.values()),
        body_sha256=body_before['coordinates'], report=str(OUT/'apply.json'), native_saved=False, ART=False)))


if not globals().get('MIA_REAR_ROOT01_LIBRARY_ONLY', False): main()
