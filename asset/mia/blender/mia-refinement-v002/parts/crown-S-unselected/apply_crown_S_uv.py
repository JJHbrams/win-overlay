"""Frozen hybrid Crown unique-UV/baked-pigment slot, no full-scene replay.

4759 actual well-resolved outer-sheet faces use one UV+one texture. The240
legacy peripheral/return exceptions keep the exact existing/R route.
"""
import bpy,numpy as np,json,hashlib
from pathlib import Path
def apply(folder):
 folder=Path(folder);cfg=json.loads((folder/'manifest.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();payload=folder/'crown-flow-frozen.npz';imageFile=folder/'Crown_S_ExistingPigment_Bake.png'
 assert sha(payload)==cfg['payload_sha256'] and sha(imageFile)==cfg['seed_pigment_sha256']
 ob=bpy.data.objects['MIA_V17_PIXAL_DetailedHair'];me=ob.data;co=np.array([v.co[:] for v in me.vertices],np.float32);T=np.array([p.vertices[:] for p in me.polygons],np.int32);raw=np.array([x.value for x in me.attributes['MIA_SOURCE_POLYGON'].data],np.int32)
 assert hashlib.sha256(co.tobytes()).hexdigest()==cfg['expected_coords_sha256'];assert hashlib.sha256(T.tobytes()).hexdigest()==cfg['expected_topology_sha256'];assert hashlib.sha256(raw.tobytes()).hexdigest()==cfg['expected_raw_ids_sha256'];assert cfg['new_UV'] not in me.uv_layers
 for name,digest in cfg['old_UV_hashes'].items():assert hashlib.sha256(np.array([v.uv[:] for v in me.uv_layers[name].data],np.float32).tobytes()).hexdigest()==digest
 old=ob.material_slots[0].material;assert old.name.startswith('MIA_v002_R_SideNape_');assert all(p.material_index==0 for p in me.polygons)
 data=np.load(payload);ids=data['polygon_indices'];assert len(ids)==4759;assert np.array_equal(raw[ids],data['raw_ids']) and np.array_equal(T[ids],data['vertices']);uv=data['loop_uv'];cross=(uv[:,1,0]-uv[:,0,0])*(uv[:,2,1]-uv[:,0,1])-(uv[:,1,1]-uv[:,0,1])*(uv[:,2,0]-uv[:,0,0]);assert np.all(cross>0)
 state=[(u.name,bool(u.active_render),bool(u.active_clone)) for u in me.uv_layers];active=me.uv_layers.active_index;allUV=np.zeros((len(me.loops),2),np.float32);loops=np.array([p.loop_indices[:] for p in me.polygons],int);allUV[loops[ids].ravel()]=uv.reshape(-1,2);new=me.uv_layers.new(name=cfg['new_UV']);new.data.foreach_set('uv',allUV.ravel());new.active_render=False;new.active_clone=False
 for name,render,clone in state:me.uv_layers[name].active_render=render;me.uv_layers[name].active_clone=clone
 me.uv_layers.active_index=active
 image=bpy.data.images.load(str(imageFile),check_existing=False);image.name='MIA_v002_S_ExistingPigment_UniqueUV_Bake';image.colorspace_settings.name='sRGB';image.alpha_mode='CHANNEL_PACKED';image.pack();ma=old.copy();ma.name='MIA_v002_S_CrownFlow_ExistingPigment_Bake';n=ma.node_tree.nodes;l=ma.node_tree.links;uvnode=n.new('ShaderNodeUVMap');uvnode.name='S_OWNED_CROWN_FLOW_UV';uvnode.uv_map=cfg['new_UV'];tex=n.new('ShaderNodeTexImage');tex.name='S_OWNED_EXISTING_PIGMENT_BAKE';tex.image=image;tex.interpolation='Linear';tex.extension='EXTEND';l.new(uvnode.outputs[0],tex.inputs['Vector']);grade=n['V002_SOURCE_ASH_GRADE_INPUT'];l.new(tex.outputs['Color'],grade.inputs[0])
 def active_nodes():
  output=next(x for x in n if x.type=='OUTPUT_MATERIAL' and x.is_active_output);visited=set();stack=[output]
  while stack:
   node=stack.pop()
   if node in visited:continue
   visited.add(node)
   for inp in node.inputs:
    for link in inp.links:stack.append(link.from_node)
  return visited
 geo=n['V002_ACTUAL_DEFORMED_GEOMETRIC_NORMAL']
 for node in active_nodes():
  if node.type=='BSDF_DIFFUSE':l.new(geo.outputs['Normal'],node.inputs['Normal'])
 used=active_nodes()
 for node in list(n):
  if node not in used:n.remove(node)
 assert sum(x.type=='TEX_IMAGE' for x in n)==1 and sum(x.type=='UVMAP' for x in n)==1 and sum(x.type=='ATTRIBUTE' for x in n)==0
 slot=len(me.materials);me.materials.append(ma)
 for i in ids:me.polygons[int(i)].material_index=slot
 return {'variant':'S hybrid Crown UV/bake review','new_UV':new.name,'new_material':ma.name,'slot':slot,'new_material_faces':len(ids),'legacy_route_exceptions':len(data['legacy_polygon_indices']),'complete_documented_layer_faces':len(data['full_layer_polygon_indices']),'active_texture_images':1,'active_UV_attributes':1,'active_generic_attributes':0,'actual_deformed_geometry_normal_and_K_toon_light_route':True,'old_R_material_and_original_maps_unchanged':True,'pigment_is_existing_numeric_bake_only':True,'authored_fill_not_yet_generated':True,'not_fully_migrated_or_export_ready':True,'ART':'BOUNDARY_UV_BAKE_REVIEW_ONLY'}
