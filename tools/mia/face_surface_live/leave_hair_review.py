"""Return the borrowed camera, viewport and source visibility, never body geometry."""
import hashlib
import json
import bpy
import numpy as np

state = bpy.app.driver_namespace['MIA_HairReviewState']
body = bpy.data.objects['MIA_Review12_H_LiveRepair']
assert hashlib.sha256(np.array([v.co[:] for v in body.data.vertices], np.float32).tobytes()).hexdigest() == state['body_sha256']
if bpy.context.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
for name, (hidden, render, selected) in state['objects'].items():
    ob = bpy.data.objects.get(name)
    if ob is not None:
        ob.hide_set(hidden); ob.hide_render = render; ob.select_set(selected)
bpy.context.view_layer.objects.active = state['active']
scene = bpy.context.scene
scene.camera = state['camera']; scene.camera.matrix_world = state['camera_matrix']
scene.camera.data.ortho_scale = state['camera_scale']
scene.camera['MIA12_target_world'] = state['camera_target']
scene.render.resolution_x, scene.render.resolution_y = state['resolution']
for s, shading, color, overlay, loc, rot, distance, perspective in state['viewport']:
    s.shading.type = shading; s.shading.color_type = color; s.overlay.show_overlays = overlay
    s.region_3d.view_location = loc; s.region_3d.view_rotation = rot
    s.region_3d.view_distance = distance; s.region_3d.view_perspective = perspective
bpy.context.view_layer.update()
bpy.app.driver_namespace['MIA_HairReviewStateFinished'] = state
del bpy.app.driver_namespace['MIA_HairReviewState']
print(json.dumps(dict(borrowed_state_restored=True, body_sha256=state['body_sha256'],
                      native_saved=False, source_geometry_modified=False)))
