"""Read-only actual M1 ownership/occlusion probe; root invokes through live MCP.

Default phase ``probe`` writes one compact immutable packet, without rendering,
camera changes or model edits. Optional ``show``/``restore`` borrows only three
temporary family wire objects for a root-owned screenshot. Original mesh
attributes, groups, UVs, modifiers and coordinates are never written.
"""
from pathlib import Path
import hashlib
import json
import math
import runpy
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'.mia-cache/face-live/live/fringe-probe01'
KEY = 'MIA_FringeProbe01_Overlay'
RAW = 'MIA_V17_PIXAL_DetailedHair'
REMAINING = 'MIA_Hair_CurvedRear03Base_RemainingMain'
BASE_SHA = '16d192576cd8ecc1905f4eba96b4686c038e8c94a56e6eec7dee552e6eee0b2c'
FAMILIES = {
    'screen_left_outer_forelock': [34013, 37707, 39972, 42926, 46927, 35163],
    'screen_left_fine_forelock': [47790, 47982, 48443],
    'screen_left_inner_forelock': [48868, 48535, 41036, 49058, 48600],
}
COLORS = [(0.2, 0.65, 0.95, 1), (1, 0.6, 0.1, 1), (0.8, 0.25, 0.6, 1)]


def sha(value):
    return hashlib.sha256(np.ascontiguousarray(value).tobytes()).hexdigest()


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def triangle_key(q):
    """Exact float32 world triangle key, retaining every coincident owner."""
    q = np.asarray(q, np.float32)
    return np.ascontiguousarray(q[np.lexsort((q[:, 2], q[:, 1], q[:, 0]))]).tobytes()


def ray_triangle(origin, direction, q):
    """Double-sided ray intersection; returns distance, never nearest owner."""
    edge1, edge2 = q[1]-q[0], q[2]-q[0]
    p = np.cross(direction, edge2); determinant = float(edge1@p)
    if abs(determinant) < 1e-15: return None
    t = origin-q[0]; u = float(t@p)/determinant
    cross = np.cross(t, edge1); v = float(direction@cross)/determinant
    distance = float(edge2@cross)/determinant
    if u < -1e-6 or v < -1e-6 or u+v > 1+1e-6 or distance < 0: return None
    return distance


def uv_centerline(world, triangles, loop_uv, maximum=65):
    """Sample actual UV centerline; preserve distinct overlapping surfaces.

    Neither point count nor vertex ordering is assumed. Missing/degenerate UV
    support stays unresolved instead of inventing a 65-section ribbon.
    """
    uv = np.asarray(loop_uv, float).reshape(-1, 3, 2)
    assert len(uv) == len(triangles)
    unique_u = np.unique(np.round(uv[:, :, 0].ravel(), 7))
    indices = np.unique(np.rint(np.linspace(0, len(unique_u)-1, min(maximum, len(unique_u)))).astype(int))
    sample_u = unique_u[indices]
    center_v = float((uv[:, :, 1].min()+uv[:, :, 1].max())/2)
    a, e1, e2 = uv[:, 0], uv[:, 1]-uv[:, 0], uv[:, 2]-uv[:, 0]
    det = e1[:, 0]*e2[:, 1]-e1[:, 1]*e2[:, 0]
    good = abs(det) > 1e-14
    samples = []
    for u in sample_u:
        d = np.array([u, center_v])-a
        b = np.zeros(len(uv)); c = b.copy()
        b[good] = (d[good, 0]*e2[good, 1]-d[good, 1]*e2[good, 0])/det[good]
        c[good] = (e1[good, 0]*d[good, 1]-e1[good, 1]*d[good, 0])/det[good]
        hit = np.flatnonzero(good & (b >= -1e-6) & (c >= -1e-6) & (b+c <= 1+1e-6))
        values = []
        for i in hit:
            q = world[triangles[i]]
            point = q[0]+b[i]*(q[1]-q[0])+c[i]*(q[2]-q[0])
            if not any(np.linalg.norm(point-v) < 1e-5 for v in values): values.append(point)
        samples.append(dict(u=float(u), v=center_v, world_candidates=[v.tolist() for v in values],
                            ambiguous=len(values) > 1, missing=not len(values)))
    return dict(unique_u_count=len(unique_u), sampled_count=len(samples),
                method='Actual evaluated BrowParamUV triangle interpolation, no assumed section count', samples=samples)


def helpers():
    h = runpy.run_path(str(ROOT/'tools/mia/face_surface_live/lock_look01.py'),
                      init_globals={'MIA_LOCK_LOOK01_LIBRARY_ONLY': True})
    sys.path.insert(0, str(ROOT/'asset/mia/blender/mia-fit-v003/body/surface-review12'))
    import review_fixture
    return h, review_fixture


def mesh_world(ob, deps, uv_name=None):
    """Actual evaluated world triangles and optional per-triangle UV corners."""
    ev = ob.evaluated_get(deps); mesh = ev.to_mesh(preserve_all_data_layers=True, depsgraph=deps)
    try:
        mesh.calc_loop_triangles()
        world = np.asarray([ev.matrix_world@v.co for v in mesh.vertices], np.float32)
        faces = np.asarray([t.vertices[:] for t in mesh.loop_triangles], np.int32).reshape(-1, 3)
        loops = np.asarray([t.loops[:] for t in mesh.loop_triangles], np.int32).reshape(-1, 3)
        uv = None
        if uv_name and mesh.uv_layers.get(uv_name):
            layer = mesh.uv_layers[uv_name]
            values = np.empty((len(layer.data), 2), np.float32); layer.data.foreach_get('uv', values.ravel())
            uv = values[loops]
        return world, faces, uv
    finally:
        ev.to_mesh_clear()


def object_context(ob):
    modifiers = []
    for m in ob.modifiers:
        row = dict(name=m.name, type=m.type, show_viewport=bool(m.show_viewport), show_render=bool(m.show_render))
        for key in ('vertex_group', 'node_group', 'object'):
            value = getattr(m, key, None)
            if value is not None: row[key] = value if isinstance(value, str) else value.name
        modifiers.append(row)
    return dict(name=ob.name, data=ob.data.name if ob.data else None,
                data_pointer=int(ob.data.as_pointer()) if ob.data else None,
                object_pointer=int(ob.as_pointer()), matrix=[list(row) for row in ob.matrix_world],
                hide_render=bool(ob.hide_render), hide_get=bool(ob.hide_get()),
                visible_get=bool(ob.visible_get()), modifiers=modifiers,
                materials=[slot.material.name if slot.material else None for slot in ob.material_slots],
                active_shape_keys={k.name:float(k.value) for k in ob.data.shape_keys.key_blocks if abs(k.value) > 1e-8}
                                  if ob.data.shape_keys else {},
                mia_role=ob.get('mia_role', ob.get('MIA_role', '')))


def frozen_support(bpy, h):
    raw, remaining = bpy.data.objects[RAW], bpy.data.objects[REMAINING]
    assert bpy.context.mode == 'OBJECT'
    analysis_path = ROOT/'.mia-cache/face-live/source-audit/analysis.npz'
    components_path = ROOT/'.mia-cache/face-live/source-audit/components.npz'
    with np.load(analysis_path) as data:
        raw_values = data['main_raw']; faces = data['main_triangles']
    with np.load(components_path) as data: face_root = data['face_root']
    fingerprints = {ob.name: h['fingerprint'](ob) for ob in (raw, remaining)}
    assert sha(raw_values) == BASE_SHA
    assert all(row['coordinates'] == BASE_SHA for row in fingerprints.values()), 'Current Main differs from frozen ownership'
    actual_faces = np.asarray([p.vertices[:] for p in raw.data.polygons], np.int32)
    derived_faces = np.asarray([p.vertices[:] for p in remaining.data.polygons], np.int32)
    assert np.array_equal(actual_faces, faces) and np.array_equal(derived_faces, faces)
    assert len(face_root) == len(faces)
    families = {}
    for family, roots in FAMILIES.items():
        face_ids = np.flatnonzero(np.isin(face_root, roots)); point_ids = np.unique(faces[face_ids])
        families[family] = dict(component_roots=roots, faces=face_ids, points=point_ids)
    points = np.unique(np.concatenate([r['points'] for r in families.values()]))
    selected_faces = np.unique(np.concatenate([r['faces'] for r in families.values()]))
    assert len(points) == 741 and len(selected_faces) == 951
    return raw, remaining, faces, face_root, families, fingerprints, dict(
        analysis_sha256=file_sha(analysis_path), components_sha256=file_sha(components_path),
        raw_coordinate_sha256=BASE_SHA, points=741, faces=951, roots=14)


def render_objects(layer):
    """At least one active-layer, render-enabled collection path."""
    names = set()
    def walk(item, allowed):
        allowed = allowed and not item.exclude and not item.collection.hide_render
        if allowed: names.update(ob.name for ob in item.collection.objects if not ob.hide_render)
        for child in item.children: walk(child, allowed)
    walk(layer.layer_collection, True)
    return names


def hit_stack(tree, q, origin, direction, stop):
    """Depth clusters include nearby/coincident triangles, never one chosen owner."""
    from mathutils import Vector
    cursor = 0.; result = []; maximum = 48
    for _ in range(maximum):
        loc, normal, index, distance = tree.ray_cast(Vector(origin+cursor*direction), Vector(direction), stop-cursor)
        if index is None: break
        total = cursor+float(distance); candidates = {int(index)}
        candidates.update(int(item[2]) for item in tree.find_nearest_range(loc, 5e-5))
        coincident = []
        for face in candidates:
            t = ray_triangle(origin, direction, q[face])
            if t is not None and abs(t-total) <= 5e-5: coincident.append((face, t))
        if not coincident: coincident = [(int(index), total)]
        result.append(dict(distance=total, triangle_hits=sorted(coincident)))
        cursor = max(t for _, t in coincident)+1e-5
        if cursor >= stop: break
    return result, len(result) == maximum


def probe():
    import bpy
    from mathutils.bvhtree import BVHTree
    assert not (OUT/'probe.json').exists(), 'Immutable probe exists'
    assert 'MIA_HairReviewState' in bpy.app.driver_namespace, 'Root must enter actual hair visibility first'
    h, fixture = helpers()
    raw, remaining, source_faces, face_root, families, frozen, source = frozen_support(bpy, h)
    assert raw.hide_render and not remaining.hide_render
    scene = bpy.context.scene; deps = bpy.context.evaluated_depsgraph_get()
    body = bpy.data.objects['MIA_Review12_H_LiveRepair']
    body_before = h['fingerprint'](body)
    brow_objects = [ob for ob in scene.objects if ob.type == 'MESH' and
                    ('brow' in ob.name.lower() or 'brow' in str(ob.get('mia_role', '')).lower())]
    brow_inventory = [object_context(ob) for ob in brow_objects]
    visible = render_objects(bpy.context.view_layer)
    # Known SourceBrow names are preferred only after discovering actual UVs.
    brows = [ob for ob in brow_objects if ob.name.startswith('V31_SourceBrow_') and ob.name in visible]
    if not brows:
        brows = [ob for ob in brow_objects if ob.name in visible and ('sourcebrow' in ob.name.lower() or 'eyebrow' in ob.name.lower())
                 and not any(t in ob.name.lower() for t in ('ink', 'display', 'overlay', 'projection'))]
    curves = {}; gaps = []
    for ob in brows:
        world, triangles, uv = mesh_world(ob, deps, 'BrowParamUV')
        if uv is None:
            gaps.append(ob.name+': no verified BrowParamUV; no curve invented'); continue
        curves[ob.name] = uv_centerline(world, triangles, uv)
    if not curves: gaps.append('No verified actual brow UV centerline')
    hair = [ob for ob in fixture.hair_actors(scene) if ob.name in visible]
    inventory = [object_context(ob) for ob in hair]
    if any(ob.instance_type != 'NONE' for ob in hair):
        gaps.append('A hair actor instances other geometry; this object-mesh probe does not expand separate object instances')
    watched = {ob.name: h['fingerprint'](ob) for ob in set(hair+brow_objects+[raw, remaining])}
    contexts = {ob.name: object_context(ob) for ob in set(hair+brow_objects+[raw, remaining])}
    raw_world, raw_triangles, _ = mesh_world(raw, deps)
    topology_verified = np.array_equal(raw_triangles, source_faces)
    source_lookup = {}
    if topology_verified:
        for i, tri in enumerate(raw_world[raw_triangles]):
            source_lookup.setdefault(triangle_key(tri), []).append(i)
    else: gaps.append('Evaluated raw Main topology differs; Main hit ownership left unresolved')
    root_to_family = {r: name for name, values in FAMILIES.items() for r in values}
    trees = []
    for ob in hair:
        world, triangles, _ = mesh_world(ob, deps)
        if not len(triangles): continue
        q = world[triangles].astype(float)
        trees.append((ob.name, BVHTree.FromPolygons(world.tolist(), triangles.tolist(), all_triangles=True), q,
                      q.min((0, 1)), q.max((0, 1))))
    packet_path = ROOT/'.mia-cache/face-live/fringe-resume01/capture-v2.json'
    packet = json.loads(packet_path.read_text())
    front = next(row['fixture'] for row in packet['frames'] if row['view'] == 'front')
    assert fixture.digest(fixture.pose(scene)) == front['pose_sha256'], 'Pose changed since actual front capture'
    matrix = np.asarray(front['camera_matrix'], float)
    target = np.asarray(front['target_world'], float)
    views = []
    for yaw in (0, -35, 35):
        a = math.radians(yaw); r = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
        m = matrix.copy(); m[:3, :3] = r@matrix[:3, :3]; m[:3, 3] = target+r@(matrix[:3, 3]-target)
        direction = -m[:3, 2]; direction /= np.linalg.norm(direction)
        views.append((yaw, m, direction))
    registry = {}; entries = []; samples = []
    def register(name, face, tri):
        key = (name, int(face))
        if key in registry: return registry[key]
        owners = source_lookup.get(triangle_key(tri), []) if name in (RAW, REMAINING) else []
        value = dict(actor=name, evaluated_triangle=int(face), source_faces=owners,
                     owners=[dict(source_face=int(i), component_root=int(face_root[i]),
                                  family=root_to_family.get(int(face_root[i]), 'other_Main_component')) for i in owners],
                     ownership='exact_world_triangle_all_coincident_sources' if owners else
                               ('unresolved_Main_triangle' if name in (RAW, REMAINING) else 'actor_only'),
                     ambiguous_sources=len(owners) > 1)
        index = len(entries); entries.append(value); registry[key] = index; return index
    for yaw, m, direction in views:
        for name, curve in curves.items():
            for index, sample in enumerate(curve['samples']):
                for variant, point in enumerate(sample['world_candidates']):
                    point = np.asarray(point, float); origin = point-direction*2.; hit_rows = []; truncated = []
                    for actor, tree, q, lower, upper in trees:
                        # Conservative finite-segment box rejection only.
                        if np.any(np.maximum(origin, point) < lower) or np.any(np.minimum(origin, point) > upper): continue
                        hits, limited = hit_stack(tree, q, origin, direction, 2.-2e-5)
                        if limited: truncated.append(actor)
                        for hit in hits:
                            hit_rows.append(dict(distance_m=hit['distance'], before_brow_mm=(2.-hit['distance'])*1000,
                                cluster_triangles=[register(actor, face, q[face]) for face, _ in hit['triangle_hits']]))
                    hit_rows.sort(key=lambda value: value['distance_m'])
                    samples.append(dict(yaw_offset=yaw, brow=name, sample=index, variant=variant, hits=hit_rows,
                                        truncated_actors=truncated, clear_of_queried_hair=not hit_rows))
    assert body_before == h['fingerprint'](body)
    assert watched == {name: h['fingerprint'](bpy.data.objects[name]) for name in watched}
    assert contexts == {name: object_context(bpy.data.objects[name]) for name in contexts}
    assert frozen == {name: h['fingerprint'](bpy.data.objects[name]) for name in frozen}
    report = dict(status='ACTUAL_READ_ONLY_M1_PROBE_NOT_ART', source=source,
        selected_families={name: dict(roots=row['component_roots'], points=len(row['points']), faces=len(row['faces'])) for name, row in families.items()},
        main_contexts={name:contexts[name] for name in (RAW, REMAINING)}, main_fingerprints=frozen,
        source_evaluated_topology_verified=topology_verified, body_sha256=body_before['coordinates'],
        brow_inventory=brow_inventory, current_evaluated_brow_curves=curves,
        pose=fixture.pose(scene), frame=scene.frame_current,
        curve_pose_limit='Actual current frame/pose only; no pose reset or automatic neutral/expressive validation',
        hair_inventory=inventory, camera_source=str(packet_path.relative_to(ROOT)), camera_source_sha256=file_sha(packet_path),
        ray_views=[dict(yaw_offset=yaw, matrix=m.tolist(), kind='actual frozen front' if yaw == 0 else 'virtual world-Z probe offset, not an actual render or recovered drawing camera') for yaw, m, _ in views],
        triangle_registry=entries, ray_samples=samples, evidence_gaps=gaps,
        limits=['Hair-classified actual render-visible geometry union; name/material classifier is conservatively inventoried',
                'Hair geometry rays do not evaluate alpha/textures, graphic brow ink, head/skin self-occlusion, or final pixels',
                'Near-coincident hits within0.05mm retain multiple triangles; no nearest-owner semantic invention',
                'Actual drawing registration and expressions remain unverified; source images untouched'],
        geometry_UV_normals_material_fingerprints_held=True,
        object_pointers_visibility_modifiers_contexts_held=True,
        original_groups_attributes_not_written=True, camera_changed=False,
        native_saved=False, rendered=False, ART=False)
    text = json.dumps(report, separators=(',', ':'))+'\n'
    assert len(text.encode('utf8')) < 5*1024**2, 'Probe exceeds bounded output; do not write partial success'
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT/'probe.json').open('x', encoding='utf8') as stream: stream.write(text)
    print(json.dumps(dict(status=report['status'], curves=len(curves), samples=len(samples),
        hair_actors=len(hair), registry_triangles=len(entries), evidence_gaps=gaps, report=str(OUT/'probe.json'),
        model_unchanged=True, native_saved=False, ART=False)))


def overlay(phase):
    import bpy
    ns = bpy.app.driver_namespace
    h, _ = helpers()
    if phase == 'show':
        assert KEY not in ns and 'MIA_HairReviewState' in ns
        raw, remaining, faces, face_root, families, fingerprints, source = frozen_support(bpy, h)
        deps = bpy.context.evaluated_depsgraph_get()
        world, evaluated_faces, _ = mesh_world(raw, deps)
        assert np.array_equal(evaluated_faces, faces), 'Cannot invent evaluated overlay point correspondence'
        actual_world, actual_faces, _ = mesh_world(remaining, deps)
        selected_faces = np.concatenate([row['faces'] for row in families.values()])
        required_keys = {triangle_key(tri) for tri in world[faces[selected_faces]]}
        actual_keys = {triangle_key(tri) for tri in actual_world[actual_faces]}
        assert required_keys <= actual_keys, 'A selected frontal source face is absent/deformed in actual RemainingMain'
        state = dict(objects=[], meshes=[], selected=[ob.name for ob in bpy.context.selected_objects],
                     active=bpy.context.view_layer.objects.active, viewports=[], fingerprints=fingerprints)
        try:
            for ob in bpy.context.selected_objects: ob.select_set(False)
            for color, (name, row) in zip(COLORS, families.items()):
                ids = row['points']; inverse = np.full(len(raw.data.vertices), -1, np.int32); inverse[ids] = np.arange(len(ids))
                values = world[ids].tolist()
                mesh = bpy.data.meshes.new('MIA_TMP_FringeProbe01_'+name); state['meshes'].append(mesh)
                mesh.from_pydata(values, [], inverse[faces[row['faces']]].tolist()); mesh.update()
                ob = bpy.data.objects.new(mesh.name, mesh); state['objects'].append(ob); ob['mia_probe_owner'] = KEY
                bpy.context.scene.collection.objects.link(ob)
                ob.color = color; ob.display_type = 'WIRE'
                ob.show_in_front = True; ob.hide_render = True
            for screen in bpy.data.screens:
                for area in screen.areas:
                    if area.type != 'VIEW_3D': continue
                    space = area.spaces.active
                    state['viewports'].append((space, space.overlay.show_overlays,
                        getattr(space.shading, 'wireframe_color_type', None)))
                    space.overlay.show_overlays = True
                    if hasattr(space.shading, 'wireframe_color_type'): space.shading.wireframe_color_type = 'OBJECT'
            assert fingerprints == {name:h['fingerprint'](bpy.data.objects[name]) for name in fingerprints}
            ns[KEY] = state
        except Exception:
            remove_overlay(bpy, state)
            raise
        print(json.dumps(dict(status='TEMPORARY_FAMILY_WIRE_ONLY', actors=3, points=741, faces=951,
                              next='Root screenshot then explicit restore', geometry_modified=False, ART=False)))
    else:
        state = ns[KEY]
        assert state['fingerprints'] == {name:h['fingerprint'](bpy.data.objects[name]) for name in state['fingerprints']}
        remove_overlay(bpy, state); del ns[KEY]
        print(json.dumps(dict(status='OWNED_FAMILY_WIRES_REMOVED', original_meshes_exact=True, native_saved=False)))


def remove_overlay(bpy, state):
    for ob in state['objects']:
        assert ob.get('mia_probe_owner') == KEY
        bpy.data.objects.remove(ob, do_unlink=True)
    for mesh in state['meshes']:
        if mesh.users == 0: bpy.data.meshes.remove(mesh)
    for ob in bpy.context.selected_objects: ob.select_set(False)
    for name in state['selected']:
        ob = bpy.data.objects.get(name)
        if ob: ob.select_set(True)
    bpy.context.view_layer.objects.active = state['active']
    for space, overlays, wire_color in state['viewports']:
        space.overlay.show_overlays = overlays
        if wire_color is not None: space.shading.wireframe_color_type = wire_color


if not globals().get('MIA_FRINGE_PROBE01_LIBRARY_ONLY', False):
    phase = globals().get('MIA_FRINGE_PROBE_PHASE', 'probe')
    assert phase in ('probe', 'show', 'restore')
    probe() if phase == 'probe' else overlay(phase)
