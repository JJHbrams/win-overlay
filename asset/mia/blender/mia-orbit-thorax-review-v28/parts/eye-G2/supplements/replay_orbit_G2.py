"""Apply compact G2 on an F-equivalent input, preserving any Body-prefix work.
Stage1: replay_patch.py E9_OR_BODY.blend F_OUTPUT.blend F
Stage2: blender -b --python replay_orbit_G2.py -- F_OUTPUT.blend G_OUTPUT.blend
"""
import bpy,numpy as np,json,sys
from pathlib import Path
from mathutils import Matrix
O=Path(__file__).parent;args=sys.argv[sys.argv.index('--')+1:];assert len(args)==2,'INPUT_F OUTPUT_G2 required';source=Path(args[0]);dest=Path(args[1]);assert source.resolve()!=dest.resolve();bpy.ops.wm.open_mainfile(filepath=str(source));master=bpy.data.objects['MIA_V27_Foundation_Face'];skin=bpy.data.objects['MIA_V27_SharedHeadBody'];rig=next(m.object for m in master.modifiers if m.type=='ARMATURE');names=[k.name for k in master.data.shape_keys.key_blocks];meta=json.loads((O/'v28G2-components.json').read_text());blob=np.load(O/'v28G2-components.npz',allow_pickle=True);assert len(names)==42;assert all(r['keys']==names for r in meta);assert not any(bpy.data.objects.get(r['name']) for r in meta),'G2 already applied / owners exist';before={o.name:np.array([[v.co[:] for v in k.data] for k in o.data.shape_keys.key_blocks]) for o in [master,skin]};hair={o.name:np.array([v.co[:] for v in o.data.vertices]) for o in bpy.data.objects if o.type=='MESH' and any(s in o.name for s in ['Hair','Braid','RootLining','Crown','Gather'])};white=master.data.materials[1];iris=master.data.materials[5];wall=skin.data.materials[0].copy();wall.name='V28G_ActualFaceUV_InnerLidSkin_Replay';wall.use_backface_culling=False
for r in meta:
 cs=blob[r['prefix']+'_coords'];faces=[tuple(int(j) for j in f) for f in blob[r['prefix']+'_faces']];mesh=bpy.data.meshes.new(r['name']+'_Replay');mesh.from_pydata(cs[0],[],faces);mat=wall if r['material_role']=='wall_face_uv' else white if r['material_role']=='white_source_slot1' else iris;mesh.materials.append(mat)
 for f in mesh.polygons:f.use_smooth=r['polygons_smooth']
 if r['has_uv']:
  uv=mesh.uv_layers.new(name='UVMap');data=blob[r['prefix']+'_uv'];assert len(data)==len(uv.data)
  for d,q in zip(uv.data,data):d.uv=q
 ob=bpy.data.objects.new(r['name'],mesh);bpy.context.scene.collection.objects.link(ob);ob.matrix_world=Matrix(r['matrix_world'])
 for ki,(kn,c) in enumerate(zip(names,cs)):
  k=ob.shape_key_add(name=kn,from_mix=False)
  for v,q in zip(k.data,c):v.co=q
  if ki:
   d=k.driver_add('value').driver;d.type='AVERAGE';var=d.variables.new();var.name='face_key';var.type='SINGLE_PROP';var.targets[0].id_type='KEY';var.targets[0].id=master.data.shape_keys;var.targets[0].data_path='key_blocks['+json.dumps(kn)+'].value'
 for gn,weights in r['vertex_groups'].items():
  g=ob.vertex_groups.new(name=gn)
  for j,w in weights:g.add([int(j)],float(w),'REPLACE')
 for mr in r['modifiers']:
  m=ob.modifiers.new(mr['name'],mr['type'])
  if m.type=='ARMATURE':m.object=rig;m.use_deform_preserve_volume=mr['preserve_volume'];m.use_vertex_groups=True;m.use_bone_envelopes=False
  elif m.type=='DATA_TRANSFER':m.object=skin;m.use_loop_data=True;m.data_types_loops=set(mr['loop_types']);m.loop_mapping=mr['loop_mapping'];m.vertex_group=mr['vertex_group'];m.mix_mode=mr['mix_mode'];m.mix_factor=mr['mix_factor'];m.use_object_transform=True
hidden=bpy.data.materials.new('V28G_ArchivedOriginalOcular_Transparent_Replay');hidden.use_nodes=True;hidden.node_tree.nodes.clear();tr=hidden.node_tree.nodes.new('ShaderNodeBsdfTransparent');out=hidden.node_tree.nodes.new('ShaderNodeOutputMaterial');out.is_active_output=True;hidden.node_tree.links.new(tr.outputs[0],out.inputs[0]);master.data.materials[1]=hidden;master.data.materials[5]=hidden
for ob in bpy.context.scene.objects:
 if ('BoundaryRibbon' in ob.name and not ob.hide_render) or ob.name.startswith('V28_LashFan_'):
  m=ob.modifiers.get('V28G_LashActualSideThickness') or ob.modifiers.new('V28G_LashActualSideThickness','SOLIDIFY');m.thickness=.00020;m.offset=0;m.use_even_offset=True;m.use_quality_normals=True;m.use_rim=True
for o in [master,skin]:assert np.array_equal(before[o.name],np.array([[v.co[:] for v in k.data] for k in o.data.shape_keys.key_blocks]))
assert all(np.array_equal(p,np.array([v.co[:] for v in bpy.data.objects[n].data.vertices])) for n,p in hair.items())
for k in master.data.shape_keys.key_blocks:k.value=0
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(dest));print('G2_REPLAY_SAVED',str(dest));print('F_MASTER_SKIN_ALL42KEYS_EXACT; BODY_PREFIX_AND_HAIR_PRESERVED')
