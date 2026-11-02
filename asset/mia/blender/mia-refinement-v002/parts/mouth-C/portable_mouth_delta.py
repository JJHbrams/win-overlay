"""Apply mouth-only A payload to the CURRENT scene; no native open/save/render."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parent
NAME='Face.M_F00_000_00_Fcl_MIA_ToothyGrin'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def apply_to_current_scene(variant='C'):
 assert variant in ['A','B','C'];meta=json.loads((P/('payload/mouth-rig-'+variant+'.json')).read_text());file=P/'payload'/meta['payload'];assert sha(file)==meta['payload_sha256'];data=np.load(file)
 skin=bpy.data.objects['MIA_V27_SharedHeadBody'];master=bpy.data.objects['MIA_V27_Foundation_Face'];rig=bpy.data.objects[meta['head_armature']]
 assert 'MIA_v002_MouthAnchor' not in bpy.data.objects,'Mouth delta is already applied'
 expected=json.loads((P/'audit/input-guards.json').read_text());sp=importlib.util.spec_from_file_location('mouth_portable_guard',P/'guard_helpers.py');h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h)
 old=master.material_slots[0].material;assert old.name==meta['original_mouth_material'] and h.jhash(h.graph(old.node_tree))==meta['original_mouth_material_hash'],'Legacy oral output changed; re-evaluate explicitly'
 for ob in [skin,master]:
  assert {n:hashlib.sha256(h.arr(u.data,'uv',2).tobytes()).hexdigest() for n,u in [(u.name,u) for u in ob.data.uv_layers]}==expected['owners'][ob.name]['UV'],'Mouth UV/topology precondition changed'
  assert [k.name for k in ob.data.shape_keys.key_blocks][:42]==expected['owners'][ob.name]['key_names'][:42]
 # Supply only the sparse43rd grin if root's final scene has not added it yet.
 for ob,role in [(master,'master'),(skin,'skin')]:
  ids=data[role+'_grin_ids'];delta=data[role+'_grin_delta'];basis=ob.data.shape_keys.key_blocks['Basis'];existing=ob.data.shape_keys.key_blocks.get(NAME)
  if existing:
   measured=np.array([existing.data[int(i)].co-basis.data[int(i)].co for i in ids]);assert np.allclose(measured,delta,rtol=0,atol=2e-7),'Existing grin differs; no overwrite'
  else:
   key=ob.shape_key_add(name=NAME,from_mix=False)
   for i,d in zip(ids,delta):key.data[int(i)].co=basis.data[int(i)].co+Vector(d)
   key.value=0.
   if role=='skin':
    f=key.driver_add('value');f.driver.type='AVERAGE';v=f.driver.variables.new();v.name='source_grin';v.type='SINGLE_PROP';v.targets[0].id_type='KEY';v.targets[0].id=master.data.shape_keys;v.targets[0].data_path='key_blocks["'+NAME+'"].value'
 # Explicit output ancestry with the original packed atlas and explicit unchanged UVMap.
 atlas=bpy.data.images[meta['atlas']];old.use_fake_user=True
 def toon(mat,enamel=False):
  mat.use_nodes=True;n=mat.node_tree.nodes;l=mat.node_tree.links
  if enamel:n.clear()
  uv=n.new('ShaderNodeUVMap');uv.name='V002M_OriginalUVMap';uv.uv_map='UVMap';tex=n.new('ShaderNodeTexImage');tex.name='V002M_OriginalPackedOralAtlas';tex.image=atlas;tex.extension='EXTEND';l.new(uv.outputs[0],tex.inputs['Vector'])
  diffuse=n.new('ShaderNodeBsdfDiffuse');diffuse.name='V002M_ActualWhiteDiffuse';diffuse.inputs['Color'].default_value=(1,1,1,1);diffuse.inputs['Roughness'].default_value=1.;rgb=n.new('ShaderNodeShaderToRGB');rgb.name='V002M_ActualSceneLight';l.new(diffuse.outputs[0],rgb.inputs[0]);bw=n.new('ShaderNodeRGBToBW');l.new(rgb.outputs[0],bw.inputs[0]);level=n.new('ShaderNodeMapRange');level.name='V002M_ControlledToonLight';level.clamp=True;level.inputs['From Min'].default_value=0.;level.inputs['From Max'].default_value=1.;level.inputs['To Min'].default_value=.67 if enamel else .53;level.inputs['To Max'].default_value=1.;l.new(bw.outputs[0],level.inputs['Value']);pigment=n.new('ShaderNodeMixRGB');pigment.name='V002M_AtlasTimesActualLight';pigment.blend_type='MULTIPLY';pigment.inputs[0].default_value=1.;l.new(tex.outputs['Color'],pigment.inputs[1]);l.new(level.outputs['Result'],pigment.inputs[2]);signal=pigment.outputs[0]
  if enamel:
   spec=n.new('ShaderNodeBsdfPrincipled');spec.name='V002M_RestrainedEnamelReflection';spec.inputs['Base Color'].default_value=(0,0,0,1);spec.inputs['Metallic'].default_value=0.;spec.inputs['Roughness'].default_value=.28;spec.inputs['IOR'].default_value=1.46;spec.inputs['Specular IOR Level'].default_value=.4;srgb=n.new('ShaderNodeShaderToRGB');l.new(spec.outputs[0],srgb.inputs[0]);add=n.new('ShaderNodeMixRGB');add.name='V002M_RestrainedActualSpec';add.blend_type='ADD';add.inputs[0].default_value=.06;l.new(signal,add.inputs[1]);l.new(srgb.outputs[0],add.inputs[2]);signal=add.outputs[0]
  em=n.new('ShaderNodeEmission');em.name='V002M_ToonOutput';l.new(signal,em.inputs['Color']);out=mat.node_tree.get_output_node('EEVEE')
  if out is None:out=n.new('ShaderNodeOutputMaterial')
  out.target='ALL';out.is_active_output=True;l.new(em.outputs[0],out.inputs['Surface']);mat.use_backface_culling=enamel;mat['V002M_route']='Original512 packed atlas and explicit UVMap; actual scene Diffuse->RGB controlled light->Emission, restrained actual enamel spec where applicable. Legacy rough-metal fallback is archived, not claimed to cause prior thin tooth band.'
 cavity=old.copy();cavity.name='MIA_v002_OralCavity_ActualToon';toon(cavity);master.material_slots[0].material=cavity
 enamel=bpy.data.materials.new('MIA_v002_Enamel_ActualToon');toon(enamel,True)
 archive=master.vertex_groups.new(name='MIA_v002_ArchiveLegacyWhiteAndOuterLining');archive.add(sorted(set(meta['archive_white_vertices'])|set(meta['archive_outer_liner_vertices'])),1.,'REPLACE');mask=master.modifiers.new('MIA_v002_LegacyMouth_RenderArchive','MASK');mask.vertex_group=archive.name;mask.invert_vertex_group=True
 head=rig.pose.bones[meta['head_bone']];delta=rig.matrix_world@head.matrix@Matrix(meta['reference_head_matrix_world']).inverted()
 anchor=bpy.data.objects.new('MIA_v002_MouthAnchor',None);bpy.context.scene.collection.objects.link(anchor);anchor.empty_display_size=.004;anchor.parent=rig;anchor.parent_type='BONE';anchor.parent_bone=meta['head_bone'];anchor.matrix_world=delta
 hinge=bpy.data.objects.new('MIA_v002_DentalJawHinge',None);bpy.context.scene.collection.objects.link(hinge);hinge.empty_display_size=.006;hinge.parent=anchor;hinge.location=meta['jaw_pivot_reference_world'];hinge.rotation_mode='XYZ';hinge['ManualDentalJaw']=0.;hinge.id_properties_ui('ManualDentalJaw').update(min=0.,max=1.,description='Extra dental-jaw opening only; skin mouth remains controlled by existing facial keys. Default0.');hinge['Estimate']='Rotation-only pivot estimate calibrated to lower-lip motion; not clinical TMJ reconstruction.'
 f=hinge.driver_add('rotation_euler',0);d=f.driver;d.type='SCRIPTED';terms=[]
 for j,(name,amount) in enumerate(meta['jaw_coefficients_rad'].items()):
  v=d.variables.new();v.name='k'+str(j);v.type='SINGLE_PROP';v.targets[0].id_type='KEY';v.targets[0].id=master.data.shape_keys;v.targets[0].data_path='key_blocks["'+name+'"].value';terms.append(f'{amount:.9g}*{v.name}')
 v=d.variables.new();v.name='manual';v.type='SINGLE_PROP';v.targets[0].id=hinge;v.targets[0].data_path='["ManualDentalJaw"]';d.expression=f'min({meta["jaw_limit_rad"]},max(0,{meta["manual_jaw_max_rad"]}*manual+'+('+'.join(terms) or '0')+'))'
 def make(name,verts,uv,faces,material,parent):
  mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();ob=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(ob);ob.data.materials.append(material);layer=mesh.uv_layers.new(name='UVMap')
  for loop in mesh.loops:layer.data[loop.index].uv=uv[loop.vertex_index]
  for face in mesh.polygons:face.use_smooth=True
  ob.parent=parent;ob.matrix_parent_inverse=Matrix.Identity(4);ob.matrix_basis=Matrix.Identity(4)
  return ob
 upper=make('MIA_v002_UpperDentalCrowns',data['upper_positions'],data['upper_uv'],meta['upper_faces'],enamel,anchor)
 lower=make('MIA_v002_LowerDentalCrowns',data['lower_positions']-np.array(meta['jaw_pivot_reference_world']),data['lower_uv'],meta['lower_faces'],enamel,hinge)
 collar=make('MIA_v002_EvaluatedLipCollar',data['collar_positions'][0],data['collar_uv'],meta['collar_faces'],cavity,anchor)
 for j,name in enumerate(meta['key_names']):
  key=collar.shape_key_add(name=name,from_mix=False);key.data.foreach_set('co',data['collar_positions'][j].ravel());key.value=0.
  if name!='Basis':
   fc=key.driver_add('value');fc.driver.type='AVERAGE';v=fc.driver.variables.new();v.name='master';v.type='SINGLE_PROP';v.targets[0].id_type='KEY';v.targets[0].id=master.data.shape_keys;v.targets[0].data_path='key_blocks["'+name+'"].value'
 for ob,parts in [(upper,meta['upper_parts']),(lower,meta['lower_parts'])]:
  at=ob.data.attributes.new('MIA_CrownID','INT','POINT');values=np.zeros(len(ob.data.vertices),dtype=np.int32)
  for j,part in enumerate(parts):a,b=part['vertex_range'];values[a:b]=j
  at.data.foreach_set('value',values);ob['V002M_scope']='14 closed volume crowns on a curved dental arch; hidden anatomy inferred. Upper head-fixed; lower moves rigidly with dental hinge. Original flat tooth strips archived reversibly.'
 collar['V002M_scope']='128 evaluated skin-border samples to unchanged16-point inner lining boundary. Only outer48 legacy lining faces archived; deeper272 pink cavity/tongue faces retained. Skin key arrays unchanged.'
 for ob in [anchor,hinge,upper,lower,collar]:ob['mia_component']='mouth'
 if variant=='C':apply_style_to_current_scene('C')
 bpy.context.view_layer.update()
 return {'objects':[anchor.name,hinge.name,upper.name,lower.name,collar.name],'archive_group':archive.name,'archive_modifier':mask.name,'new_materials':[cavity.name,enamel.name],'grin_existing_arrays_overwritten':False,'new_controls_default_zero':{'ManualDentalJaw':hinge['ManualDentalJaw']},'global_head_control_added':False,'payload_sha256':meta['payload_sha256']}

def apply_style_to_current_scene(variant='C'):
 """Runtime amendment of the owned new dental rows only. Opens/saves no native."""
 assert variant=='C';meta=json.loads((P/'payload/mouth-rig-C.json').read_text());file=P/'payload'/meta['payload'];assert sha(file)==meta['payload_sha256'];data=np.load(file)
 for role,name in [('upper','MIA_v002_UpperDentalCrowns'),('lower','MIA_v002_LowerDentalCrowns')]:
  ob=bpy.data.objects[name];points=data[role+'_positions'].copy()
  if role=='lower':points-=np.array(meta['jaw_pivot_reference_world'])
  assert len(points)==len(ob.data.vertices);ob.data.vertices.foreach_set('co',points.ravel());ob.data.update()
 enamel=bpy.data.materials['MIA_v002_Enamel_ActualToon'];enamel.node_tree.nodes['V002M_ControlledToonLight'].inputs['To Min'].default_value=meta['enamel_styling']['light_floor'];enamel.node_tree.nodes['V002M_RestrainedActualSpec'].inputs[0].default_value=meta['enamel_styling']['specular_gain'];enamel['V002M_style']='C: narrower proximal visibility through restrained anterior shoulder contact; softer enamel separation shade; true upper/lower seam and crown depth retained.'
 for name in ['MIA_v002_MouthAnchor','MIA_v002_DentalJawHinge','MIA_v002_UpperDentalCrowns','MIA_v002_LowerDentalCrowns','MIA_v002_EvaluatedLipCollar']:bpy.data.objects[name]['mia_component']='mouth'
 bpy.context.view_layer.update();return {'variant':'C','payload_sha256':meta['payload_sha256'],'native_saved':False}
