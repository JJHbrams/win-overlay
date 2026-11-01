"""Read-only native shader/UV/pigment inventory. Never saves the Blender file."""
import bpy,numpy as np,json,hashlib
from pathlib import Path
P=Path(__file__).parent;S=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-orbit-thorax-review-v28/integrated-G2L/Mia_Foundation_v28_G2L.blend')
EXPECTED='f0dead17dba4f492c47652dab62c48a93bcd0100bc2586ca3ac315d41a977ee2'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert sha(S)==EXPECTED
bpy.ops.wm.open_mainfile(filepath=str(S),use_scripts=False);scene=bpy.context.scene
def val(x):
 if isinstance(x,(str,bool,int,float)) or x is None:return x
 try:return list(x)
 except:return str(x)
def socket(s):
 r={'name':s.name,'identifier':s.identifier,'linked':s.is_linked}
 if hasattr(s,'default_value'):r['default']=val(s.default_value)
 return r
def image_info(im):
 return {'name':im.name,'filepath':im.filepath,'source':im.source,'size':list(im.size),'channels':im.channels,'depth':im.depth,'float_buffer':im.is_float,'colorspace':im.colorspace_settings.name,'alpha_mode':im.alpha_mode,'packed':bool(im.packed_file),'packed_sha256':hashlib.sha256(im.packed_file.data).hexdigest() if im.packed_file else None}
def node_info(n):
 r={'name':n.name,'label':n.label,'type':n.bl_idname,'mute':n.mute,'inputs':[socket(i) for i in n.inputs]}
 for a in ['operation','blend_type','data_type','vector_type','convert_from','convert_to','uv_map','attribute_name','attribute_type','interpolation','extension','projection','space','distribution']:
  if hasattr(n,a):r[a]=val(getattr(n,a))
 if n.type=='TEX_IMAGE':r['image']=image_info(n.image) if n.image else None
 if n.type=='VALTORGB':r['ramp']={'interpolation':n.color_ramp.interpolation,'elements':[{'position':e.position,'color':list(e.color)} for e in n.color_ramp.elements]}
 if n.type=='RGB':r['output_color']=list(n.outputs[0].default_value)
 if n.type=='VALUE':r['output_value']=n.outputs[0].default_value
 if n.type=='GROUP':r['group']=n.node_tree.name if n.node_tree else None
 return r
def trace(tree,root_type):
 roots=[n for n in tree.nodes if n.type==root_type and (not hasattr(n,'is_active_output') or n.is_active_output)];seen=set();queue=list(roots)
 while queue:
  n=queue.pop()
  if n.name in seen:continue
  seen.add(n.name)
  for inp in n.inputs:
   for link in inp.links:queue.append(link.from_node)
 links=[[l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier] for l in tree.links if l.to_node.name in seen and l.from_node.name in seen]
 groups={}
 for n in tree.nodes:
  if n.name in seen and n.type=='GROUP' and n.node_tree:groups[n.name]=trace(n.node_tree,'GROUP_OUTPUT')
 return {'active_outputs':[n.name for n in roots],'reachable_nodes':[node_info(n) for n in tree.nodes if n.name in seen],'reachable_links':links,'unconnected_node_count':len(tree.nodes)-len(seen),'unconnected_nodes':[{'name':n.name,'type':n.bl_idname} for n in tree.nodes if n.name not in seen],'nested_groups':groups}
owner=bpy.data.objects['MIA_V27_SharedHeadBody'];m=owner.data;coords=np.array([list(owner.matrix_world@v.co) for v in m.vertices]);basis=np.array([list(owner.matrix_world@v.co) for v in m.shape_keys.key_blocks[0].data])
slots=[]
for i,slot in enumerate(owner.material_slots):
 polys=[p for p in m.polygons if p.material_index==i];vids=np.unique([v for p in polys for v in p.vertices]).astype(int);facepolys=[p for p in polys if any(v>=3957 for v in p.vertices)]
 slots.append({'index':i,'material':slot.material.name if slot.material else None,'polygons':len(polys),'vertex_count':len(vids),'Face690_polygons':len(facepolys),'Body3957_polygons':len(polys)-len(facepolys),'basis_world_bbox':[basis[vids].min(0).tolist(),basis[vids].max(0).tolist()] if len(vids) else None,'uv_bounds':{uv.name:[np.array([list(uv.data[j].uv) for p in polys for j in p.loop_indices]).min(0).tolist(),np.array([list(uv.data[j].uv) for p in polys for j in p.loop_indices]).max(0).tolist()] for uv in m.uv_layers} if polys else {}})
attributes=[]
for a in m.attributes:
 r={'name':a.name,'type':a.data_type,'domain':a.domain,'length':len(a.data)}
 if a.data_type=='FLOAT' and a.domain=='POINT':
  v=np.array([d.value for d in a.data]);r['range']=[float(v.min()),float(v.max())];r['Face690_range']=[float(v[3957:].min()),float(v[3957:].max())];r['head_neck_body_range']=[float(v[(basis[:,2]>1.40)&(np.arange(len(v))<3957)].min()),float(v[(basis[:,2]>1.40)&(np.arange(len(v))<3957)].max())];np.save(P/(a.name.replace('/','_')+'-attribute.npy'),v)
 attributes.append(r)
objects=[];used=set()
for o in scene.objects:
 if o.type!='MESH':continue
 mats=[s.material.name if s.material else None for s in o.material_slots];used.update(x for x in mats if x)
 if o==owner or any(t in o.name.lower() for t in ['eye','lid','lash','brow','face','skin','hair','neck']):objects.append({'name':o.name,'mesh':o.data.name,'vertices':len(o.data.vertices),'hide_render':o.hide_render,'hide_viewport':o.hide_viewport,'hide_get':o.hide_get(),'materials':mats,'collections':[c.name for c in o.users_collection]})
materials={name:trace(bpy.data.materials[name].node_tree,'OUTPUT_MATERIAL') for name in sorted(used) if bpy.data.materials[name].use_nodes}
active_images={}
for name,route in materials.items():
 for n in route['reachable_nodes']:
  if n.get('image'):active_images.setdefault(n['image']['name'],[]).append({'material':name,'node':n['name']})
pigments={}
for name,uses in active_images.items():
 im=bpy.data.images[name]
 if 'face' not in name.lower() and not any('face' in x['material'].lower() for x in uses):continue
 pixels=np.empty(len(im.pixels),dtype=np.float32);im.pixels.foreach_get(pixels);pixels=pixels.reshape(im.size[1],im.size[0],im.channels);filename='active-face-image-'+str(len(pigments))+'.npz';np.savez_compressed(P/filename,pixels=pixels)
 pigments[name]={'image':image_info(im),'reachable_uses':uses,'pixels_sha256':hashlib.sha256(pixels.tobytes()).hexdigest(),'pixel_array':filename,'per_channel_min':pixels.min((0,1)).tolist(),'per_channel_max':pixels.max((0,1)).tolist(),'per_channel_mean':pixels.mean((0,1)).tolist()}
uv={u.name:{'active':u.active,'active_render':u.active_render,'active_clone':u.active_clone,'loops':len(u.data)} for u in m.uv_layers}
groups={g.name:{'count':0,'min':1.,'max':0.} for g in owner.vertex_groups if any(t in g.name.lower() for t in ['head','neck','face'])}
for v in m.vertices:
 for g in v.groups:
  name=owner.vertex_groups[g.group].name
  if name in groups:r=groups[name];r['count']+=1;r['min']=min(r['min'],g.weight);r['max']=max(r['max'],g.weight)
report={'native':str(S),'native_sha256':EXPECTED,'blender_version':bpy.app.version_string,'native_saved':False,'scene':{'frame':scene.frame_current,'engine':scene.render.engine,'world':scene.world.name if scene.world else None,'world_graph':trace(scene.world.node_tree,'OUTPUT_WORLD') if scene.world and scene.world.use_nodes else None,'display':{'transform':scene.view_settings.view_transform,'look':scene.view_settings.look,'exposure':scene.view_settings.exposure,'gamma':scene.view_settings.gamma},'active_shape_keys':{o.name:{k.name:k.value for k in o.data.shape_keys.key_blocks if k.value} for o in scene.objects if o.type=='MESH' and o.data.shape_keys},'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'color':list(o.data.color),'matrix':[list(r) for r in o.matrix_world],'hide_render':o.hide_render} for o in scene.objects if o.type=='LIGHT']},'owner':{'name':owner.name,'mesh':m.name,'vertices':len(m.vertices),'polygons':len(m.polygons),'material_slots':slots,'uv_layers':uv,'attributes':attributes,'relevant_vertex_groups':groups},'objects':objects,'used_material_active_routes':materials,'active_image_routes':active_images,'face_pigment_arrays':pigments,'route_semantics':'Only nodes reachable from actual active outputs are listed as active. Constant-zero Mix branch influence still requires reading node defaults/links; graph reachability is not proof a map contributes. Unconnected legacy PBR nodes are explicitly excluded.','baseline_sha256_after':sha(S)}
assert report['baseline_sha256_after']==EXPECTED
(P/'active-surface-inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print('ACTIVE_SURFACE_AUDIT_DONE',len(materials),'usedmaterials',len(pigments),'faceimages',flush=True)
