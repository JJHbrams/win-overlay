"""Run through live Blender MCP. Review navigation/lights only; never save the native."""
from pathlib import Path
import hashlib
import json
import bpy
from mathutils import Matrix, Vector

P = Path(__file__).resolve().parent
native = P / 'surface-C/native/Mia_FaceFinish_v29_C.blend'
expected = 'd7e2f7d7027e7ce65746e18af25562ec25a19c61bca847d5363080259b27d3be'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(native) == expected
spec = json.loads((P / 'final-review/source/render-records.json').read_text())[0]['camera']
bpy.ops.wm.open_mainfile(filepath=str(native), use_scripts=False)
s = bpy.context.scene
for ob in s.objects:
    if ob.type == 'LIGHT':
        ob.hide_render = True
for i, item in enumerate(spec['lighting']['areas']):
    data = bpy.data.lights.new('V29_LIVE_ReviewLight_' + str(i), 'AREA')
    data.energy, data.shape, data.size, data.color = item['watts'], item['shape'], item['size'], item['color']
    ob = bpy.data.objects.new(data.name, data)
    s.collection.objects.link(ob)
    ob.matrix_world = Matrix(item['matrix'])
world = bpy.data.worlds.new('V29_LIVE_ReviewWorld')
world.use_nodes = True
n = world.node_tree.nodes
n.clear()
bg = n.new('ShaderNodeBackground')
bg.inputs['Color'].default_value = (*spec['lighting']['world_linear'], 1)
bg.inputs['Strength'].default_value = spec['lighting']['world_strength']
out = n.new('ShaderNodeOutputWorld')
out.is_active_output = True
world.node_tree.links.new(bg.outputs[0], out.inputs['Surface'])
s.world = world
head = bpy.data.objects.new('V29_LIVE_Head', bpy.data.cameras.new('V29_LIVE_Head'))
s.collection.objects.link(head)
head.data.type = 'ORTHO'
head.data.ortho_scale = spec['ortho_scale']
head.matrix_world = Matrix(spec['matrix'])
body = bpy.data.objects.new('V29_LIVE_FullBody', bpy.data.cameras.new('V29_LIVE_FullBody'))
s.collection.objects.link(body)
body.data.type = 'ORTHO'
body.data.ortho_scale = 1.92
body.location = (0, -4, .87)
body.rotation_euler = (Vector((0,0,.87))-body.location).to_track_quat('-Z','Y').to_euler()
s.camera = head
s.render.engine = 'BLENDER_EEVEE'
s.render.use_freestyle = False
s.render.resolution_x = s.render.resolution_y = 512
s.render.resolution_percentage = 100
s.render.image_settings.file_format = 'PNG'
s.render.film_transparent = False
cm = spec['color_management']
s.view_settings.view_transform, s.view_settings.look = cm['view_transform'], cm['look']
s.view_settings.exposure, s.view_settings.gamma = cm['exposure'], cm['gamma']
for window in bpy.context.window_manager.windows:
    for area in window.screen.areas:
        if area.type == 'VIEW_3D':
            space = area.spaces.active
            space.clip_start, space.clip_end = .001, 100
            space.region_3d.view_location = (0,0,1.55)
            space.region_3d.view_distance = .45
            space.region_3d.view_perspective = 'ORTHO'
            space.region_3d.view_rotation = head.rotation_euler.to_quaternion()
            space.shading.type = 'MATERIAL'
            space.shading.use_scene_lights = True
            space.shading.use_scene_world = True
bpy.context.view_layer.update()
s.render.filepath = str(P/'final-review/live-head.png')
bpy.ops.render.render(write_still=True)
assert sha(native) == expected
report = {'native': str(native), 'sha256_before': expected, 'sha256_after': sha(native),
    'scene_file': bpy.data.filepath, 'native_saved': False, 'image': s.render.filepath,
    'image_sha256': sha(s.render.filepath), 'head_camera': head.name, 'body_camera': body.name,
    'projection': 'ORTHO', 'head_orbit_pivot': [0,0,1.55], 'mesh_origins_changed': False,
    'runtime_only': 'Matched actual source front lights/camera, head-centred orbit and full-body camera. Reviewed asset bytes unchanged.'}
(P/'final-review/live-review.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report))
