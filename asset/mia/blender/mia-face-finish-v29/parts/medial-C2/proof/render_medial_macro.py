import bpy,json,hashlib,sys
from pathlib import Path
from mathutils import Matrix,Vector
O=Path(__file__).parent;B=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-orbit-thorax-review-v28/integrated-G2L/Mia_Foundation_v28_G2L.blend');pkg=json.loads((O.parent/'mia-orbit-review-v28/reference-review-G2.json').read_text());args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];fringe='fringe' in args;selected=next((a for a in args if a in ['A','B','C','C2','D']),None);folder=O/('medial-review/fringe' if fringe else 'medial-review/macros');folder.mkdir(parents=True,exist_ok=True);records=[]
for tag,N in ([(selected,O/('Mia_EyeLash_v29_'+selected+'.blend'))] if selected else [('A',O/'Mia_EyeLash_v29_A.blend')] if fringe else [('baseline',B),('A',O/'Mia_EyeLash_v29_A.blend')]):
 bpy.ops.wm.open_mainfile(filepath=str(N));sc=bpy.context.scene;master=bpy.data.objects['MIA_V27_Foundation_Face'];skin=bpy.data.objects['MIA_V27_SharedHeadBody']
 for k in master.data.shape_keys.key_blocks:k.value=0
 visible=[o for o in sc.objects if o.type=='MESH' and not o.hide_render];walls=[o for o in visible if o.name.startswith('V28G_InnerLid_')];ocular=[o for o in visible if o.name.startswith('V28G_Sclera_') or o.name.startswith('V28G_Iris_')]
 for o in visible:o.hide_render=True
 for o in [skin]+walls+ocular:o.hide_render=False
 originals={o.name:list(o.data.materials) for o in [skin]+walls}
 mat=bpy.data.materials.new('V29_MACRO_NoPigment');mat.use_nodes=True;nn=mat.node_tree.nodes;nn.clear();bs=nn.new('ShaderNodeBsdfPrincipled');bs.inputs['Base Color'].default_value=(.23,.23,.23,1);bs.inputs['Roughness'].default_value=.85;out=nn.new('ShaderNodeOutputMaterial');out.is_active_output=True;mat.node_tree.links.new(bs.outputs[0],out.inputs[0]);wire=mat.copy();wire.name='V29_MACRO_Wire';nn=wire.node_tree.nodes;wf=nn.new('ShaderNodeWireframe');wf.use_pixel_size=True;wf.inputs[0].default_value=.8;black=nn.new('ShaderNodeEmission');black.inputs[0].default_value=(.002,.002,.002,1);mix=nn.new('ShaderNodeMixShader');out=next(n for n in nn if n.type=='OUTPUT_MATERIAL' and n.is_active_output);bs=next(n for n in nn if n.type=='BSDF_PRINCIPLED');wire.node_tree.links.new(wf.outputs[0],mix.inputs[0]);wire.node_tree.links.new(bs.outputs[0],mix.inputs[1]);wire.node_tree.links.new(black.outputs[0],mix.inputs[2]);wire.node_tree.links.new(mix.outputs[0],out.inputs[0])
 for ob in [skin]+walls:
  for i in range(len(ob.data.materials)):ob.data.materials[i]=mat
 sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=sc.render.resolution_y=768;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.use_freestyle=False;sc.render.film_transparent=False;sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
 world=bpy.data.worlds.new('V29_MACRO_World');world.use_nodes=True;nn=world.node_tree.nodes;nn.clear();bg=nn.new('ShaderNodeBackground');bg.inputs[0].default_value=(.18,.18,.18,1);bg.inputs[1].default_value=.1;wo=nn.new('ShaderNodeOutputWorld');wo.is_active_output=True;world.node_tree.links.new(bg.outputs[0],wo.inputs[0]);sc.world=world
 for ob in sc.objects:
  if ob.type=='LIGHT':ob.hide_render=True
 lights=[]
 for i,ld in enumerate(pkg['views'][0]['candidate_camera']['lighting']['areas']):
  d=bpy.data.lights.new('V29_MACRO_L'+str(i),'AREA');d.energy=ld['watts']*.25;d.shape=ld['shape'];d.size=ld['size'];ob=bpy.data.objects.new(d.name,d);sc.collection.objects.link(ob);ob.matrix_world=Matrix(ld['matrix']);lights.append({'watts':d.energy,'size':d.size,'matrix':[list(r) for r in ob.matrix_world]})
 cam=bpy.data.objects.new('V29_MACRO_Camera',bpy.data.cameras.new('V29_MACRO_Camera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.045;target=Vector((.022,-.064,1.541))
 for vi,mode in ([(0,m) for m in ['NOiris','NOsclera','wallONLY','whiteONLY','irisONLY','productionNoInk']] if fringe else [(0,'clean'),(2,'clean')] if tag=='baseline' or selected else [(0,'clean'),(2,'clean'),(2,'wallwire'),(2,'skinwallONLY')]):
  v=pkg['views'][vi];rot=Matrix(v['candidate_camera']['matrix']).to_3x3();cam.matrix_world=rot.to_4x4();cam.location=target+rot@Vector((0,0,2))
  skin.hide_render=mode in ['wallONLY','whiteONLY','irisONLY']
  for ob in [skin]+walls:
   for i in range(len(ob.data.materials)):ob.data.materials[i]=originals[ob.name][i] if mode=='productionNoInk' else wire if mode=='wallwire' and ob in walls else mat
  for ob in walls:ob.hide_render=mode in ['whiteONLY','irisONLY']
  for ob in ocular:ob.hide_render=mode in ['skinwallONLY','wallwire','wallONLY'] or (mode in ['NOiris','whiteONLY'] and 'Iris_' in ob.name) or (mode in ['NOsclera','irisONLY'] and 'Sclera_' in ob.name)
  bpy.context.view_layer.update();name=tag+'-'+v['id']+'-'+mode;sc.render.filepath=str(folder/(name+'.png'));bpy.ops.render.render(write_still=True)
  records.append({'id':name,'native_sha256':hashlib.sha256(N.read_bytes()).hexdigest(),'visible_owners':[o.name for o in visible if not o.hide_render],'camera_matrix':[list(r) for r in cam.matrix_world],'ortho_scale':cam.data.ortho_scale,'resolution':[768,768],'lights':lights,'world':{'linear':list(bg.inputs[0].default_value)[:3],'strength':bg.inputs[1].default_value},'layers':'No master/legacy/ink/brow/lash/UV makeup. Native alpha ocular optional per mode. Wallwire hides ocular.','material':'Active Principled gray.23 roughness.85, optional actual evaluated wall wire overlay','active_keys':{},'pose':'RestHead; source4camera rotation retained, common eye-centered target22,-64,1541mm'})
(folder/('records-'+selected+'.json' if selected else 'records.json')).write_text(json.dumps(records,indent=2));print('MEDIAL_MACROS_DONE',len(records))
