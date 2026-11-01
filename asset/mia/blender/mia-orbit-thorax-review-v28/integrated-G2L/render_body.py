"""Read-only matched orthographic body/chest renders of the actual saved native."""
import bpy, json, math, hashlib, sys, argparse
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--native',required=True);ap.add_argument('--role',required=True);ap.add_argument('--mode',default='clay');ap.add_argument('--views',default='front,profile,back,oblique,yaw30,yaw60,low,high');ap.add_argument('--pose',type=float,default=0);ap.add_argument('--orbit',action='store_true');a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
S=Path(a.native);OUT=P/'renders'/a.role/(a.mode+('-pose-'+str(a.pose) if a.pose else '')+('-orbit' if a.orbit else ''));OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
digest=sha(S);bpy.ops.wm.open_mainfile(filepath=str(S),use_scripts=False);s=bpy.context.scene;s.frame_set(1)
for o in s.objects:
 if o.type=='MESH' and o.data.shape_keys:
  for k in o.data.shape_keys.key_blocks[1:]:k.value=0
owner=bpy.data.objects['MIA_V27_SharedHeadBody'];arm=next(mod.object for mod in owner.modifiers if mod.type=='ARMATURE');pose_before={name:arm.pose.bones[name].matrix.copy() for name in ['J_Bip_L_UpperArm','J_Bip_R_UpperArm']}
if a.pose:
 for name,sign in [('J_Bip_L_UpperArm',-1),('J_Bip_R_UpperArm',1)]:
  bone=arm.pose.bones[name];head=(arm.matrix_world@pose_before[name]).translation;rot=Matrix.Translation(head)@Matrix.Rotation(math.radians(a.pose)*sign,4,'Y')@Matrix.Translation(-head);bone.matrix=arm.matrix_world.inverted()@rot@arm.matrix_world@pose_before[name]
bpy.context.view_layer.update()
pose_record={'diagnostic_degrees':a.pose,'method':'Bilateral upper-arm world-Y rotations about native joint heads; +20 raises arms, -20 lowers arms; saved rig unchanged','armature_object':arm.name,'armature_matrix':[list(r) for r in arm.matrix_world],'body_matrix':[list(r) for r in owner.matrix_world],'pose_basis':{b.name:[list(r) for r in b.matrix_basis] for b in arm.pose.bones if any(t in b.name for t in ['UpperArm','Shoulder','Chest','Spine','Neck','Head'])}}
def visible():
 ids=set()
 def walk(lc,h=False):
  h=h or lc.exclude or lc.collection.hide_render
  if not h:ids.update(q.as_pointer() for q in lc.collection.objects)
  for c in lc.children:walk(c,h)
 walk(bpy.context.view_layer.layer_collection)
 return [q for q in s.objects if q.type=='MESH' and q.as_pointer() in ids and not q.hide_render]
members={o.as_pointer() for c in bpy.data.collections if 'HAIR' in c.name.upper() for o in c.all_objects}
for o in s.objects:
 if o.type=='MESH' and (o.as_pointer() in members or any(t in o.name for t in ['Hair','HAIR','PIXAL','Braid','Gather','RootLining'])):o.hide_render=True
if a.mode in ('clay','geometry-clay','owner-clay','subsurf-clay','armature-clay'):
 if a.mode in ('owner-clay','subsurf-clay','armature-clay'):
  for o in s.objects:
   if o.type=='MESH' and o.name!='MIA_V27_SharedHeadBody':o.hide_render=True
 m=bpy.data.materials.new('ThoraxReview_Clay');m.use_nodes=True;n=m.node_tree.nodes;n.clear();d=n.new('ShaderNodeBsdfDiffuse');d.inputs['Color'].default_value=(.33,.33,.33,1);out=n.new('ShaderNodeOutputMaterial');out.is_active_output=True;m.node_tree.links.new(d.outputs[0],out.inputs[0])
 for o in visible():
  for slot in o.material_slots:slot.material=m
  if a.mode in ('geometry-clay','owner-clay','subsurf-clay','armature-clay'):
   for mod in o.modifiers:
    if mod.type=='NODES' and 'Outline' in mod.name:mod.show_render=False;mod.show_viewport=False
 if a.mode in ('subsurf-clay','armature-clay'):
  owner=bpy.data.objects['MIA_V27_SharedHeadBody']
  for mod in owner.modifiers:
   if mod.type=='SMOOTH' or (a.mode=='armature-clay' and mod.type in ('WELD','SUBSURF')):mod.show_render=False;mod.show_viewport=False
s.render.engine='BLENDER_EEVEE';s.render.use_freestyle=False;s.render.resolution_x=512 if a.orbit else 700;s.render.resolution_y=512 if a.orbit else 800;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.render.film_transparent=True
s.render.pixel_aspect_x=s.render.pixel_aspect_y=1
s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
world=bpy.data.worlds.new('ThoraxReview_World');world.use_nodes=True;bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.18,.18,.18,1);bg.inputs['Strength'].default_value=.15;s.world=world
wout=next(n for n in world.node_tree.nodes if n.type=='OUTPUT_WORLD');wout.is_active_output=True;assert wout.inputs['Surface'].is_linked and wout.inputs['Surface'].links[0].from_node==bg
shader_audit={'world':{'active_output':wout.name,'linked_background':bg.name,'color':list(bg.inputs['Color'].default_value),'strength':bg.inputs['Strength'].default_value},'clay':None}
if a.mode in ('clay','geometry-clay','owner-clay','subsurf-clay','armature-clay'):
 assert out.is_active_output and out.inputs['Surface'].links[0].from_node==d
 shader_audit['clay']={'active_output':out.name,'linked_node':d.name,'type':d.bl_idname,'color':list(d.inputs['Color'].default_value),'roughness':d.inputs['Roughness'].default_value}
for o in s.objects:
 if o.type=='LIGHT':o.hide_render=True
def aim(o,loc,t):o.location=loc;o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()
lamps=[]
for nm,power,size in [('Key',110,1.3),('Fill',38,1.4),('Rim',22,1)]:
 d=bpy.data.lights.new('ThoraxReview_'+nm,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(d.name,d);s.collection.objects.link(o);lamps.append(o)
d=bpy.data.cameras.new('ThoraxReview_Camera');cam=bpy.data.objects.new(d.name,d);s.collection.objects.link(cam);s.camera=cam;d.type='ORTHO';d.ortho_scale=.56 if a.orbit else .64;d.shift_x=d.shift_y=0
views={'front':(0,0),'profile':(90,0),'back':(180,0),'oblique':(45,0),'yaw30':(30,0),'yaw60':(60,0),'low':(30,-17),'high':(30,17),'highfront35':(0,35),'highoblique35':(45,35),'lowfront35':(0,-35),'lowoblique35':(45,-35)}
if a.orbit:
 views={'orbit_'+str(i).zfill(3):(i*10,10*math.sin(math.radians(i*20))) for i in range(36)};a.views=','.join(views)
records={}
for name in a.views.split(','):
 yaw,pitch=views[name];y,p=math.radians(yaw),math.radians(pitch);target=(0,-.018,1.21 if a.orbit else 1.24)
 aim(cam,(3*math.sin(y)*math.cos(p),-3*math.cos(y)*math.cos(p),target[2]+3*math.sin(p)),target)
 for lamp,loc in zip(lamps,[(-1.2,-1.8,2.1),(1.4,-1.4,1.7),(0,1.6,2)]):
  x,z,h=loc;aim(lamp,(x*math.cos(y)-z*math.sin(y),x*math.sin(y)+z*math.cos(y),h),target)
 bpy.context.view_layer.update();path=OUT/(name+'.png');s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 records[name]={'path':str(path),'sha256':sha(path),'camera':{'matrix':[list(r) for r in cam.matrix_world],'projection':d.type,'ortho_scale':d.ortho_scale,'target':target,'yaw':yaw,'pitch':pitch,'roll':0,'resolution':[s.render.resolution_x,s.render.resolution_y],'pixel_aspect':[1,1],'lens_shift':[0,0],'frame':s.frame_current,'active_keys':{}},'pose':pose_record,'actual_linked_shader_audit':shader_audit,'lights':[{'name':l.name,'matrix':[list(r) for r in l.matrix_world],'energy':l.data.energy,'size':l.data.size,'color':list(l.data.color)} for l in lamps],'material_mode':a.mode,'display':{'transform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma},'visible_mesh_owners':[o.name for o in visible()]}
 (OUT/'render-records.json').write_text(json.dumps({'native':str(S),'native_sha256':digest,'records':records,'native_saved':False,'camera_uncertainty':'Front/profile/back orthographic diagnostic; oblique45 is estimate for v06 illustration, not proof of exact source yaw.'},indent=2),encoding='utf8')
assert sha(S)==digest
print('RENDER_DONE',a.role,a.mode,len(records),flush=True)
