"""Read-only signatures used by the fresh-process verifier."""
import hashlib
import json

import bpy
import numpy as np


def _plain(value):
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, bpy.types.ID):
        return {'id_type': value.id_type, 'name': value.name_full}
    if hasattr(value, 'to_dict'):
        return {k: _plain(v) for k, v in value.to_dict().items()}
    try:
        return [_plain(v) for v in value]
    except TypeError:
        return str(type(value).__name__)


def rna(value):
    result = {}
    for prop in value.bl_rna.properties:
        if prop.identifier == 'rna_type' or prop.type == 'COLLECTION':
            continue
        if prop.type == 'POINTER':
            val = getattr(value, prop.identifier, None)
            if isinstance(val, bpy.types.ID) or val is None:
                result[prop.identifier] = _plain(val)
        else:
            try:
                result[prop.identifier] = _plain(getattr(value, prop.identifier))
            except (AttributeError, TypeError):
                pass
    if hasattr(value, 'keys'):
        try:
            result['custom_properties'] = {k: _plain(value[k]) for k in value.keys()}
        except TypeError:
            pass
    return result


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=True).encode()).hexdigest()


def _buffer(collection, attr, width, dtype=np.float64):
    buf = np.empty(len(collection) * width, dtype=dtype)
    collection.foreach_get(attr, buf)
    return hashlib.sha256(buf.tobytes()).hexdigest()


def _tree(tree):
    return {'settings': rna(tree), 'nodes': [
        {'settings': rna(n), 'inputs': [rna(s) for s in n.inputs], 'outputs': [rna(s) for s in n.outputs]}
        for n in tree.nodes], 'links': sorted((l.from_node.name, l.from_socket.identifier,
                                              l.to_node.name, l.to_socket.identifier) for l in tree.links)}


def _object(obj):
    state = {'settings': rna(obj), 'matrix_world': _plain(obj.matrix_world),
             'collections': sorted(c.name for c in obj.users_collection),
             'hide_get': obj.hide_get(), 'select_get': obj.select_get(),
             'modifiers': [rna(m) for m in obj.modifiers], 'constraints': [rna(c) for c in obj.constraints],
             'vertex_groups': [rna(g) for g in obj.vertex_groups],
             'material_slots': [rna(s) for s in obj.material_slots]}
    if obj.type == 'ARMATURE':
        state['rest'] = [rna(b) for b in obj.data.bones]
        state['pose'] = [{'settings': rna(b), 'matrix': _plain(b.matrix),
                          'matrix_basis': _plain(b.matrix_basis),
                          'constraints': [rna(c) for c in b.constraints]} for b in obj.pose.bones]
    if obj.type == 'MESH':
        state['weights'] = [[(g.group, g.weight) for g in v.groups] for v in obj.data.vertices]
    return _hash(state)


def snapshot():
    """All original owners/meshes/keys/UV/materials/rig+scene, not only target owner."""
    bpy.context.view_layer.update()
    meshes = {}
    for mesh in bpy.data.meshes:
        state = {'settings': rna(mesh), 'vertices': _buffer(mesh.vertices, 'co', 3),
                 'edges': _buffer(mesh.edges, 'vertices', 2, np.int64),
                 'loops': _buffer(mesh.loops, 'vertex_index', 1, np.int64),
                 'polygons': [(p.loop_start, p.loop_total, p.material_index, p.use_smooth) for p in mesh.polygons],
                 'materials': [m.name_full if m else None for m in mesh.materials],
                 'uv': [{'name': u.name, 'active_render': u.active_render,
                         'uv': _buffer(u.data, 'uv', 2),
                         'pin': _buffer(u.data, 'pin_uv', 1, np.bool_)} for u in mesh.uv_layers]}
        if mesh.shape_keys:
            state['keys'] = {'settings': rna(mesh.shape_keys),
                             'blocks': [{'settings': rna(k), 'co': _buffer(k.data, 'co', 3)}
                                        for k in mesh.shape_keys.key_blocks]}
        meshes[mesh.name_full] = _hash(state)
    ids = {}
    for name in ('objects', 'meshes', 'shape_keys', 'materials', 'node_groups', 'armatures',
                 'cameras', 'lights', 'worlds', 'scenes', 'collections', 'actions', 'images', 'textures'):
        ids[name] = sorted(v.name_full for v in getattr(bpy.data, name))
    envelope = {'scenes': [{'settings': rna(s), 'render': rna(s.render),
                            'display': rna(s.display), 'view': rna(s.view_settings),
                            'world': s.world.name if s.world else None,
                            'objects': sorted(o.name for o in s.objects)} for s in bpy.data.scenes],
                'collections': {c.name: {'settings': rna(c), 'objects': sorted(o.name for o in c.objects),
                                        'children': sorted(ch.name for ch in c.children)} for c in bpy.data.collections},
                'cameras': {c.name: rna(c) for c in bpy.data.cameras},
                'lights': {l.name: rna(l) for l in bpy.data.lights},
                'worlds': {w.name: {'settings': rna(w), 'nodes': _tree(w.node_tree) if w.node_tree else None}
                           for w in bpy.data.worlds},
                'active_object': bpy.context.view_layer.objects.active.name if bpy.context.view_layer.objects.active else None}
    return {'id_inventory': _hash(ids), 'object_count': len(bpy.data.objects),
            'objects': {o.name_full: _object(o) for o in bpy.data.objects}, 'meshes': meshes,
            'materials': {m.name_full: _hash({'settings': rna(m), 'tree': _tree(m.node_tree) if m.node_tree else None})
                          for m in bpy.data.materials},
            'node_groups': {n.name_full: _hash(_tree(n)) for n in bpy.data.node_groups},
            'scene_envelope': _hash(envelope), 'id_inventory_names': ids}
