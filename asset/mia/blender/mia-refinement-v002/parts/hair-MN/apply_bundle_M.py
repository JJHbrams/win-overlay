"""Apply a selected hair-only bundle to an already loaded guarded target."""
import bpy,numpy as np,json,hashlib
from pathlib import Path
from mathutils import Matrix
def apply(folder,include_binding=False):
 O=Path(folder);r=json.loads((O/'manifest.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();dig=lambda x:hashlib.sha256(np.asarray(x).tobytes()).hexdigest();assert sha(O/r['library']['file'])==r['library']['sha256'];datasets={}
 # All existing shape/UV guards are checked before the first mutation.
 for a in r['actors']:
  assert sha(O/a['data'])==a['data_sha256'];datasets[a['owner']]=np.load(O/a['data'])
  if not a['existing']:assert a['owner'] not in bpy.data.objects;continue
  ob=bpy.data.objects[a['owner']];m=ob.data;e=a['expected'];assert len(m.vertices)==e['verts'] and len(m.polygons)==e['polys'];assert dig(np.array([v.co[:] for v in m.vertices],'<f4'))==e['coords'];assert dig(np.array([v.vertex_index for v in m.loops],'<i4'))==e['loop_vertices'];assert dig(np.array([f.loop_total for f in m.polygons],'<i4'))==e['polygon_sizes'];assert m.uv_layers.active_index==e['active_uv']
  for name,h in e['old_uvs'].items():assert dig(np.array([v.uv[:] for v in m.uv_layers[name].data],'<f4'))==h
  for name,h in a['groups_before'].items():
   group=ob.vertex_groups.get(name);assert group is not None;values=[(v.index,float(g.weight)) for v in m.vertices for g in v.groups if g.group==group.index];assert hashlib.sha256(json.dumps(values).encode()).hexdigest()==h
 names={x for a in r['actors'] for x in a['static_materials']+a['bound_materials'] if x}
 with bpy.data.libraries.load(str(O/r['library']['file']),link=False) as (src,dst):assert names<=set(src.materials);dst.materials=sorted(names)
 loaded={name:mat for name,mat in zip(sorted(names),dst.materials)};created=[]
 for a in r['actors']:
  d=datasets[a['owner']]
  if a['existing']:
   ob=bpy.data.objects[a['owner']];m=ob.data
   for v,p in zip(m.vertices,d['target_coords']):v.co=p
  else:
   m=bpy.data.meshes.new(a['owner']);faces=[d['loop_vertices'][s:s+n].tolist() for s,n in zip(d['polygon_starts'],d['polygon_sizes'])];m.from_pydata(d['coords'].tolist(),[],faces);m.update();ob=bpy.data.objects.new(a['owner'],m);collection=bpy.data.collections.get('MIA_V17_PIXAL_HAIR') or bpy.context.scene.collection;collection.objects.link(ob);ob.matrix_world=Matrix(a['matrix_world']);created.append(ob.name)
   for f,sm,mi in zip(m.polygons,d['smooth'],d['material_indices']):f.use_smooth=bool(sm);f.material_index=int(mi)
  for u in a['new_uvs']:uv=m.uv_layers.new(name=u['name']);uv.data.foreach_set('uv',d[u['key']].ravel())
  flags=a['expected']['uv_flags'] if a['existing'] else a['uv_flags'];m.uv_layers.active_index=a['expected']['active_uv'] if a['existing'] else a['active_uv']
  for name,render,clone in flags:m.uv_layers[name].active_render=render;m.uv_layers[name].active_clone=clone
  for name,key in a['new_attributes'].items():attr=m.attributes.new(name,'FLOAT','POINT');attr.data.foreach_set('value',d[key])
  for name,key in a['new_groups'].items():
   if name in ['J_Bip_C_Head','J_Bip_C_UpperChest'] and not include_binding:continue
   assert name not in ob.vertex_groups;g=ob.vertex_groups.new(name=name)
   for vi,w in d[key]:g.add([int(vi)],float(w),'REPLACE')
  m.materials.clear()
  for matname in a['bound_materials'] if include_binding else a['static_materials']:m.materials.append(loaded[matname])
  ob['mia_component']='hair';m.update();assert dig(np.array([v.co[:] for v in m.vertices],'<f4'))==a['output_coords_sha256']
  if not a['existing']:m.normals_split_custom_set(d['corner_normals'].tolist())
 binding_errors={}
 if include_binding:
  def worldcoords(ob):
   eo=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=eo.to_mesh();q=np.array([eo.matrix_world@v.co for v in m.vertices]);eo.to_mesh_clear();return q
  bpy.context.view_layer.update();static_world={a['owner']:worldcoords(bpy.data.objects[a['owner']]) for a in r['actors']}
  meta=r['new_carrier'];rig=bpy.data.objects[meta['rig']];head=rig.pose.bones[meta['bone']];assert np.allclose(np.array(head.matrix_basis),np.eye(4),atol=1e-6),'Apply binding in real neutral, not under an active source pose';carrier=bpy.data.objects.new(meta['name'],None);bpy.context.scene.collection.objects.link(carrier);carrier.parent=rig;carrier.parent_type='BONE';carrier.parent_bone=head.name;bpy.context.view_layer.update();carrier.matrix_world=rig.matrix_world@head.matrix;bpy.context.view_layer.update()
  for a in r['actors']:
   ob=bpy.data.objects[a['owner']];assert not ob.parent and not any(m.type=='ARMATURE' for m in ob.modifiers),'Do not double bind existing target'
   if a['parent_mode']=='HEAD_CARRIER':world=ob.matrix_world.copy();ob.parent=carrier;ob.matrix_world=world
   else:mod=ob.modifiers.new('MIA_V002_HangingHeadChest','ARMATURE');mod.object=rig;mod.use_deform_preserve_volume=False
  bpy.context.view_layer.update();binding_errors={name:float(np.linalg.norm(worldcoords(bpy.data.objects[name])-q,axis=1).max()) for name,q in static_world.items()};assert max(binding_errors.values())<1e-6,binding_errors
 bpy.context.view_layer.update();return {'applied_bundle':str(O),'manifest_sha256':sha(O/'manifest.json'),'new_actors':created,'binding':bool(include_binding),'binding_neutral_evaluated_world_max_errors_m':binding_errors,'no_full_scene_replay':True,'ART':'UNVERIFIED'}
