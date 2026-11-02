# Static read-only audit helpers derived from canonical v31 audit_mesh_helpers.py.
import bpy, numpy as np, json, hashlib, collections, sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

def digest(b):
    return hashlib.sha256(b).hexdigest()

def arr(data, attr, n):
    a = np.empty(len(data) * n, dtype=np.float32)
    data.foreach_get(attr, a)
    return a

def jhash(x):
    return digest(json.dumps(x, sort_keys=True, default=str).encode())

def value(v):
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    try:
        return list(v)
    except:
        return str(v)

def graph(nt, visited=None):
    if nt is None:
        return None
    visited = set() if visited is None else visited
    if nt.name in visited:
        return {'shared': nt.name}
    visited.add(nt.name)
    nodes = []
    for n in nt.nodes:
        d = {'name': n.name, 'type': n.bl_idname, 'inputs': [(s.identifier, value(s.default_value)) for s in n.inputs if hasattr(s, 'default_value')], 'outputs': [(s.identifier, value(s.default_value)) for s in n.outputs if hasattr(s, 'default_value')]}
        for p in ['operation', 'blend_type', 'interpolation', 'extension', 'projection', 'uv_map', 'attribute_name', 'is_active_output']:
            if hasattr(n, p):
                d[p] = value(getattr(n, p))
        if getattr(n, 'image', None):
            d['image'] = n.image.name
        if getattr(n, 'node_tree', None):
            d['group'] = graph(n.node_tree, visited)
        if hasattr(n, 'color_ramp'):
            d['ramp'] = [(e.position, list(e.color)) for e in n.color_ramp.elements]
        nodes.append(d)
    return {'name': nt.name, 'nodes': nodes, 'links': [(l.from_node.name, l.from_socket.identifier, l.to_node.name, l.to_socket.identifier) for l in nt.links]}

def snapshot(path=None):
    if path is not None:
        bpy.ops.wm.open_mainfile(filepath=str(path), use_scripts=False)
    out = {}
    raw = {}
    for ob in bpy.context.scene.objects:
        if ob.type != 'MESH':
            continue
        me = ob.data
        co = arr(me.vertices, 'co', 3).reshape(-1, 3)
        kn = []
        ks = None
        if me.shape_keys:
            kn = [k.name for k in me.shape_keys.key_blocks]
            ks = np.array([arr(k.data, 'co', 3).reshape(-1, 3) for k in me.shape_keys.key_blocks])
        if ob.name.startswith('V28G_Iris_') or ob.name == 'MIA_V27_SharedHeadBody':
            raw[ob.name] = {'coordinates': ks, 'UVMap': arr(me.uv_layers['UVMap'].data, 'uv', 2).reshape(-1, 2) if me.uv_layers else None, 'loop_vertex_indices': np.array([li.vertex_index for li in me.loops]), 'polygons': [list(f.vertices) for f in me.polygons]}
        dr = []
        if me.shape_keys and me.shape_keys.animation_data:
            for f in me.shape_keys.animation_data.drivers:
                dr.append({'data_path': f.data_path, 'type': f.driver.type, 'expression': f.driver.expression, 'variables': [(v.name, v.type, [(t.id.name if t.id else None, t.data_path) for t in v.targets]) for v in f.driver.variables]})
        mods = []
        for m in ob.modifiers:
            md = {'name': m.name, 'type': m.type}
            for p in ['object', 'vertex_group', 'show_viewport', 'show_render', 'levels', 'render_levels', 'thickness', 'offset']:
                if hasattr(m, p):
                    v = getattr(m, p)
                    md[p] = v.name if hasattr(v, 'name') else value(v)
            mods.append(md)
        out[ob.name] = {'coordinates': digest(co.tobytes() + (ks.tobytes() if ks is not None else b'')), 'topology': jhash([(list(f.vertices), f.material_index, f.use_smooth) for f in me.polygons]), 'UV': {u.name: digest(arr(u.data, 'uv', 2).tobytes()) for u in me.uv_layers}, 'weights': jhash([[(ob.vertex_groups[g.group].name, float(g.weight)) for g in v.groups] for v in me.vertices]), 'key_names': kn, 'drivers': dr, 'modifiers': mods, 'materials': [(s.name, s.link) for s in ob.material_slots], 'matrix': [list(r) for r in ob.matrix_world]}
    mats = {m.name: jhash(graph(m.node_tree)) for m in bpy.data.materials}
    images = {im.name: {'colorspace': im.colorspace_settings.name, 'size': list(im.size), 'packed': digest(im.packed_file.data) if im.packed_file else None} for im in bpy.data.images}
    return (out, raw, mats, images)
