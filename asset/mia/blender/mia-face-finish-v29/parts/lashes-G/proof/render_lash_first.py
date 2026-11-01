import bpy,json,hashlib,sys
from pathlib import Path
from mathutils import Matrix,Vector
O=Path(__file__).parent;args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];V=args[0] if args else 'D';closure='closure' in args;hideprobe='hideprobe' in args;legacyprobe='legacyprobe' in args;gate='gate' in args;N=O/('Mia_EyeLash_v29_'+V+'.blend');bpy.ops.wm.open_mainfile(filepath=str(N));sc=bpy.context.scene;master=bpy.data.objects['MIA_V27_Foundation_Face'];skin=bpy.data.objects['MIA_V27_SharedHeadBody'];keys=master.data.shape_keys.key_blocks
for k in keys:k.value=0
visible=[o for o in sc.objects if o.type=='MESH' and not o.hide_render];lashes=[o for o in visible if o.name.startswith('V29_') and 'Lashes_' in o.name];walls=[o for o in visible if o.name.startswith('V28G_InnerLid_')];ocular=[o for o in visible if o.name.startswith('V28G_Sclera_') or o.name.startswith('V28G_Iris_')];hair=[o for o in visible if any(t in o.name for t in ['Hair','Braid','RootLining','Crown','Gather'])];original={o.name:list(o.data.materials) for o in [skin]+walls+lashes}
def mat(name,c,rough):
 m=bpy.data.materials.new(name);m.use_nodes=True;nn=m.node_tree.nodes;nn.clear();bs=nn.new('ShaderNodeBsdfPrincipled');bs.inputs['Base Color'].default_value=(c,c,c,1);bs.inputs['Roughness'].default_value=rough;out=nn.new('ShaderNodeOutputMaterial');out.is_active_output=True;m.node_tree.links.new(bs.outputs[0],out.inputs[0]);return m
gray=mat('V29_LashProof_SkinGray',.23,.85);lashgray=mat('V29_LashProof_LashGray',.24,.55)
sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=sc.render.resolution_y=768;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.use_freestyle=False;sc.render.film_transparent=False;sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
world=bpy.data.worlds.new('V29_LashProofWorld');world.use_nodes=True;nn=world.node_tree.nodes;nn.clear();bg=nn.new('ShaderNodeBackground');bg.inputs[0].default_value=(.18,.18,.18,1);bg.inputs[1].default_value=.1;wo=nn.new('ShaderNodeOutputWorld');wo.is_active_output=True;world.node_tree.links.new(bg.outputs[0],wo.inputs[0]);sc.world=world
pkg=json.loads((O.parent/'mia-orbit-review-v28/reference-review-G2.json').read_text())
for o in sc.objects:
 if o.type=='LIGHT':o.hide_render=True
lights=[]
for i,l in enumerate(pkg['views'][0]['candidate_camera']['lighting']['areas']):
 d=bpy.data.lights.new('V29_LashProofL'+str(i),'AREA');d.energy=l['watts']*.25;d.shape=l['shape'];d.size=l['size'];o=bpy.data.objects.new(d.name,d);sc.collection.objects.link(o);o.matrix_world=Matrix(l['matrix']);lights.append({'watts':d.energy,'size':d.size,'matrix':[list(r) for r in o.matrix_world]})
cam=bpy.data.objects.new('V29_LashProofCamera',bpy.data.cameras.new('V29_LashProofCamera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';folder=O/('lash-review/'+V+('-gate' if gate else '-legacyprobe' if legacyprobe else '-hideprobe' if hideprobe else '-closure' if closure else '-first'));folder.mkdir(parents=True,exist_ok=True);records=[];outline=[m for m in skin.modifiers if m.type=='NODES' and 'Outline' in m.name];outline_original={m.name:m.show_render for m in outline}
jobs=[(0,'production',0),(0,'upperONLY',0),(0,'lowerONLY',0),(1,'production',0),(1,'cleancontact',0),(1,'lashONLY',0),(2,'production',0),(2,'lashONLY',0)] if not closure else [(vi,mode,value) for value in [.5,1] for vi,mode in [(0,'production'),(1,'cleancontact')]]
if hideprobe:jobs=[(2,'noNewLashes',0)]
if legacyprobe:jobs=[(2,'noOldRibbons',0),(2,'noMaster',0),(2,'noSkinOutlineNodes',0)]
if gate:jobs=[(0,'production',0),(2,'production',0),(1,'cleancontact',.5),(1,'cleancontact',1),(0,'production',.5),(0,'production',1),(2,'lowproduction',0),(0,'unilateralR',1),(0,'unilateralL',1)]
for vi,mode,value in jobs:
 for k in keys:k.value=value if k.name.endswith('Fcl_EYE_Close') else 0
 if mode in ['unilateralR','unilateralL']:
  for k in keys:k.value=1 if k.name.endswith('Fcl_EYE_Close_'+mode[-1]) else 0
 for o in visible:o.hide_render=True
 for m in outline:m.show_render=outline_original[m.name]
 isprod=mode in ['production','noNewLashes','noOldRibbons','noMaster','noSkinOutlineNodes','lowproduction','unilateralR','unilateralL']
 if isprod:
  for o in visible:o.hide_render=o in hair
  if mode=='noNewLashes':
   for o in lashes:o.hide_render=True
  if mode=='noOldRibbons':
   for o in visible:
    if 'BoundaryRibbon' in o.name:o.hide_render=True
  if mode=='noMaster':master.hide_render=True
  if mode=='noSkinOutlineNodes':
   for m in outline:m.show_render=False
 elif mode=='cleancontact':
  for o in [skin]+walls+ocular+lashes:o.hide_render=False
 else:
  for o in lashes:o.hide_render=(mode=='upperONLY' and 'Upper' not in o.name) or (mode=='lowerONLY' and 'Lower' not in o.name)
 for o in [skin]+walls+lashes:
  for i,m in enumerate(original[o.name]):o.data.materials[i]=m if isprod else lashgray if o in lashes else gray
 v=pkg['views'][vi];cam.matrix_world=Matrix(v['candidate_camera']['matrix']);cam.data.ortho_scale=.14
 if vi in [1,2]:rot=cam.matrix_world.to_3x3();cam.location=Vector((.036,-.060,1.541))+rot@Vector((0,0,2));cam.data.ortho_scale=.080 if vi==1 else .090
 if mode=='lowproduction':
  import math
  y=math.radians(35);p=math.radians(-25);target=Vector((.036,-.060,1.541));cam.location=target+Vector((2*math.sin(y)*math.cos(p),-2*math.cos(y)*math.cos(p),2*math.sin(p)));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.090
 bpy.context.view_layer.update();name=v['id']+'-'+mode+('-Close'+str(value) if closure or gate else '');sc.render.filepath=str(folder/(name+'.png'));bpy.ops.render.render(write_still=True)
 records.append({'id':name,'native_sha256':hashlib.sha256(N.read_bytes()).hexdigest(),'visible_owners':[o.name for o in visible if not o.hide_render],'skin_outline_modifier_render_states':{m.name:m.show_render for m in outline},'camera_matrix':[list(r) for r in cam.matrix_world],'ortho_scale':cam.data.ortho_scale,'resolution':[768,768],'world_linear':list(bg.inputs[0].default_value)[:3],'world_strength':bg.inputs[1].default_value,'lights':lights,'active_keys':{k.name:k.value for k in keys if k.value},'pose':'RestHead actualkeysrecorded','material':'Native production' if isprod else 'Explicit physical Principled lashgray.24 roughness.55 / skin.23 roughness.85','layers':'Hair temporarilyhidden; original lower/upper BoundaryRibbon ink retained separately in production only. Newfourlashowners isolated perlabel.'});print('LASH_FIRST_IMAGE',name,flush=True)
(folder/'records.json').write_text(json.dumps(records,indent=2));print('LASH_FIRST_DONE')
