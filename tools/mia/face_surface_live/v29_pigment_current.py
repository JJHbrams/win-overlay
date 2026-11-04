"""Bounded, reversible v29 STATIC pigment replay on RemainingMain only.

Library import is inert. Root's live MCP may call inspect(root), then
apply(expected_body_sha256, root). For runpy, explicitly pass
MIA_V29_PIGMENT_PHASE='apply' and MIA_EXPECT_BODY_SHA256. This never runs the
legacy raw-Main helper, renders, saves a native, or promotes ART. Call restore()
before restoring older rear-root/look stages. Keep the namespace until review.
"""
from pathlib import Path
import hashlib
import json
import runpy

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
TARGET = 'MIA_Hair_CurvedRear03Base_RemainingMain'
RAW = 'MIA_V17_PIXAL_DetailedHair'
BODY = 'MIA_Review12_H_LiveRepair'
KEY = 'MIA_V29PigmentCurrent'
UV = 'MIA_v003_RecoveredCrown_UV'
MATERIAL = 'MIA_v003_CurrentRemainingMain_StaticPigment_WIP'
COORDS = '16d192576cd8ecc1905f4eba96b4686c038e8c94a56e6eec7dee552e6eee0b2c'
SELECTED_SHA = 'c4bbb08a5983a01f561e97a2003452543d6f7e65360b16dc73db06bb5a951f82'
NATIVE_SHA = '0d62eff09b4e95809a9f852d3e68654c1bb5a9e35fe70c065a939bc433e017ed'


def digest(value):
    return hashlib.sha256(np.ascontiguousarray(value).tobytes()).hexdigest()


def file_sha(path):
    sha = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(4*1024*1024): sha.update(block)
    return sha.hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def package(root):
    """Read-only offline validation; no bpy import and no legacy execution."""
    folder = Path(root)/'asset/mia/blender/mia-fit-v003/hair'
    selected = folder/'SELECTED_CHECKPOINT.json'
    assert file_sha(selected) == SELECTED_SHA, 'Selected legacy package changed'
    manifest = json.loads(selected.read_text(encoding='utf8'))
    assert manifest['status'] == 'PROVISIONAL_PRODUCER_COLOR_CHECKPOINT_NOT_HAIR_ART_PASS'
    assert len(manifest['runtime_files']) == 7
    for name, row in manifest['runtime_files'].items():
        path = folder/name
        assert path.resolve().is_relative_to(folder.resolve())
        assert path.stat().st_size == row['bytes'] and file_sha(path) == row['sha256'], name
    folder /= 'v29-pigment'
    base = json.loads((folder/'current-UV-boundary-report.json').read_text())
    baked = json.loads((folder/'baked-report.json').read_text())
    rear = json.loads((folder/'rear-guide-report.json').read_text())
    assert base['current_coords_sha256'] == COORDS and len(base['original_six_UV_hashes']) == 6
    assert baked['new_unique_UV_overlap_pairs'] == 0 and rear['front_protected_face_rows'] == 2651
    assert baked['payload_sha256'] == rear['payload_sha256'] == file_sha(folder/'fallback-baked-payload.npz')
    with np.load(folder/'fallback-baked-payload.npz', allow_pickle=False) as archive:
        data = {name: archive[name].copy() for name in archive.files}
    assert set(data) == {'polygon_indices', 'raw_source_ids', 'raw_vertices', 'loop_uv'}
    assert data['polygon_indices'].shape == data['raw_source_ids'].shape == (4999,)
    assert data['raw_vertices'].shape == (4999, 3) and data['loop_uv'].shape == (4999, 3, 2)
    assert all(data[name].dtype == np.int32 for name in ('polygon_indices', 'raw_source_ids', 'raw_vertices'))
    assert data['loop_uv'].dtype == np.float32 and np.isfinite(data['loop_uv']).all()
    assert len(np.unique(data['polygon_indices'])) == len(np.unique(data['raw_source_ids'])) == 4999
    assert data['polygon_indices'].min() >= 0 and data['polygon_indices'].max() < 120915
    # baked.target_UV_sha256 hashes the old proxy NPZ, not this UV array.
    assert digest(data['loop_uv']) == '07db5e7c4f9218bf64c723b1a56d50f065de8a74429a55312e617335267f8921'
    return folder, manifest, base, data


def _bpy():
    import bpy
    return bpy


def _value(value):
    bpy = _bpy()
    if isinstance(value, bpy.types.ID): return (value.bl_rna.identifier, value.name, value.as_pointer())
    if isinstance(value, (str, bool, int, float)) or value is None: return value
    if isinstance(value, set): return sorted(value)
    try: return [_value(item) for item in value]
    except TypeError: return str(value)


def _rna(owner):
    result = {}
    for prop in owner.bl_rna.properties:
        key = prop.identifier
        # Users/GPU/preview/update bookkeeping changes on copying or rendering;
        # it is not a shader operation and must not block a later exact restore.
        if key in {'rna_type', 'users', 'tag', 'preview', 'bindcode', 'pixels',
                   'dimensions', 'location', 'location_absolute', 'width', 'height',
                   'is_updated', 'is_updated_data', 'is_updated_geometry'} or prop.type == 'COLLECTION': continue
        # Image pixels are not expanded into Python floats/JSON. Packed bytes,
        # image identity/space/dirty state are hashed below. UI layout is not shading.
        try: result[key] = _value(getattr(owner, key))
        except (AttributeError, TypeError, ValueError, RuntimeError): continue
    return result


def graph_signature(tree, visited=None, image_cache=None):
    """Full source graph, image identity/content, nested groups and defaults."""
    visited = set() if visited is None else visited
    image_cache = {} if image_cache is None else image_cache
    if tree is None: return None
    if tree.as_pointer() in visited: return tree.as_pointer()
    visited.add(tree.as_pointer())
    nodes = []
    for node in sorted(tree.nodes, key=lambda item: item.name):
        row = dict(rna=_rna(node), inputs=[_rna(s) for s in node.inputs], outputs=[_rna(s) for s in node.outputs])
        if hasattr(node, 'color_ramp'):
            row['ramp'] = dict(rna=_rna(node.color_ramp), points=[_rna(e) for e in node.color_ramp.elements])
        if getattr(node, 'node_tree', None): row['group'] = graph_signature(node.node_tree, visited, image_cache)
        image = getattr(node, 'image', None)
        if image:
            if image.as_pointer() not in image_cache:
                image_cache[image.as_pointer()] = dict(rna=_rna(image), colorspace=_rna(image.colorspace_settings),
                    packed=[hashlib.sha256(p.packed_file.data).hexdigest() for p in image.packed_files])
            row['image'] = image_cache[image.as_pointer()]
        nodes.append(row)
    links = sorted((x.from_node.name, x.from_socket.identifier, x.to_node.name,
                    x.to_socket.identifier, x.is_muted) for x in tree.links)
    return hashlib.sha256(canonical(dict(nodes=nodes, links=links)).encode()).hexdigest()


def materials_signature():
    cache = {}
    return {m.name: dict(pointer=m.as_pointer(), graph=graph_signature(m.node_tree, image_cache=cache), rna=_rna(m))
            for m in _bpy().data.materials}


def _uv_state(mesh):
    return dict(active=mesh.uv_layers.active_index,
                layers=[(u.name, bool(u.active_render), bool(u.active_clone)) for u in mesh.uv_layers])


def _slots(ob):
    return [(s.link, s.material.as_pointer() if s.material else None) for s in ob.material_slots]


def _helpers(root):
    return runpy.run_path(str(Path(root)/'tools/mia/face_surface_live/lock_look01.py'),
                         init_globals={'MIA_LOCK_LOOK01_LIBRARY_ONLY': True})


def evaluated_geometry(ob):
    bpy = _bpy(); depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = ob.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
    try:
        co = np.empty((len(mesh.vertices), 3), np.float32); mesh.vertices.foreach_get('co', co.ravel())
        vi = np.empty(len(mesh.loops), np.int32); mesh.loops.foreach_get('vertex_index', vi)
        starts = np.empty(len(mesh.polygons), np.int32); mesh.polygons.foreach_get('loop_start', starts)
        totals = np.empty(len(mesh.polygons), np.int32); mesh.polygons.foreach_get('loop_total', totals)
        normals = np.empty((len(mesh.corner_normals), 3), np.float32)
        mesh.corner_normals.foreach_get('vector', normals.ravel())
        source = mesh.attributes.get('MIA_SOURCE_POLYGON')
        assert source and source.domain == 'FACE' and source.data_type == 'INT'
        ids = np.empty(len(mesh.polygons), np.int32); source.data.foreach_get('value', ids)
        return dict(coordinates=digest(co), topology=digest(np.r_[vi, starts, totals]),
                    corner_normals=digest(normals), source_ids=digest(ids), polygons=len(ids)), ids
    finally: evaluated.to_mesh_clear()


def _validate_mesh(ob, base, data, helper):
    mesh = ob.data; fp = helper['fingerprint'](ob)
    assert fp['coordinates'] == COORDS and len(mesh.polygons) == 120915
    assert fp['UV'] == base['original_six_UV_hashes'], 'Exactly the original six UVs are required'
    assert UV not in mesh.uv_layers and len(mesh.materials) == 2
    assert all(p.material_index == 0 for p in mesh.polygons)
    ids = data['polygon_indices']
    assert np.array_equal(np.asarray([mesh.polygons[int(i)].vertices[:] for i in ids]), data['raw_vertices'])
    source = mesh.attributes.get('MIA_SOURCE_POLYGON')
    assert source and source.domain == 'FACE' and source.data_type == 'INT'
    assert np.array_equal(np.asarray([source.data[int(i)].value for i in ids]), data['raw_source_ids'])
    scope = mesh.attributes.get('MIA_R_SourceAshAndScope')
    assert scope and scope.domain == 'POINT'
    assert all(scope.data[int(i)].color[3] == 0 for i in np.unique(data['raw_vertices']))
    return fp


def inspect(root=ROOT, expected_body_sha256=None):
    """Fail closed before allocating or assigning anything in Blender."""
    bpy = _bpy(); root = Path(root).resolve(); folder, manifest, base, data = package(root)
    assert bpy.context.mode == 'OBJECT' and bpy.context.scene.render.engine == 'BLENDER_EEVEE'
    assert KEY not in bpy.app.driver_namespace
    current = json.loads((root/'asset/mia/CURRENT_STATE.json').read_text(encoding='utf8'))['active_live_checkpoint']
    native = (root/current['path']).resolve()
    assert current['sha256'] == NATIVE_SHA and Path(bpy.data.filepath).resolve() == native
    assert file_sha(native) == NATIVE_SHA
    target, raw = bpy.data.objects[TARGET], bpy.data.objects[RAW]
    assert target.type == raw.type == 'MESH' and target != raw and target.data != raw.data
    owners = sorted(o.name for o in bpy.data.objects if o.type == 'MESH' and o.data == target.data)
    assert owners == [TARGET] and target.data.users == 1, 'Unexpected shared RemainingMain data ownership'
    assert raw.hide_render and not target.hide_render
    helper = _helpers(root)
    before = _validate_mesh(target, base, data, helper)
    _validate_mesh(raw, base, data, helper)
    assert before['topology'] == helper['fingerprint'](raw)['topology']
    slots = list(target.material_slots)
    assert len(slots) == 2 and slots[0].material.name == 'MIA_v002_R_SideNape_SourceAshEnvelope'
    assert slots[0].material.node_tree.get_output_node('EEVEE') is not None
    assert slots[0].material.node_tree.nodes.get('V002_COHERENT_AUTHORED_PIGMENT')
    assert slots[0].material.node_tree.nodes.get('V002_SOURCE_ASH_GRADE_INPUT')
    rear = bpy.app.driver_namespace['MIA_CurvedRear03Base']
    actors = list(rear['objects']); assert len(actors) == 19 and target in actors
    assert len({ob.as_pointer() for ob in actors}) == 19
    body_sha = helper['array_sha'](helper['coordinates'](bpy.data.objects[BODY]))
    if expected_body_sha256 is not None: assert body_sha == expected_body_sha256, 'Body state changed'
    geometry, retained = evaluated_geometry(target)
    count = int(np.isin(retained, data['raw_source_ids']).sum())
    assert 0 < count <= 4999 and len(np.unique(retained)) == len(retained)
    return dict(target=TARGET, owners=owners, native=str(native), native_sha256=NATIVE_SHA,
                body_sha256=body_sha, raw_input_faces=120915, selected_input_faces=4999,
                selected_retained_faces=count, selected_deleted_faces=4999-count,
                evaluated_geometry=geometry, original_fingerprint=before,
                original_UV_flags=_uv_state(target.data), mode='combined', new_paint=False,
                ART=False, native_saved=False, shader_compilation='NOT TESTED: actual EEVEE render required')


def _active_nodes(material):
    output = material.node_tree.get_output_node('EEVEE'); assert output
    found, stack = set(), [output]
    while stack:
        node = stack.pop()
        if node in found: continue
        found.add(node)
        stack.extend(link.from_node for socket in node.inputs for link in socket.links)
    return found


def _build_material(original, folder, state):
    """Exact selected combined pigment branch; current light/normal path held."""
    bpy = _bpy(); material = original.copy(); material.name = MATERIAL
    state['material'] = material  # Cleanup owns this even if a later guard fails.
    nodes, links = material.node_tree.nodes, material.node_tree.links
    mix = nodes['V002_COHERENT_AUTHORED_PIGMENT']; grade = nodes['V002_SOURCE_ASH_GRADE_INPUT']
    assert not mix.inputs[1].is_linked
    fallback = list(mix.inputs[1].default_value)
    assert np.allclose(fallback, (.12, .115, .12, 1), rtol=0, atol=1e-8)
    links.new(mix.outputs['Color'], grade.inputs[0])
    uv = nodes.new('ShaderNodeUVMap'); uv.name = 'V003_RECOVERED_CROWN_UNIQUE_UV'; uv.uv_map = UV
    textures = []
    for filename, name in [('RecoveredStaticCrown_4096_RGBA.png', 'V003_STATIC_COLOR_AND_BOUNDARY_GATE'),
                            ('RecoveredRearCrown_4096_RGBA.png', 'V003_REAR_OVERRIDE_GATE')]:
        image = bpy.data.images.load(str(folder/filename), check_existing=False); state['images'].append(image)
        image.colorspace_settings.name = 'sRGB'; image.alpha_mode = 'CHANNEL_PACKED'
        assert tuple(image.size) == (4096, 4096)
        image.pack()
        tex = nodes.new('ShaderNodeTexImage'); tex.name = name; tex.image = image
        tex.interpolation = 'Linear'; tex.extension = 'CLIP'; links.new(uv.outputs[0], tex.inputs['Vector'])
        textures.append(tex)
    tex, gate = textures
    blend = nodes.new('ShaderNodeMixRGB'); blend.name = 'V003_EXISTING_PAINT_IN_OLD_FALLBACK_ONLY'
    blend.inputs[1].default_value = fallback
    links.new(tex.outputs['Alpha'], blend.inputs[0]); links.new(tex.outputs['Color'], blend.inputs[2])
    links.new(blend.outputs[0], mix.inputs[1])
    over = nodes.new('ShaderNodeMixRGB'); over.name = 'V003_REAR_GUIDE_ART_OVER_FALLBACK_BASE'
    links.new(gate.outputs['Alpha'], over.inputs[0]); links.new(mix.outputs['Color'], over.inputs[1])
    links.new(tex.outputs['Color'], over.inputs[2]); links.new(over.outputs[0], grade.inputs[0])
    active = _active_nodes(material)
    for node in list(nodes):
        if node not in active: nodes.remove(node)
    attrs = {n.attribute_name for n in nodes if n.type == 'ATTRIBUTE'}
    uvs = {n.uv_map for n in nodes if n.type == 'UVMAP'}
    assert len(attrs) == 9 and len(uvs) == 5 and UV in uvs
    assert not any(n.type == 'NORMAL_MAP' for n in nodes)
    return material


def _watched(root):
    bpy = _bpy(); helper = _helpers(root)
    actors = list(bpy.app.driver_namespace['MIA_CurvedRear03Base']['objects'])
    objects = {o.name:o for o in actors+[bpy.data.objects[RAW], bpy.data.objects[BODY]]}
    return helper, objects


def _snapshot(root):
    helper, objects = _watched(root)
    return {name: dict(data=ob.data.as_pointer(), fingerprint=helper['fingerprint'](ob), slots=_slots(ob))
            for name, ob in objects.items()}


def _modifiers(ob):
    return [dict(rna=_rna(m), group=graph_signature(getattr(m, 'node_group', None))) for m in ob.modifiers]


def _mesh_payload(mesh):
    """Copied attributes, deformation keys and weights, beyond six UV hashes."""
    fields = {'FLOAT': ('value', 1, np.float32), 'INT': ('value', 1, np.int32),
              'INT8': ('value', 1, np.int32), 'BOOLEAN': ('value', 1, np.int32),
              'FLOAT_VECTOR': ('vector', 3, np.float32), 'FLOAT2': ('vector', 2, np.float32),
              'FLOAT_COLOR': ('color', 4, np.float32), 'BYTE_COLOR': ('color', 4, np.float32),
              'INT16_2D': ('value', 2, np.int32), 'INT32_2D': ('value', 2, np.int32),
              'QUATERNION': ('value', 4, np.float32)}
    attrs = {}
    for attr in mesh.attributes:
        assert attr.data_type in fields, 'Unsupported attribute; inspect before copying: '+attr.name
        field, size, dtype = fields[attr.data_type]
        values = np.empty((len(attr.data), size), dtype); attr.data.foreach_get(field, values.ravel())
        if attr.data_type == 'INT16_2D':
            # Actual Blender 5.2 custom_normal RNA: Short2AttributeValue.value
            # is INT[2]. Read integers into the standard RNA int buffer, range
            # check, then hash their exact signed-short encoding, never vectors.
            assert np.all((values >= -32768) & (values <= 32767)), attr.name
            values = values.astype(np.int16)
        attrs[attr.name] = (attr.domain, attr.data_type, digest(values))
    keys = {}
    if mesh.shape_keys:
        for key in mesh.shape_keys.key_blocks:
            values = np.empty((len(key.data), 3), np.float32); key.data.foreach_get('co', values.ravel())
            keys[key.name] = (digest(values), key.relative_key.name, key.value, key.mute)
    weights = np.asarray([(v.index, g.group, g.weight) for v in mesh.vertices for g in v.groups], np.float64)
    return dict(attributes=attrs, keys=keys, weights=digest(weights))


def _receipt(root, phase, report):
    from datetime import datetime, timezone
    out = Path(root)/'.mia-cache/face-live/live/v29-pigment-current'
    out.mkdir(parents=True, exist_ok=True)
    path = out/(phase+'-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json')
    with path.open('x', encoding='utf8') as stream: stream.write(json.dumps(report, indent=2)+'\n')
    return str(path)


def _ownership(state):
    """Bookkeeping excluded from graph hashes is an explicit restore guard."""
    bpy = _bpy(); mesh, material = state['owned_data'], state['material']
    return dict(mesh_users=mesh.users, mesh_objects=sorted(o.name for o in bpy.data.objects
                    if o.type == 'MESH' and o.data == mesh), material_users=material.users,
                material_slots=sorted((o.name, i) for o in bpy.data.objects
                    for i,s in enumerate(o.material_slots) if s.material == material),
                image_users=[(image.as_pointer(), image.users) for image in state['images']])


def apply(expected_body_sha256, root=ROOT):
    """One in-RAM mesh copy, one copied material, two immutable baked images."""
    bpy = _bpy(); root = Path(root).resolve()
    assert isinstance(expected_body_sha256, str) and len(expected_body_sha256) == 64
    report = inspect(root, expected_body_sha256)
    folder, _, base, data = package(root)
    assert bpy.data.materials.get(MATERIAL) is None
    target = bpy.data.objects[TARGET]; old_data = target.data
    before, graphs, modifiers = _snapshot(root), materials_signature(), _modifiers(target)
    payload = _mesh_payload(old_data)
    original_slots = [(s.link, s.material) for s in target.material_slots]
    state = dict(root=str(root), original_data=old_data, original_slots=original_slots,
                 before=before, original_graphs=graphs, modifiers=modifiers,
                 original_payload=payload,
                 native=report['native'], native_sha256=NATIVE_SHA, body_sha256=expected_body_sha256,
                 images=[], material=None, owned_data=None, report=report)
    try:
        mesh = old_data.copy(); state['owned_data'] = mesh  # The only Mesh.copy.
        mesh.name = 'MIA_RemainingMain_V29StaticPigment_RAM_WIP'
        uv = np.zeros((len(mesh.loops), 2), np.float32)
        loops = np.asarray([mesh.polygons[int(i)].loop_indices[:] for i in data['polygon_indices']], np.int32)
        uv[loops.ravel()] = data['loop_uv'].reshape(-1, 2)
        layer = mesh.uv_layers.new(name=UV); layer.data.foreach_set('uv', uv.ravel())
        layer.active_render = layer.active_clone = False
        flags = report['original_UV_flags']
        for name, render, clone in flags['layers']:
            mesh.uv_layers[name].active_render = render; mesh.uv_layers[name].active_clone = clone
        mesh.uv_layers.active_index = flags['active']
        material = _build_material(original_slots[0][1], folder, state)
        mesh.materials.append(material)
        for i in data['polygon_indices']: mesh.polygons[int(i)].material_index = len(mesh.materials)-1
        target.data = mesh
        # Existing bindings and material datablocks are never edited.
        assert _slots(target)[:2] == before[TARGET]['slots']
        slot = target.material_slots[-1]; slot.link = 'OBJECT'; slot.material = material
        bpy.context.view_layer.update()
        after = _snapshot(root); fp = after[TARGET]['fingerprint']; old = before[TARGET]['fingerprint']
        assert {k:v for k,v in fp.items() if k not in ('UV', 'face_material_indices')} == {
            k:v for k,v in old.items() if k not in ('UV', 'face_material_indices')}
        assert {name:fp['UV'][name] for name in base['original_six_UV_hashes']} == base['original_six_UV_hashes']
        assert len(fp['UV']) == 7 and _uv_state(mesh)['layers'][:6] == flags['layers']
        assert fp['UV'][UV] == digest(uv)
        copied = _mesh_payload(mesh); copied['attributes'].pop(UV)
        # Material indices are an explicitly changed built-in FACE attribute.
        copied['attributes'].pop('material_index', None)
        immutable = dict(payload, attributes=dict(payload['attributes']))
        immutable['attributes'].pop('material_index', None)
        assert copied == immutable, 'Copied attributes, keys or vertex weights changed'
        expected_indices = np.zeros(len(mesh.polygons), np.int32)
        expected_indices[data['polygon_indices']] = len(mesh.materials)-1
        assert fp['face_material_indices'] == digest(expected_indices)
        assert _modifiers(target) == modifiers
        evaluated, retained = evaluated_geometry(target)
        assert evaluated == report['evaluated_geometry'], 'Evaluated geometry/normals/delete result changed'
        assert int(np.isin(retained, data['raw_source_ids']).sum()) == report['selected_retained_faces']
        for name in before:
            if name != TARGET: assert after[name] == before[name], 'Protected actor changed: '+name
        applied_graphs = materials_signature()
        assert {name:applied_graphs[name] for name in graphs} == graphs, 'Original material/image graph changed'
        state.update(after=after, applied_graphs=applied_graphs, owned_graph=graph_signature(material.node_tree))
        state['owned_users'] = _ownership(state)
        report.update(status='APPLIED_STATIC_PIGMENT_REVIEW_WIP', material=material.name,
                      new_UV=UV, original_six_UV_held=True, original_data_pointer_retained=True,
                      new_generic_attributes=0, evaluated_geometry_exact=True, raw_Main_held=True,
                      protected_actors=len(before)-1, source_material_graphs_held=True,
                      source_graphs_before_after={name:row['graph'] for name,row in graphs.items()},
                      copied_material_graph=state['owned_graph'], attributes_keys_weights_held=True,
                      existing_deleted_faces_not_resurrected=True,
                      review_required='Actual EEVEE compile and matched source front/back/oblique; not M2/ART')
        bpy.app.driver_namespace[KEY] = state
        report['receipt'] = _receipt(root, 'apply', report)
        return report
    except BaseException:
        # Preserve recovery ownership even if rollback itself is interrupted.
        bpy.app.driver_namespace[KEY] = state
        _restore_binding(target, state)
        bpy.context.view_layer.update()
        assert _snapshot(root) == before
        _remove_owned(state)
        assert materials_signature() == graphs
        bpy.app.driver_namespace.pop(KEY, None)
        raise


def _present(collection, value):
    """Deleted Blender RNA references raise; they are not live cleanup owners."""
    if value is None: return None
    try: pointer = value.as_pointer()
    except ReferenceError: return None
    return next((item for item in collection if item.as_pointer() == pointer), None)


def _restore_binding(target, state):
    bpy = _bpy(); mesh = _present(bpy.data.meshes, state['owned_data'])
    if mesh is not None and target.data == mesh:
        # Release the owned OBJECT override BEFORE shrinking to two data slots.
        # Otherwise Blender can retain its user outside visible material_slots.
        index = len(state['original_slots'])
        if len(target.material_slots) > index:
            assert len(target.material_slots) == index+1
            slot = target.material_slots[index]
            if slot.link == 'OBJECT':
                assert slot.material in (None, state['material'])
                slot.material = None
                slot.link = 'DATA'
        target.data = state['original_data']
    else:
        assert target.data == state['original_data'], 'An unrelated mesh is active'
    assert len(target.material_slots) == len(state['original_slots'])
    for slot, (link, material) in zip(target.material_slots, state['original_slots']):
        slot.link = link; slot.material = material
    state['restore_phase'] = 'ORIGINAL_BINDING_RESTORED'


def _remove_owned(state):
    """Preflight the complete owned reference chain, then delete resumably."""
    bpy = _bpy()
    mesh = _present(bpy.data.meshes, state['owned_data'])
    material = _present(bpy.data.materials, state['material'])
    images = [image for old in state['images'] if (image := _present(bpy.data.images, old)) is not None]
    if mesh is not None: assert mesh.users == 0, 'Owned mesh still has a user'
    phantom = False
    if material is not None:
        expected = sum(m == material for m in mesh.materials) if mesh is not None else 0
        assert not material.use_fake_user and not material.use_extra_user
        if material.users != expected:
            # Blender 5.2 actual lifecycle: shrinking an OBJECT-override slot
            # can lose its pointer yet leave users=1 and user_map empty. Only
            # this declared new material, after exact original restoration,
            # may receive bounded unlink removal. No user_clear or source IDs.
            assert mesh is None and expected == 0 and material.users == 1
            assert state.get('restore_phase') == 'ORIGINAL_BINDING_RESTORED'
            assert not bpy.data.user_map(subset={material}).get(material, set())
            assert state['applied_graphs'][material.name]['pointer'] == material.as_pointer()
            assert graph_signature(material.node_tree) == state['owned_graph']
            assert _snapshot(state['root']) == state['before']
            source = materials_signature()
            assert {name:source[name] for name in state['original_graphs']} == state['original_graphs']
            phantom = True
    for image in images:
        expected = sum(getattr(node, 'image', None) == image for node in material.node_tree.nodes) if material is not None else 0
        assert not image.use_fake_user and not image.use_extra_user
        assert image.users == expected, 'Owned image has an undeclared user'
    # No delete happens until all expected refcounts have been checked.
    if mesh is not None:
        bpy.data.meshes.remove(mesh, do_unlink=False)
    state['owned_data'] = None
    if material is not None:
        assert material.users == (1 if phantom else 0)
        bpy.data.materials.remove(material, do_unlink=phantom)
        state['owned_phantom_user_repaired'] = phantom
    state['material'] = None
    for image in images:
        assert image.users == 0; bpy.data.images.remove(image, do_unlink=False)
    state['images'] = []
    state['restore_phase'] = 'OWNED_ASSETS_REMOVED'


def restore(root=None):
    """Exact original data pointer; refuse changes made since this apply."""
    from types import SimpleNamespace
    bpy = _bpy(); state = bpy.app.driver_namespace[KEY]
    root = Path(state['root'] if root is None else root).resolve()
    assert Path(state['root']) == root and bpy.context.mode == 'OBJECT'
    target = bpy.data.objects[TARGET]
    mesh = _present(bpy.data.meshes, state['owned_data'])
    material = _present(bpy.data.materials, state['material'])
    if mesh is not None and target.data == mesh:
        assert _snapshot(root) == state['after']
        assert materials_signature() == state['applied_graphs'], 'Restore later material changes first'
        assert _ownership(state) == state['owned_users'], 'Owned data gained a user; detach it before restore'
    else:
        # Resume legacy failure after original binding and possibly mesh deletion.
        assert target.data == state['original_data'] and _snapshot(root) == state['before']
        graphs = materials_signature()
        assert {name:graphs[name] for name in state['original_graphs']} == state['original_graphs']
        extra = set(graphs)-set(state['original_graphs'])
        assert extra == ({material.name} if material is not None else set()), 'Unrelated material appeared'
        if material is not None:
            assert graph_signature(material.node_tree) == state['owned_graph'], 'Owned shader was edited'
    assert _modifiers(target) == state['modifiers'], 'Modifier changed since apply'
    assert Path(bpy.data.filepath).resolve() == Path(state['native']) and file_sha(state['native']) == state['native_sha256']
    original = state['original_data']
    # Check the retained, currently unassigned mesh before switching pointers.
    helper = _helpers(root)
    proxy = SimpleNamespace(data=original, matrix_world=target.matrix_world)
    assert helper['fingerprint'](proxy) == state['before'][TARGET]['fingerprint']
    assert _mesh_payload(original) == state['original_payload'], 'Retained original mesh was edited'
    _restore_binding(target, state)
    bpy.context.view_layer.update()
    assert _snapshot(root) == state['before']
    _remove_owned(state)
    assert materials_signature() == state['original_graphs']
    del bpy.app.driver_namespace[KEY]
    report = dict(status='RESTORED_ORIGINAL_REMAININGMAIN_DATA_AND_SLOTS', original_pointer_exact=True,
                  original_graphs_UV_geometry_normals_exact=True, body_sha256=state['body_sha256'],
                  legacy_owned_phantom_user_repaired=state.get('owned_phantom_user_repaired', False),
                  native_saved=False, ART=False)
    report['receipt'] = _receipt(root, 'restore', report)
    return report


if globals().get('MIA_V29_PIGMENT_PHASE') == 'inspect':
    print(json.dumps(inspect(globals().get('MIA_ROOT', ROOT))))
elif globals().get('MIA_V29_PIGMENT_PHASE') == 'apply':
    print(json.dumps(apply(globals()['MIA_EXPECT_BODY_SHA256'], globals().get('MIA_ROOT', ROOT))))
