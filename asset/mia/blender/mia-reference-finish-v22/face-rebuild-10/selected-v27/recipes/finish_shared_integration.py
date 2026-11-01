import bpy,numpy as np,json
from pathlib import Path
O=Path(__file__).parent;OUT=O/'face-shared-final';bpy.ops.wm.open_mainfile(filepath=str(OUT/'Mia_Foundation_v27.blend'));body=bpy.data.objects['MIA_V27_SharedHeadBody'];master=bpy.data.objects['MIA_V27_Foundation_Face'];arm=next(m for m in body.modifiers if m.type=='ARMATURE');owners=[master]+[o for o in bpy.context.scene.objects if 'BoundaryRibbon' in o.name and not o.hide_render];bpy.context.view_layer.update()
def worldpoints(o):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();p=np.array([e.matrix_world@v.co for v in m.vertices]);e.to_mesh_clear();return p
neutral={o.name:worldpoints(o) for o in owners}
for o in owners:
 if o!=master:
  g=o.vertex_groups.get('J_Bip_C_Head') or o.vertex_groups.new(name='J_Bip_C_Head');g.add(list(range(len(o.data.vertices))),1.,'REPLACE')
 mod=o.modifiers.new('V27_FaceHead_RigFollow','ARMATURE');mod.object=arm.object;mod.use_deform_preserve_volume=arm.use_deform_preserve_volume;mod.use_vertex_groups=True;mod.use_bone_envelopes=False
bpy.context.view_layer.update();neutral_error={o.name:float(abs(worldpoints(o)-neutral[o.name]).max()) for o in owners};assert max(neutral_error.values())<1e-6,neutral_error
# The original rig's rest-space Head weights define only the head/upper-neck blend.
attr=body.data.attributes.new('V27_HeadMaterialBlend','FLOAT','POINT');head=body.vertex_groups['J_Bip_C_Head'];active=[]
for v in body.data.vertices:
 w=next((g.weight for g in v.groups if g.group==head.index),0.);attr.data[v.index].value=w
 if w:active.append((body.matrix_world@v.co).z)
uniform=body.material_slots[0].material.copy();uniform.name='V27_HeadUniformRoute_Source';nt=uniform.node_tree;n=nt.nodes;l=nt.links;mix=n['PigmentTimesControlledLight'];
for link in list(mix.inputs[1].links):l.remove(link)
mix.inputs[1].default_value=(.82,.63,.55,1)
out=next(x for x in n if x.type=='OUTPUT_MATERIAL' and x.is_active_output);used=set()
def visit(x):
 if x in used:return
 used.add(x)
 for socket in x.inputs:
  for link in socket.links:visit(link.from_node)
visit(out);group=bpy.data.node_groups.new('V27_UniformHeadControlledLight','ShaderNodeTree');group.interface.new_socket(name='Shader',in_out='OUTPUT',socket_type='NodeSocketShader');gm={}
for old in used:
 if old==out:continue
 new=group.nodes.new(old.bl_idname);new.name=old.name;gm[old]=new
 for prop in old.bl_rna.properties:
  name=prop.identifier
  if prop.is_readonly or name in {'rna_type','name','location','dimensions','parent','width','height','select'}:continue
  try:setattr(new,name,getattr(old,name))
  except (TypeError,AttributeError,ValueError):pass
 for a,b in zip(old.inputs,new.inputs):
  if hasattr(a,'default_value'):
   try:b.default_value=a.default_value
   except (TypeError,AttributeError,ValueError):pass
 if hasattr(old,'color_ramp'):
  src=old.color_ramp;dst=new.color_ramp;dst.interpolation=src.interpolation
  while len(dst.elements)>2:dst.elements.remove(dst.elements[-1])
  for i,e in enumerate(src.elements):
   t=dst.elements[i] if i<2 else dst.elements.new(e.position);t.position=e.position;t.color=e.color
go=group.nodes.new('NodeGroupOutput')
for link in nt.links:
 if link.from_node not in gm:continue
 if link.to_node==out:group.links.new(gm[link.from_node].outputs[list(link.from_node.outputs).index(link.from_socket)],go.inputs['Shader'])
 elif link.to_node in gm:group.links.new(gm[link.from_node].outputs[list(link.from_node.outputs).index(link.from_socket)],gm[link.to_node].inputs[list(link.to_node.inputs).index(link.to_socket)])
copies={};mapping={}
for i,slot in enumerate(list(body.material_slots)):
 if i==0:continue
 old=slot.material
 if old not in copies:
  m=old.copy();m.name='V27_HeadBlend_'+old.name;nn=m.node_tree.nodes;ll=m.node_tree.links;oo=next(x for x in nn if x.type=='OUTPUT_MATERIAL' and x.is_active_output);prior=oo.inputs['Surface'].links[0].from_socket;gn=nn.new('ShaderNodeGroup');gn.node_tree=group;factor=nn.new('ShaderNodeAttribute');factor.attribute_name=attr.name;blend=nn.new('ShaderNodeMixShader');ll.new(factor.outputs['Fac'],blend.inputs[0]);ll.new(prior,blend.inputs[1]);ll.new(gn.outputs['Shader'],blend.inputs[2]);ll.new(blend.outputs[0],oo.inputs['Surface']);body.data.materials.append(m);copies[old]=len(body.material_slots)-1
 mapping[i]=copies[old]
changed=0
for p in body.data.polygons:
 if p.material_index and any(attr.data[i].value>0 for i in p.vertices):p.material_index=mapping[p.material_index];changed+=1
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Mia_Foundation_v27.blend'))
(OUT/'integration-finish-audit.json').write_text(json.dumps({'neutral_rig_follow_max_component_error_m':neutral_error,'rig':arm.object.name,'ribbon_head_weight':1,'expression_drivers_unchanged':True,'head_material_mask':'Original rig Head vertex weights in rest space, interpolated FLOAT attribute','head_mask_nonzero_min_z':min(active),'head_mask_nonzero_max_z':max(active),'head_material_polygons':changed,'head_uniform_base_linear':[.82,.63,.55],'uniform_route_nodes':[(x.name,x.bl_idname) for x in used if x!=out],'lowerbody_original_material_slots_retained':True,'limits':'Small head-pose and final actual image checks pending. Not full motion rig acceptance.'},indent=2));print('SHARED_INTEGRATION_FINISHED')
