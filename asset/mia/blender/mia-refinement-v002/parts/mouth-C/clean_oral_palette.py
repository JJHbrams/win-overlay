"""Brand-new clean oral materials plus a default-off depth palette. No native save."""
from pathlib import Path
import bpy,numpy as np,json,hashlib
P=Path(__file__).resolve().parent
def mtoon_state(mat):
 ext=getattr(mat,'vrm_addon_extension',None);mt=getattr(ext,'mtoon1',None);rna=getattr(mt,'enabled',None)
 stored=mat.get('vrm_addon_extension');stored_value=None
 try:stored_value=stored.get('mtoon1',{}).get('enabled') if stored is not None else None
 except Exception:pass
 return {'RNA_enabled':rna,'stored_IDProperty_enabled':stored_value,'resolved_enabled':rna if rna is not None else stored_value}
def material_state(ob):
 mat=ob if isinstance(ob,bpy.types.Material) else ob.material_slots[0].material;owner=None if isinstance(ob,bpy.types.Material) else ob;nt=mat.node_tree;out=nt.get_output_node('EEVEE')
 graph={'nodes':[{'name':n.name,'type':n.bl_idname,'target':getattr(n,'target',None),'active':getattr(n,'is_active_output',None),'inputs':[(s.identifier,list(s.default_value) if hasattr(s.default_value,'__len__') and not isinstance(s.default_value,str) else s.default_value) for s in n.inputs if hasattr(s,'default_value')],'outputs':[(s.identifier,list(s.default_value) if hasattr(s.default_value,'__len__') and not isinstance(s.default_value,str) else s.default_value) for s in n.outputs if hasattr(s,'default_value')],'image':n.image.name if getattr(n,'image',None) else None} for n in nt.nodes],'links':[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in nt.links]}
 return {'material':mat.name,'slot_link':owner.material_slots[0].link if owner else None,'data_slot':owner.data.materials[0].name if owner else None,'mtoon':mtoon_state(mat),'graph_sha256':hashlib.sha256(json.dumps(graph,sort_keys=True,default=str).encode()).hexdigest(),'EEVEE_output':None if out is None else {'name':out.name,'target':out.target,'Surface':[(l.from_node.name,l.from_socket.identifier) for l in out.inputs['Surface'].links]},'top_outputs':[(n.name,n.target,n.is_active_output) for n in nt.nodes if n.type=='OUTPUT_MATERIAL'],'groups':[n.name for n in nt.nodes if n.type=='GROUP']}
def apply_to_current_scene(amount=0.):
 assert 0<=amount<=1;master=bpy.data.objects['MIA_V27_Foundation_Face'];collar=bpy.data.objects['MIA_v002_EvaluatedLipCollar'];assert len(collar.data.vertices)==512
 meta=json.loads((P/'payload/mouth-rig-C.json').read_text());payload=P/'payload'/meta['payload'];assert hashlib.sha256(payload.read_bytes()).hexdigest()==meta['payload_sha256'];data=np.load(payload);index=meta['key_names'].index('Face.M_F00_000_00_Fcl_MIA_ToothyGrin');points=data['collar_positions'][index].reshape(4,128,3);distance=np.zeros((4,128),dtype=np.float32)
 for r in range(1,4):distance[r]=distance[r-1]+np.linalg.norm(points[r]-points[r-1],axis=1)
 attr=collar.data.attributes.get('MIA_v002_OralDepthDistance') or collar.data.attributes.new('MIA_v002_OralDepthDistance','FLOAT','POINT');attr.data.foreach_set('value',distance.ravel());created=[];sources={}
 for ob,inner in [(master,False),(collar,True)]:
  source=ob.material_slots[0].material
  if source.get('V002M_clean_oral'):
   source.node_tree.nodes['V002M_CleanDepthAmount'].outputs[0].default_value=amount;created.append(source.name);continue
  sources[ob.name]=material_state(ob);source.use_fake_user=True;out=source.node_tree.get_output_node('EEVEE');assert out and 'V002M_ToonOutput' in source.node_tree.nodes
  keep={out};stack=[l.from_node for l in out.inputs['Surface'].links]
  while stack:
   n=stack.pop()
   if n in keep:continue
   keep.add(n);stack.extend(l.from_node for s in n.inputs for l in s.links)
  assert all(n.type!='GROUP' for n in keep),'Unexpected inherited group in intended toon ancestry'
  clean=bpy.data.materials.new('MIA_v002_CleanOral_'+('Collar' if inner else 'Deep'));initial_flag=mtoon_state(clean)
  if initial_flag['resolved_enabled'] is True:
   clean.vrm_addon_extension.mtoon1.enabled=False
  clean.use_nodes=True;nt=clean.node_tree;nt.nodes.clear();mapping={}
  for n in source.node_tree.nodes:
   if n not in keep:continue
   q=nt.nodes.new(n.bl_idname);q.name=n.name;mapping[n.name]=q
   for prop in ['operation','blend_type','interpolation','extension','projection','uv_map','attribute_name','target','is_active_output','clamp','interpolation_type','data_type','use_clamp']:
    if hasattr(n,prop) and hasattr(q,prop):
     try:setattr(q,prop,getattr(n,prop))
     except (AttributeError,TypeError):pass
   if getattr(n,'image',None):q.image=n.image
   for src,dst in zip(n.inputs,q.inputs):
    if hasattr(src,'default_value') and hasattr(dst,'default_value'):
     try:dst.default_value=src.default_value
     except (AttributeError,TypeError,ValueError):pass
  for l in source.node_tree.links:
   if l.from_node in keep and l.to_node in keep:
    src=mapping[l.from_node.name].outputs[l.from_socket.identifier];dst=mapping[l.to_node.name].inputs[l.to_socket.identifier];nt.links.new(src,dst)
  clean.use_backface_culling=source.use_backface_culling;clean['V002M_clean_oral']=True;clean['mia_component']='mouth';clean['V002M_original_material']=source.name;clean['V002M_original_mtoon']=json.dumps(mtoon_state(source));clean['V002M_new_material_initial_mtoon']=json.dumps(initial_flag)
  n=nt.nodes;l=nt.links;lit=n['V002M_AtlasTimesActualLight'];original=lit.inputs[1].links[0].from_socket;switch=n.new('ShaderNodeValue');switch.name='V002M_CleanDepthAmount';switch.outputs[0].default_value=amount;hs=n.new('ShaderNodeHueSaturation');hs.name='V002M_CleanDepthPalette';hs.inputs['Hue'].default_value=.5;hs.inputs['Saturation'].default_value=.12;hs.inputs['Value'].default_value=.18;hs.inputs['Fac'].default_value=1.;l.new(original,hs.inputs['Color']);fac=switch.outputs[0]
  if inner:
   attribute=n.new('ShaderNodeAttribute');attribute.attribute_name='MIA_v002_OralDepthDistance';attribute.name='V002M_ActualRootDistance';r=n.new('ShaderNodeMapRange');r.name='V002M_NarrowRootFalloff';r.clamp=True;r.interpolation_type='SMOOTHSTEP';r.inputs['From Min'].default_value=.00010;r.inputs['From Max'].default_value=.00065;r.inputs['To Min'].default_value=0.;r.inputs['To Max'].default_value=1.;l.new(attribute.outputs['Fac'],r.inputs['Value']);weight=n.new('ShaderNodeMath');weight.operation='MULTIPLY';l.new(r.outputs['Result'],weight.inputs[0]);l.new(switch.outputs[0],weight.inputs[1]);fac=weight.outputs[0]
  mix=n.new('ShaderNodeMixRGB');mix.name='V002M_CleanPaletteMix';mix.blend_type='MIX';mix.use_clamp=False;l.new(fac,mix.inputs[0]);l.new(original,mix.inputs[1]);l.new(hs.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],lit.inputs[1]);ob.material_slots[0].material=clean;assert mtoon_state(clean)['resolved_enabled'] is not True;created.append(clean.name)
 bpy.context.view_layer.update();return {'amount':amount,'materials':created,'source_materials':sources,'brand_new_materials':True,'no_inherited_groups':True,'root_distance_reference':'Current C P10 collar geodesic field','protected_root_distance_m':.00010,'full_depth_distance_m':.00065,'core_payload_unchanged':meta['payload_sha256'],'native_saved':False}
