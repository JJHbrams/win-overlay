"""Unified source-scaffold structural cage + finite pectoral branch transport.
No hard breast/arm cutoff; no sphere/cone or volume multiplier. No scene save.
"""
from pathlib import Path
import json,hashlib
import numpy as np
P=Path(__file__).resolve().parent;O=P/'scaffold-D';d=np.load(P/'current-body-limit.npz');p=d['raw_world'].copy();core=d['core'];soft=d['soft_G'];w=np.load(P/'current-body-weights.npz');names=w['names'].tolist();weights=w['weights'];arm=w['arm_sum'];n=len(p);guide=json.loads((O/'guide-data.json').read_text());actual=json.loads((O/'guide-actual-Blender.json').read_text());assert guide['revision']==2
def smooth(t):t=np.clip(t,0,1);return t*t*(3-2*t)
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
cyq=np.interp(z,heights,cy);theta=np.arctan2(coreC[:,0]-center,-(coreC[:,1]-cyq));targets=[]
for st in stations:
    pts=np.asarray(next(q for q in actual['curves'] if q['name'].endswith('core.section.'+str(st['id']).zfill(2)))['points'])[:-1];cc=(st['front_core_y']+st['back_y'])/2;ang=np.arctan2(pts[:,0],-(pts[:,1]-cc));order=np.argsort(ang);aa=ang[order];pp=pts[order];aa=np.r_[aa[-1]-2*np.pi,aa,aa[0]+2*np.pi];pp=np.vstack([pp[-1],pp,pp[0]]);targets.append(np.column_stack([np.interp(theta,aa,pp[:,axis]) for axis in [0,1]]))
targets=np.asarray(targets);hi=np.clip(np.searchsorted(heights,z),1,len(heights)-1);lo=hi-1;blend=np.clip((z-heights[lo])/(heights[hi]-heights[lo]),0,1);ix=np.arange(n);targetxy=targets[lo,ix]*(1-blend[:,None])+targets[hi,ix]*blend[:,None];targetcore=coreC.copy();strength=smooth((z-1.145)/.055)*smooth((1.415-z)/.060);targetcore[:,:2]+=strength[:,None]*(targetxy-coreC[:,:2])
# Finite pectoral fan web supplies the rounded front-plane/root-to-arm branch.
# It is not the posterior fold corridor, which must remain OPEN.
fan_y=np.full(n,np.nan);fan_margin=np.zeros(n)
for mesh in actual['meshes']:
    if 'anterior_fan_web' not in mesh['name']:continue
    vv=np.asarray(mesh['vertices'])
    for face in mesh['faces']:
        for tri in [(face[0],face[1],face[2]),(face[0],face[2],face[3])]:
            a,b,c=vv[list(tri)];mat=np.column_stack([(b-a)[[0,2]],(c-a)[[0,2]]]);det=np.linalg.det(mat)
            if abs(det)<1e-10:continue
            uv=(coreC[:,[0,2]]-a[[0,2]])@np.linalg.inv(mat).T;u,vv0=uv.T;bary=np.column_stack([1-u-vv0,u,vv0]);inside=(bary.min(1)>=0);yy=bary@np.array([a[1],b[1],c[1]]);facing=smooth((-coreC[:,1]-.004)/.025);margin=smooth(bary.min(1)/.12)*facing
            for j in np.flatnonzero(inside):
                if not np.isfinite(fan_y[j]) or yy[j]<fan_y[j]:fan_y[j]=yy[j];fan_margin[j]=margin[j]
valid=np.isfinite(fan_y);fan_fill=np.zeros(n);fan_fill[valid]=np.minimum(fan_y[valid]-targetcore[valid,1],0)*fan_margin[valid];targetcore[:,1]+=fan_fill
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
support=targetcore+softC;torsoW=np.clip(1-arm-shoulderSum,0,1);q=p+(support-p)*torsoW[:,None]+armT+shoulderT
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
np.savez_compressed(P/'form-D-delta.npz',indices=ids,local_delta=local[ids].astype(np.float32),world_delta=delta[ids],baseline_selected=d['raw'][ids],selected_world=q,baseline_world=p,key_names=d['key_names'],core_target=targetcore,soft_C=softC,fan_fill=fan_fill,fair_weight=fair)
(P/'form-D-rest-delta.json').write_text(json.dumps(dict(owner=rest['owner'],baseline_matrix_world=rest['matrix_world'],bones=rest_delta,pose_basis=rest['pose_basis']),indent=2)+'\n',encoding='utf-8')
report=dict(method='Actual rounded Blender section loft + finite pectoral branch web + continuous normalized torso/shoulder/arm transport; paired rest deltas. No hard arm mask, ring-only two-globe fit, volume multiplier, posterior membrane or original-key rewrite.',guide_revision=guide['revision'],guide_sha256=hashlib.sha256((O/'guide-data.json').read_bytes()).hexdigest(),changed_controls=len(ids),rest_bones=len(rest_delta),maximum_move_mm=float(np.linalg.norm(delta,axis=1).max()*1000),maximum_fan_fill_mm=float(abs(fan_fill).max()*1000),head_above_chin_raw_exact=True,Face690_all_delta_zero=True,hips_legs_exact=True,arm_skin_translation_mm=[15,0,-12],neck_join_max_raw_z=float(z[(np.linalg.norm(delta,axis=1)>1e-9)&(z>1.38)&(arm<.01)].max()),pole_control3697=dict(current=p[3697].tolist(),C=np.load(P/'form-C-delta.npz')['selected_world'][3697].tolist(),D=q[3697].tolist()),status='CPU_HYPOTHESIS_ONLY; fresh head/pose/neckROI guard and actual gray/no-shadow/normal/source required')
(P/'form-D-construction.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('V003_FORM_D_FIELD_DONE',json.dumps(report),flush=True)
