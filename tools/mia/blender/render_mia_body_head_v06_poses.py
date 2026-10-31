"""Render expression and stress-pose proof without persisting pose changes."""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mia_world_pose_v09 import yaw_world, arm_forward_world

def parse():
 p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output-dir',required=True);p.add_argument('--cases',default='',help='Comma separated case names; empty renders all');return p.parse_args(sys.argv[sys.argv.index('--')+1:])
def digest(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def aim(c,l,t):c.location=l;c.rotation_euler=(Vector(t)-c.location).to_track_quat('-Z','Y').to_euler()
def review_camera(scene):
 for obj in scene.objects:
  if obj.type=='LIGHT':obj.hide_render=True
 data=bpy.data.cameras.new('MIA_V06_FINAL_POSE_CAMERA');data.type='ORTHO';obj=bpy.data.objects.new(data.name,data);scene.collection.objects.link(obj);scene.camera=obj
 for index,(loc,energy) in enumerate((((2.2,-2.9,2.7),240),((-2.0,-2.2,2.0),110),((0,2.4,2.4),150))):
  light=bpy.data.lights.new('MIA_V06_FINAL_POSE_LIGHT_%d'%index,'AREA');light.energy=energy;light.shape='DISK';light.size=2
  lo=bpy.data.objects.new(light.name,light);scene.collection.objects.link(lo);lo.location=loc;aim(lo,loc,(0,0,1.2))
 return obj
def main():
 a=parse();selected=set(filter(None,a.cases.split(',')));native=Path(a.input).resolve();out=Path(a.output_dir).resolve();out.mkdir(parents=True,exist_ok=True);bpy.ops.wm.open_mainfile(filepath=str(native));s=bpy.context.scene
 s.render.engine='BLENDER_EEVEE';s.render.resolution_x=s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
 face=bpy.data.objects['MIA_V06_FACE_SKIN'];body=bpy.data.objects['MIA_V06_BODY_SKIN'];rig=bpy.data.objects['MIA_V06_RIG'];cam=review_camera(s)
 for obj in s.objects:
  if obj.type=='MESH':obj.hide_render=obj not in (face,body)
 s.view_settings.view_transform='Standard';s.view_settings.look='Medium High Contrast';s.view_settings.exposure=0.0;s.view_settings.gamma=1.0
 keys=face.data.shape_keys.key_blocks; saved_keys={k.name:k.value for k in keys}; saved_bones={b.name:{'matrix_basis':b.matrix_basis.copy(),'rotation_mode':b.rotation_mode} for b in rig.pose.bones}
 report={'input_native':str(native),'input_native_sha256':digest(native),'script':str(Path(__file__).resolve()),'script_sha256':digest(Path(__file__).resolve()),'facial':[],'body':[],'neutral_return':{},'case_filter':sorted(selected),'world_pose_utility_sha256':digest(Path(__file__).with_name('mia_world_pose_v09.py'))}
 def render(name,pos,target):
  aim(cam,pos,target);s.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
 def face_views(name):
  cam.data.ortho_scale=.32
  for suffix,pos in [('front',(0,-1.5,1.55)),('three_quarter_l',(1.10,-1.10,1.55))]:render('face_'+name+'_'+suffix,pos,(0,.02,1.55))
 def identity_values():return {k.name:k.value for k in keys if k.name.startswith('MIA_FaceArt_')}
 def reset():
  for k in keys:k.value=saved_keys[k.name]
  for b in rig.pose.bones:b.rotation_mode=saved_bones[b.name]['rotation_mode'];b.matrix_basis=saved_bones[b.name]['matrix_basis'].copy()
  bpy.context.view_layer.update()
 def eyes(dx,dz):
  actual=[]
  for n in ('J_Adj_L_FaceEye','J_Adj_R_FaceEye'):
   b=rig.pose.bones.get(n)
   if b:b.rotation_mode='XYZ';b.rotation_euler=(dz,0,dx);actual.append(n)
  return actual
 for name,dx,dz in [('neutral',0,0),('gaze_l',.16,0),('gaze_r',-.16,0),('gaze_u',0,.13),('gaze_d',0,-.13)]:
  if selected and name not in selected:continue
  reset();used=eyes(dx,dz);actual={n:list(rig.pose.bones[n].rotation_euler) for n in used};face_views(name);report['facial'].append({'case':name,'eye_bones':used,'local_rotation':[dx,dz],'actual_rotation_euler':actual,'identity_profile_actual_values':identity_values(),'views':['front','three_quarter_l']})
 for name,key,value in [('blink_half','Fcl_EYE_Close',.5),('blink_full','Fcl_EYE_Close',1),('mouth_a','Fcl_MTH_A',1),('mouth_sorrow','Fcl_MTH_Sorrow',.8)]:
  if selected and name not in selected:continue
  reset();m=next((k for k in keys if k.name.endswith(key)),None)
  if m:m.value=value
  face_views(name);report['facial'].append({'case':name,'key':m.name if m else None,'value':value,'identity_profile_actual_values':identity_values(),'views':['front','three_quarter_l']})
 # Neutral-only elevation checks reveal brow/eyelid and cap plane collapse.
 reset();cam.data.ortho_scale=.32
 for name,pos in [('neutral_up_10deg',(0,-1.477,1.81)),('neutral_down_10deg',(0,-1.477,1.29))]:
  if not selected or name in selected:render('face_'+name,pos,(0,.02,1.55))
 if not selected:report['facial'].append({'case':'neutral_elevation_checks','identity_profile_actual_values':identity_values(),'views':['up_10deg','down_10deg']})
 for name,bone,rot in [('arm_raise','J_Bip_L_UpperArm',(-.3,0,0)),('arm_forward','J_Bip_R_UpperArm',(-1.08,.45,0)),('torso_yaw','J_Bip_C_Chest',(0,0,.26)),('knee_bend','J_Bip_L_LowerLeg',(.42,0,0))]:
  if selected and name not in selected:continue
  reset();b=rig.pose.bones.get(bone);world_proof=None
  if b and name=='torso_yaw':world_proof=yaw_world(rig,b,.26)
  elif b and name=='arm_forward':world_proof=arm_forward_world(rig,b)
  elif b:b.rotation_mode='XYZ';b.rotation_euler=rot
  bpy.context.view_layer.update()
  cam.data.ortho_scale=1.9
  for view,pos in [('front',(0,-3.35,1.0)),('three_quarter_l',(2.25,-2.65,1.0))]:render('body_%s_%s'%(name,view),pos,(0,0,.95))
  report['body'].append({'case':name,'bone':bone,'legacy_local_rotation':rot,'world_pose_proof':world_proof,'actual_rotation_euler':list(b.rotation_euler) if b else None,'views':['front','three_quarter_l']})
 reset();cam.data.ortho_scale=1.9
 if not selected or 'neutral_return' in selected:render('neutral_return_front',(0,-3.35,1.0),(0,0,.95));render('neutral_return_three_quarter_l',(2.25,-2.65,1.0),(0,0,.95))
 report['neutral_return']={'shape_keys_restored':all(k.value==saved_keys[k.name] for k in keys),'bones_restored':all(b.matrix_basis==saved_bones[b.name]['matrix_basis'] and b.rotation_mode==saved_bones[b.name]['rotation_mode'] for b in rig.pose.bones)}
 report['input_native_sha256_after']=digest(native)
 assert report['input_native_sha256_after']==report['input_native_sha256']
 assert report['neutral_return']['shape_keys_restored'] and report['neutral_return']['bones_restored']
 (out/'pose-proof-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
if __name__=='__main__':main()
