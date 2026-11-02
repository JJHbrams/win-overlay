"""First coarse whole-body STATIC POSED target. No inverse/rest/scene replay.

Fits actual low-A control coordinates to the shared section/branch scaffold.
Source uncertainty drives confidence; hidden posterior is not forced outward.
"""
from pathlib import Path
import json,hashlib
import numpy as np
from field_math import smooth,cubic_z,periodic_theta
P=Path(__file__).resolve().parent;O=P/'posed-target';O.mkdir(exist_ok=True);G=P/'scaffold-fullbody';guide=json.loads((G/'guide-data.json').read_text());actual=json.loads((G/'guide-actual-Blender.json').read_text());cachepath=(Path(__file__).resolve().parent/'inputs/mapping-frame1.npz');assert hashlib.sha256(cachepath.read_bytes()).hexdigest()=='c36230677c7491af3ec35f1cd0dce579647ce3bad9e4c5db5495304fbd567045';m=np.load(cachepath);q0=m['q0_world'];N=len(q0);W=np.load(P/'current-body-weights.npz');weights=W['weights'];names=W['names'].tolist();rest=json.loads((P/'current-rig-rest.json').read_text());pose=rest['pose_endpoints_world'];raw=np.load(P/'current-body-limit.npz');gsoft=raw['soft_G'];R=np.asarray(m['matrix_world'])[:3,:3];softlocal=gsoft@np.linalg.inv(R).T;softworld=np.einsum('nij,nj->ni',m['J_world_from_local'],softlocal);mass=np.linalg.norm(gsoft,axis=1)
def clip_delta(v,cap):
    n=np.linalg.norm(v,axis=1);c=np.asarray(cap);return v*(c*np.tanh(n/np.maximum(c,1e-12))/np.maximum(n,1e-15))[:,None]
def side_weight(side,parts):
    ids=[i for i,n in enumerate(names) if n.startswith('J_Bip_'+side+'_') and any(n.split('_')[-1].startswith(x) for x in parts)];return weights[:,ids].sum(1) if ids else np.zeros(N)
def getcurve(suffix):return np.asarray(next(c for c in actual['curves'] if c['name'].endswith(suffix))['points'])[:-1]
def ring_center(points):return (points.min(0)+points.max(0))/2
def sample_torso(points):
    rings=[getcurve('support.section.'+str(i).zfill(2)) for i in range(1,8)]+[getcurve('pelvis.section.'+str(i).zfill(2)) for i in range(4)];neck=json.loads((G/'neck-supplement.json').read_text());rings+=[np.asarray(r) for r in neck['rings']];rings.sort(key=lambda a:float(a[:,2].mean()));z=np.asarray([a[:,2].mean() for a in rings]);params=np.clip(points[:,2],.90,1.455)
    axes=[]
    for name in ['J_Bip_C_Hips','J_Bip_C_Spine','J_Bip_C_Chest','J_Bip_C_UpperChest','J_Bip_C_Neck','J_Bip_C_Head']:
        p=np.asarray(pose[name]['head']);axes.append(p)
    axes=np.asarray(sorted(axes,key=lambda p:p[2]));cx=cubic_z(axes[:,2],axes[:,0],params);cy=cubic_z(axes[:,2],axes[:,1],params);theta=np.arctan2(points[:,0]-cx,-(points[:,1]-cy));values=[]
    for ring in rings:
        zz=float(ring[:,2].mean());ox=float(np.interp(zz,axes[:,2],axes[:,0]));oy=float(np.interp(zz,axes[:,2],axes[:,1]));ang=np.arctan2(ring[:,0]-ox,-(ring[:,1]-oy));values.append(periodic_theta(ang,ring[:,:2],theta))
    target=points.copy();target[:,:2]=cubic_z(z,np.asarray(values),params)
    # Slightly inside the cloth support envelope, not a naked-root trace.
    radial=target[:,:2]-np.column_stack([cx,cy]);length=np.linalg.norm(radial,axis=1);cloth=smooth((params-1.18)/.025)*smooth((1.35-params)/.025);target[:,:2]-=radial/np.maximum(length[:,None],1e-12)*(.0015*cloth)[:,None]
    upper=smooth((params-1.13)/.06);front=smooth((cy-points[:,1]+.015)/.050);confidence=(.30*(1-upper)+.90*upper*front);uncertainty=.012*(1-upper)+.006*upper;delta=target-points;n=np.linalg.norm(delta,axis=1);significance=1-np.exp(-(n/uncertainty)**4);gain=smooth((params-.90)/.05)*smooth((1.425-params)/.035);cap=.018*(1-upper)+.042*upper;return clip_delta(delta,cap)*(confidence*significance*gain)[:,None],cy
def tube(points,side,region,count,shift):
    rings=[getcurve(f'{side}.{region}.section.{i:02d}') for i in range(count)];centers=np.asarray([ring_center(r) for r in rings]);current=centers-np.asarray(shift);knots=np.r_[0,np.cumsum(np.linalg.norm(np.diff(centers,axis=0),axis=1))];knots/=knots[-1]
    # Closest canonical centerline segment locates limb-local t, not imageY.
    best=np.full(N,np.inf);param=np.zeros(N)
    for i,(a,b) in enumerate(zip(current[:-1],current[1:])):
        v=b-a;tt=np.clip(((points-a)*v).sum(1)/np.dot(v,v),0,1);distance=np.linalg.norm(points-(a+tt[:,None]*v),axis=1);take=distance<best;param[take]=knots[i]+tt[take]*(knots[i+1]-knots[i]);best[take]=distance[take]
    if region=='foot':
        knots=(centers[0,2]-centers[:,2])/(centers[0,2]-centers[-1,2]);param=(centers[0,2]-points[:,2])/(centers[0,2]-centers[-1,2]);cnow=cubic_z(knots,np.repeat(current[:,None,:],N,axis=1),param);u=np.tile([0.,0.,-1.],(N,1))
    else:
        repeated=np.repeat(current[:,None,:],N,axis=1);eps=1e-4
        for iteration in range(3):
            c0=cubic_z(knots,repeated,param);plus=cubic_z(knots,repeated,param+eps);minus=cubic_z(knots,repeated,param-eps);d1=(plus-minus)/(2*eps);d2=(plus-2*c0+minus)/eps**2;den=(d1*d1).sum(1)+((c0-points)*d2).sum(1);param-=np.clip(((c0-points)*d1).sum(1)/np.maximum(den,1e-8),-.20,.20);param=np.clip(param,-.35,1.35)
        cnow=cubic_z(knots,repeated,param);u=(cubic_z(knots,repeated,param+eps)-cubic_z(knots,repeated,param-eps))/(2*eps);u/=np.maximum(np.linalg.norm(u,axis=1),1e-12)[:,None]
    directions=np.gradient(current,knots,axis=0);front=np.tile([0.,-1.,0.],(N,1));front-=(front*u).sum(1)[:,None]*u;front/=np.maximum(np.linalg.norm(front,axis=1),1e-12)[:,None];right=np.cross(u,-front);right/=np.maximum(np.linalg.norm(right,axis=1),1e-12)[:,None];rad=points-cnow;theta=np.arctan2((rad*right).sum(1),(rad*front).sum(1));values=[]
    for i,ring in enumerate(rings):
        ui=np.array([0.,0.,-1.]) if region=='foot' else directions[i]/np.linalg.norm(directions[i]);fi=np.array([0.,-1.,0.]);fi-=np.dot(fi,ui)*ui;fi/=np.linalg.norm(fi);ri=np.cross(ui,-fi);ri/=np.linalg.norm(ri);rr=ring-centers[i];ang=np.arctan2(rr@ri,rr@fi);values.append(periodic_theta(ang,rr,theta))
    # C2 sections/centerline. Original posed limbs define the editing pose.
    vals=np.asarray(values);radial=cubic_z(knots,vals,param);ct=cubic_z(knots,np.repeat(centers[:,None,:],N,axis=1),param);target=ct+radial;transport=np.asarray(shift);morph=target-(points+transport);uncertainty={'arm':.012,'hand':.015,'leg':.010,'foot':.012}[region];confidence={'arm':.55,'hand':.25,'leg':.50,'foot':.35}[region];cap={'arm':.020,'hand':.008,'leg':.018,'foot':.012}[region];n=np.linalg.norm(morph,axis=1);gain=confidence*(1-np.exp(-(n/uncertainty)**4));return transport+clip_delta(morph,cap)*gain[:,None]
# Restore a supported vertical material flow using the ACTUAL posed soft
# vector, rather than interpreting raw T-pose coordinates as source-world.
support=q0.copy();support[:,2]-=.80*softworld[:,2];support[3957:]=q0[3957:];torso_delta,cy=sample_torso(support);fields={};parts={}
for side,sign in [('L',1),('R',-1)]:
    handw=side_weight(side,['Hand','Thumb','Index','Middle','Ring','Little']);armw=side_weight(side,['UpperArm','LowerArm']);legw=side_weight(side,['UpperLeg','LowerLeg']);footw=side_weight(side,['Foot','Toe']);shift=np.array([sign*.015,0.,-.012]);parts[side+'.arm']=armw;parts[side+'.hand']=handw;parts[side+'.leg']=legw;parts[side+'.foot']=footw
    fields[side+'.arm']=tube(q0,side,'arm',5,shift);fields[side+'.hand']=tube(q0,side,'hand',3,shift);fields[side+'.leg']=tube(q0,side,'leg',9,np.zeros(3));fields[side+'.foot']=tube(q0,side,'foot',4,np.zeros(3))
sumlimb=np.sum(list(parts.values()),axis=0);tw=np.clip(1-sumlimb,0,1);q=q0+tw[:,None]*((support-q0)+torso_delta)
for name,w in parts.items():q+=w[:,None]*fields[name]
# Smooth finite pectoral support branch: one volumetric field, no internal
# triangle-edge fades and no membrane spanning the axilla.
controls={};frontids=np.flatnonzero((q[:,1]<.005)&(q[:,2]>1.245)&(q[:,2]<1.405)&(np.arange(N)<3957))
for mesh in actual['meshes']:
    if 'anterior_fan_web' not in mesh['name']:continue
    for pt in np.asarray(mesh['vertices']):
        j=int(frontids[np.linalg.norm(q[frontids]-pt,axis=1).argmin()]);controls.setdefault(j,[]).append(float(np.clip(pt[1]-q[j,1],-.007,0)))
for j in np.flatnonzero((mass>.055)&(np.arange(N)<3957)):controls[j]=[0.]
for zz in [1.20,1.425]:
    for xx in [-.19,-.10,0,.10,.19]:
        j=int(frontids[np.linalg.norm(q[frontids]-[xx,-.04,zz],axis=1).argmin()]);controls[j]=[0.]
ids=np.asarray(list(controls));pos=q[ids];values=np.array([np.mean(controls[i]) for i in ids]);sigma=.050;K=np.exp(-((pos[:,None]-pos[None,:])**2).sum(2)/sigma**2);coef=np.linalg.solve(K+np.eye(len(K))*.006,values);branch=np.exp(-((q[:,None]-pos[None,:])**2).sum(2)/sigma**2)@coef;branch=.008*np.tanh(branch/.008);branch*=smooth((q[:,2]-1.215)/.025)*smooth((1.420-q[:,2])/.025)*smooth((cy-q[:,1]+.005)/.035)*(1-smooth((mass-.050)/.015));q[:,1]+=branch
# Frozen accepted face/head; crotch medial seam keeps its current separation.
q[3957:]=q0[3957:];q[q0[:,2]>=1.425]=q0[q0[:,2]>=1.425];anchor=smooth((q0[:,2]-.78)/.03)*smooth((.97-q0[:,2])/.03)*(1-smooth((abs(q0[:,0])-.008)/.015));q[:,0]=q0[:,0]+(q[:,0]-q0[:,0])*(1-anchor);delta=q-q0
# The native Weld acts only on its named seam group at6microns. Preserve
# those existing aliases by a shared DISPLACEMENT (not by collapsing original
# offsets or deleting nail parts). This keeps the physical cage continuous.
props=json.loads((P/'protected-current-data.json').read_text(encoding='utf-8'))['shared_face']['modifiers'];weld=next(x['properties'] for x in props if x['type']=='WELD');radius=weld['merge_threshold'];eligible=np.flatnonzero(weights[:,names.index(weld['vertex_group'])]>.5);parent=np.arange(N)
def find(i):
    while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
    return i
cells={};base=m['q0_local'];pairs=[]
for i in eligible:
    cell=tuple(np.floor(base[i]/radius).astype(np.int64))
    for a0 in [-1,0,1]:
        for a1 in [-1,0,1]:
            for a2 in [-1,0,1]:
                for j in cells.get((cell[0]+a0,cell[1]+a1,cell[2]+a2),[]):
                    if np.linalg.norm(base[i]-base[j])<radius:parent[find(i)]=find(j);pairs.append([int(i),int(j)])
    cells.setdefault(cell,[]).append(int(i))
groups={}
for i in eligible:groups.setdefault(find(int(i)),[]).append(int(i))
groups=[ids for ids in groups.values() if len(ids)>1]
for ids in groups:
    shared=np.zeros(3) if any(i>=3957 or q0[i,2]>=1.425 for i in ids) else delta[ids].mean(0);delta[ids]=shared
q=q0+delta;local=m['q0_local']+delta@np.linalg.inv(R).T;local[3957:]=m['q0_local'][3957:];local[q0[:,2]>=1.425]=m['q0_local'][q0[:,2]>=1.425];assert np.array_equal(q[3957:],q0[3957:]);assert np.isfinite(local).all();assert np.linalg.norm(delta,axis=1).max()<.080
(O/'weld-aliases-01.json').write_text(json.dumps(dict(native_modifier=weld,eligible_vertices=len(eligible),existing_pairs=pairs,existing_groups=groups,rule='Shared posed displacement preserves original offsets, UV seam/nail geometry and baseline6micron equivalence; head-attached groups frozen.'),indent=2)+'\n',encoding='utf-8')
np.savez_compressed(O/'target-01.npz',q0_world=q0,target_world=q,target_local=local,delta_world=delta,branch_field=branch,torso_weight=tw,control_ids=np.flatnonzero(np.linalg.norm(delta,axis=1)>1e-9))
report=dict(method='Whole-body canonical-posed scaffold fit with periodic-C2 angular sections/natural-C2 axial interpolation, normalized continuous anatomical weights and finite Gaussian branch support. No rest56 replay or inverse skinning yet.',base_native_sha256='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1',mapping_sha256=hashlib.sha256(cachepath.read_bytes()).hexdigest(),guide_sha256=hashlib.sha256((G/'guide-data.json').read_bytes()).hexdigest(),neck_sha256=hashlib.sha256((G/'neck-supplement.json').read_bytes()).hexdigest(),posed_vertices=N,changed_controls=int((np.linalg.norm(delta,axis=1)>1e-9).sum()),max_move_mm=float(np.linalg.norm(delta,axis=1).max()*1000),max_branch_mm=float(abs(branch).max()*1000),face690_exact=True,head_control_above1_425_exact=True,rig_untouched=True,keys47_untouched=True,static_only=True,status='COARSE_STATIC_POSED_HYPOTHESIS; actual surface/source/highlow review required; no anatomy or motion-rig PASS')
(O/'construction-01.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('POSED_TARGET_01_DATA_DONE',json.dumps(report),flush=True)
