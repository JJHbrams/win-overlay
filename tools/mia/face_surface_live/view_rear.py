"""Inspect depth and root underlap in the actual live rear hair trial."""
from pathlib import Path
import sys
import json
import bpy
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'asset/mia/blender/mia-fit-v003/body/surface-review12'))
import review_fixture as fixture
view=globals().get('MIA_VIEW_REQUEST','oblique')
yaw,pitch=dict(back=(180,0),profile=(90,0),oblique=(135,0),high=(145,30),low=(145,-25))[view]
target=(0,.04,1.49);scale=.53
fixture.aim(bpy.context.scene,yaw,pitch,target,scale,(768,768))
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type!='VIEW_3D':continue
        s=area.spaces.active;s.overlay.show_overlays=False;s.shading.type='SOLID';s.shading.color_type='MATERIAL'
        s.region_3d.view_location=target;s.region_3d.view_rotation=bpy.context.scene.camera.rotation_euler.to_quaternion()
        s.region_3d.view_distance=scale;s.region_3d.view_perspective='ORTHO'
print(json.dumps(dict(view=view,actual_camera=fixture.record(bpy.context.scene),native_saved=False)))
