"""Whole-height source fixture and high/low checks on the same live hair WIP."""
from pathlib import Path
import sys
import json
import hashlib
import bpy
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'asset/mia/blender/mia-fit-v003/body/surface-review12'))
import review_fixture as fixture
assert bpy.app.driver_namespace['MIA_CurvedRear03Base']['provisional_keep']
view=globals().get('MIA_VIEW_REQUEST','front')
if view in ('high','low'):
    yaw,pitch=(40,30) if view=='high' else (-40,-25)
    target=(0,.035,1.39);scale=.83;resolution=(800,800)
else:
    yaw,pitch=dict(front=(0,0),profile=(90,0),back=(180,0),oblique=(30,0))[view]
    target=fixture.FULL_TARGET;scale=fixture.FULL_SCALE;resolution=fixture.FULL_RES
fixture.aim(bpy.context.scene,yaw,pitch,target,scale,resolution)
review=bpy.app.driver_namespace['MIA_HairReviewState']
if 'camera_view' not in review:
    review['camera_view']=[]
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                r=area.spaces.active.region_3d
                review['camera_view'].append((r,r.view_camera_zoom,tuple(r.view_camera_offset)))
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type!='VIEW_3D':continue
        s=area.spaces.active;s.shading.type='SOLID';s.shading.color_type='MATERIAL';s.overlay.show_overlays=False
        s.region_3d.view_location=target;s.region_3d.view_rotation=bpy.context.scene.camera.rotation_euler.to_quaternion()
        s.region_3d.view_distance=scale;s.region_3d.view_perspective='CAMERA'
        s.region_3d.view_camera_zoom=0;s.region_3d.view_camera_offset=(0,0)
body=bpy.data.objects['MIA_Review12_H_LiveRepair']
body_sha=hashlib.sha256(np.array([v.co[:] for v in body.data.vertices],np.float32).tobytes()).hexdigest()
assert body_sha==bpy.app.driver_namespace['MIA_HairReviewState']['body_sha256']
print(json.dumps(dict(view=view,actual_camera=fixture.record(bpy.context.scene),body_sha256=body_sha,
                      scope='Actual solid viewport diagnostic. Viewport raster is not claimed to equal the saved camera raster.',ART=False,native_saved=False)))
