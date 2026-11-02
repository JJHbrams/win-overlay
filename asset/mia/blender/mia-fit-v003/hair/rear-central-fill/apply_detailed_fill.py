"""Actual detailed Main-fragment copies + buried support. No original owner mutation."""
from pathlib import Path
import bpy,numpy as np,json,hashlib
from mathutils import Matrix
COLL='MIA_v003_DetailedRearFill_B'
def core_material():
 ma=bpy.data.materials.new('MIA_v003_BuriedCore_DarkAsh');ma.use_nodes=True;n=ma.node_tree.nodes;n.clear();l=ma.node_tree.links;d=n.new('ShaderNodeBsdfDiffuse');d.inputs['Color'].default_value=(1,1,1,1);s=n.new('ShaderNodeShaderToRGB');l.new(d.outputs[0],s.inputs[0]);m=n.new('ShaderNodeMixRGB');m.blend_type='MULTIPLY';m.inputs[0].default_value=1;m.inputs[1].default_value=(.105,.095,.09,1);l.new(s.outputs['Color'],m.inputs[2]);e=n.new('ShaderNodeEmission');l.new(m.outputs[0],e.inputs['Color']);o=n.new('ShaderNodeOutputMaterial');o.is_active_output=True;l.new(e.outputs[0],o.inputs['Surface']);return ma
def attach(ob,weights,rig):
 ob['mia_component']='hair';ob.parent=rig;ob.matrix_parent_inverse=rig.matrix_world.inverted();ob.matrix_world=Matrix.Identity(4);a=ob.vertex_groups.new(name='J_Bip_C_Head');b=ob.vertex_groups.new(name='J_Bip_C_UpperChest')
 for i,w in enumerate(weights):a.add([i],float(w),'REPLACE');b.add([i],1-float(w),'REPLACE')
 mod=ob.modifiers.new('Current rig rest attachment','ARMATURE');mod.object=rig
def apply(folder):
 P=Path(folder);cfg=json.loads((P/'detailed-fill.json').read_text());assert hashlib.sha256((P/'detailed-fill.npz').read_bytes()).hexdigest()==cfg['payload_sha256'];core=json.loads((P/'buried-core.json').read_text());assert hashlib.sha256((P/'buried-core.npz').read_bytes()).hexdigest()==core['payload_sha256'];assert bpy.data.collections.get(COLL) is None;source=bpy.data.objects['MIA_V17_PIXAL_DetailedHair'];sm=source.data;assert hashlib.sha256(np.array([v.co[:] for v in sm.vertices],np.float32).tobytes()).hexdigest()==cfg['source_main_co_sha256'];d=np.load(P/'detailed-fill.npz');c=np.load(P/'buried-core.npz')
 for row in cfg['layers']:
  name=row['name'];faces=d[name+'_faces'];sv=d[name+'_source_vertex'];sf=d[name+'_source_face']
  for i in np.flatnonzero(sf>=0):assert set(sm.polygons[int(sf[i])].vertices)==set(int(v) for v in sv[faces[i]]),'Source topology changed; no mutation performed'
 collection=bpy.data.collections.new(COLL);bpy.context.scene.collection.children.link(collection);rig=bpy.data.objects['MIA_V06_RIG'];ma=core_material();created=[];checks=[]
 for row in core['volumes']:
  name=row['name'];me=bpy.data.meshes.new('MIA_V003_RearCore_'+name);me.from_pydata(c[name+'_co'].tolist(),[],c[name+'_faces'].tolist());me.update();me.materials.append(ma)
  for p in me.polygons:p.use_smooth=True
  ob=bpy.data.objects.new(me.name,me);collection.objects.link(ob);ob['MiaDetailedFillOwner']=name;ob['MiaFillRole']='BURIED_SUPPORT_NOT_VISIBLE_FINISH';attach(ob,c[name+'_head_weight'],rig);created.append(ob.name)
 # The CURRENT Main paint/semantic fields and corner UVs are the source, not an old graph replay.
 sourceuv={u.name:np.array([q.uv[:] for q in u.data],np.float32) for u in sm.uv_layers};uvfirst={}
 for name,uv in sourceuv.items():
  values=np.zeros((len(sm.vertices),2),np.float32);used=np.zeros(len(sm.vertices),bool)
  for loop in sm.loops:
   if not used[loop.vertex_index]:values[loop.vertex_index]=uv[loop.index];used[loop.vertex_index]=True
  uvfirst[name]=values
 fields=[]
 for a in sm.attributes:
  if a.domain!='POINT' or a.name=='position':continue
  prop='color' if a.data_type in ['FLOAT_COLOR','BYTE_COLOR'] else 'vector' if a.data_type=='FLOAT_VECTOR' else 'value';width=4 if prop=='color' else 3 if prop=='vector' else 1;values=np.array([getattr(x,prop) for x in a.data]);fields.append((a.name,a.data_type,prop,width,values))
 for row in cfg['layers']:
  name=row['name'];co=d[name+'_co'];faces=d[name+'_faces'];sv=d[name+'_source_vertex'];sf=d[name+'_source_face'];caps={x['new_vertex']:x['interpolate_source_vertices'] for x in row['caps']};me=bpy.data.meshes.new('MIA_V003_DetailedRear_'+name);me.from_pydata(co.tolist(),[],faces.tolist());me.update();me.materials.append(sm.materials[0]);ob=bpy.data.objects.new(me.name,me);collection.objects.link(ob);ob['MiaDetailedFillOwner']=name;ob['MiaFillRole']=row['layer'];ob['MiaSourcePrototype']=row['prototype'];ob['MiaSourcePayloadSHA']=cfg['payload_sha256'];ob['MiaNewMacroNormals']='Recomputed from fitted geometry, not donor custom-normal replay';ob['MiaSourceCurve']=json.dumps(row['source_controls'])
  for uvname,old in sourceuv.items():
   layer=me.uv_layers.new(name=uvname);values=[]
   for fi,t in enumerate(faces):
    if sf[fi]>=0:
     p=sm.polygons[int(sf[fi])];lookup={int(v):int(li) for v,li in zip(p.vertices,p.loop_indices)};values.extend(old[lookup[int(sv[int(v)])]].tolist() for v in t)
    else:
     for v in t:values.append(uvfirst[uvname][int(sv[v])].tolist() if sv[v]>=0 else uvfirst[uvname][caps[int(v)]].mean(0).tolist())
   layer.data.foreach_set('uv',np.array(values,np.float32).ravel());layer.active_render=sm.uv_layers[uvname].active_render;layer.active_clone=sm.uv_layers[uvname].active_clone
  me.uv_layers.active_index=sm.uv_layers.active_index;me.uv_layers[next(u.name for u in sm.uv_layers if u.active_render)].active_render=True
  for field,kind,prop,width,values in fields:
   a=me.attributes.new(name=field,type=kind,domain='POINT');new=np.array([values[int(v)] if v>=0 else (values[caps[i]].mean(0) if kind not in ['INT','BOOLEAN'] else values[caps[i][0]]) for i,v in enumerate(sv)]);a.data.foreach_set(prop,new.astype(np.float32 if kind not in ['INT','BOOLEAN'] else np.int32).ravel())
  raw=me.attributes.new(name='MIA_SOURCE_POLYGON',type='INT',domain='FACE');raw.data.foreach_set('value',np.array([sm.attributes['MIA_SOURCE_POLYGON'].data[int(v)].value if v>=0 else -1 for v in sf],np.int32));origin=me.attributes.new(name='MIA_Central_SourceVertex',type='INT',domain='POINT');origin.data.foreach_set('value',sv)
  for p in me.polygons:p.use_smooth=True
  attach(ob,d[name+'_head_weight'],rig);sub=ob.modifiers.new('New copy source-detail smoothing','SUBSURF');sub.subdivision_type='CATMULL_CLARK';sub.levels=sub.render_levels=1;created.append(ob.name);tree=sm.materials[0].node_tree;stack=[tree.get_output_node('EEVEE')];active=set()
  while stack:
   node=stack.pop()
   if node in active:continue
   active.add(node)
   for sock in node.inputs:
    for link in sock.links:stack.append(link.from_node)
  required=[n.uv_map for n in active if n.type=='UVMAP'];assert all(v in me.uv_layers for v in required);assert all(n.attribute_name in me.attributes for n in active if n.type=='ATTRIBUTE' and n.attribute_name);checks.append(dict(name=ob.name,source_faces=int(np.sum(sf>=0)),new_caps=int(np.sum(sf<0)),UV_names=[u.name for u in me.uv_layers],POINT_fields=[f[0] for f in fields],material=me.materials[0].name,source_corner_UV_and_POINT_fields_copied_by_ID=True))
 bpy.context.view_layer.update();return dict(collection=COLL,created=created,core_count=len(core['volumes']),detailed_count=len(cfg['layers']),new_detailed_data=checks,native_saved=False,old_owners_modified=False,ART=False)
