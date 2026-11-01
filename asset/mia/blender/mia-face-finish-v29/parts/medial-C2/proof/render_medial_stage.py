"""Small actual clean-lid before/after + closure on exact saved natives."""
import bpy,json,hashlib,sys,math
from pathlib import Path
from mathutils import Matrix,Vector
O=Path(__file__).parent;args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];tag=args[0] if args else 'A';mode=args[1] if len(args)>1 else 'normal'
N=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-orbit-thorax-review-v28/integrated-G2L/Mia_Foundation_v28_G2L.blend') if tag.startswith('baseline') else O/('Mia_EyeLash_v29_'+tag+'.blend');sha=hashlib.sha256(N.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(N))
sc=bpy.context.scene;master=bpy.data.objects['MIA_V27_Foundation_Face'];skin=bpy.data.objects['MIA_V27_SharedHeadBody'];keys=master.data.shape_keys.key_blocks
visible=[o for o in sc.objects if o.type=='MESH' and not o.hide_render];walls=[o for o in visible if o.name.startswith('V28G_InnerLid_')];ocular=[o for o in visible if o.name.startswith('V28G_Sclera_') or o.name.startswith('V28G_Iris_')];original_materials={o.name:list(o.data.materials) for o in [skin]+walls}
for ob in visible:ob.hide_render=True
for ob in [skin]+walls+ocular:ob.hide_render=False
mat=bpy.data.materials.new('V29_CLEAN_NoPigment');mat.use_nodes=True;nn=mat.node_tree.nodes;nn.clear();p=nn.new('ShaderNodeBsdfPrincipled');p.inputs['Base Color'].default_value=(.23,.23,.23,1);p.inputs['Roughness'].default_value=.85;out=nn.new('ShaderNodeOutputMaterial');out.is_active_output=True;mat.node_tree.links.new(p.outputs[0],out.inputs[0])
for ob in [skin]+walls:
 for i in range(len(ob.data.materials)):ob.data.materials[i]=mat
sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=sc.render.resolution_y=768;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.film_transparent=False;sc.render.use_freestyle=False;sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
world=bpy.data.worlds.new('V29_CLEAN_ActualWorld');world.use_nodes=True;nn=world.node_tree.nodes;nn.clear();bg=nn.new('ShaderNodeBackground');bg.inputs[0].default_value=(.18,.18,.18,1);bg.inputs[1].default_value=.1;wo=nn.new('ShaderNodeOutputWorld');wo.is_active_output=True;world.node_tree.links.new(bg.outputs[0],wo.inputs[0]);sc.world=world
v28=O.parent/'mia-orbit-review-v28';pkg=json.loads((v28/'reference-review-G2.json').read_text())
for o in sc.objects:
 if o.type=='LIGHT':o.hide_render=True
lights=[]
for i,ld in enumerate(pkg['views'][0]['candidate_camera']['lighting']['areas']):
 d=bpy.data.lights.new('V29_CLEAN_Light'+str(i),'AREA');d.energy=ld['watts']*.25;d.shape=ld['shape'];d.size=ld['size'];d.color=ld['color'];ob=bpy.data.objects.new(d.name,d);sc.collection.objects.link(ob);ob.matrix_world=Matrix(ld['matrix']);lights.append({'watts':d.energy,'size':d.size,'matrix':[list(r) for r in ob.matrix_world]})
cam=bpy.data.objects.new('V29_CLEAN_Camera',bpy.data.cameras.new('V29_CLEAN_Camera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';folder=O/'medial-review'/(tag if mode=='normal' else tag+'-'+mode);folder.mkdir(parents=True,exist_ok=True);records=[];rig=next(m.object for m in master.modifiers if m.type=='ARMATURE');head=rig.pose.bones['J_Bip_C_Head'];rest=head.matrix_basis.copy()
jobs=[{'value':val,'vi':vi,'name':pkg['views'][vi]['id']+'-Close'+str(val)} for val in ([0] if tag=='baseline' else [.5,1] if tag=='baseline-close' else [0,.5,1]) for vi in [0,2,1]]
if mode=='post':jobs=[{'vi':3,'name':'right_oblique-clean'},{'vi':0,'low':True,'name':'lowRIGHT-clean'},{'vi':0,'unilateral':'R','name':'unilateralR-front'},{'vi':0,'unilateral':'L','name':'unilateralL-front'},{'vi':0,'head':-12,'name':'head-12-clean'},{'vi':0,'head':12,'name':'head+12-clean'}]
if mode=='identity':jobs=[{'vi':0,'name':'front-production-hairOFF','production':True}]
for job in jobs:
 for k in keys:k.value=0
 if job.get('value'):
  for k in keys:k.value=job['value'] if k.name.endswith('Fcl_EYE_Close') else 0
 if 'unilateral' in job:
  for k in keys:k.value=1 if k.name.endswith('Fcl_EYE_Close_'+job['unilateral']) else 0
 head.matrix_basis=rest
 if 'head' in job:head.rotation_mode='XYZ';head.rotation_euler=(0,math.radians(job['head']),0)
 v=pkg['views'][job['vi']];cam.matrix_world=Matrix(v['candidate_camera']['matrix']);cam.data.ortho_scale=.14;cam.data.shift_x=cam.data.shift_y=0
 if v['id']=='profile':cam.location+=cam.matrix_world.to_3x3()@Vector((-.0515,-.009,0));cam.data.ortho_scale=.095
 if job.get('low'):
  y=math.radians(35);p=math.radians(-30);target=Vector((0,0,1.55));cam.location=target+Vector((2*math.sin(y)*math.cos(p),-2*math.cos(y)*math.cos(p),2*math.sin(p)));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
 if job.get('production'):
  cam.data.ortho_scale=.29
  for ob in visible:ob.hide_render=any(t in ob.name for t in ['Hair','Braid','RootLining','Crown','Gather'])
  for ob in [skin]+walls:
   for i,m in enumerate(original_materials[ob.name]):ob.data.materials[i]=m
 bpy.context.view_layer.update();name=job['name'];sc.render.filepath=str(folder/(name+'.png'));bpy.ops.render.render(write_still=True)
 records.append({'id':name,'native_path':str(N),'native_sha256':sha,'visible_owners':[o.name for o in visible if not o.hide_render],'hidden_layers':'Hair only' if job.get('production') else 'All hair/master legacy cards/brows/ribbons/fans; skin+wall no pigment/makeup. Native alpha ocular retained.','shader':'Native production' if job.get('production') else 'Explicit active-output Principled gray.23 roughness.85','lights':lights,'world_linear':list(bg.inputs[0].default_value)[:3],'world_strength':bg.inputs[1].default_value,'camera_matrix':[list(r) for r in cam.matrix_world],'ortho_scale':cam.data.ortho_scale,'resolution':[768,768],'active_master_keys':{k.name:k.value for k in keys if k.value},'head_matrix_basis':[list(r) for r in head.matrix_basis],'pose':'Original source4 cameraaxes unless labeledlow; profile only recentered identically for macro; no chord normalization.'});print('V29_IMAGE_DONE',tag,name,flush=True)
(folder/'records.json').write_text(json.dumps(records,indent=2));print('MEDIAL_REVIEW_DONE',tag,len(records))
