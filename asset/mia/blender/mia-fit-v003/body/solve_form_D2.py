"""Unified source-scaffold structural cage + finite pectoral branch transport.
No hard breast/arm cutoff; no sphere/cone or volume multiplier. No scene save.
"""
from pathlib import Path
import json,hashlib
import numpy as np
P=Path(__file__).resolve().parent;O=P/'scaffold-D';d=np.load(P/'current-body-limit.npz');p=d['raw_world'].copy();core=d['core'];soft=d['soft_G'];w=np.load(P/'current-body-weights.npz');names=w['names'].tolist();weights=w['weights'];arm=w['arm_sum'];n=len(p);guide=json.loads((O/'guide-data.json').read_text());actual=json.loads((O/'guide-actual-Blender.json').read_text());assert guide['revision']==2
def smooth(t):t=np.clip(t,0,1);return t*t*(3-2*t)
def cubic_z(nodes,values,query):
    """Natural C2 cubic; linear endpoint continuation retains C2 continuity."""
    nodes=np.asarray(nodes);values=np.asarray(values);query=np.asarray(query);h=np.diff(nodes);N=len(nodes);A=np.zeros((N,N));rhs=np.zeros_like(values);A[0,0]=A[-1,-1]=1
    for i in range(1,N-1):A[i,i-1]=h[i-1];A[i,i]=2*(h[i-1]+h[i]);A[i,i+1]=h[i];rhs[i]=6*((values[i+1]-values[i])/h[i]-(values[i]-values[i-1])/h[i-1])
    M=np.linalg.solve(A,rhs.reshape(N,-1)).reshape(values.shape);ii=np.clip(np.searchsorted(nodes,query),1,N-1);jj=ii-1;ix=np.arange(len(query));q=np.clip(query,nodes[0],nodes[-1]);hh=nodes[ii]-nodes[jj];aa=(nodes[ii]-q)/hh;bb=(q-nodes[jj])/hh
    shape=(len(query),)+(1,)*(values.ndim-2);aa=aa.reshape(shape);bb=bb.reshape(shape);hh=hh.reshape(shape)
    if values.ndim==1:
        lo=values[jj];hi=values[ii];ml=M[jj];mh=M[ii]
    else:lo=values[jj,ix];hi=values[ii,ix];ml=M[jj,ix];mh=M[ii,ix]
    result=aa*lo+bb*hi+((aa**3-aa)*ml+(bb**3-bb)*mh)*hh**2/6
    low=query<nodes[0];high=query>nodes[-1];sl=(values[1]-values[0])/h[0]-h[0]*(2*M[0]+M[1])/6;sh=(values[-1]-values[-2])/h[-1]+h[-1]*(M[-2]+2*M[-1])/6
    if values.ndim==1:result[low]=values[0]+(query[low]-nodes[0])*sl;result[high]=values[-1]+(query[high]-nodes[-1])*sh
    else:result[low]=values[0,low]+(query[low]-nodes[0])[:,None]*sl[low];result[high]=values[-1,high]+(query[high]-nodes[-1])[:,None]*sh[high]
    return result
def periodic_theta(angles,points,query):
    """Periodic C2 interpolation of the actual Blender ring readback."""
    order=np.argsort(angles);a=angles[order];p0=points[order];unique=np.r_[True,np.diff(a)>1e-9];a=a[unique];p0=p0[unique];N=len(a);h=np.diff(np.r_[a,a[0]+2*np.pi]);A=np.zeros((N,N));rhs=np.zeros_like(p0)
    for i in range(N):
        prev=(i-1)%N;nx=(i+1)%N;A[i,prev]=h[prev];A[i,i]=2*(h[prev]+h[i]);A[i,nx]=h[i];rhs[i]=6*((p0[nx]-p0[i])/h[i]-(p0[i]-p0[prev])/h[prev])
    M=np.linalg.solve(A,rhs);q=(query-a[0])%(2*np.pi)+a[0];lo=np.clip(np.searchsorted(a,q)-1,0,N-1);hi=(lo+1)%N;t=(q-a[lo])/h[lo];aa=1-t;return aa[:,None]*p0[lo]+t[:,None]*p0[hi]+(((aa**3-aa)[:,None]*M[lo]+(t**3-t)[:,None]*M[hi])*h[lo,None]**2/6)
center=-.0004777;x=abs(core[:,0]-center);z=core[:,2];mass=np.linalg.norm(soft,axis=1)
# Reopen C's support height/width without its rejected arm-mask wall.
v=smooth((z-1.125)/.085)*smooth((1.345-z)/.040);lat=smooth((.170-x)/.045);env=v*lat
coreC=core.copy();coreC[:,0]+=(core[:,0]-center)*.30*env;coreC[:,1]+=(core[:,1]+.010)*.10*env
seat=smooth((mass-.045)/.025)*np.exp(-((z-1.256)/.045)**4)
unmasked=p.copy();unmasked[:,0]+=(core[:,0]-center)*.30*env*(1-seat);unmasked[:,1]+=(core[:,1]+.010)*.10*env-.007*smooth(mass/.018)*np.exp(-((z-1.286)/.030)**2)*smooth((1.345-z)/.015);unmasked[:,2]-=.80*soft[:,2]*smooth((1.345-z)/.015)
softC=unmasked-coreC
# Explicit actual Blender3D cross-sections, interpolated by registered height.
# Angular coordinates only establish correspondence around each REAL curve;
# the target shape is the sampled non-elliptic guide, not a radial primitive.
stations=sorted(guide['stations'],key=lambda s:s['z']);heights=np.array([s['z'] for s in stations]);cy=[]
for st in stations:
    pts=coreC[(abs(coreC[:,2]-st['z'])<.018)&(abs(coreC[:,0])<.12)&(arm<.15)]
    cy.append((np.percentile(pts[:,1],2)+np.percentile(pts[:,1],98))/2 if len(pts) else -.015)
cyq=cubic_z(heights,np.asarray(cy),z);theta=np.arctan2(coreC[:,0]-center,-(coreC[:,1]-cyq));targets=[]
for st in stations:
    pts=np.asarray(next(q for q in actual['curves'] if q['name'].endswith('core.section.'+str(st['id']).zfill(2)))['points'])[:-1];cc=(st['front_core_y']+st['back_y'])/2;ang=np.arctan2(pts[:,0],-(pts[:,1]-cc));targets.append(periodic_theta(ang,pts[:,:2],theta))
targets=np.asarray(targets);targetxy=cubic_z(heights,targets,z);targetcore=coreC.copy();strength=smooth((z-1.145)/.055)*smooth((1.415-z)/.060)
# Observation/inference affects the FIT: unobserved posterior has zero cage
# depth force, not merely a label. Anterior inferred core movement is bounded.
confidence=smooth((cyq-coreC[:,1]+.015)/.040);dc=(targetxy-coreC[:,:2])*confidence[:,None];norm=np.linalg.norm(dc,axis=1);cap=.020;dc*=np.where(norm>1e-15,cap*np.tanh(norm/cap)/np.maximum(norm,1e-15),1)[:,None];targetcore[:,:2]+=strength[:,None]*dc
fan_fill=np.zeros(n)
# Source-sized shoulder/rest transport: actual normalized skin weights are
# CONTINUOUS blend coordinates, not a .5 cutoff isolating the breast root.
rest=json.loads((P/'current-rig-rest.json').read_text());rm=np.asarray(rest['matrix_world']);inv=np.linalg.inv(rm);armT=np.zeros((n,3));shoulderT=np.zeros((n,3));shoulderSum=np.zeros(n);rest_delta=[]
for side,sign in [('L',1),('R',-1)]:
    def under(name,ancestor):
        while name:
            if name==ancestor:return True
            name=rest['bones'][name]['parent']
        return False
    chain=[name for name in rest['bones'] if under(name,'J_Bip_'+side+'_UpperArm')];groupids=[names.index(name) for name in chain if name in names];sw=weights[:,groupids].sum(1);T=np.array([sign*.015,0,-.012]);armT+=sw[:,None]*T
    for name in chain:
        b=rest['bones'][name];h=np.asarray(b['head']);t=np.asarray(b['tail']);localT=(inv@np.r_[T,0])[:3];rest_delta.append(dict(name=name,baseline_head=h.tolist(),baseline_tail=t.tolist(),target_head=(h+localT).tolist(),target_tail=(t+localT).tolist(),kind='arm-descendant rigid rest translation'))
    name='J_Bip_'+side+'_Shoulder';b=rest['bones'][name];h=(rm@np.r_[b['head'],1])[:3];t=(rm@np.r_[b['tail'],1])[:3];v0=t-h;u=np.clip(((p-h)*v0).sum(1)/np.dot(v0,v0),0,1);H=np.array([0.,0.,-.007]);st=H*(1-u[:,None])+T*u[:,None];ww=weights[:,names.index(name)] if name in names else np.zeros(n);shoulderT+=ww[:,None]*st;shoulderSum+=ww
    rest_delta.append(dict(name=name,baseline_head=b['head'],baseline_tail=b['tail'],target_head=(inv@np.r_[h+H,1])[:3].tolist(),target_tail=(inv@np.r_[t+T,1])[:3].tolist(),kind='paired clavicle/shoulder rest pivot'))
support=targetcore+softC;torsoW=np.clip(1-arm-shoulderSum,0,1);q=p+(support-p)*torsoW[:,None]+armT+shoulderT;basecore=core+(targetcore-core)*torsoW[:,None]+armT+shoulderT
# One C-infinity volumetric Gaussian branch field replaces triangle-wise
# fades. Internal fan diagonals are NOT boundaries and cannot leave seams.
controls={};frontids=np.flatnonzero((core[:,1]<.006)&(z>1.225)&(z<1.405)&(np.arange(n)<3957))
for mesh in actual['meshes']:
    if 'anterior_fan_web' not in mesh['name']:continue
    for pt in np.asarray(mesh['vertices']):
        dist=np.linalg.norm(basecore[frontids]-pt,axis=1);j=int(frontids[dist.argmin()]);desired=float(np.clip(pt[1]-basecore[j,1],-.010,.006));controls.setdefault(j,[]).append(desired)
for j in np.flatnonzero((mass>.060)&(np.arange(n)<3957)):controls[j]=[0.]
for zz in [1.195,1.425]:
    for xx in [-.18,-.10,0,.10,.18]:
        pt=np.array([xx,-.045,zz]);j=int(frontids[np.linalg.norm(basecore[frontids]-pt,axis=1).argmin()]);controls[j]=[0.]
controlids=np.asarray(list(controls));pos=basecore[controlids];values=np.asarray([np.mean(controls[j]) for j in controlids]);sigma=.055;rr=((pos[:,None]-pos[None,:])**2).sum(2);K=np.exp(-rr/sigma**2);coef=np.linalg.solve(K+np.eye(len(K))*.005,values);field=np.exp(-((basecore[:,None]-pos[None,:])**2).sum(2)/sigma**2)@coef
facing=smooth((cyq-basecore[:,1]+.005)/.035);extent=smooth((z-1.200)/.030)*smooth((1.420-z)/.025);polehold=1-smooth((mass-.050)/.015);fan_fill=.010*np.tanh(field/.010)*facing*extent*polehold;fan_fill[np.arange(n)>=3957]=0;q[:,1]+=fan_fill
# Small continuous neck/trap transition below the accepted head. This is an
# inferred guide-support adjustment, not the withdrawn bone-vs-skin estimate.
neck=smooth((z-1.355)/.045)*smooth((1.420-z)/.015)*smooth((.095-x)/.055);q[:,2]-=.004*neck*torsoW
q[np.arange(n)>=3957]=p[np.arange(n)>=3957];q[z>=1.425]=p[z>=1.425]
# Remove only high-frequency support noise across the WHOLE root/axilla fan,
# including arm-weighted skin. Hard pole and head/lowerbody constraints stay.
edges=d['raw_edges'];a,b=edges.T;length=np.linalg.norm(p[a]-p[b],axis=1);ew=1/np.maximum(length,.004);deg=np.bincount(np.r_[a,b],weights=np.r_[ew,ew],minlength=n)
fair=smooth((abs(q[:,0])-.050)/.030)*smooth((.185-abs(q[:,0]))/.035)*smooth((z-1.225)/.025)*smooth((1.405-z)/.025);fair*=1-smooth((mass-.045)/.020);fair[np.arange(n)>=3957]=0
anchor=q.copy()
for iteration in range(3):
    for step in [.20,-.205]:
        avg=np.zeros_like(q)
        for axis in range(3):avg[:,axis]=(np.bincount(a,weights=ew*q[b,axis],minlength=n)+np.bincount(b,weights=ew*q[a,axis],minlength=n))/np.maximum(deg,1e-12)
        q+=step*fair[:,None]*(avg-q)
q[z>=1.425]=p[z>=1.425];q[np.arange(n)>=3957]=p[np.arange(n)>=3957];q[(z<1.12)&(arm<1e-8)]=p[(z<1.12)&(arm<1e-8)];delta=q-p;ids=np.flatnonzero(np.linalg.norm(delta,axis=1)>1e-9);local=delta@np.linalg.inv(d['matrix_world'][:3,:3]).T
assert np.max(abs(delta[3957:]))==0;assert np.max(abs(delta[(z<1.12)&(arm<1e-8)]))==0;assert np.linalg.norm(delta,axis=1).max()<.080
np.savez_compressed(P/'form-D2-delta.npz',indices=ids,local_delta=local[ids].astype(np.float32),world_delta=delta[ids],baseline_selected=d['raw'][ids],selected_world=q,baseline_world=p,key_names=d['key_names'],core_target=targetcore,soft_C=softC,fan_fill=fan_fill,fair_weight=fair)
(P/'form-D2-rest-delta.json').write_text(json.dumps(dict(owner=rest['owner'],baseline_matrix_world=rest['matrix_world'],bones=rest_delta,pose_basis=rest['pose_basis']),indent=2)+'\n',encoding='utf-8')
report=dict(method='Actual rounded Blender section loft + finite pectoral branch web + continuous normalized torso/shoulder/arm transport; paired rest deltas. No hard arm mask, ring-only two-globe fit, volume multiplier, posterior membrane or original-key rewrite.',guide_revision=guide['revision'],guide_sha256=hashlib.sha256((O/'guide-data.json').read_bytes()).hexdigest(),changed_controls=len(ids),rest_bones=len(rest_delta),maximum_move_mm=float(np.linalg.norm(delta,axis=1).max()*1000),maximum_fan_fill_mm=float(abs(fan_fill).max()*1000),head_above_chin_raw_exact=True,Face690_all_delta_zero=True,hips_legs_exact=True,arm_skin_translation_mm=[15,0,-12],neck_join_max_raw_z=float(z[(np.linalg.norm(delta,axis=1)>1e-9)&(z>1.38)&(arm<.01)].max()),pole_control3697=dict(current=p[3697].tolist(),C=np.load(P/'form-C-delta.npz')['selected_world'][3697].tolist(),D=q[3697].tolist()),status='CPU_HYPOTHESIS_ONLY; fresh head/pose/neckROI guard and actual gray/no-shadow/normal/source required')
(P/'form-D2-construction.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('V003_FORM_D2_FIELD_DONE',json.dumps(report),flush=True)
