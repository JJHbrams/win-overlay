import bpy,numpy as np,json,hashlib
from pathlib import Path
from collections import Counter,defaultdict
P=Path(__file__).parent;SRC=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v22/integration-wip-9-review/Mia_FaceReview_v22_WIP9.blend');SHA='fb85468a623e1befc590176a24636548b944491ce4ae19decaece625304945b2';DST=P/'Mia_JawBuccal_Q10.blend';assert hashlib.sha256(SRC.read_bytes()).hexdigest()==SHA;assert not DST.exists()
bpy.ops.wm.open_mainfile(filepath=str(SRC),use_scripts=False);o=bpy.data.objects['MIA_V14_SculptedSkin'];m=o.data;keys=m.shape_keys.key_blocks
for k in keys:k.value=0.
a=np.array([v.co[:] for v in keys[0].data]);m.update();norm=np.array([v.normal[:] for v in m.vertices]);x=np.abs(a[:,0]);y=a[:,1];z=a[:,2]
def ss(lo,hi,v):
 t=np.clip((v-lo)/(hi-lo),0,1);return t*t*(3-2*t)
# Continuous actual frontal jaw section envelope, excluding ear/posterior sheet.
edges=np.array([e.vertices[:] for e in m.edges]);ea=a[edges[:,0]];eb=a[edges[:,1]];grid=np.linspace(1.470,1.530,241);width=[]
for zz in grid:
 hit=(ea[:,2]-zz)*(eb[:,2]-zz)<=0;hit&=abs(ea[:,2]-eb[:,2])>1e-9
 u=(zz-ea[hit,2])/(eb[hit,2]-ea[hit,2]);v=ea[hit]+u[:,None]*(eb[hit]-ea[hit]);valid=(v[:,1]>0)&(abs(v[:,0])<.061)
 width.append(float(np.max(abs(v[valid,0]))) if np.any(valid) else .001)
width=np.array(width);old=np.interp(z,grid,width);t=np.clip((z-1.468)/.057,0,1);target=.057*np.sqrt(t)*(.9+.1*t)
contour=(target-old)*ss(1.474,1.480,z)*(1-ss(1.516,1.528,z));contour=np.clip(contour,-.005,.003)
wx=ss(.30,.88,x/np.maximum(old,.001))*ss(-.025,0,y)*(1-ss(.060,.070,x));d=np.zeros_like(a);d[:,0]=np.sign(a[:,0])*contour*wx
# Locate actual eye and mouth holes; preserve their corrected contact curves.
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
mouth=next(ids for ids in loops if 1.48<a[ids,2].mean()<1.51 and a[ids,1].mean()>.06);eyes=[i for ids in loops if 1.53<a[ids,2].mean()<1.55 and a[ids,1].mean()>.05 for i in ids]
def distance(ids):
 out=np.full(len(a),np.inf)
 for i in ids:out=np.minimum(out,np.linalg.norm(a-a[i],axis=1))
 return out
mouthdist=distance(mouth);eyedist=distance(eyes)
# A broad anterior lower-face surface, fitted once to actual stable samples.
# Corrected lip/orbit boundary positions are protected; legacy intervening
# wrinkles are not used as fixed positional anchors.
b=a+d;ax=np.abs(b[:,0]);zz=b[:,2];yy=b[:,1];u=(ax-.025)/.030;v=(zz-1.501)/.025;A=np.column_stack([np.ones_like(u),u,v,u*u,u*v,v*v,u**3,u*u*v,u*v*v,v**3])
samples=(ax>.010)&(ax<.048)&(zz>1.479)&(zz<1.529)&(yy>.044)&(norm[:,1]>.48)&(mouthdist>.006)&~((ax<.014)&(zz>1.506))
F=A[samples];vals=yy[samples];coef=np.linalg.lstsq(F,vals,rcond=None)[0]
for _ in range(4):
 residual=vals-F@coef;wt=1/np.sqrt(1+(residual/.0025)**2);coef=np.linalg.lstsq(F*wt[:,None],vals*wt,rcond=None)[0]
ytarget=A@coef;w=ss(1.477,1.489,zz)*(1-ss(1.521,1.533,zz))*ss(.002,.012,ax)*(1-ss(.047,.064,ax))*ss(.025,.045,yy)*ss(.0005,.005,mouthdist)*ss(.001,.005,eyedist)
d[:,1]=.004*np.tanh((ytarget-yy)/.004)*w
# Exact contacts, not just almost-zero spatial falloff.
d[mouth]=0;d[eyes]=0
for k in keys:
 v=np.array([q.co[:] for q in k.data]);k.data.foreach_set('co',(v+d).astype(np.float32).ravel())
m.vertices.foreach_set('co',(a+d).astype(np.float32).ravel());m.update();bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(DST));np.savez_compressed(P/'q10-deltas.npz',basis=a,delta=d,mouth_ids=mouth,eye_ids=eyes)
r={'source':str(SRC),'source_sha256':SHA,'candidate':str(DST),'candidate_sha256':hashlib.sha256(DST.read_bytes()).hexdigest(),'target':'single continuous chin-to-malar section arc, broad anterior buccal/muzzle sheet, fixed actual lip/eye contacts; no Z scale','envelope_z':grid.tolist(),'original_envelope':width.tolist(),'target_formula':'x=0.057*sqrt(t)*(0.9+0.1*t), t=(z-1.468)/0.057; transition below z1.528','surface_fit_coefficients':coef.tolist(),'fit_samples':int(sum(samples)),'changed_vertices':int(np.count_nonzero(np.linalg.norm(d,axis=1)>1e-9)),'max_abs_xyz_mm':(np.max(abs(d),axis=0)*1000).tolist(),'lip_contact_delta_mm':float(np.max(np.linalg.norm(d[mouth],axis=1))*1000),'eye_contact_delta_mm':float(np.max(np.linalg.norm(d[eyes],axis=1))*1000),'art_status':'UNREVIEWED SINGLE TARGET CANDIDATE'};(P/'q10-audit.json').write_text(json.dumps(r,indent=2));print('Q10_BUILT',r['max_abs_xyz_mm'],r['changed_vertices'])
