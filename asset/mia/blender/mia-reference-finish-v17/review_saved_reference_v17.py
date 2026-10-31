"""Fresh read-only review of the integrated head/face/Pixal hair candidate."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

p = argparse.ArgumentParser()
p.add_argument('--source', required=True)
p.add_argument('--output-dir', required=True)
p.add_argument('--hair-collection', action='append', required=True)
p.add_argument('--skin', default='MIA_V14_SculptedSkin')
p.add_argument('--upper-oblique', action='store_true')
p.add_argument('--face-identity', action='store_true')
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
src, out = Path(a.source).resolve(), Path(a.output_dir).resolve()
out.mkdir(parents=True, exist_ok=True)
sha = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
input_sha = sha(src)
bpy.ops.wm.open_mainfile(filepath=str(src))
scene, cam = bpy.context.scene, bpy.context.scene.camera
skin = bpy.data.objects[a.skin]
hair = list({o for name in a.hair_collection for o in bpy.data.collections[name].all_objects
             if o.type in {'MESH', 'CURVE'} and not o.hide_render})
assert hair, 'No visible hair found in requested collections'
scene.render.resolution_x = scene.render.resolution_y = 896
scene.render.resolution_percentage = 100
views = [('front', (0, -2)), ('left', (1.4, -1.4)),
         ('right', (-1.4, -1.4)), ('profile', (2, 0)), ('back', (0, 2))]
renders = []

def render(name, xy, scale=.48, z=1.555, elevation=0):
    cam.location = (xy[0], xy[1], z + math.hypot(*xy) * math.tan(math.radians(elevation)))
    cam.rotation_euler = (Vector((0, 0, z)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.ortho_scale = scale
    path = out / (name + '.png')
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    renders.append({'name': name, 'path': str(path), 'scale': scale,
                    'location': list(cam.location), 'rotation': list(cam.rotation_euler)})

for framing, scale, z in [('close', .48, 1.555), ('wide', .75, 1.42)]:
    for view, xy in views:
        render(f'{framing}_{view}_hair', xy, scale, z)
        for o in hair:
            o.hide_render = True
        render(f'{framing}_{view}_bald', xy, scale, z)
        for o in hair:
            o.hide_render = False

if a.upper_oblique:
    for label, xy, elevation in [('upper20_left', (1.4, -1.4), 20),
                                  ('upper35_right', (-1.4, -1.4), 35)]:
        render(label + '_hair', xy, .48, 1.555, elevation)
        for o in hair:
            o.hide_render = True
        render(label + '_bald', xy, .29, 1.55, elevation)
        for o in hair:
            o.hide_render = False

if a.face_identity:
    for view, xy in views[:4]:
        render('identity_' + view + '_hair', xy, .29, 1.55)

# Blender-generated diagnostic UV grid; no artwork or native is modified.
grid = bpy.data.images.new('V17_Review_UV_Grid', width=1024, height=1024)
grid.generated_type = 'COLOR_GRID'
check = bpy.data.materials.new('V17_Review_Checker')
check.use_nodes = True
nodes = check.node_tree.nodes
nodes.clear()
tex = nodes.new('ShaderNodeTexImage'); tex.image = grid
emit = nodes.new('ShaderNodeEmission')
output = nodes.new('ShaderNodeOutputMaterial')
check.node_tree.links.new(tex.outputs['Color'], emit.inputs['Color'])
check.node_tree.links.new(emit.outputs['Emission'], output.inputs['Surface'])
original_slots = {o.name: [s.material for s in o.material_slots] for o in hair + [skin]}
for o in hair:
    for slot in o.material_slots:
        slot.material = check
for view, xy in [views[0], views[1], views[4]]:
    render('uv_hair_' + view, xy)
for o in hair:
    for slot, old in zip(o.material_slots, original_slots[o.name]):
        slot.material = old
    o.hide_render = True
for slot in skin.material_slots:
    slot.material = check
for view, xy in [views[0], views[1]]:
    render('uv_face_' + view, xy, .29, 1.55)
for slot, old in zip(skin.material_slots, original_slots[skin.name]):
    slot.material = old
for o in hair:
    o.hide_render = False

# Separate clay lighting reveals geometry independently of painted strand detail.
vs = scene.view_settings
beauty_view = (vs.view_transform, vs.look, vs.exposure, vs.gamma)
vs.view_transform, vs.look, vs.exposure, vs.gamma = 'Standard', 'None', 0, 1
clay = bpy.data.materials.new('V17_Review_Clay')
clay.use_nodes = True
bsdf = next(n for n in clay.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
bsdf.inputs['Base Color'].default_value = (.32, .32, .32, 1)
bsdf.inputs['Roughness'].default_value = .8
saved_lights = [(o, o.hide_render) for o in scene.objects if o.type == 'LIGHT']
for o, _ in saved_lights:
    o.hide_render = True
review_lights = []
for name, location, power, size in [('key', (1, -1.4, 2.1), 110, 1.2),
                                     ('fill', (-1.2, -.4, 1.8), 65, 1.5),
                                     ('rear', (.5, 1.1, 2), 100, 1.2)]:
    data = bpy.data.lights.new('V17_Review_' + name, 'AREA')
    data.energy, data.shape, data.size = power, 'DISK', size
    lamp = bpy.data.objects.new(data.name, data)
    scene.collection.objects.link(lamp)
    lamp.location = location
    lamp.rotation_euler = (Vector((0, 0, 1.55)) - lamp.location).to_track_quat('-Z', 'Y').to_euler()
    review_lights.append(lamp)
for o in hair + [skin]:
    for slot in o.material_slots:
        slot.material = clay
for view, xy in views:
    render('clay_' + view + '_hair', xy)
for o in hair:
    o.hide_render = True
render('clay_profile_bald', views[3][1], .29, 1.55)
if a.upper_oblique:
    render('clay_left_bald', views[1][1], .29, 1.55)
    render('clay_right_bald', views[2][1], .29, 1.55)
    render('clay_upper20_bald', views[1][1], .29, 1.55, 20)
for o in hair + [skin]:
    for slot, old in zip(o.material_slots, original_slots[o.name]):
        slot.material = old
for o, hidden in saved_lights:
    o.hide_render = hidden
for lamp in review_lights:
    bpy.data.objects.remove(lamp, do_unlink=True)
vs.view_transform, vs.look, vs.exposure, vs.gamma = beauty_view
render('eye_close_front', views[0][1], .18, 1.54)
render('eye_close_left', views[1][1], .18, 1.54)
for o in hair:
    o.hide_render = False

def active_images(material):
    if not material or not material.use_nodes:
        return []
    roots = [n for n in material.node_tree.nodes
             if n.type == 'OUTPUT_MATERIAL' and n.is_active_output]
    todo, seen, found = list(roots), set(), []
    while todo:
        node = todo.pop()
        if node in seen:
            continue
        seen.add(node)
        if node.type == 'TEX_IMAGE' and node.image:
            found.append(node.image.name)
        todo.extend(link.from_node for sock in node.inputs for link in sock.links)
    return sorted(set(found))

owners = []
for o in hair + [skin, bpy.data.objects['MIA_V14_EyeSurface']]:
    uv_layers = []
    if o.type == 'MESH':
        for layer in o.data.uv_layers:
            values = [tuple(x.uv) for x in layer.data]
            uv_layers.append({'name': layer.name, 'loops': len(values),
                              'finite': all(math.isfinite(x) for pair in values for x in pair)})
    owners.append({'name': o.name, 'type': o.type,
                   'vertices': len(o.data.vertices) if o.type == 'MESH' else None,
                   'uv_layers': uv_layers,
                   'active_uv': (o.data.uv_layers.active.name if o.type == 'MESH' and o.data.uv_layers.active else None),
                   'render_uv': (next((u.name for u in o.data.uv_layers if u.active_render), None) if o.type == 'MESH' else None),
                   'groups': [{'name': g.name,
                               'weighted_vertices': sum(1 for v in o.data.vertices
                                                        if any(w.group == g.index and w.weight > 0 for w in v.groups))}
                              for g in o.vertex_groups] if o.type == 'MESH' else [],
                   'modifiers': [(m.name, m.type) for m in o.modifiers],
                   'materials': [{'name': s.material.name if s.material else None,
                                  'active_images': active_images(s.material)} for s in o.material_slots]})
report = {'source': str(src), 'sha_before': input_sha, 'sha_after': sha(src),
          'native_not_saved': True, 'owners': owners, 'renders': renders,
          'images': [{'name': im.name, 'size': list(im.size),
                      'packed': bool(im.packed_file or im.packed_files), 'path': im.filepath}
                     for im in bpy.data.images if im.name != grid.name and im.source != 'VIEWER'],
          'limits': 'Static native replay only. Render existence and UV finiteness are not art/rig acceptance.'}
assert report['sha_before'] == report['sha_after']
(out / 'review-evidence.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('V17_FRESH_REVIEW', input_sha, len(renders))
