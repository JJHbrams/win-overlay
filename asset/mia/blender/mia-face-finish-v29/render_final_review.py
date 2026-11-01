"""Fresh saved-native source/critical/orbit review; never saves navigation overrides."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector

P = Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
ap.add_argument('--native', required=True)
ap.add_argument('--sha256', required=True)
ap.add_argument('--mode', choices=['source', 'critical', 'orbit', 'protection'], required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
native = Path(a.native).resolve()
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
assert sha(native) == a.sha256
package = json.loads((P.parent / 'mia-orbit-thorax-review-v28/reviews/G2L-face/reference-review.json').read_text())
out = P / 'final-review' / a.mode
out.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(native), use_scripts=False)
sc = bpy.context.scene
master = bpy.data.objects['MIA_V27_Foundation_Face']
skin = bpy.data.objects['MIA_V27_SharedHeadBody']
for key in master.data.shape_keys.key_blocks:
    key.value = 0
rig = next(m.object for m in master.modifiers if m.type == 'ARMATURE')
head = rig.pose.bones['J_Bip_C_Head']
spec = copy.deepcopy(package['views'][0]['candidate_camera'])
if 'head_eye_pose' in spec:
    head.matrix_basis = Matrix(spec['head_eye_pose']['head_matrix_basis'])
sc.frame_set(spec['frame'])
sc.render.engine = 'BLENDER_EEVEE'
sc.render.use_freestyle = False
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGBA'
sc.render.film_transparent = False
cm = spec['color_management']
sc.view_settings.view_transform = cm['view_transform']
sc.view_settings.look = cm['look']
sc.view_settings.exposure = cm['exposure']
sc.view_settings.gamma = cm['gamma']
for ob in sc.objects:
    if ob.type == 'LIGHT':
        ob.hide_render = True
lamps = []
for i, item in enumerate(spec['lighting']['areas']):
    light = bpy.data.lights.new('V29_FinalReview_' + str(i), 'AREA')
    light.energy = item['watts']
    light.shape = item['shape']
    light.size = item['size']
    light.color = item['color']
    ob = bpy.data.objects.new(light.name, light)
    sc.collection.objects.link(ob)
    ob.matrix_world = Matrix(item['matrix'])
    lamps.append(ob)
world = bpy.data.worlds.new('V29_FinalReviewWorld')
world.use_nodes = True
n = world.node_tree.nodes
n.clear()
bg = n.new('ShaderNodeBackground')
bg.inputs['Color'].default_value = (*spec['lighting']['world_linear'], 1)
bg.inputs['Strength'].default_value = spec['lighting']['world_strength']
wo = n.new('ShaderNodeOutputWorld')
wo.is_active_output = True
world.node_tree.links.new(bg.outputs[0], wo.inputs['Surface'])
sc.world = world
cam = bpy.data.objects.new('V29_FinalReviewCamera', bpy.data.cameras.new('V29_FinalReviewCamera'))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.type = 'ORTHO'
hair = [o for o in sc.objects if o.type == 'MESH' and not o.hide_render and
        (any(t in o.name for t in ['Hair', 'HAIR', 'Braid', 'RootLining', 'Crown', 'Gather', 'PIXAL']) or
         any('HAIR' in c.name.upper() for c in o.users_collection))]
walls = [o for o in sc.objects if o.type == 'MESH' and o.name.startswith('V28G_InnerLid_')]
original_slots = {o.name: list(o.data.materials) for o in [skin] + walls}
matte = bpy.data.materials.new('V29_ReviewNeutralMatte')
matte.use_nodes = True
nn = matte.node_tree.nodes
nn.clear()
bs = nn.new('ShaderNodeBsdfPrincipled')
bs.inputs['Base Color'].default_value = (.23, .23, .23, 1)
bs.inputs['Roughness'].default_value = .85
mo = nn.new('ShaderNodeOutputMaterial')
mo.is_active_output = True
matte.node_tree.links.new(bs.outputs[0], mo.inputs['Surface'])
records = []

def render(label, camera_spec, hide_hair=False, mode='production'):
    cam.matrix_world = Matrix(camera_spec['matrix'])
    cam.data.ortho_scale = camera_spec['ortho_scale']
    cam.data.shift_x, cam.data.shift_y = camera_spec['lens_shift']
    sc.render.resolution_x, sc.render.resolution_y = camera_spec['resolution']
    sc.render.pixel_aspect_x, sc.render.pixel_aspect_y = camera_spec['pixel_aspect']
    for ob in hair:
        ob.hide_render = hide_hair
    for ob in [skin] + walls:
        for i, mat in enumerate(original_slots[ob.name]):
            ob.data.materials[i] = matte if mode == 'neutral_matte' else mat
    bpy.context.view_layer.update()
    file = out / (label + '.png')
    sc.render.filepath = str(file)
    bpy.ops.render.render(write_still=True)
    actual = copy.deepcopy(camera_spec)
    actual['matrix'] = [list(row) for row in cam.matrix_world]
    actual['ortho_scale'] = cam.data.ortho_scale
    actual['resolution'] = [sc.render.resolution_x, sc.render.resolution_y]
    actual['pixel_aspect'] = [sc.render.pixel_aspect_x, sc.render.pixel_aspect_y]
    actual['lens_shift'] = [cam.data.shift_x, cam.data.shift_y]
    actual['frame'] = sc.frame_current
    actual['active_shape_keys'] = {k.name: k.value for k in master.data.shape_keys.key_blocks if k.value}
    actual['lighting']['areas'] = [dict(item, matrix=[list(row) for row in lamp.matrix_world],
        watts=lamp.data.energy, shape=lamp.data.shape, size=lamp.data.size, color=list(lamp.data.color))
        for item, lamp in zip(camera_spec['lighting']['areas'], lamps)]
    actual['lighting']['world_linear'] = list(bg.inputs['Color'].default_value)[:3]
    actual['lighting']['world_strength'] = bg.inputs['Strength'].default_value
    actual['head_eye_pose'] = {'armature': rig.name, 'head_bone': head.name,
        'head_matrix_basis': [list(row) for row in head.matrix_basis],
        'eye_pose': 'rest; master shape keys recorded above'}
    records.append({'id': label, 'native': str(native), 'native_sha256': a.sha256,
        'path': str(file), 'sha256': sha(file), 'camera': actual, 'material_mode': mode,
        'temporarily_hidden_hair': [o.name for o in hair] if hide_hair else [],
        'arm_pose_basis': {name: [list(r) for r in rig.pose.bones[name].matrix_basis]
            for name in ['J_Bip_L_UpperArm', 'J_Bip_R_UpperArm']},
        'native_saved': False})
    (out / 'render-records.json').write_text(json.dumps(records, indent=2), encoding='utf-8')

if a.mode == 'protection':
    arm_names = ['J_Bip_L_UpperArm', 'J_Bip_R_UpperArm']
    rest_arms = {name: rig.pose.bones[name].matrix.copy() for name in arm_names}
    for angle in [0, 20, -20]:
        for name, sign in zip(arm_names, [-1, 1]):
            bone = rig.pose.bones[name]
            joint = (rig.matrix_world @ rest_arms[name]).translation
            rot = Matrix.Translation(joint) @ Matrix.Rotation(math.radians(angle)*sign, 4, 'Y') @ Matrix.Translation(-joint)
            bone.matrix = rig.matrix_world.inverted() @ rot @ rig.matrix_world @ rest_arms[name]
        target = Vector((0, 0, .87 if angle == 0 else 1.25))
        cam.location = target + Vector((0, -2, 0))
        cam.rotation_euler = (target-cam.location).to_track_quat('-Z', 'Y').to_euler()
        bpy.context.view_layer.update()
        view = copy.deepcopy(spec)
        view['matrix'] = [list(row) for row in cam.matrix_world]
        view['ortho_scale'] = 1.92 if angle == 0 else .86
        view['resolution'] = [640, 640]
        render('fullbody-rest' if angle == 0 else 'arms' + str(angle), view, False)
elif a.mode == 'source':
    for row in package['views']:
        for label, hide, mode in [('hairON', False, 'production'), ('hairOFF', True, 'production'),
                                  ('matte', True, 'neutral_matte')]:
            render(row['id'] + '-' + label, row['candidate_camera'], hide, mode)
else:
    if a.mode == 'critical':
        angles = [('highFront', 0, 45), ('lowFront', 0, -30), ('lowRight', 35, -30),
                  ('highLeft', -35, 40), ('profileLow', 85, -20), ('topDown', 0, 70)]
    else:
        angles = [(f'{i:03}', i * 15, 8 + 17 * math.sin(math.radians(i * 30))) for i in range(24)]
    for label, yaw, pitch in angles:
        target = Vector((0, 0, 1.55))
        y, p = math.radians(yaw), math.radians(pitch)
        loc = target + Vector((2 * math.sin(y) * math.cos(p), -2 * math.cos(y) * math.cos(p), 2 * math.sin(p)))
        cam.location = loc
        cam.rotation_euler = (target - loc).to_track_quat('-Z', 'Y').to_euler()
        bpy.context.view_layer.update()
        view = copy.deepcopy(spec)
        view['matrix'] = [list(row) for row in cam.matrix_world]
        view['resolution'] = [640, 640] if a.mode == 'critical' else [512, 512]
        view['ortho_scale'] = .29 if a.mode == 'critical' else .36
        view['estimated_yaw_pitch_roll_deg'] = [yaw, pitch, 0]
        render(label, view, a.mode == 'critical')
assert sha(native) == a.sha256
print('V29_FINAL_REVIEW_DONE', a.mode, len(records), flush=True)
