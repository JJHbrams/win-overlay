"""Live saved WIP camera/light scene, two actual renders, no asset save."""
import bpy,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;native=Path(REVIEW_NATIVE).resolve()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(native)==REVIEW_SHA
bpy.ops.wm.open_mainfile(filepath=str(native),use_scripts=False)
s=bpy.context.scene;cam=s.camera;assert cam.name=='MIA_Review_front' and cam.data.type=='ORTHO' and cam.data.clip_end==10
out=P/'live'/REVIEW_TAG;out.mkdir(parents=True,exist_ok=True)
s.render.resolution_x=s.render.resolution_y=512;s.render.resolution_percentage=100
for ob in bpy.context.view_layer.objects:ob.select_set(False)
for window in bpy.context.window_manager.windows:
 for area in window.screen.areas:
  if area.type=='VIEW_3D':
   v=area.spaces.active;v.clip_start=.001;v.clip_end=10;v.region_3d.view_location=(0,0,1.55);v.region_3d.view_distance=.45;v.region_3d.view_perspective='ORTHO';v.region_3d.view_rotation=cam.rotation_euler.to_quaternion();v.shading.type='MATERIAL';v.shading.use_scene_lights=True;v.shading.use_scene_world=True;v.overlay.show_overlays=False
import importlib.util
ownership_spec=importlib.util.spec_from_file_location('mia_review_ownership',P/'component_ownership.py')
ownership=importlib.util.module_from_spec(ownership_spec);ownership_spec.loader.exec_module(ownership)
hair=[ob for ob in s.objects if ob.type=='MESH' and not ob.hide_render and ownership.is_hair_object(ob)]
records=[]
try:
 for hide in [False,True]:
  for ob in hair:ob.hide_render=hide
  bpy.context.view_layer.update();f=out/('head-hairOFF.png' if hide else 'head-hairON.png');assert not f.exists();s.render.filepath=str(f);bpy.ops.render.render(write_still=True)
  records.append({'path':str(f),'sha256':sha(f),'hair_hidden':hide})
finally:
 for ob in hair:ob.hide_render=False
bpy.context.view_layer.update();assert sha(native)==REVIEW_SHA
report={'native':str(native),'native_sha256':REVIEW_SHA,'native_saved':False,'runtime_only_resolution512':True,'camera':{'name':cam.name,'projection':cam.data.type,'matrix':[list(r) for r in cam.matrix_world],'ortho_scale':cam.data.ortho_scale,'clip_start':cam.data.clip_start,'clip_end':cam.data.clip_end},'head_pivot':[0,0,1.55],'mesh_origins_changed':False,'images':records,'status':globals().get('REVIEW_STATUS','Working review only. Full face/hair/body source ART remains open.')}
(out/'live-review.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
