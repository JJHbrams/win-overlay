"""C: retain A modeled skin; remove invisible alpha-zero iris carrier exterior.
Every new vertex is mapped barycentrically to an A triangle for all42 keys.
UV ellipse is circumscribed, so no opaque source surface is cut away.
"""
import bpy,numpy as np,json,hashlib,math,sys
from pathlib import Path
O=Path(__file__).parent;args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];V=args[0] if args else 'C';phase=float(args[1]) if len(args)>1 else 0;src=O/'Mia_EyeLash_v29_A.blend';bpy.ops.wm.open_mainfile(filepath=str(src));master=bpy.data.objects['MIA_V27_Foundation_Face'];names=[k.name for k in master.data.shape_keys.key_blocks];skin=bpy.data.objects['MIA_V27_SharedHeadBody'];skinbefore=np.array([[v.co[:] for v in k.data] for k in skin.data.shape_keys.key_blocks]);payload={};audit=[]
N=256;r=1/math.cos(math.pi/N);theta=(np.arange(N)+phase)*2*math.pi/N;poly=np.stack([np.cos(theta),np.sin(theta)],1)*r
for side in [-1,1]:
 ob=bpy.data.objects['V28G_Iris_'+str(side)];me=ob.data;me.calc_loop_triangles();old=np.array([[v.co[:] for v in k.data] for k in me.shape_keys.key_blocks]);materials=list(me.materials);points=[];faces=[];uvpoints=[];source_ids=[];source_weights=[];lookup={};uc=.25 if side<0 else .75
 for t in me.loop_triangles:
  ids=np.array(t.vertices);uv=np.array([me.uv_layers['UVMap'].data[j].uv[:] for j in t.loops]);q=(uv-np.array([uc,.5]))/np.array([.29352959990501404/2,.22200000286102295]);clipped=[(q[i],np.eye(3)[i]) for i in range(3)]
  for a,b in zip(poly,np.roll(poly,-1,axis=0)):
   if not clipped:break
   edge=b-a;out=[]
   def signed(p):return edge[0]*(p[1]-a[1])-edge[1]*(p[0]-a[0])
   prev=clipped[-1];dp=signed(prev[0])
   for cur in clipped:
    dc=signed(cur[0]);ip=dp>=-1e-12;ic=dc>=-1e-12
    if ip!=ic:
     f=dp/(dp-dc);out.append((prev[0]+f*(cur[0]-prev[0]),prev[1]+f*(cur[1]-prev[1])))
    if ic:out.append(cur)
    prev=cur;dp=dc
   clipped=out
  if len(clipped)<3:continue
  fi=[]
  for q,bc in clipped:
   uvnew=q*np.array([.29352959990501404/2,.22200000286102295])+[uc,.5];p=bc@old[0,ids];key=tuple(np.round(uvnew,10))
   if key not in lookup:
    lookup[key]=len(points);points.append(p);uvpoints.append(uvnew);source_ids.append(ids);source_weights.append(bc)
   else:assert np.linalg.norm(np.array(points[lookup[key]])-p)<1e-6
   fi.append(lookup[key])
  fans=[]
  for anchor in (range(len(fi)) if V!='C' else [0]):
   rot=fi[anchor:]+fi[:anchor];ff=[[rot[0],rot[j],rot[j+1]] for j in range(1,len(rot)-1) if len({rot[0],rot[j],rot[j+1]})==3]
   pp=np.array(points)[np.array(ff)];quality=float((np.linalg.norm(np.cross(pp[:,1]-pp[:,0],pp[:,2]-pp[:,0]),axis=1)/2).min()) if ff else 0
   fans.append((quality,ff))
  faces.extend(max(fans,key=lambda x:x[0])[1])
 ids=np.array(source_ids);weights=np.array(source_weights);new=np.einsum('kvij,vi->kvj',old[:,ids],weights);cleanup=[]
 def faceareas(ff):
  pp=new[:,np.array(ff)];return np.linalg.norm(np.cross(pp[:,:,1]-pp[:,:,0],pp[:,:,2]-pp[:,:,0]),axis=2)/2
 if V!='C':
  for _ in range(12):
   areas=faceareas(faces).min(0);bad=int(np.argmin(areas))
   if areas[bad]>=1e-12:break
   adj={}
   for fi,ff in enumerate(faces):
    for a,b in zip(ff,ff[1:]+ff[:1]):adj.setdefault(tuple(sorted((a,b))),[]).append(fi)
   best=None;f=faces[bad]
   for j in range(3):
    a,b,c=f[j],f[(j+1)%3],f[(j+2)%3];other=next((i for i in adj[tuple(sorted((a,b)))] if i!=bad),None)
    if other is None:continue
    d=next(i for i in faces[other] if i not in [a,b])
    if tuple(sorted((c,d))) in adj:continue
    proposal=[[c,a,d],[c,d,b]];uvv=np.array(uvpoints);pp=uvv[np.array(proposal)];z=np.cross(pp[:,1]-pp[:,0],pp[:,2]-pp[:,0]);oldp=uvv[np.array([f,faces[other]])];oz=np.cross(oldp[:,1]-oldp[:,0],oldp[:,2]-oldp[:,0])
    if not ((z*oz[0]>0).all() and oz[0]*oz[1]>0):continue
    quality=float(faceareas(proposal).min())
    if best is None or quality>best[0]:best=(quality,other,proposal,[a,b],[c,d])
   assert best is not None and best[0]>areas[bad],('unrepairable sliver',bad,float(areas[bad]))
   quality,other,proposal,oldedge,newedge=best;cleanup.append({'old_faces':[faces[bad],faces[other]],'new_faces':proposal,'flipped_edge':oldedge,'replacement_edge':newedge,'old_minimum_allkey_area_m2':float(min(areas[bad],areas[other])),'new_minimum_allkey_area_m2':quality});faces[bad],faces[other]=proposal
 minimum_area=float(faceareas(faces).min());print('CLIP_MIN_AREA',V,side,phase,minimum_area,'FLIPS',len(cleanup),flush=True)
 if V!='C':assert minimum_area>=1e-12,('clip sliver',side,phase,minimum_area)
 mesh=bpy.data.meshes.new('V29_Iris_AlphaBounded_'+str(side));mesh.from_pydata(new[0],[],faces)
 for m in materials:mesh.materials.append(m)
 uv=mesh.uv_layers.new(name='UVMap')
 for f in mesh.polygons:
  f.use_smooth=True
  for li,vi in zip(f.loop_indices,f.vertices):uv.data[li].uv=uvpoints[vi]
 ob.data=mesh;ob.vertex_groups.clear();vg=ob.vertex_groups.new(name='J_Bip_C_Head');vg.add(list(range(len(new[0]))),1,'REPLACE')
 for ki,(kn,coords) in enumerate(zip(names,new)):
  key=ob.shape_key_add(name=kn,from_mix=False)
  for v,p in zip(key.data,coords):v.co=p
  if ki:
   d=key.driver_add('value').driver;d.type='AVERAGE';v=d.variables.new();v.name='face_key';v.type='SINGLE_PROP';v.targets[0].id_type='KEY';v.targets[0].id=master.data.shape_keys;v.targets[0].data_path='key_blocks['+json.dumps(kn)+'].value'
 prefix='iris_'+str(side);payload[prefix+'_source_triangles']=ids;payload[prefix+'_source_barycentric']=weights;payload[prefix+'_faces']=np.array(faces);payload[prefix+'_UV']=np.array(uvpoints)
 audit.append({'owner':ob.name,'source_vertices':len(old[0]),'new_vertices':len(new[0]),'new_faces':len(faces),'same_all42_key_names':True,'allkey_source_triangle_mapping_max_error_mm':float(np.linalg.norm(new-np.einsum('kvij,vi->kvj',old[:,ids],weights),axis=2).max()*1000),'minimum_all42_triangle_area_m2':minimum_area,'quality_internal_edge_flips':cleanup,'opaque_alpha_surface_preserved':str(N)+'-plane UV polygon circumscribes actual radial alpha ellipse. All retained vertices map to A for all42; internal-edge cleanup changes no boundary/UV/vertices. Fresh UV-sampled surface comparison is required for flipped interpolation.','clip_polygon_sides':N,'clip_polygon_phase_steps':phase,'UV_ellipse_center':[uc,.5],'UV_ellipse_radii':[.29352959990501404/2,.22200000286102295],'circumscribed_normalized_radius':r,'named_weights':'J_Bip_C_Head=1','original_armature_modifier_retained':any(m.type=='ARMATURE' for m in ob.modifiers)})
for k in master.data.shape_keys.key_blocks:k.value=0
bpy.context.view_layer.update();assert np.array_equal(skinbefore,np.array([[v.co[:] for v in k.data] for k in skin.data.shape_keys.key_blocks]));np.savez_compressed(O/('medial-'+V+'-iris-topology-remap.npz'),**payload);dest=O/('Mia_EyeLash_v29_'+V+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(dest));(O/('medial-'+V+'-iris-remap-audit.json')).write_text(json.dumps({'input_native':str(src),'input_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'output_native':str(dest),'output_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'A_skin_all42_exact':True,'A_walls_and_white_cap_untouched':True,'materials_and_FaceUV_layout_untouched':True,'only_two_iris_carrier_topologies_changed':True,'owners':audit,'reason':'Actual NOiris isolates remove dark fringe; alpha-aware pixel rays locate invisible exterior iris sheet nearly coplanar with skin/wall. Remove non-visible carrier exterior rather than hide artifact with lashes or deform corrected skin. B posterior-tuck probe retained but not adopted.','limits':'Actual macro/closure/critical-angle validation still required; construction mapping is not art approval.'},indent=2));print('IRIS_TRIM_SAVED',V)
