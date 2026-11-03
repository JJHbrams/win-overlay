"""Shared review fixture, actual design cage, camera state restored on exit."""
from pathlib import Path
import sys,json,hashlib
import bpy,numpy as np
ROOT=Path('D:/MiaWorkCache/mia-reference-work/win-overlay');ns=bpy.app.driver_namespace
sys.path.insert(0,str(ROOT/'asset/mia/blender/mia-fit-v003/body/surface-review12'))
import review_fixture as fixture
object_name='MIA_ChartedBody_Design' if 'MIA_ChartedBody_Design' in bpy.data.objects else 'MIA_ConnectedBody_Design'
prefix='MIA_Charted_' if object_name=='MIA_ChartedBody_Design' else 'MIA_Connected_'
ob=bpy.data.objects[object_name]
mode=ob.mode
if mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
scene=bpy.context.scene;cam=scene.camera
if prefix+'Camera' not in ns:
    ns[prefix+'Camera']=dict(matrix=cam.matrix_world.copy(),type=cam.data.type,ortho_scale=cam.data.ortho_scale,lens=cam.data.lens,
        clip_start=cam.data.clip_start,clip_end=cam.data.clip_end,resolution_x=scene.render.resolution_x,resolution_y=scene.render.resolution_y,
        resolution_percentage=scene.render.resolution_percentage,pixel_aspect_x=scene.render.pixel_aspect_x,pixel_aspect_y=scene.render.pixel_aspect_y)
    ns[prefix+'Viewport']=[(area.spaces.active,dict(location=area.spaces.active.region_3d.view_location.copy(),
        rotation=area.spaces.active.region_3d.view_rotation.copy(),distance=area.spaces.active.region_3d.view_distance,
        perspective=area.spaces.active.region_3d.view_perspective,clip_start=area.spaces.active.clip_start,clip_end=area.spaces.active.clip_end,
        shading_type=area.spaces.active.shading.type,color_type=area.spaces.active.shading.color_type,
        single_color=tuple(area.spaces.active.shading.single_color))) for screen in bpy.data.screens for area in screen.areas if area.type=='VIEW_3D']
name=globals().get('MIA_VIEW_REQUEST','front')
yaw,pitch=dict(front=(0,0),profile=(90,0),back=(180,0),oblique=(35,0),high=(40,25),low=(-40,-25))[name]
target=(0.,-.01,1.36);scale=.82
fixture.aim(scene,yaw,pitch,target,scale,(800,800))
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type!='VIEW_3D':continue
        s=area.spaces.active;s.clip_start=.1;s.clip_end=10.;s.shading.type='SOLID';s.shading.color_type='SINGLE';s.shading.single_color=(.58,.58,.58)
        s.region_3d.view_location=target;s.region_3d.view_distance=scale;s.region_3d.view_rotation=cam.rotation_euler.to_quaternion();s.region_3d.view_perspective='ORTHO'
        s.overlay.show_overlays=mode=='EDIT'
if mode=='EDIT':bpy.ops.object.mode_set(mode='EDIT')
co=np.array([p.co[:]for p in ob.data.vertices],np.float32)
print(json.dumps(dict(view=name,shown_object=ob.name,mode=mode,geometry_local_sha256=hashlib.sha256(co.tobytes()).hexdigest(),camera=fixture.record(scene),native_saved=False)))
