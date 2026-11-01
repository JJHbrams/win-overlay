import bpy,numpy as np,json,hashlib,sys
from pathlib import Path
from mathutils import Matrix
O=Path(__file__).parent;args=sys.argv[sys.argv.index('--')+1:];src=Path(args[0]);dest=Path(args[1]);V=args[2] if len(args)>2 else 'G';meta=json.loads((O/('lash-'+V+'-components.json')).read_text());assert hashlib.sha256(src.read_bytes()).hexdigest()==meta['input_C2_sha256'];data=np.load(O/('lash-'+V+'-components.npz'));bpy.ops.wm.open_mainfile(filepath=str(src));master=bpy.data.objects['MIA_V27_Foundation_Face'];assert [k.name for k in master.data.shape_keys.key_blocks]==meta['key_names'];matinfo=meta['material_copy'];material=bpy.data.objects[matinfo['source_owner_in_C2']].data.materials[matinfo['source_slot']].copy();material.name=matinfo['new_material_name']
for own in meta['owners']:
 pre=own['payload_prefix'];coords=data[pre+'_coords'];flat=data[pre+'_face_vertices'];sizes=data[pre+'_face_sizes'];off=0;faces=[]
 for n in sizes:faces.append(flat[off:off+n].tolist());off+=n
 me=bpy.data.meshes.new(own['name']);me.from_pydata(coords[0],[],faces);me.materials.append(material);uv=me.uv_layers.new(name='UVMap')
 for f in me.polygons:f.use_smooth=True
 for u,q in zip(uv.data,data[pre+'_UVMap']):u.uv=q
 ob=bpy.data.objects.new(own['name'],me);bpy.context.scene.collection.objects.link(ob);ob.matrix_world=Matrix(own['matrix_world'])
 for ki,(kn,q) in enumerate(zip(meta['key_names'],coords)):
  k=ob.shape_key_add(name=kn,from_mix=False)
  for v,p in zip(k.data,q):v.co=p
  if ki:
   d=k.driver_add('value').driver;d.type='AVERAGE';v=d.variables.new();v.name='face_key';v.type='SINGLE_PROP';v.targets[0].id_type='KEY';v.targets[0].id=master.data.shape_keys;v.targets[0].data_path='key_blocks['+json.dumps(kn)+'].value'
 vg=ob.vertex_groups.new(name=own['weight_group']);vg.add(list(range(len(me.vertices))),own['all_vertices_weight'],'REPLACE');arm=ob.modifiers.new('V29_Lash_HeadFollow','ARMATURE');arm.object=bpy.data.objects[own['armature_target']]
for n in meta['archive_hidden_fan_owners']:bpy.data.objects[n].hide_render=True;bpy.data.objects[n].hide_viewport=True
m=meta['master_mask'];vg=master.vertex_groups.new(name=m['group_name']);vg.add(m['keep_vertex_indices'],1,'REPLACE');mask=master.modifiers.new(m['modifier_name'],'MASK');mask.vertex_group=vg.name;mask.threshold=m['threshold'];mask.invert_vertex_group=False
if hasattr(mask,'use_smooth'):mask.use_smooth=False
for k in master.data.shape_keys.key_blocks:k.value=0
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(dest));print('LASH_COMPONENT_REPLAY_SAVED',str(dest))
