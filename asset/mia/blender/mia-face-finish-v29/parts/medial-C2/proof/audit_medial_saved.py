"""Fresh native-to-native preservation audit. Computes every asserted equality."""
import bpy,json,numpy as np,hashlib
from pathlib import Path
O=Path(__file__).parent
N=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-orbit-thorax-review-v28/integrated-G2L/Mia_Foundation_v28_G2L.blend');A=O/'Mia_EyeLash_v29_A.blend'
def digest(b):return hashlib.sha256(b).hexdigest()
def arr(data,attr,n):
 a=np.empty(len(data)*n,dtype=np.float32);data.foreach_get(attr,a);return a
def jhash(x):return digest(json.dumps(x,sort_keys=True,default=str).encode())
def val(v):
 if isinstance(v,(float,int,bool,str)) or v is None:return v
 try:return list(v)
 except:return str(v)
def treesnapshot(nt,visited=None):
 if nt is None:return None
 visited=set() if visited is None else visited
 if nt.name in visited:return {'shared_tree':nt.name}
 visited.add(nt.name);nn=[]
 for n in nt.nodes:
  d={'name':n.name,'type':n.bl_idname,'inputs':[(s.identifier,val(s.default_value)) for s in n.inputs if hasattr(s,'default_value')],'outputs':[(s.identifier,val(s.default_value)) for s in n.outputs if hasattr(s,'default_value')]}
  for p in ['operation','blend_type','interpolation','extension','projection','uv_map','attribute_name','is_active_output','target']:
   if hasattr(n,p):d[p]=val(getattr(n,p))
  if getattr(n,'image',None):d['image']=n.image.name
  if getattr(n,'node_tree',None):d['group']=treesnapshot(n.node_tree,visited)
  if hasattr(n,'color_ramp'):d['ramp']={'interpolation':n.color_ramp.interpolation,'elements':[(e.position,list(e.color)) for e in n.color_ramp.elements]}
  nn.append(d)
 return {'name':nt.name,'nodes':nn,'links':[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in nt.links]}
def snapshot(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));out={};prefix=None;skincoords=None
 for ob in bpy.context.scene.objects:
  if ob.type!='MESH':continue
  me=ob.data;chunks=[arr(me.vertices,'co',3).tobytes()];names=[]
  if me.shape_keys:
   names=[k.name for k in me.shape_keys.key_blocks]
   ks=np.array([arr(k.data,'co',3).reshape(-1,3) for k in me.shape_keys.key_blocks]);chunks.append(ks.tobytes())
   if ob.name=='MIA_V27_SharedHeadBody':prefix=digest(ks[:,:3957].tobytes());skincoords=ks.copy()
  uv={u.name:digest(arr(u.data,'uv',2).tobytes()) for u in me.uv_layers}
  weights=[[(ob.vertex_groups[g.group].name,float(g.weight)) for g in v.groups] for v in me.vertices]
  topo=jhash({'polygons':[(list(f.vertices),f.material_index,f.use_smooth) for f in me.polygons],'edges':[list(e.vertices) for e in me.edges]})
  out[ob.name]={'coordinates':digest(b''.join(chunks)),'topology':topo,'uv':uv,'named_weights':jhash(weights),'key_names':names,'material_slots':[(s.name,s.link) for s in ob.material_slots],'matrix':[list(r) for r in ob.matrix_world]}
 mats={m.name:jhash({'tree':treesnapshot(m.node_tree),'diffuse_color':list(m.diffuse_color),'use_nodes':m.use_nodes,'backface_culling':m.use_backface_culling}) for m in bpy.data.materials}
 images={im.name:{'colorspace':im.colorspace_settings.name,'source':im.source,'size':list(im.size),'packed_sha256':digest(im.packed_file.data) if im.packed_file else None} for im in bpy.data.images}
 return {'objects':out,'materials':mats,'images':images,'bodyprefix':prefix,'skincoords':skincoords}
b=snapshot(N);a=snapshot(A);ownerlist=json.loads((O/'medial-A-audit.json').read_text())['changes'];checks={}
for field in ['topology','uv','named_weights','key_names','material_slots','matrix']:
 checks[field+'_exact_all_meshes']=all(a['objects'][n][field]==d[field] for n,d in b['objects'].items())
checks['all_unrelated_mesh_coordinates_exact']=all(a['objects'][n]['coordinates']==d['coordinates'] for n,d in b['objects'].items() if n not in ownerlist)
checks['body_L_original_prefix_exact_all42']=a['bodyprefix']==b['bodyprefix'];checks['all_material_graphs_and_slot_defaults_exact']=a['materials']==b['materials'];checks['all_packed_image_payloads_and_colorspaces_exact']=a['images']==b['images']
ii=np.flatnonzero(abs(a['skincoords']-b['skincoords']).max(axis=(0,2))>0);delta=(a['skincoords']-b['skincoords']);basisii=np.flatnonzero(abs(delta[0]).max(axis=1)>0)
result={'baseline_native_sha256':digest(N.read_bytes()),'candidate_native_sha256':digest(A.read_bytes()),'checks':checks,'all_computed_checks_pass':all(checks.values()),'actual_skin_changed_indices_allkeys':ii.tolist(),'actual_skin_basis_changed_indices':basisii.tolist(),'max_allkey_skin_displacement_mm':float(np.linalg.norm(delta,axis=2).max()*1000),'protected_body_prefix_sha256':a['bodyprefix'],'comparison_scope':'Freshly reopened saved native; all mesh topology/UV/named weights/materialslots/matrices/keynames; unrelated geometry; all42 BodyL prefix coordinates; all material node graphs including nested groups, socket defaults, ramps; packed image bytes/colorspaces.'}
(O/'medial-A-fresh-preservation.json').write_text(json.dumps(result,indent=2));assert result['all_computed_checks_pass'],result;print('FRESH_NATIVE_PRESERVATION_PASS',len(a['objects']),'meshes',len(a['materials']),'materials')
