"""V22 whole anterior-thorax reconstruction. New continuous triangulated patch, not breast radial cages."""
import bpy,sys,json,hashlib,math,struct
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt
from mathutils.bvhtree import BVHTree
OUT=Path(__file__).parent;SRC=Path(r'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-correction-v20/integrated-r2/Mia_Corrected_v20.blend')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();source_sha=sha(SRC);assert source_sha=='c02b8ad73b86b278f2768e61eff019be223a8828bd92df62ce0ab7cb60f56936'
bpy.ops.wm.open_mainfile(filepath=str(SRC),use_scripts=False);body=bpy.data.objects['MIA_V06_BODY_SKIN'];old=body.data;old.calc_loop_triangles();world=body.matrix_world.copy();inv=world.inverted();pts=np.array([list(world@v.co) for v in old.vertices]);faces=[list(f.vertices) for f in old.polygons]
# Source archive is a retained native mesh datablock; all unrelated owners stay untouched.
def other_sig():
 out={}
 for o in bpy.data.objects:
  if o.type=='MESH' and o!=body:
   m=o.data;blob=b''.join(struct.pack('<3f',*v.co) for v in m.vertices)+b''.join(struct.pack('<I',i) for f in m.polygons for i in f.vertices)+b''.join(struct.pack('<2f',*v.uv) for uv in m.uv_layers for v in uv.data)
   if m.shape_keys:blob+=b''.join(struct.pack('<3f',*v.co) for k in m.shape_keys.key_blocks for v in k.data)
   out[o.name]=hashlib.sha256(blob).hexdigest()
 return out
protected=other_sig();images={i.name:hashlib.sha256(bytes(i.packed_file.data)).hexdigest() if i.packed_file else None for i in bpy.data.images};materials=set(m.name for m in bpy.data.materials)
for m in bpy.data.materials:m.use_fake_user=True
for im in bpy.data.images:im.use_fake_user=True
old.use_fake_user=True
sel=(pts[:,2]>1.18)&(pts[:,2]<1.395)&(abs(pts[:,0])<.14)&(pts[:,1]<.005);patchids=[f.index for f in old.polygons if all(sel[i] for i in f.vertices)];# Preserve one original coarse face collar around the replacement. This
# prevents dense new faces from directly changing the source clavicle limit surface.
patchset=set(patchids)
source_ec=Counter(tuple(sorted((faces[i][k],faces[i][(k+1)%len(faces[i])]))) for i in patchids for k in range(len(faces[i])))
source_bd={e for e,c in source_ec.items() if c==1}
patchids=[i for i in patchids if not any(tuple(sorted((faces[i][k],faces[i][(k+1)%len(faces[i])]))) in source_bd for k in range(len(faces[i])))]
ef=defaultdict(list)
for i in patchids:
 for k in range(len(faces[i])):ef[tuple(sorted((faces[i][k],faces[i][(k+1)%len(faces[i])])))].append(i)
fa=defaultdict(set)
for ids in ef.values():
 for i in ids:fa[i].update(ids)
seen=set();components=[]
for i in patchids:
 if i in seen:continue
 todo=[i];comp=set()
 while todo:
  k=todo.pop()
  if k in comp:continue
  comp.add(k);todo.extend(fa[k]-comp)
 seen|=comp;components.append(comp)
patchids=sorted(max(components,key=len));patchset=set(patchids);pf=[faces[i] for i in patchids]
ed=Counter(tuple(sorted((f[k],f[(k+1)%len(f)]))) for f in pf for k in range(len(f)));bd=[e for e,c in ed.items() if c==1];adj=defaultdict(set)
for a,b in bd:adj[a].add(b);adj[b].add(a)
assert all(len(a)==2 for a in adj.values());start=min(adj);boundary=[start];prev=-1;cur=start
while True:
 nxt=next(i for i in adj[cur] if i!=prev)
 if nxt==start:break
 boundary.append(nxt);prev,cur=cur,nxt
assert len(boundary)==len(bd)
N=len(boundary)
param=np.column_stack((.1*np.arctan2(pts[:,0]+.00047769,-pts[:,1]),pts[:,2]));poly=param[boundary]
area=sum(poly[k,0]*poly[(k+1)%len(poly),1]-poly[(k+1)%len(poly),0]*poly[k,1] for k in range(len(poly)))
if area<0:boundary.reverse();poly=param[boundary]
def inside(x,z):
 yes=False
 for a,b in zip(poly,np.roll(poly,-1,axis=0)):
  if (a[1]>z)!=(b[1]>z) and x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0]:yes=not yes
 return yes
def boundary_distance(x,z):
 q=np.array([x,z]);best=1.
 for a,b in zip(poly,np.roll(poly,-1,axis=0)):
  d=b-a;t=np.clip(np.dot(q-a,d)/np.dot(d,d),0,1);best=min(best,float(np.linalg.norm(q-a-t*d)))
 return best
# Uniform patch domain replaces both radial poles and closed return bands.
input2=[Vector(q) for q in param[boundary]]
for z in np.arange(1.184,1.393,.0085):
 for x in np.arange(-.166,.168,.0085):
  if inside(x,z) and boundary_distance(x,z)>.009:input2.append(Vector((x,z)))
constraints=[(k,(k+1)%N) for k in range(N)]
cv,ce,cf,origv,orige,origf=delaunay_2d_cdt(input2,constraints,[list(range(N))],1,1e-8,True)
# Join well-shaped adjacent CDT triangles into a regular quad-dominant net.
# Boundary constraints/vertices are unchanged; no shape smoothing is applied.
edge_faces=defaultdict(list)
for fi,f in enumerate(cf):
 for k in range(len(f)):edge_faces[tuple(sorted((f[k],f[(k+1)%len(f)])))].append(fi)
options=[]
for edge,fs in edge_faces.items():
 if len(fs)!=2:continue
 a,b=fs;count=Counter(tuple(sorted((f[k],f[(k+1)%len(f)]))) for f in [cf[a],cf[b]] for k in range(len(f)));outer=[e for e,c in count.items() if c==1];qa=defaultdict(set)
 for i,j in outer:qa[i].add(j);qa[j].add(i)
 if len(qa)!=4 or any(len(v)!=2 for v in qa.values()):continue
 order=[next(iter(qa))];prev=-1;cur=order[0]
 for _ in range(3):
  nxt=next(i for i in qa[cur] if i!=prev);order.append(nxt);prev,cur=cur,nxt
 q=np.array([list(cv[i]) for i in order]);area=sum(np.cross(q[(k+1)%4]-q[k],q[(k+2)%4]-q[(k+1)%4]) for k in range(4))
 if area<0:order.reverse();q=q[::-1]
 angles=[];convex=True
 for k in range(4):
  v=q[(k-1)%4]-q[k];w=q[(k+1)%4]-q[k];ang=math.degrees(math.acos(float(np.clip(np.dot(v,w)/np.linalg.norm(v)/np.linalg.norm(w),-1,1))));angles.append(ang)
  if np.cross(-v,w)<=0:convex=False
 if convex and min(angles)>48 and max(angles)<132:options.append((sum(abs(x-90) for x in angles),a,b,order))
used=set();joined=[]
for score,a,b,order in sorted(options):
 if a not in used and b not in used:used.update([a,b]);joined.append(order)
cf=joined+[f for i,f in enumerate(cf) if i not in used]
print('QUAD_NET',len(joined),'remaining_triangles',sum(len(f)==3 for f in cf))
def pchip(x,y,t,zero_start=False):
 h=np.diff(x);d=np.diff(y,axis=0)/h[:,None] if y.ndim>1 else np.diff(y)/h
 m=np.zeros_like(y);m[0]=0 if zero_start else d[0];m[-1]=d[-1]
 for k in range(1,len(x)-1):
  a,b=d[k-1],d[k];same=(a*b)>0;w1=2*h[k]+h[k-1];w2=h[k]+2*h[k-1]
  if y.ndim>1:
   m[k][same]=(w1+w2)/(w1/a[same]+w2/b[same])
  elif same:m[k]=(w1+w2)/(w1/a+w2/b)
 k=max(0,min(len(x)-2,int(np.searchsorted(x,t)-1)));u=float(np.clip((t-x[k])/h[k],0,1));return (2*u**3-3*u*u+1)*y[k]+(u**3-2*u*u+u)*h[k]*m[k]+(-2*u**3+3*u*u)*y[k+1]+(u**3-u*u)*h[k]*m[k+1]
def loft(u,z):
 # One smooth thorax height field. Source sternum measured at z1.18/1.36/1.38
 # anchors the base; source profile guides peak at1.285 rather than c2's1.25.
 levels=np.array([1.18,1.22,1.26,1.30,1.34,1.36,1.38,1.395])
 anterior=np.array([.117,.111,.106,.100,.094,.0867,.0707,.054])
 lateral=np.array([.119,.122,.129,.137,.148,.155,.159,.160])
 theta=u/.1;x=float(pchip(levels,lateral,z))*math.sin(theta)
 base=float(pchip(levels,anterior,z))*math.cos(theta)
 dz=z-1.285;h=.040+.014*math.tanh(dz/.024)
 # Smooth asymmetric round fullness; no closed rim or explicit underfold curve.
 fullness=.051*math.exp(-.5*(dz/h)**2)*(math.exp(-.5*((x-.061)/.032)**2)+math.exp(-.5*((x+.061)/.032)**2))
 return np.array([-.00047769+x,-base-fullness,z])
tris=[t for t in old.loop_triangles];vtri=np.array([[pts[i] for i in t.vertices] for t in tris]);patchtris=[k for k,t in enumerate(tris) if t.polygon_index in patchset];bvh=BVHTree.FromPolygons([Vector(q) for q in pts],[list(t.vertices) for t in tris],all_triangles=True)
def bary(q,a,b,c):
 v0=b-a;v1=c-a;v2=q-a;d00=np.dot(v0,v0);d01=np.dot(v0,v1);d11=np.dot(v1,v1);den=d00*d11-d01*d01
 if abs(den)<1e-15:return np.array([1.,0,0])
 v=(d11*np.dot(v2,v0)-d01*np.dot(v2,v1))/den;w=(d00*np.dot(v2,v1)-d01*np.dot(v2,v0))/den;return np.array([1-v-w,v,w])
def old_position(u,z):
 for k in patchtris:
  q=param[list(tris[k].vertices)];b=bary(np.array([u,z]),q[0],q[1],q[2])
  if min(b)>-1e-6:return b@vtri[k]
 loc,normal,k,dist=bvh.find_nearest(Vector(loft(u,z)));return np.array(loc)
allpatchverts=set(i for f in pf for i in f);removed=allpatchverts-set(boundary);kept=[i for i in range(len(pts)) if i not in removed];old2new={i:n for n,i in enumerate(kept)}
# Fit a smooth residual surface to exact boundary plus an exterior source ring.
# This replaces local old-triangle blending, which preserved unwanted ring dents.
outer_neighbors=set()
for edge in old.edges:
 a,b=edge.vertices
 if a in boundary and b not in allpatchverts:outer_neighbors.add(b)
 if b in boundary and a not in allpatchverts:outer_neighbors.add(a)
fit_ids=boundary+sorted(i for i in outer_neighbors if pts[i,1]<.01 and 1.16<pts[i,2]<1.43)
fitq=[param[i].copy() for i in fit_ids]
fitval=[pts[i]-loft(*param[i]) for i in fit_ids]
for q in cv:
 u,z=float(q.x),float(q.y)
 if boundary_distance(u,z)>.038:
  fitq.append(np.array([u,z]));fitval.append(np.zeros(3))
fitq=np.array(fitq);fitval=np.array(fitval);scaled=fitq/.1
r=np.linalg.norm(scaled[:,None,:]-scaled[None,:,:],axis=2)
K=r*r*np.log(np.maximum(r,1e-12));pol=np.column_stack((np.ones(len(scaled)),scaled))
A=np.block([[K+np.eye(len(K))*1e-9,pol],[pol.T,np.zeros((3,3))]])
coef=np.linalg.solve(A,np.vstack((fitval,np.zeros((3,3)))))
def residual(u,z):
 q=np.array([u,z])/.1;r=np.linalg.norm(scaled-q,axis=1)
 return (r*r*np.log(np.maximum(r,1e-12)))@coef[:-3]+np.array([1,*q])@coef[-3:]
(OUT/'boundary-residual-controls.json').write_text(json.dumps({'source_ids':fit_ids,'parameters':fitq.tolist(),'residuals':fitval.tolist(),'kernel':'thin plate r^2 log r with affine term','purpose':'continuous original boundary and incoming exterior collar derivative; zero interior correction anchors; not art acceptance'},indent=2))
newworld=[pts[i].copy() for i in kept];cdt2new={};transfer={};new_records=[]
for k,q in enumerate(cv):
 ids=[i for i in origv[k] if i<N]
 if ids:
  assert len(ids)==1;cdt2new[k]=old2new[boundary[ids[0]]];continue
 u,z=float(q.x),float(q.y);target=loft(u,z)+residual(u,z);w=1.
 ni=len(newworld);newworld.append(target);cdt2new[k]=ni
 loc,normal,ti,dd=bvh.find_nearest(Vector(target));weights=bary(np.array(loc),*vtri[ti]);transfer[ni]=(ti,weights)
 new_records.append({'new_vertex':ni,'target_world':target.tolist(),'boundary_blend':w,'source_triangle':ti,'barycentric':weights.tolist()})
assert len({cdt2new[k] for k in range(len(cv)) if any(i<N for i in origv[k])})==N
outside=[i for i in range(len(faces)) if i not in patchset];newfaces=[[old2new[v] for v in faces[i]] for i in outside]+[[cdt2new[i] for i in f] for f in cf]
mesh=bpy.data.meshes.new('MIA_V22_ContinuousThorax_PATCH1');mesh.from_pydata([list(inv@Vector(q)) for q in newworld],[],newfaces);mesh.update()
for mat in old.materials:mesh.materials.append(mat)
for f in mesh.polygons:f.use_smooth=True
for k,pi in enumerate(outside):
 mesh.polygons[k].material_index=old.polygons[pi].material_index
 mesh.polygons[k].use_smooth=old.polygons[pi].use_smooth
for f in mesh.polygons[len(outside):]:
 loc,n,ti,dd=bvh.find_nearest(world@f.center);f.material_index=old.polygons[tris[ti].polygon_index].material_index
for uv in old.uv_layers:
 layer=mesh.uv_layers.new(name=uv.name)
 for k,pi in enumerate(outside):
  for a,b in zip(mesh.polygons[k].loop_indices,old.polygons[pi].loop_indices):layer.data[a].uv=uv.data[b].uv
 for f in mesh.polygons[len(outside):]:
  for li in f.loop_indices:
   ni=mesh.loops[li].vertex_index
   if ni in transfer:ti,w=transfer[ni]
   else:
    loc,n,ti,dd=bvh.find_nearest(Vector(newworld[ni]));w=bary(np.array(loc),*vtri[ti])
   vals=np.array([list(uv.data[i].uv) for i in tris[ti].loops]);layer.data[li].uv=w@vals
# Keep source group names, copy untouched weights exactly, barycentrically transfer patch.
oldweights=[[(g.group,g.weight) for g in v.groups] for v in old.vertices];groupnames=[g.name for g in body.vertex_groups];body.data=mesh
if not len(body.vertex_groups):
 for name in groupnames:body.vertex_groups.new(name=name)
assert [g.name for g in body.vertex_groups]==groupnames
mesh.uv_layers.active_index=old.uv_layers.active_index
for oi,ni in old2new.items():
 for group,weight in oldweights[oi]:body.vertex_groups[group].add([ni],weight,'REPLACE')
for ni,(ti,w) in transfer.items():
 weights=defaultdict(float)
 for oi,ww in zip(tris[ti].vertices,w):
  for group,value in oldweights[oi]:weights[group]+=float(ww)*value
 total=sum(max(0,v) for v in weights.values())
 # Some groups are masks, not deform groups: preserve interpolation without normalization.
 for group,weight in weights.items():
  if weight>1e-8:body.vertex_groups[group].add([ni],max(0,min(1,weight)),'REPLACE')
# Exact outside geometry/UV/weights and shared seam topology are independently checked.
for oi,ni in old2new.items():assert np.linalg.norm(np.array(world@mesh.vertices[ni].co)-pts[oi])<2e-7
edgecounts=Counter(tuple(sorted((f[k],f[(k+1)%len(f)]))) for f in newfaces for k in range(len(f)))
badseams=[{'edge':[a,b],'incidence':edgecounts[tuple(sorted((old2new[a],old2new[b])))],'world':[pts[a].tolist(),pts[b].tolist()]} for a,b in bd if edgecounts[tuple(sorted((old2new[a],old2new[b])))]!=2]
print('SEAM_DIAGNOSTIC',json.dumps({'input_count':len(input2),'cdt_count':len(cv),'new_intersections':[list(q) for k,q in enumerate(cv) if not origv[k]],'badseams':badseams}))
assert not badseams
orig_boundary=sum(c==1 for c in Counter(tuple(sorted((f[k],f[(k+1)%len(f)]))) for f in faces for k in range(len(f))).values());new_boundary=sum(c==1 for c in edgecounts.values());assert orig_boundary==new_boundary,(orig_boundary,new_boundary)
assert protected==other_sig();body['V22_patch_provenance']='Continuous anterior thorax patch; original mesh datablock retained; topology and interpolated UV/weights are derived, no art acceptance.'
DST=OUT/'Mia_BodyContinuous_v22_candidate4.blend';bpy.ops.wm.save_as_mainfile(filepath=str(DST));bpy.ops.wm.open_mainfile(filepath=str(DST),use_scripts=False);body=bpy.data.objects['MIA_V06_BODY_SKIN'];assert protected==other_sig();assert set(m.name for m in bpy.data.materials)==materials;assert images=={i.name:hashlib.sha256(bytes(i.packed_file.data)).hexdigest() if i.packed_file else None for i in bpy.data.images};assert sha(SRC)==source_sha
(OUT/'patch-provenance.json').write_text(json.dumps({'source':str(SRC),'source_sha256':source_sha,'native_sha256':sha(DST),'original_mesh_archive':old.name if False else 'source body mesh retained with fake user','removed_source_faces':patchids,'removed_source_vertices':sorted(removed),'boundary_source_ids':boundary,'source_to_new_preserved_vertices':old2new,'new_patch_vertices':new_records,'new_patch_faces':len(cf),'source_boundary_edge_count':orig_boundary,'candidate_boundary_edge_count':new_boundary,'seam_edges_checked':N,'all_seam_edges_incidence2':True,'nonbody_signatures':protected,'protected_head_world_z_min':1.46,'uv_weight_transfer':'nearest source control triangle barycentric; approximate on reconstructed patch, exact outside','integration':'Replace body data and transferred vertex weights; all other object owners stay c02. Above1.46 source IDs remapped in source_to_new_preserved_vertices, positions exact. Keep source archive. UV deformation review still required.'},indent=2))
(OUT/'surface-control-net.json').write_text(json.dumps({'construction': 'Continuous thorax height field plus thin-plate boundary residual; old angular loft net unused and removed from this recipe.', 'source_base_z': [1.18, 1.22, 1.26, 1.3, 1.34, 1.36, 1.38, 1.395], 'anterior_radius': [0.117, 0.111, 0.106, 0.1, 0.094, 0.0867, 0.0707, 0.054], 'lateral_radius': [0.119, 0.122, 0.129, 0.137, 0.148, 0.155, 0.159, 0.16], 'fullness': {'centres_x': [-0.061, 0.061], 'centre_z': 1.285, 'depth': 0.051, 'sigma_x': 0.032, 'sigma_z_formula': '.040 + .014*tanh((z-1.285)/.024)'}, 'boundary_residual': 'boundary-residual-controls.json', 'parameter_basis': 'artist-authored approximation informed by actual source comparisons and measured source sternum, not a calibrated anatomical measurement', 'topology': '365 quads + 98 triangles, shared unchanged source boundary; retained old IDs exact'},indent=2));print('CONTINUOUS_NATIVE',sha(DST),'VERTICES',len(mesh.vertices) if False else len(newworld),'PATCH_FACES',len(cf))
