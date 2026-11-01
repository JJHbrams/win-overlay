"""Independent fresh C vs A verification, including controlled topology exception."""
import bpy,numpy as np,json,hashlib,collections,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
O=Path(__file__).parent;V=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'C';A=O/'Mia_EyeLash_v29_A.blend';C=O/('Mia_EyeLash_v29_'+V+'.blend');remap=np.load(O/('medial-'+V+'-iris-topology-remap.npz'))
def digest(b):return hashlib.sha256(b).hexdigest()
def arr(data,attr,n):
 a=np.empty(len(data)*n,dtype=np.float32);data.foreach_get(attr,a);return a
def jhash(x):return digest(json.dumps(x,sort_keys=True,default=str).encode())
def value(v):
 if isinstance(v,(str,int,float,bool)) or v is None:return v
 try:return list(v)
 except:return str(v)
def graph(nt,visited=None):
 if nt is None:return None
 visited=set() if visited is None else visited
 if nt.name in visited:return {'shared':nt.name}
 visited.add(nt.name);nodes=[]
 for n in nt.nodes:
  d={'name':n.name,'type':n.bl_idname,'inputs':[(s.identifier,value(s.default_value)) for s in n.inputs if hasattr(s,'default_value')],'outputs':[(s.identifier,value(s.default_value)) for s in n.outputs if hasattr(s,'default_value')]}
  for p in ['operation','blend_type','interpolation','extension','projection','uv_map','attribute_name','is_active_output']:
   if hasattr(n,p):d[p]=value(getattr(n,p))
  if getattr(n,'image',None):d['image']=n.image.name
  if getattr(n,'node_tree',None):d['group']=graph(n.node_tree,visited)
  if hasattr(n,'color_ramp'):d['ramp']=[(e.position,list(e.color)) for e in n.color_ramp.elements]
  nodes.append(d)
 return {'name':nt.name,'nodes':nodes,'links':[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in nt.links]}
def snapshot(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));out={};raw={}
 for ob in bpy.context.scene.objects:
  if ob.type!='MESH':continue
  me=ob.data;co=arr(me.vertices,'co',3).reshape(-1,3);kn=[];ks=None
  if me.shape_keys:kn=[k.name for k in me.shape_keys.key_blocks];ks=np.array([arr(k.data,'co',3).reshape(-1,3) for k in me.shape_keys.key_blocks])
  if ob.name.startswith('V28G_Iris_') or ob.name=='MIA_V27_SharedHeadBody':raw[ob.name]={'coordinates':ks,'UVMap':arr(me.uv_layers['UVMap'].data,'uv',2).reshape(-1,2) if me.uv_layers else None,'loop_vertex_indices':np.array([li.vertex_index for li in me.loops]),'polygons':[list(f.vertices) for f in me.polygons]}
  dr=[]
  if me.shape_keys and me.shape_keys.animation_data:
   for f in me.shape_keys.animation_data.drivers:dr.append({'data_path':f.data_path,'type':f.driver.type,'expression':f.driver.expression,'variables':[(v.name,v.type,[(t.id.name if t.id else None,t.data_path) for t in v.targets]) for v in f.driver.variables]})
  mods=[]
  for m in ob.modifiers:
   md={'name':m.name,'type':m.type}
   for p in ['object','vertex_group','show_viewport','show_render','levels','render_levels','thickness','offset']:
    if hasattr(m,p):v=getattr(m,p);md[p]=v.name if hasattr(v,'name') else value(v)
   mods.append(md)
  out[ob.name]={'coordinates':digest(co.tobytes()+(ks.tobytes() if ks is not None else b'')),'topology':jhash([(list(f.vertices),f.material_index,f.use_smooth) for f in me.polygons]),'UV':{u.name:digest(arr(u.data,'uv',2).tobytes()) for u in me.uv_layers},'weights':jhash([[(ob.vertex_groups[g.group].name,float(g.weight)) for g in v.groups] for v in me.vertices]),'key_names':kn,'drivers':dr,'modifiers':mods,'materials':[(s.name,s.link) for s in ob.material_slots],'matrix':[list(r) for r in ob.matrix_world]}
 mats={m.name:jhash(graph(m.node_tree)) for m in bpy.data.materials};images={im.name:{'colorspace':im.colorspace_settings.name,'size':list(im.size),'packed':digest(im.packed_file.data) if im.packed_file else None} for im in bpy.data.images}
 return out,raw,mats,images
ao,ar,am,ai=snapshot(A);co,cr,cm,ci=snapshot(C);iris={'V28G_Iris_-1','V28G_Iris_1'};checks={'same_scene_mesh_owner_names':set(ao)==set(co),'all_noniris_objects_exact_all_recorded_fields':all(ao[n]==co[n] for n in ao if n not in iris),'all_material_graphs_exact':am==cm,'all_packed_images_and_colorspaces_exact':ai==ci,'A_skin_all42_exact':np.array_equal(ar['MIA_V27_SharedHeadBody']['coordinates'],cr['MIA_V27_SharedHeadBody']['coordinates'])};details=[]
for name in sorted(iris):
 s=name.rsplit('_',1)[1];prefix='iris_'+s;ids=remap[prefix+'_source_triangles'];bc=remap[prefix+'_source_barycentric'];faces=remap[prefix+'_faces'];uv=remap[prefix+'_UV'];expected=np.einsum('kvij,vi->kvj',ar[name]['coordinates'][:,ids],bc);actual=cr[name]['coordinates'];err=float(np.max(np.linalg.norm(actual-expected,axis=2))*1000);uvexpected=uv[cr[name]['loop_vertex_indices']];uverr=float(np.max(np.linalg.norm(cr[name]['UVMap']-uvexpected,axis=1)))
 q=actual[:,faces];cross=np.cross(q[:,:,1]-q[:,:,0],q[:,:,2]-q[:,:,0]);area=np.linalg.norm(cross,axis=2)/2;srcq=ar[name]['coordinates'][:,ids];# Per-output-face expected normal lies on its mapped source-triangle plane.
 eq=expected[:,faces];ecross=np.cross(eq[:,:,1]-eq[:,:,0],eq[:,:,2]-eq[:,:,0]);dot=np.sum(cross*ecross,axis=2)
 counts=collections.Counter(tuple(sorted((a,b))) for f in faces for a,b in zip(f,np.roll(f,-1)));be=[e for e,n in counts.items() if n==1];deg=collections.Counter(i for e in be for i in e)
 boundary=np.unique(np.array(be));radii=np.sqrt(((uv[boundary,0]*2%1-.5)/.29352959990501404)**2+((uv[boundary,1]-.5)/.22200000286102295)**2)
 # Compare sampled triangle interiors in actual UV domain, independently of
 # new-vertex mapping. This bounds the internal quality-edge-flip difference.
 oldtri=np.array(ar[name]['polygons']);olduv=ar[name]['UVMap'].reshape(-1,3,2);uvverts=np.c_[olduv.reshape(-1,2),np.zeros(olduv.size//2)];uvbv=BVHTree.FromPolygons([Vector(p) for p in uvverts],np.arange(len(uvverts)).reshape(-1,3).tolist(),all_triangles=True);samples=np.array([[1,0,0],[0,1,0],[0,0,1],[.5,.5,0],[0,.5,.5],[.5,0,.5],[1/3,1/3,1/3]]);surfaceerr=0.;tested=0;missing=0
 for ff in faces:
  for bb in samples:
   targetuv=bb@uv[ff];rr=((targetuv[0]*2%1-.5)/.29352959990501404)**2+((targetuv[1]-.5)/.22200000286102295)**2
   if rr>1+1e-8:continue
   hit,_,idx,_=uvbv.ray_cast(Vector((targetuv[0],targetuv[1],1)),Vector((0,0,-1)))
   if hit is None:missing+=1;continue
   uu=olduv[idx];uvbc=np.linalg.solve(np.stack([uu[1]-uu[0],uu[2]-uu[0]],1),targetuv-uu[0]);uvbc=np.r_[1-uvbc.sum(),uvbc];oldsurface=np.einsum('kij,i->kj',ar[name]['coordinates'][:,oldtri[idx]],uvbc);newsurface=np.einsum('kij,i->kj',actual[:,ff],bb);surfaceerr=max(surfaceerr,float(np.linalg.norm(oldsurface-newsurface,axis=1).max()));tested+=1
 uvcross=np.cross(uv[faces[:,1]]-uv[faces[:,0]],uv[faces[:,2]]-uv[faces[:,0]]);oldcross=np.cross(olduv[:,1]-olduv[:,0],olduv[:,2]-olduv[:,0]);uvwindok=bool((uvcross*np.median(oldcross)>0).all())
 ob=bpy.data.objects[name];weightsok=all(len(v.groups)==1 and ob.vertex_groups[v.groups[0].group].name=='J_Bip_C_Head' and v.groups[0].weight==1 for v in ob.data.vertices)
 d={'owner':name,'new_vertices':len(actual[0]),'faces':len(faces),'weights_nonnegative':bool((bc>=-1e-10).all()),'weights_sum1_maxerror':float(abs(bc.sum(1)-1).max()),'fresh_all42_barycentric_coordinate_maxerror_mm':err,'fresh_UV_source_remap_maxerror':uverr,'fresh_all42_UVsampled_opaque_surface_maxerror_mm':surfaceerr*1000,'opaque_surface_UV_samples_each_key':tested,'opaque_UV_query_misses':missing,'UV_winding_matches_source_A':uvwindok,'all42_finite':bool(np.isfinite(actual).all()),'minimum_all42_triangle_area_mm2':float(area.min()*1e6),'zero_area_count':int((area==0).sum()),'tiny_area_below_1e_minus12_m2_count':int((area<1e-12).sum()),'winding_dot_positive_count':int((dot>0).sum()),'winding_total_count':int(dot.size),'boundary_degrees_all2':all(v==2 for v in deg.values()),'boundary_vertex_count':len(boundary),'boundary_normalized_alpha_radius_range':[float(radii.min()),float(radii.max())],'actual_new_named_Head_weights_all1':weightsok,'keynames_drivers_modifiers_materials_exact':all(ao[name][f]==co[name][f] for f in ['key_names','drivers','modifiers','materials','matrix'])}
 details.append(d);checks[name+'_remap_valid']=d['weights_nonnegative'] and d['weights_sum1_maxerror']<1e-8 and err<.0003 and uverr<1e-7 and surfaceerr<.0000003 and missing==0 and uvwindok and d['all42_finite'] and d['zero_area_count']==0 and d['tiny_area_below_1e_minus12_m2_count']==0 and bool((dot>0).all()) and d['boundary_degrees_all2'] and weightsok and d['keynames_drivers_modifiers_materials_exact']
out={'source_A_sha256':digest(A.read_bytes()),'candidate_native':str(C),'candidate_sha256':digest(C.read_bytes()),'checks':checks,'all_computed_checks_pass':all(checks.values()),'local_topology_exception_only':sorted(iris),'iris_mapping_details':details,'BodyL_preservation':'A skin all42 exact here; A vsf0dead BodyL originalprefix exact independently in medial-A-fresh-preservation.json.','limits':'Opaque source geometry preserved by independent saved-coordinate remap within serialization precision; actual rendered glint/gaze/edge also required.'};(O/('medial-'+V+'-fresh-remap-preservation.json')).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2));assert out['all_computed_checks_pass']
