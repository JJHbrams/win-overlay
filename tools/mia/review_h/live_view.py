"""Set an actual live review view or toggle a reversible before/after mask."""
from pathlib import Path
import hashlib
import json
import sys
import bpy
import numpy as np

ROOT = Path('D:/MiaWorkCache/mia-reference-work/win-overlay')
sys.path.insert(0, str(ROOT/'asset/mia/blender/mia-fit-v003/body/surface-review12'))
import review_fixture as fixture

name = globals().get('MIA_VIEW_REQUEST', 'profile')
body = bpy.data.objects['MIA_Review12_H_LiveRepair']
ns = bpy.app.driver_namespace
if body.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
if name == 'mask_before':
    ns['MIA_Live_Neck_Operation_After'] = np.array([v.co[:] for v in body.data.vertices], np.float32)
    body.data.vertices.foreach_set('co', ns['MIA_Live_Neck_Operation_Before'].ravel()); body.data.update()
elif name == 'profile_after':
    assert 'MIA_Live_UpperFair_After' not in ns, 'Do not restore a stale earlier operation after a later edit'
    body.data.vertices.foreach_set('co', ns['MIA_Live_Neck_Operation_After'].ravel()); body.data.update()

jobs = dict(front=(0,0), profile=(90,0), back=(180,0), oblique=(35,0),
            high=(40,25), low=(-40,-25), mask_before=(35,10), profile_after=(90,0))
yaw, pitch = jobs[name]
target = (0,.005,1.42); scale = .42
fixture.aim(bpy.context.scene, yaw, pitch, target, scale, (800,800))
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type != 'VIEW_3D': continue
        space = area.spaces.active
        space.clip_start = .1; space.clip_end = 10
        space.shading.color_type = 'SINGLE'
        space.shading.single_color = (.58, .58, .58)
        space.region_3d.view_location = target
        space.region_3d.view_distance = scale
        space.region_3d.view_rotation = bpy.context.scene.camera.rotation_euler.to_quaternion()
        space.region_3d.view_perspective = 'ORTHO'
        space.overlay.show_overlays = name == 'mask_before'
        for attr in ['show_extras','show_relationship_lines','show_bones','show_floor','show_axis_x','show_axis_y']:
            if hasattr(space.overlay, attr): setattr(space.overlay, attr, False)
if name == 'mask_before': bpy.ops.object.mode_set(mode='EDIT')
bpy.context.view_layer.update()
coordinates = np.array([v.co[:] for v in body.data.vertices], np.float32)
print(json.dumps(dict(view=name, state='before selected neck interior' if name=='mask_before' else 'current live candidate',
                      world_sha256=hashlib.sha256(coordinates.tobytes()).hexdigest(),
                      camera=fixture.record(bpy.context.scene),
                      native_saved=False)))
