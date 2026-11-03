"""Actual live geometry view; root lends camera/visibility and receives them back."""
from pathlib import Path
import json
import hashlib
import sys
import bpy
import numpy as np
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'asset/mia/blender/mia-fit-v003/body/surface-review12'))
import review_fixture as fixture

state = bpy.app.driver_namespace['MIA_HairReviewState']
body = bpy.data.objects['MIA_Review12_H_LiveRepair']
assert hashlib.sha256(np.array([v.co[:] for v in body.data.vertices], np.float32).tobytes()).hexdigest() == state['body_sha256']
view = globals().get('MIA_VIEW_REQUEST', 'front')
scene = bpy.context.scene
if bpy.context.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
if view == 'front':
    records = json.loads((ROOT/'asset/mia/blender/mia-refinement-v002/review/integrated-R3b/source/render-records.json').read_text())
    record = next(r['camera'] for r in records if r['id'] == 'front-hairON')
    scene.camera.matrix_world = Matrix(record['matrix'])
    scene.camera.data.ortho_scale = record['ortho_scale']
    scene.render.resolution_x = scene.render.resolution_y = 768
    target = (0, 0, 1.55)
else:
    yaw, pitch = dict(back=(180,0), profile=(90,0), oblique=(35,0), high=(40,30), low=(-40,-25))[view]
    target = (0, .04, 1.49) if view == 'back' else (0, 0, 1.55)
    fixture.aim(scene, yaw, pitch, target, .53 if view == 'back' else .36, (768,768))
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type != 'VIEW_3D': continue
        s = area.spaces.active
        s.shading.type = 'SOLID'
        s.shading.color_type = 'MATERIAL'
        s.overlay.show_overlays = False
        s.region_3d.view_location = target
        s.region_3d.view_rotation = scene.camera.rotation_euler.to_quaternion()
        s.region_3d.view_distance = scene.camera.data.ortho_scale
        s.region_3d.view_perspective = 'ORTHO'
        s.clip_start = .1; s.clip_end = 10
bpy.context.view_layer.update()
print(json.dumps(dict(view=view, actual_camera=fixture.record(scene), body_preserved=True,
                      geometry_modified=False, native_saved=False)))
