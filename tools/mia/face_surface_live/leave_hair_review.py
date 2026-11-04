"""Return the borrowed camera, viewport and source visibility, never body geometry."""
import hashlib
import json
import bpy
import numpy as np

state = bpy.app.driver_namespace['MIA_HairReviewState']
body = bpy.data.objects['MIA_Review12_H_LiveRepair']
assert hashlib.sha256(np.array([v.co[:] for v in body.data.vertices], np.float32).tobytes()).hexdigest() == state['body_sha256']
if bpy.context.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
main=bpy.data.objects['MIA_V17_PIXAL_DetailedHair']
for domain,values in state.get('main_selection',{}).items():
    for item,value in zip(getattr(main.data,domain),values):item.select=bool(value)
if 'mesh_select_mode' in state:bpy.context.tool_settings.mesh_select_mode=state['mesh_select_mode']
for name, (hidden, render, selected) in state['objects'].items():
    ob = bpy.data.objects.get(name)
    if ob is not None:
        ob.hide_set(hidden); ob.hide_render = render; ob.select_set(selected)
replacement=state.get('retained_replacement')
if replacement:
    original=bpy.data.objects[replacement['source']]
    old_hidden,old_render,_=state['objects'][original.name]
    original.hide_set(True);original.hide_render=True
    for ob in bpy.app.driver_namespace[replacement['namespace']]['objects']:
        ob.hide_set(old_hidden);ob.hide_render=old_render;ob.select_set(False)
bpy.context.view_layer.objects.active = state['active']
scene = bpy.context.scene
scene.camera = state['camera']
channels = state.get('camera_channels')
if channels:
    # Restore exact channels instead of decomposing a matrix again. Repeated
    # camera-matrix roundtrips otherwise introduce one-ULP fixture drift.
    scene.camera.rotation_mode = channels['rotation_mode']
    rotation = ('rotation_quaternion' if channels['rotation_mode'] == 'QUATERNION' else
                'rotation_axis_angle' if channels['rotation_mode'] == 'AXIS_ANGLE' else 'rotation_euler')
    for name in ('location', 'scale', rotation):
        setattr(scene.camera, name, channels[name])
elif scene.camera.matrix_world != state['camera_matrix']:
    scene.camera.matrix_world = state['camera_matrix']
scene.camera.data.ortho_scale = state['camera_scale']
scene.camera['MIA12_target_world'] = state['camera_target']
scene.render.resolution_x, scene.render.resolution_y = state['resolution']
for s, shading, color, overlay, loc, rot, distance, perspective in state['viewport']:
    s.shading.type = shading; s.shading.color_type = color; s.overlay.show_overlays = overlay
    s.region_3d.view_location = loc; s.region_3d.view_rotation = rot
    s.region_3d.view_distance = distance; s.region_3d.view_perspective = perspective
for r,zoom,offset in state.get('camera_view',[]):
    r.view_camera_zoom=zoom;r.view_camera_offset=offset
bpy.context.view_layer.update()
if channels:
    assert scene.camera.matrix_world == state['camera_matrix'], 'Borrowed camera channels did not restore exactly'
bpy.app.driver_namespace['MIA_HairReviewStateFinished'] = state
del bpy.app.driver_namespace['MIA_HairReviewState']
print(json.dumps(dict(borrowed_state_restored=True, body_sha256=state['body_sha256'],
                      camera_channels_restored_exactly=bool(channels),
                      retained_modular_replacement=bool(replacement),
                      native_saved=False, source_geometry_modified=False)))
