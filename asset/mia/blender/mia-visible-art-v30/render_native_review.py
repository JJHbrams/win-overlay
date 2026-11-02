"""Actual immutable-native source/critical/orbit renders; no display fitting in Blender."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import sys
import bpy
from mathutils import Matrix, Vector

P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser()
ap.add_argument('--native',required=True)
ap.add_argument('--sha256',required=True)
ap.add_argument('--tag',required=True)
ap.add_argument('--preset',choices=['source','critical','orbit'],default='source')
ap.add_argument('--only',default='')
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
native=Path(a.native).resolve()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(native)==a.sha256
out=P/'reviews'/a.tag/a.preset
out.mkdir(parents=True,exist_ok=True)
oldpath=P.parent/'mia-orbit-thorax-review-v28/reviews/G2L-face/reference-review.json'
pkg=json.loads(oldpath.read_text())
spec=pkg['views'][0]['candidate_camera']
bpy.ops.wm.open_mainfile(filepath=str(native),use_scripts=False)
s=bpy.context.scene;s.frame_set(1)
master=bpy.data.objects['MIA_V27_Foundation_Face']
for k in master.data.shape_keys.key_blocks:k.value=0
rig=next(m.object for m in master.modifiers if m.type=='ARMATURE')
head=rig.pose.bones['J_Bip_C_Head']
head.matrix_basis=Matrix(spec['head_eye_pose']['head_matrix_basis'])
for o in s.objects:
 if o.type=='LIGHT':o.hide_render=True
lamps=[]
for i,l in enumerate(spec['lighting']['areas']):
 data=bpy.data.lights.new('V30_Review_'+str(i),'AREA');data.energy=l['watts'];data.shape=l['shape'];data.size=l['size'];data.color=l['color']
 ob=bpy.data.objects.new(data.name,data);s.collection.objects.link(ob);ob.matrix_world=Matrix(l['matrix']);lamps.append(ob)
w=bpy.data.worlds.new('V30_ActualReviewWorld');w.use_nodes=True;n=w.node_tree.nodes;n.clear();bg=n.new('ShaderNodeBackground');wo=n.new('ShaderNodeOutputWorld');wo.is_active_output=True;w.node_tree.links.new(bg.outputs[0],wo.inputs['Surface']);bg.inputs['Color'].default_value=(*spec['lighting']['world_linear'],1);bg.inputs['Strength'].default_value=spec['lighting']['world_strength'];s.world=w
s.render.engine='BLENDER_EEVEE';s.render.use_freestyle=False;s.render.film_transparent=False;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA'
cm=spec['color_management'];s.view_settings.view_transform=cm['view_transform'];s.view_settings.look=cm['look'];s.view_settings.exposure=cm['exposure'];s.view_settings.gamma=cm['gamma']
cam=bpy.data.objects.new('V30_ReviewCamera',bpy.data.cameras.new('V30_ReviewCamera'));s.collection.objects.link(cam);cam.data.type='ORTHO';cam.data.clip_start=.1;cam.data.clip_end=10.;s.camera=cam
hair=[o for o in s.objects if o.type=='MESH' and not o.hide_render and
 (any(x in o.name for x in ['Hair','HAIR','Braid','Crown','Gather','RootLining','PIXAL']) or any('HAIR' in c.name.upper() for c in o.users_collection))]
skin=bpy.data.objects['MIA_V27_SharedHeadBody'];walls=[o for o in s.objects if o.name.startswith('V28G_InnerLid_')]
original={o.name:list(o.data.materials) for o in [skin]+walls}
gray=bpy.data.materials.new('V30_ActualNeutralGray');gray.use_nodes=True;gn=gray.node_tree.nodes;gn.clear();bs=gn.new('ShaderNodeBsdfPrincipled');bs.inputs['Base Color'].default_value=(.23,.23,.23,1);bs.inputs['Roughness'].default_value=.85;go=gn.new('ShaderNodeOutputMaterial');go.is_active_output=True;gray.node_tree.links.new(bs.outputs[0],go.inputs['Surface'])
records=[]
def render(label,v,hide=False,neutral=False):
 if a.only and a.only not in label:return
 for o in hair:o.hide_render=hide
 for o in [skin]+walls:
  for i,m in enumerate(original[o.name]):o.data.materials[i]=gray if neutral else m
 cam.matrix_world=Matrix(v['matrix']);cam.data.ortho_scale=v['ortho_scale'];cam.data.shift_x,cam.data.shift_y=v['lens_shift'];s.render.resolution_x,s.render.resolution_y=v['resolution'];s.render.pixel_aspect_x,s.render.pixel_aspect_y=v['pixel_aspect'];bpy.context.view_layer.update()
 file=out/(label+'.png');assert not file.exists(),'Use a new immutable review tag'
 s.render.filepath=str(file);bpy.ops.render.render(write_still=True)
 actual=copy.deepcopy(v);actual.update(matrix=[list(r) for r in cam.matrix_world],ortho_scale=cam.data.ortho_scale,clip_start=cam.data.clip_start,clip_end=cam.data.clip_end,resolution=[s.render.resolution_x,s.render.resolution_y],pixel_aspect=[s.render.pixel_aspect_x,s.render.pixel_aspect_y],lens_shift=[cam.data.shift_x,cam.data.shift_y],frame=s.frame_current,active_shape_keys={k.name:k.value for k in master.data.shape_keys.key_blocks if k.value})
 actual['head_eye_pose']={'armature':rig.name,'head_bone':head.name,'head_matrix_basis':[list(r) for r in head.matrix_basis],'eye_pose':'rest; master shape keys recorded above'}
 actual['lighting']['areas']=[dict(item,matrix=[list(r) for r in o.matrix_world],watts=o.data.energy,shape=o.data.shape,size=o.data.size,color=list(o.data.color)) for item,o in zip(v['lighting']['areas'],lamps)]
 actual['lighting']['world_linear']=list(bg.inputs['Color'].default_value)[:3];actual['lighting']['world_strength']=bg.inputs['Strength'].default_value
 records.append({'id':label,'native':str(native),'native_sha256':a.sha256,'renderer_sha256':sha(Path(__file__)),'path':str(file),'sha256':sha(file),'camera':actual,'material_mode':'neutral physical gray.23 rough.85' if neutral else 'actual default production','hair_temporarily_hidden':[o.name for o in hair] if hide else [],'native_saved':False})
 (out/'render-records.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
if a.preset=='source':
 for row in pkg['views']:
  v=row['candidate_camera']
  for label,hide,neutral in [('hairON',False,False),('hairOFF',True,False),('neutral',True,True)]:render(row['id']+'-'+label,v,hide,neutral)
else:
 angles=([('highFront',0,45),('lowFront',0,-30),('lowRight',35,-30),('lowLeft',-35,-30),('highLeft',-35,40),('profileLow',85,-20)] if a.preset=='critical' else [(f'{i:03}',i*15,8+17*math.sin(math.radians(i*30))) for i in range(24)])
 for label,yaw,pitch in angles:
  y,p=math.radians(yaw),math.radians(pitch);target=Vector((0,0,1.55));cam.location=target+Vector((2*math.sin(y)*math.cos(p),-2*math.cos(y)*math.cos(p),2*math.sin(p)));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();bpy.context.view_layer.update();v=copy.deepcopy(spec);v['matrix']=[list(r) for r in cam.matrix_world];v['ortho_scale']=.29 if a.preset=='critical' else .36;v['resolution']=[640,640] if a.preset=='critical' else [512,512];v['estimated_yaw_pitch_roll_deg']=[yaw,pitch,0]
  render(label+'-production',v,a.preset=='critical')
  if a.preset=='critical':render(label+'-neutral',v,True,True)
assert sha(native)==a.sha256
print('V30_ACTUAL_REVIEW_DONE',a.tag,a.preset,len(records),flush=True)
