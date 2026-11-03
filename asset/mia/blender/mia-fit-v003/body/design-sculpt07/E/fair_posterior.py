"""One connected measured posterior-strip Taubin fair with fixed rails/band.
Only new E mesh changes. D coordinates provide exact same-sheet correspondence.
"""
from pathlib import Path
import json,hashlib,heapq
import numpy as np
P=Path(__file__).resolve().parent;D=P.parent/'D';e=np.load(P/'breast-step.npz');v=e['world'].astype(float);tri=e['triangles'];old=v.copy();d=np.load(D/'sculpt07-D.npz');dv=d['world'];dt=d['triangles'];sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
def normals(v):
    face=np.cross(v[tri[:,1]]-v[tri[:,0]],v[tri[:,2]]-v[tri[:,0]]);vn=np.zeros_like(v)
    for j in range(3):np.add.at(vn,tri[:,j],face)
    vn/=np.maximum(np.linalg.norm(vn,axis=1)[:,None],1e-30);return face,vn
def volume(v):
    a,b,c=v[tri[:,0]],v[tri[:,1]],v[tri[:,2]];return float(np.einsum('ij,ij->i',a,np.cross(b,c)).sum()/6)
face0,vn=normals(v);dedges=np.sort(np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]),axis=1);edges=np.unique(dedges,axis=0);a,b=edges.T;degree=np.bincount(edges.ravel(),minlength=len(v));adj=[[] for _ in v]
for aa,bb in edges:
    length=float(np.linalg.norm(v[aa]-v[bb]));adj[aa].append((int(bb),length));adj[bb].append((int(aa),length))
lookup={tuple(q):i for i,q in enumerate(e['world'])};dcent=dv[dt].mean(1);dn=np.cross(dv[dt[:,1]]-dv[dt[:,0]],dv[dt[:,2]]-dv[dt[:,0]]);dn/=np.linalg.norm(dn,axis=1)[:,None]
positive_seed=[117439,117681,117690,117699];positive_fixed=[117879,114437,114428,117614,117927,117923,117735];positive_monitor=[117704,117634];guard=[116925]
def mirror_face(fi):
    q=dcent[fi].copy();q[0]*=-1;allowed=(dcent[:,0]<0)&(np.linalg.norm(dcent-q,axis=1)<.006)&(dn[:,1]>.25);ids=np.flatnonzero(allowed);assert len(ids);chosen=int(ids[np.argmin(np.linalg.norm(dcent[ids]-q,axis=1))]);assert np.linalg.norm(dcent[chosen]-q)<.0025;return chosen
def vertices_for(ids):
    result=[]
    for fi in ids:
        for vi in dt[fi]:
            q=tuple(dv[vi]);assert q in lookup,('Posterior D/E coordinate identity missing',fi,q);result.append(lookup[q])
    return np.unique(result)
def distances(seeds,allowed,cutoff=.05):
    dist=np.full(len(v),np.inf);queue=[]
    for s in seeds:
        if allowed[s]:dist[s]=0.;heapq.heappush(queue,(0.,int(s)))
    while queue:
        dd,i=heapq.heappop(queue)
        if dd!=dist[i] or dd>cutoff:continue
        for j,ll in adj[i]:
            nd=dd+ll
            if allowed[j] and nd<dist[j] and nd<=cutoff:dist[j]=nd;heapq.heappush(queue,(nd,j))
    return dist
def smooth(t):t=np.clip(t,0,1);return t**3*(10-15*t+6*t*t)
weight=np.zeros(len(v));ownership=[];all_fixed=[];all_seeds=[]
for sign in [1,-1]:
    seed_ids=positive_seed if sign==1 else[14739,14856,14864,mirror_face(117699)];fixed_ids=positive_fixed if sign==1 else[mirror_face(fi) for fi in positive_fixed];monitor_ids=positive_monitor if sign==1 else[mirror_face(fi) for fi in positive_monitor]
    seeds=vertices_for(seed_ids);fixed=vertices_for(fixed_ids);all_fixed.extend(fixed);all_seeds.extend(seeds)
    allowed=(sign*v[:,0]>.132)&(sign*v[:,0]<.171)&(v[:,1]>.012)&(v[:,1]<.050)&(v[:,2]>1.255)&(v[:,2]<1.289)&(vn[:,1]>.25)
    ds=distances(seeds,allowed,.030);connected=np.isfinite(ds);boundary=allowed.copy();boundary[:]=False
    for i in np.flatnonzero(connected):
        if any(not connected[j] for j,_ in adj[i]):boundary[i]=True
    boundary[fixed]=True;df=distances(np.flatnonzero(boundary),connected,.050);ww=(1-smooth(ds/.012))*smooth(df/.006);ww[~connected]=0.;ww[fixed]=0.;weight=np.maximum(weight,ww)
    ownership.append(dict(side_sign=sign,seed_D_triangles=seed_ids,fixed_D_triangles=fixed_ids,monitored_bottom_D_triangles=monitor_ids,connected_candidate_vertices=int(connected.sum()),active_vertices=int((ww>0).sum()),normal_guard='Actual E vertex nY>.25; same-sheet geodesic connectivity; opposite/anterior shell excluded.',fixed_band='Actual inner/outer/top rails plus connected-domain outer boundary; C2 distance taper. Apex allowed bounded motion; lower passage measured, not locked to arbitraryZ.'))
guard_vertices=vertices_for(guard);assert not weight[guard_vertices].any();all_fixed=np.unique(all_fixed)
def lap(q):
    total=np.zeros_like(q);np.add.at(total,a,q[b]);np.add.at(total,b,q[a]);return total/degree[:,None]-q
for iteration in range(4):
    v+=.50*weight[:,None]*lap(v);v-=.53*weight[:,None]*lap(v)
delta=v-old;length=np.linalg.norm(delta,axis=1);cap=.0008;delta*=np.minimum(1,cap/np.maximum(length,1e-30))[:,None];v=old+delta
vol0=volume(old);pre_comp=volume(v)
for iteration in range(3):
    g=np.zeros_like(v);aa,bb,cc=v[tri[:,0]],v[tri[:,1]],v[tri[:,2]]
    for j,gg in enumerate([np.cross(bb,cc)/6,np.cross(cc,aa)/6,np.cross(aa,bb)/6]):np.add.at(g,tri[:,j],gg)
    residual=volume(v)-vol0;den=float((weight*np.sum(g*g,axis=1)).sum())
    if den<1e-30:break
    candidate=v-residual*weight[:,None]*g/den;dd=candidate-old;ll=np.linalg.norm(dd,axis=1);dd*=np.minimum(1,cap/np.maximum(ll,1e-30))[:,None];v=old+dd
face1,_=normals(v);dot=np.einsum('ij,ij->i',face0,face1);assert dot.min()>0 and np.array_equal(v[weight==0],old[weight==0]) and np.array_equal(v[guard_vertices],old[guard_vertices]) and np.array_equal(v[all_fixed],old[all_fixed])
def turns(face):
    pairs={};angles=[]
    for fi,t in enumerate(tri):
        for aa,bb in [(t[0],t[1]),(t[1],t[2]),(t[2],t[0])]:
            key=(min(aa,bb),max(aa,bb))
            if key in pairs:
                other=pairs[key]
                if weight[[aa,bb]].mean()>.2:
                    n0=face[fi]/np.linalg.norm(face[fi]);n1=face[other]/np.linalg.norm(face[other]);angles.append(np.degrees(np.arccos(np.clip(n0@n1,-1,1))))
            else:pairs[key]=fi
    return dict(n=len(angles),quantiles_degrees=np.percentile(angles,[50,90,95,99,100]).tolist())
np.savez_compressed(P/'sculpt07-E.npz',world=v.astype(np.float32),triangles=tri);np.savez_compressed(P/'posterior-fair-delta.npz',vertex_indices=np.flatnonzero(weight),weights=weight[weight>0],delta_world=(v-old)[weight>0]);p=json.loads((P/'parameters.json').read_text(encoding='utf-8'));p['posterior_fair_status']='APPLIED one measured connected posterior strip,4 Taubin pairs lambda.50/mu−.53,max.8mm, local volume compensation, actual fixed rails and opposite guard.';(P/'parameters.json').write_text(json.dumps(p,indent=2)+'\n',encoding='utf-8')
r=dict(breast_step_sha256=sha(P/'breast-step.npz'),final_mesh_sha256=sha(P/'sculpt07-E.npz'),input_parameters_sha256_at_breast_build=json.loads((P/'breast-build-report.json').read_text())['parameters_sha256'],actual_active_vertices=int((weight>0).sum()),fixed_band_vertices=len(all_fixed),opposite_guard_D_triangle=116925,opposite_guard_vertices_exact=True,outside_mask_vertices_exact=True,max_displacement_mm=float(np.linalg.norm(v-old,axis=1).max()*1000),median_active_displacement_mm=float(np.median(np.linalg.norm(v-old,axis=1)[weight>0])*1000),volume_before_m3=vol0,volume_before_compensation_m3=pre_comp,volume_after_m3=volume(v),relative_volume_change=(volume(v)-vol0)/vol0,triangle_orientation_flips=int((dot<=0).sum()),normal_turn_before=turns(face0),normal_turn_after=turns(face1),ownership=ownership,limits='Triangle normal turns include tessellation; component labels/technical checks do not grant anatomy acceptance. No global Smooth. Lower air passage requires actual post-fair sections, not a hard13mm invariant.')
(P/'posterior-fair-audit.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print('E_POSTERIOR_LOCAL_FAIR',json.dumps(r),flush=True)
