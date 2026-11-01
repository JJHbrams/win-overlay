"""Live actual-user-native eye junction inspection; all scene overrides restored."""
import bpy
import hashlib
import json
import math
from pathlib import Path
from mathutils import Vector

P=Path(__file__).resolve().parent
out=P/'outer-gap-live-diagnostic';out.mkdir(parents=True,exist_ok=True)
s=bpy.context.scene
native=Path(bpy.data.filepath)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
before=sha(native)
original_camera=s.camera
render_state=(s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage,s.render.filepath,s.render.image_settings.file_format,s.render.film_transparent)
hidden={o.name:o.hide_render for o in s.objects}
hair=[o for o in s.objects if o.type=='MESH' and (any(t in o.name for t in ['Hair','HAIR','Braid','Crown','Gather','RootLining','PIXAL']) or any('HAIR' in c.name.upper() for c in o.users_collection))]
lashes=[o for o in s.objects if o.type=='MESH' and ('Lashes_' in o.name or 'BoundaryRibbon' in o.name)]
skin=bpy.data.objects['MIA_V27_SharedHeadBody']
walls=[o for o in s.objects if o.name.startswith('V28G_InnerLid_')]
slots={o.name:[a.material for a in o.material_slots] for o in [skin]+walls}
gray=bpy.data.materials.new('V31_TemporaryDiagnosticGray');gray.use_nodes=True;n=gray.node_tree.nodes;n.clear();bs=n.new('ShaderNodeBsdfPrincipled');bs.inputs['Base Color'].default_value=(.23,.23,.23,1);bs.inputs['Roughness'].default_value=.85;mo=n.new('ShaderNodeOutputMaterial');mo.is_active_output=True;gray.node_tree.links.new(bs.outputs[0],mo.inputs['Surface'])
camdata=bpy.data.cameras.new('V31_TemporaryDiagnosticCamera');cam=bpy.data.objects.new(camdata.name,camdata);s.collection.objects.link(cam);camdata.type='ORTHO';camdata.ortho_scale=.090
records=[]
try:
 for o in hair:o.hide_render=True
 s.camera=cam;s.render.resolution_x=s.render.resolution_y=512;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.film_transparent=False
 for side,yaw,label in [(1,35,'outerRight35'),(1,65,'outerRight65'),(-1,-45,'outerLeft45')]:
  cap=bpy.data.objects['V28G_Sclera_'+str(side)];e=cap.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();points=[e.matrix_world@v.co for v in me.vertices];target=sum(points,Vector())/len(points);e.to_mesh_clear()
  y=math.radians(yaw);pitch=math.radians(-7)
  cam.location=target+Vector((.45*math.sin(y)*math.cos(pitch),-.45*math.cos(y)*math.cos(pitch),.45*math.sin(pitch)));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
  for mode in ['production','cleanGrayNoLashes']:
   for o in lashes:o.hide_render=True if mode=='cleanGrayNoLashes' else hidden[o.name]
   for o in [skin]+walls:o.material_slots[0].material=gray if mode=='cleanGrayNoLashes' else slots[o.name][0]
   bpy.context.view_layer.update();file=out/(label+'-'+mode+'.png');s.render.filepath=str(file);bpy.ops.render.render(write_still=True)
   records.append({'path':str(file),'sha256':sha(file),'native':str(native),'native_sha256':before,'side':side,'yaw':yaw,'pitch':-7,'projection':'ORTHO','ortho_scale':camdata.ortho_scale,'target':list(target),'camera_matrix':[list(r) for r in cam.matrix_world],'mode':mode,'hair_temporarily_hidden':[o.name for o in hair],'frame':s.frame_current,'active_master_keys':{k.name:k.value for k in bpy.data.objects['MIA_V27_Foundation_Face'].data.shape_keys.key_blocks if k.value}})
finally:
 for name,value in hidden.items():bpy.data.objects[name].hide_render=value
 for name,materials in slots.items():
  for i,m in enumerate(materials):bpy.data.objects[name].material_slots[i].material=m
 s.camera=original_camera
 s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage,s.render.filepath,s.render.image_settings.file_format,s.render.film_transparent=render_state
 bpy.data.objects.remove(cam,do_unlink=True);bpy.data.cameras.remove(camdata);bpy.data.materials.remove(gray)
 bpy.context.view_layer.update()
assert sha(native)==before
(out/'records.json').write_text(json.dumps({'records':records,'native_saved':False,'all_scene_overrides_restored':True,'mesh_origins_changed':False},indent=2),encoding='utf-8')
print(json.dumps({'views':len(records),'path':str(out),'native_sha256':before,'scene_restored':True}))
