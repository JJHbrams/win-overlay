"""Run in the actual Blender MCP session; preserve model transforms and source native."""
import bpy
import json
import math
from pathlib import Path
from mathutils import Vector

ROOT = Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v22')


def viewport_state():
    rows = []
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == 'VIEW_3D':
                sp, rv = area.spaces.active, area.spaces.active.region_3d
                rows.append({'location': list(rv.view_location), 'distance': rv.view_distance,
                             'projection': rv.view_perspective, 'lens': sp.lens,
                             'clip': [sp.clip_start, sp.clip_end], 'rotation': list(rv.view_rotation),
                             'shading': sp.shading.type, 'lock_camera': sp.lock_camera})
    return rows


def setup():
    scene = bpy.context.scene
    baseline = {'file': bpy.data.filepath, 'viewport': viewport_state(),
                'object_matrices': {o.name: [list(r) for r in o.matrix_world] for o in scene.objects if o.type in {'MESH', 'ARMATURE'}},
                'camera': {'name': scene.camera.name, 'projection': scene.camera.data.type, 'ortho_scale': scene.camera.data.ortho_scale}}
    coll = bpy.data.collections.get('MIA_REVIEW_V22')
    if coll is None:
        coll = bpy.data.collections.new('MIA_REVIEW_V22'); scene.collection.children.link(coll)

    def empty(name, location):
        obj = bpy.data.objects.get(name)
        if obj is None:
            obj = bpy.data.objects.new(name, None); coll.objects.link(obj)
        obj.location = location; obj.empty_display_size = .025
        obj.hide_render = True; obj.hide_set(True)
        return obj

    empty('MIA_REVIEW_FOOT_ORIGIN', (0, 0, 0))
    empty('MIA_REVIEW_BODY_CENTER', (0, 0, .85))
    empty('MIA_REVIEW_HEAD_CENTER', (0, -.02, 1.55))
    records = []
    for region, z, scale in [('Head', 1.55, .48), ('Face', 1.55, .29), ('Body', .85, 1.89)]:
        for view, yaw in [('Front', 0), ('LeftOblique', 45), ('RightOblique', -45), ('Profile', 90), ('Back', 180)]:
            name = 'MIA_REVIEW_' + region + '_' + view
            cam = bpy.data.objects.get(name)
            if cam is None:
                data = bpy.data.cameras.new(name); cam = bpy.data.objects.new(name, data); coll.objects.link(cam)
            t = math.radians(yaw); target = Vector((0, 0, z))
            cam.location = (2 * math.sin(t), -2 * math.cos(t), z)
            cam.rotation_euler = (target-cam.location).to_track_quat('-Z', 'Y').to_euler()
            cam.data.type = 'ORTHO'; cam.data.ortho_scale = scale
            cam.data.lens = 70; cam.data.clip_start = .001; cam.data.clip_end = 100
            cam.data.shift_x = cam.data.shift_y = 0
            cam.hide_set(True)
            records.append({'name': name, 'yaw': yaw, 'target': list(target), 'ortho_scale': scale})
    # Explicit scene lights for neutral/production material work; old emission-toon does not respond to them.
    for obj in scene.objects:
        if obj.type == 'LIGHT' and not obj.name.startswith('MIA_REVIEW_'):
            obj.hide_render = True; obj.hide_set(True)
    for name, pos, power, size in [('Key', (-.6, -1, 2.2), 60, 1), ('Fill', (.8, -.8, 1.8), 15, 1.5), ('Rim', (0, .9, 2.05), 8, .8)]:
        full = 'MIA_REVIEW_' + name
        lamp = bpy.data.objects.get(full)
        if lamp is None:
            light = bpy.data.lights.new(full, 'AREA'); lamp = bpy.data.objects.new(full, light); coll.objects.link(lamp)
        lamp.location = pos; lamp.rotation_euler = (Vector((0, 0, 1.55))-lamp.location).to_track_quat('-Z','Y').to_euler()
        lamp.data.energy = power; lamp.data.shape = 'DISK'; lamp.data.size = size; lamp.data.color = (1, 1, 1)
        lamp.hide_set(False); lamp.hide_render = False
    world = bpy.data.worlds.get('MIA_REVIEW_NeutralWorld') or bpy.data.worlds.new('MIA_REVIEW_NeutralWorld')
    world.use_nodes = True
    world.node_tree.nodes.clear()
    background = world.node_tree.nodes.new('ShaderNodeBackground')
    output = world.node_tree.nodes.new('ShaderNodeOutputWorld')
    world.node_tree.links.new(background.outputs['Background'], output.inputs['Surface'])
    background.inputs['Color'].default_value = (.18, .18, .18, 1)
    background.inputs['Strength'].default_value = .1
    scene.world = world
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100; scene.render.pixel_aspect_x = scene.render.pixel_aspect_y = 1
    scene.view_settings.view_transform = 'Standard'; scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0; scene.view_settings.gamma = 1
    scene.camera = bpy.data.objects['MIA_REVIEW_Head_Front']; scene.frame_set(1)
    scene.cursor.location = (0, 0, 0)
    scene.tool_settings.transform_pivot_point = 'MEDIAN_POINT'
    focus('head')
    after = {o.name: [list(r) for r in o.matrix_world] for o in scene.objects if o.type in {'MESH', 'ARMATURE'}}
    assert after == baseline['object_matrices'], 'Navigation setup must not move models or origins'
    return {'before': baseline, 'after_viewport': viewport_state(), 'camera_presets': records,
            'model_matrices_unchanged': True,
            'material_limit': 'Original emission-toon remains unchanged and does not respond to these scene area lights. Geometry/paint unchanged.'}


def focus(part='head', view='Front', distance=None, owner_name=None):
    z = 1.55 if part == 'head' else .85
    scene = bpy.context.scene
    camera = bpy.data.objects['MIA_REVIEW_' + ('Head' if part == 'head' else 'Body') + '_' + view]
    scene.camera = camera
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    name = owner_name or ('MIA_V14_SculptedSkin' if part == 'head' else 'MIA_V06_BODY_SKIN')
    owner = bpy.data.objects.get(name)
    if owner_name:
        assert owner is not None and owner.type == 'MESH', 'Requested review owner does not exist'
        assert not owner.hide_viewport and not owner.hide_get(), 'Requested review owner is hidden'
    if owner is not None:
        owner.select_set(True); bpy.context.view_layer.objects.active = owner
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type != 'VIEW_3D': continue
            sp, rv = area.spaces.active, area.spaces.active.region_3d
            rv.view_location = (0, 0, z)
            rv.view_distance = distance if distance is not None else (.63 if part == 'head' else 2.7)
            rv.view_rotation = camera.rotation_euler.to_quaternion()
            rv.view_perspective = 'ORTHO'
            sp.lens = 70; sp.clip_start = .001; sp.clip_end = 100; sp.lock_camera = False
            sp.shading.type = 'RENDERED'
            sp.shading.use_scene_lights_render = True; sp.shading.use_scene_world_render = True
            sp.overlay.show_overlays = False
            area.tag_redraw()


if __name__ == '__main__':
    report = setup()
    ROOT.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Mia_ReviewSetup_v22.blend'), check_existing=False)
    (ROOT/'live-setup-evidence.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('MIA_REVIEW_SETUP_READY')
