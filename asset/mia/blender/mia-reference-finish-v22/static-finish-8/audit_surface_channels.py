"""Read an actual native; export directly connected image bytes and UV density evidence.

Blender --background --python audit_surface_channels.py -- --native FILE --output-dir NEW
This is an inventory/geometry diagnostic, never an art acceptance test.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import bpy
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def visible_meshes():
    ids = set()
    def walk(layer, hidden=False):
        hidden = hidden or layer.exclude or layer.collection.hide_render
        if not hidden:
            ids.update(o.as_pointer() for o in layer.collection.objects)
        for child in layer.children:
            walk(child, hidden)
    walk(bpy.context.view_layer.layer_collection)
    return [o for o in bpy.context.scene.objects
            if o.type == 'MESH' and o.as_pointer() in ids and not o.hide_render]


def upstream_material(material):
    if not material.use_nodes:
        return {'status': 'NO_NODE_TREE', 'nodes': [], 'images': []}, []
    nodes = material.node_tree.nodes
    roots = [n for n in nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output]
    pending, visited = list(roots), set()
    while pending:
        node = pending.pop()
        if node.name in visited:
            continue
        visited.add(node.name)
        pending.extend(link.from_node for socket in node.inputs for link in socket.links)
    connected = [n for n in nodes if n.name in visited]
    groups = [n.name for n in connected if n.type == 'GROUP']
    images = [n.image for n in connected if n.type == 'TEX_IMAGE' and n.image]
    return {
        'status': 'GROUP_INTERNALS_NOT_RESOLVED' if groups else 'DIRECT_GRAPH_TRACED',
        'groups': groups,
        'nodes': [{'name': n.name, 'type': n.bl_idname} for n in connected],
        'images': [{'node': n.name, 'image': n.image.name,
                    'colorspace': n.image.colorspace_settings.name,
                    'size': list(n.image.size),
                    'vector_source': [[l.from_node.name, l.from_socket.name]
                                      for l in n.inputs['Vector'].links]}
                   for n in connected if n.type == 'TEX_IMAGE' and n.image],
        'uv_nodes': [{'node': n.name, 'uv_map': n.uv_map}
                     for n in connected if n.type == 'UVMAP'],
        'links': [[l.from_node.name, l.from_socket.name, l.to_node.name, l.to_socket.name]
                  for l in material.node_tree.links if l.to_node.name in visited],
    }, images


def density(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=bpy.context.evaluated_depsgraph_get())
    try:
        mesh.calc_loop_triangles()
        n = len(mesh.loop_triangles)
        co = np.empty(len(mesh.vertices) * 3, dtype=np.float64)
        mesh.vertices.foreach_get('co', co)
        co = co.reshape((-1, 3))
        matrix = np.array(evaluated.matrix_world)
        co = co @ matrix[:3, :3].T + matrix[:3, 3]
        triangles = np.empty(n * 3, dtype=np.int32)
        loops = np.empty(n * 3, dtype=np.int32)
        mesh.loop_triangles.foreach_get('vertices', triangles)
        mesh.loop_triangles.foreach_get('loops', loops)
        points = co[triangles.reshape((-1, 3))]
        areas = np.linalg.norm(np.cross(points[:, 1] - points[:, 0], points[:, 2] - points[:, 0]), axis=1) / 2
        result = {'triangles': n, 'geometric_degenerate_triangles': int(np.sum(areas < 1e-14)), 'layers': {}}
        for layer in mesh.uv_layers:
            uv = np.empty(len(layer.data) * 2, dtype=np.float64)
            layer.data.foreach_get('uv', uv)
            u = uv.reshape((-1, 2))[loops.reshape((-1, 3))]
            e, f = u[:, 1] - u[:, 0], u[:, 2] - u[:, 0]
            ua = np.abs(e[:, 0] * f[:, 1] - e[:, 1] * f[:, 0]) / 2
            valid = (areas > 1e-14) & (ua > 1e-14)
            d = np.sqrt(ua[valid] / areas[valid])
            q = np.quantile(d, [.01, .05, .5, .95, .99]).tolist() if len(d) else []
            result['layers'][layer.name] = {
                'finite': bool(np.isfinite(uv).all()),
                'zero_area_uv_on_nonzero_surface': int(np.sum((ua <= 1e-14) & (areas > 1e-14))),
                'uv_linear_density_per_world_meter_percentiles_1_5_50_95_99': q,
                'p95_over_p05': q[3] / q[1] if q and q[1] else None,
                'limits': 'Triangle density distribution, not directional stretch, island overlap, seam continuity or art quality. Different materials/islands may intentionally differ.'}
        return result
    finally:
        evaluated.to_mesh_clear()


def main(native, out, inventory_only=False):
    before = sha(native)
    if out.exists() and any(out.iterdir()):
        raise RuntimeError('Use a fresh output directory')
    out.mkdir(parents=True, exist_ok=True)
    maps = out / 'connected-map-bytes'
    maps.mkdir()
    bpy.ops.wm.open_mainfile(filepath=str(native), use_scripts=False)
    bpy.context.scene.frame_set(1)
    owners = visible_meshes()
    # Unused material slots survive imported face separation. A slot that is
    # not assigned to any polygon is not a consumed surface channel.
    used_materials = {}
    for owner in owners:
        used_slots = {p.material_index for p in owner.data.polygons}
        used_materials[owner.name] = [slot.material for i, slot in enumerate(owner.material_slots)
                                      if i in used_slots and slot.material]
    materials = {m.name: m for row in used_materials.values() for m in row}
    routes, images = {}, {}
    for name, material in materials.items():
        row, connected_images = upstream_material(material)
        row['owners'] = [o.name for o in owners if material in used_materials[o.name]]
        routes[name] = row
        for image in connected_images:
            images[image.name] = image
    inventory = []
    for name, image in images.items():
        row = {'name': name, 'size': list(image.size), 'colorspace': image.colorspace_settings.name,
               'file_format': image.file_format, 'source': image.source, 'packed': bool(image.packed_file)}
        if image.packed_file:
            content = bytes(image.packed_file.data)
            digest = hashlib.sha256(content).hexdigest()
            extension = {'PNG': '.png', 'JPEG': '.jpg', 'OPEN_EXR': '.exr', 'TIFF': '.tif'}.get(image.file_format, '.bin')
            path = maps / (digest[:12] + '-' + re.sub(r'[^A-Za-z0-9_.-]', '_', name)[:90] + extension)
            if not inventory_only:
                path.write_bytes(content)
                row['exported'] = str(path.relative_to(out))
            row.update({'sha256': digest, 'bytes': len(content)})
        else:
            path = Path(bpy.path.abspath(image.filepath)) if image.filepath else None
            row['external_exists'] = bool(path and path.is_file())
            row['path'] = str(path) if path else None
        inventory.append(row)
    bodyface = [o for o in owners if o.name in ('MIA_V14_SculptedSkin', 'MIA_V06_BODY_SKIN')]
    report = {'native': str(native), 'native_sha256': before, 'art_status': 'NOT_EVALUATED',
              'material_routes': routes, 'images': inventory, 'inventory_only': inventory_only,
              'uv_density': {o.name: density(o) for o in bodyface},
              'limitations': 'Only directly reachable material image nodes exported. Group internals marked unresolved. Map dimensions and file presence do not establish authored detail or shader quality.'}
    assert sha(native) == before, 'Read-only audit changed native'
    (out / 'surface-channel-audit.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'native_unchanged': True, 'direct_images': len(images),
                      'material_count': len(routes), 'report': str(out / 'surface-channel-audit.json')}))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--native', required=True)
    p.add_argument('--output-dir', required=True)
    p.add_argument('--inventory-only', action='store_true')
    a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
    main(Path(a.native).resolve(), Path(a.output_dir).resolve(), a.inventory_only)
