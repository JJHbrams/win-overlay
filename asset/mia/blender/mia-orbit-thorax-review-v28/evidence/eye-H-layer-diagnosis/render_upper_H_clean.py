"""G2 read-only true clean-lid evidence; no ink, lashes, brow, UV makeup or cards."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Matrix
O=Path(__file__).parent;native=O/'Mia_Orbit_v28_G2.blend';sha=hashlib.sha256(native.read_bytes()).hexdigest()
assert sha=='77a992872c2b1590e9266f01767e0236e95507b644fe96de21fe20070cc7acfb'
bpy.ops.wm.open_mainfile(filepath=str(native));sc=bpy.context.scene
master=bpy.data.objects['MIA_V27_Foundation_Face'];skin=bpy.data.objects['MIA_V27_SharedHeadBody']
for k in master.data.shape_keys.key_blocks:k.value=0
visible=[o for o in sc.objects if o.type=='MESH' and not o.hide_render]
walls=[o for o in visible if o.name.startswith('V28G_InnerLid_')]
ocular=[o for o in visible if o.name.startswith('V28G_Sclera_') or o.name.startswith('V28G_Iris_')]
for o in visible:o.hide_render=True
skin.hide_render=False
for o in walls+ocular:o.hide_render=False
mat=bpy.data.materials.new('H_DIAG_SKIN_NO_UV_NO_INK');mat.use_nodes=True;nn=mat.node_tree.nodes;nn.clear();p=nn.new('ShaderNodeBsdfPrincipled');p.inputs['Base Color'].default_value=(.35,.35,.35,1);p.inputs['Roughness'].default_value=.85;out=nn.new('ShaderNodeOutputMaterial');out.is_active_output=True;mat.node_tree.links.new(p.outputs[0],out.inputs[0])
for ob in [skin]+walls:
 for i in range(len(ob.data.materials)):ob.data.materials[i]=mat
sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=sc.render.resolution_y=768;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.film_transparent=False;sc.render.use_freestyle=False;sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
world=bpy.data.worlds.new('H_DIAG_ActualWorld');world.use_nodes=True;nn=world.node_tree.nodes;nn.clear();bg=nn.new('ShaderNodeBackground');bg.inputs[0].default_value=(.18,.18,.18,1);bg.inputs[1].default_value=.1;wo=nn.new('ShaderNodeOutputWorld');wo.is_active_output=True;world.node_tree.links.new(bg.outputs[0],wo.inputs[0]);sc.world=world
pkg=json.loads((O/'reference-review-G2.json').read_text())
for o in sc.objects:
 if o.type=='LIGHT':o.hide_render=True
for i,ld in enumerate(pkg['views'][0]['candidate_camera']['lighting']['areas']):
 d=bpy.data.lights.new('H_DIAG_Light'+str(i),'AREA');d.energy=ld['watts'];d.shape=ld['shape'];d.size=ld['size'];d.color=ld['color'];ob=bpy.data.objects.new(d.name,d);sc.collection.objects.link(ob);ob.matrix_world=Matrix(ld['matrix'])
cam=bpy.data.objects.new('H_DIAG_Camera',bpy.data.cameras.new('H_DIAG_Camera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
folder=O/'upper-H-clean-G2';folder.mkdir(exist_ok=True);records=[]
for v in pkg['views']:
 cam.matrix_world=Matrix(v['candidate_camera']['matrix']);cam.data.ortho_scale=.14;cam.data.shift_x=cam.data.shift_y=0
 for mode in ['clean-lid','skin-wall-only']:
  for ob in ocular:ob.hide_render=mode=='skin-wall-only'
  bpy.context.view_layer.update();sc.render.filepath=str(folder/(v['id']+'-'+mode+'.png'));bpy.ops.render.render(write_still=True)
  records.append({'id':v['id']+'-'+mode,'native_sha256':sha,'visible_owners':[o.name for o in visible if not o.hide_render],'all_master_legacy_cards_brows_hidden':master.hide_render,'all_ribbons_fans_hidden':all(o.hide_render for o in visible if 'BoundaryRibbon' in o.name or o.name.startswith('V28_LashFan_')),'skin_wall_material':'Explicit active-output Principled .35 roughness.85; no image texture or UV pigment','ocular_material':'Native G2 production alpha preserved' if mode=='clean-lid' else 'All ocular hidden','camera_matrix':[list(r) for r in cam.matrix_world],'ortho_scale':cam.data.ortho_scale,'resolution':[768,768],'world_linear':list(bg.inputs[0].default_value)[:3],'world_strength':bg.inputs[1].default_value,'lights':[dict(l) for l in v['candidate_camera']['lighting']['areas']],'active_master_keys':{k.name:k.value for k in master.data.shape_keys.key_blocks if k.value},'pixel_axes':'Native source camera roll retained; no eye/chord/SRT rotation'})
(folder/'records.json').write_text(json.dumps(records,indent=2));print('H_CLEAN_DONE',len(records))
