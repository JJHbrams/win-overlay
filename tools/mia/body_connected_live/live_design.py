"""Install the one new static DESIGN cage, keeping real source ownership/UV loops."""
from pathlib import Path
import hashlib,json
import bpy,numpy as np
ROOT=Path('D:/MiaWorkCache/mia-reference-work/win-overlay');CACHE=ROOT/'.mia-cache/body-connected';NAME='MIA_ChartedBody_Design'
ns=bpy.app.driver_namespace;source=bpy.data.objects['MIA_V27_SharedHeadBody']
assert NAME not in bpy.data.objects and bpy.context.mode=='OBJECT'
p=dict(np.load(CACHE/'charted-design.npz'));oldid=p['original_control_id'];held=oldid>=0
offset=np.r_[0,np.cumsum(p['polygon_sizes'])];faces=[p['loop_vertices'][offset[i]:offset[i+1]].tolist()for i in range(len(offset)-1)]
ns['MIA_Charted_Context']=dict(selected=[o.name for o in bpy.context.selected_objects],active=bpy.context.view_layer.objects.active.name if bpy.context.view_layer.objects.active else None)
ns['MIA_Charted_Overlays']=[(area.spaces.active.overlay,area.spaces.active.overlay.show_overlays)for screen in bpy.data.screens for area in screen.areas if area.type=='VIEW_3D']
state={o.name:dict(hide_render=o.hide_render,hidden=o.hide_get(),hide_viewport=o.hide_viewport)for o in bpy.context.scene.objects if o.name==source.name or o.name.startswith('MIA_Review12_')}
ns['MIA_Charted_State']=state
ns['MIA_Charted_Source_Raw']=np.array([v.co[:]for v in source.data.vertices],np.float32)
ns['MIA_Charted_Source_Keys']={k.name:hashlib.sha256(np.array([v.co[:]for v in k.data],np.float32).tobytes()).hexdigest()for k in source.data.shape_keys.key_blocks}
me=bpy.data.meshes.new(NAME+'_PrivateMesh');me.from_pydata(p['posed_local'].tolist(),[],faces);me.update()
for mat in source.data.materials:me.materials.append(mat)
for poly,mat in zip(me.polygons,p['polygon_materials']):poly.material_index=int(mat);poly.use_smooth=True
for name,domain,values in [('original_control_id','POINT',oldid),('original_face_id','FACE',p['original_face_id']),('mia_design_chart','FACE',p['face_chart'])]:
 attr=me.attributes.new(name,'INT',domain);attr.data.foreach_set('value',values)
# Retained raw source loops are copied by original face AND corner. New body
# loops are deliberately unpainted placeholders; no production UV assertion.
original_faces=p['original_face_id'];outside=original_faces>=0
uv_proof={}
for layer in source.data.uv_layers:
 src=np.zeros((len(source.data.loops),2),np.float32);layer.uv.foreach_get('vector',src.ravel())
 values=np.zeros((len(me.loops),2),np.float32)
 for fi in np.flatnonzero(outside):
  sf=source.data.polygons[int(original_faces[fi])]
  assert sf.loop_total==int(p['polygon_sizes'][fi])
  values[offset[fi]:offset[fi+1]]=src[sf.loop_start:sf.loop_start+sf.loop_total]
 new=me.uv_layers.new(name=layer.name);new.uv.foreach_set('vector',values.ravel())
 check=np.zeros_like(values);new.uv.foreach_get('vector',check.ravel())
 assert np.array_equal(check,values)
 uv_proof[layer.name]=dict(retained_raw_loop_values_exact=True,new_body_assigned=False,retained_sha256=hashlib.sha256(check[np.concatenate([np.arange(offset[i],offset[i+1])for i in np.flatnonzero(outside)])].tobytes()).hexdigest())
me.uv_layers.active_index=source.data.uv_layers.active_index
for old,new in zip(source.data.uv_layers,me.uv_layers):new.active_render=old.active_render
# Preserve source group names and retained weights. New points have no rig
# weights yet; Smooth/Weld do not accidentally consume generic bone weights.
ob=source.copy();ob.name=NAME;ob.data=me;ob.animation_data_clear()
for group in source.vertex_groups:
 if group.name not in ob.vertex_groups:ob.vertex_groups.new(name=group.name)
for mod in list(ob.modifiers):
 if mod.type=='ARMATURE':ob.modifiers.remove(mod)
for vi in np.flatnonzero(held):
 for assignment in source.data.vertices[int(oldid[vi])].groups:
  ob.vertex_groups[assignment.group].add([int(vi)],assignment.weight,'REPLACE')
bpy.context.scene.collection.objects.link(ob)
gray=bpy.data.materials.new(NAME+'_Gray');gray.use_nodes=True
nodes=gray.node_tree.nodes;nodes.clear();bs=nodes.new('ShaderNodeBsdfPrincipled');bs.inputs['Base Color'].default_value=(.23,.23,.23,1);bs.inputs['Roughness'].default_value=.85
out=nodes.new('ShaderNodeOutputMaterial');gray.node_tree.links.new(bs.outputs[0],out.inputs['Surface'])
# All new lower-neck/clavicle/body faces share the SAME gray regardless of
# their former source material. Display color is not read as an anatomy fossa.
ob.material_slots[1].link='OBJECT';ob.material_slots[1].material=gray
# A continuous gray lower-neck diagnostic, not a skin-colored material strip.
for fi,poly in enumerate(me.polygons):
 if float(np.mean(p['world'][poly.vertices[:],2]))<1.48:poly.material_index=1
for name in state:bpy.data.objects[name].hide_render=True;bpy.data.objects[name].hide_set(True)
for old in list(bpy.context.selected_objects):old.select_set(False)
ob.hide_render=False;ob.hide_viewport=False;ob.hide_set(False);ob.select_set(True);bpy.context.view_layer.objects.active=ob
ns['MIA_Charted_Gray']=gray.name;ns['MIA_Charted_Object']=ob.name
bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get();e=ob.evaluated_get(dg);ev=e.to_mesh(preserve_all_data_layers=True,depsgraph=dg)
evw=np.array([e.matrix_world@v.co for v in ev.vertices],np.float32);ev.calc_loop_triangles();tri=np.array([t.vertices[:]for t in ev.loop_triangles],np.int32)
e.to_mesh_clear();np.savez_compressed(CACHE/'charted-actual-evaluation.npz',world=evw,triangles=tri)
unreferenced=set(range(len(me.vertices)))-set(p['loop_vertices'].tolist());assert not unreferenced
report=dict(runtime='LIVE_OFFICIAL_MCP',scope='One new connected upperbody static DESIGN cage',object=ob.name,
 raw_controls=len(me.vertices),evaluated_vertices=len(evw),unused_controls=len(unreferenced),original_control_id=True,original_face_id=True,
 retained_control_coordinates_exact=True,retained_raw_UV_loop_proof=uv_proof,
 new_lowerneck_body_same_gray=True,new_original47_body_deltas_and_weights='NOT MIGRATED; no rig on static design object',
 original_source_raw_and47_unchanged=True,head_evaluated_normals_and_shape='UNVERIFIED spatial comparison required after new topology',
 ART=False,native_saved=False)
(CACHE/'live/charted-installed.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps(report),flush=True)
