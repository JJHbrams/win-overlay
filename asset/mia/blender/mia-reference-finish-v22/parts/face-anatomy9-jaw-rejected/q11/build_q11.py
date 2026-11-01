"""One bounded C2 circumferential X-only lower-jaw carrier, no depth fit."""
import bpy,numpy as np,json,hashlib
from pathlib import Path
from collections import Counter,defaultdict
P=Path(__file__).parent;SRC=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v22/integration-wip-9-review/Mia_FaceReview_v22_WIP9.blend');SHA='fb85468a623e1befc590176a24636548b944491ce4ae19decaece625304945b2';DST=P/'Mia_JawCarrier_Q11.blend';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(SRC)==SHA;assert not DST.exists()
bpy.ops.wm.open_mainfile(filepath=str(SRC),use_scripts=False);o=bpy.data.objects['MIA_V14_SculptedSkin'];m=o.data;keys=m.shape_keys.key_blocks
for k in keys:k.value=0.
def ah(a):return hashlib.sha256(np.asarray(a,dtype='<f4').tobytes()).hexdigest()
def meshguard():
 return {'uvs':{l.name:ah([v.uv[:] for v in l.data]) for l in m.uv_layers},'topology':[[int(i) for i in p.vertices] for p in m.polygons],'groups':[(g.name,g.index) for g in o.vertex_groups],'weights':[[[g.group,g.weight] for g in v.groups] for v in m.vertices],'other_meshes':{obj.name:ah([v.co[:] for v in obj.data.vertices]) for obj in bpy.data.objects if obj.type=='MESH' and obj!=o},'materials':[s.material.name if s.material else None for s in o.material_slots]}
before=meshguard();old={k.name:np.array([v.co[:] for v in k.data]) for k in keys};a=old['Basis'];x=a[:,0];ax=abs(x);z=a[:,2]
def c2(lo,hi,v):
 t=np.clip((v-lo)/(hi-lo),0,1);return t*t*t*(10+t*(-15+6*t))
def dc2(lo,hi,v):
 t=np.clip((v-lo)/(hi-lo),0,1);return 30*t*t*(1-t)*(1-t)/(hi-lo)
# The Z support ends below the measured lowest lateral/ear points (1.505514m).
low=.0015*c2(1.477,1.480,z)*(1-c2(1.482,1.485,z))
corner=-.0025*c2(1.482,1.489,z)*(1-c2(1.496,1.504,z))
f=low+corner;phi=c2(.0125,.0305,ax);d=np.zeros_like(a);d[:,0]=np.sign(x)*f*phi
# Because y'=y and z'=z, the determinant is exactly dx'/dx. No angular masks.
jac=1+f*dc2(.0125,.0305,ax);analytic_lower=1-.0025*(1.875/(.0305-.0125));assert analytic_lower>0;assert jac.min()>=analytic_lower-1e-12
# Identify actual current mouth and eye boundary loops for evidence only.
counts=Counter(tuple(sorted((p.vertices[j],p.vertices[(j+1)%len(p.vertices)]))) for p in m.polygons for j in range(len(p.vertices)));adj=defaultdict(set)
for (i,j),n in counts.items():
 if n==1:adj[i].add(j);adj[j].add(i)
seen=set();loops=[]
for i in adj:
 if i in seen:continue
 todo=[i];ids=[]
 while todo:
  j=todo.pop()
  if j in seen:continue
  seen.add(j);ids.append(j);todo.extend(adj[j]-seen)
 loops.append(ids)
lip=next(ids for ids in loops if 1.48<a[ids,2].mean()<1.51 and a[ids,1].mean()>.06);eyes=[i for ids in loops if 1.53<a[ids,2].mean()<1.55 and a[ids,1].mean()>.05 for i in ids]
assert np.max(abs(d[lip]))==0 and np.max(abs(d[eyes]))==0;assert np.max(abs(d[z>=1.504]))==0
for k in keys:k.data.foreach_set('co',(old[k.name]+d).astype(np.float32).ravel());k.value=0.
m.vertices.foreach_set('co',(a+d).astype(np.float32).ravel());m.update();bpy.context.view_layer.update();after=meshguard();assert before==after
post={k.name:np.array([v.co[:] for v in k.data]) for k in keys};actual=post['Basis']-a;res=max(float(np.max(abs(post[k]-old[k]-actual))) for k in old);assert np.max(abs(actual[:,1:]))==0;assert res<1e-7
bpy.ops.wm.save_as_mainfile(filepath=str(DST));np.savez_compressed(P/'q11-deltas.npz',basis=a,delta=d,mouth_ids=lip,eye_ids=eyes)
report={'status':'SINGLE CANDIDATE / UNREVIEWED ART','source':str(SRC),'source_sha256':SHA,'candidate':str(DST),'candidate_sha256':sha(DST),'mapping':'x_new=x+sign(x)*f(z)*C2(abs(x);12.5mm,30.5mm); y_new=y; z_new=z. Same mapping for all anterior/posterior/circumferential points.','support_z_m':[1.477,1.504],'lower_lobe':{'amplitude_m':.0015,'rise':[1.477,1.480],'fall':[1.482,1.485]},'corner_lobe':{'amplitude_m':-.0025,'rise':[1.482,1.489],'fall':[1.496,1.504]},'actual_max_abs_xyz_mm':(np.max(abs(actual),axis=0)*1000).tolist(),'actual_positive_x_abs_radius_change_mm':float(np.max(np.sign(x)*actual[:,0])*1000),'analytic_global_jacobian_lower_bound':analytic_lower,'sampled_surface_jacobian_min':float(jac.min()),'sampled_surface_jacobian_max':float(jac.max()),'mouth_boundary_max_delta_mm':float(np.max(abs(actual[lip]))*1000),'eye_boundary_max_delta_mm':float(np.max(abs(actual[eyes]))*1000),'upper_ear_region_max_delta_mm':float(np.max(abs(actual[z>=1.504]))*1000),'all_key_delta_residual_max_mm':res*1000,'key_names_unchanged':list(old)==list(post),'uv_topology_groups_weights_material_names_other_mesh_coordinates_exact':before==after,'other_mesh_count':len(before['other_meshes']),'key_count':len(keys),'changed_vertices':int(np.count_nonzero(np.linalg.norm(actual,axis=1)>1e-9)),'scope':'Only gradual lower-cheek/jaw taper; no nose/profile-depth fix, no whole-face approval'};(P/'q11-audit.json').write_text(json.dumps(report,indent=2));assert sha(SRC)==SHA;print('Q11_DONE',report['actual_max_abs_xyz_mm'],report['sampled_surface_jacobian_min'])
