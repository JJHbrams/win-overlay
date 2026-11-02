"""Ordered section resampling of a connected anterior surface.

Uncompressed posed-core angle/height provide one shared material parameterization
for original and refined rows. A broad C2 tensor surface replaces their distorted
flow; no isolated pole constraints or per-triangle fade is used.
"""
from pathlib import Path
import json,hashlib
import numpy as np
from field_math import smooth
P=Path(__file__).resolve().parent;O=P/'posed-target'
a=np.load(O/'target-01.npz');m=np.load(P/'inputs/mapping-frame1.npz');raw=np.load(P/'current-body-limit.npz');weights=np.load(P/'current-body-weights.npz');top=np.load(O/'control-topology.npz')
q0=a['q0_world'];q1=a['target_world'];N=len(q1);R=m['matrix_world'][:3,:3]
soft=np.einsum('nij,nj->ni',m['J_world_from_local'],raw['soft_G']@np.linalg.inv(R).T);core=q0-soft
axis_y=-.018;theta=np.arctan2(core[:,0],-(core[:,1]-axis_y));height=core[:,2];arm=weights['arm_sum']
umin,umax=-1.60,1.60;vmin,vmax=1.105,1.425;nu,nv=13,15

def basis(x,n,low,high,degree=3):
    x=np.asarray(x,float);knots=np.r_[np.full(degree+1,low),np.linspace(low,high,n-degree+1)[1:-1],np.full(degree+1,high)];xx=np.clip(x,low,np.nextafter(high,low));B=np.asarray([(xx>=knots[i])&(xx<knots[i+1]) for i in range(len(knots)-1)],float).T
    for p in range(1,degree+1):
        C=np.zeros((len(x),len(knots)-p-1))
        for i in range(C.shape[1]):
            if knots[i+p]>knots[i]:C[:,i]+=(xx-knots[i])/(knots[i+p]-knots[i])*B[:,i]
            if knots[i+p+1]>knots[i+1]:C[:,i]+=(knots[i+p+1]-xx)/(knots[i+p+1]-knots[i+1])*B[:,i+1]
        B=C
    assert B.shape==(len(x),n) and np.max(abs(B.sum(1)-1))<1e-10
    return B

def design(u,v):
    return np.einsum('ni,nj->nij',basis(u,nu,umin,umax),basis(v,nv,vmin,vmax)).reshape(len(u),nu*nv)

tri=top['triangles'];mat=top['triangle_materials'];skintri=tri[(mat<=1)&(tri.max(1)<3957)]
area=np.zeros(N)
for t in skintri:
    p=core[t];area[t]+=np.linalg.norm(np.cross(p[1]-p[0],p[2]-p[0]))/6
training=np.flatnonzero((np.arange(N)<3957)&(abs(theta)<1.60)&(height>vmin)&(height<vmax)&(arm<.55)&(area>0))
seed=q1.copy();mass=np.linalg.norm(raw['soft_G'],axis=1)
broad=smooth((mass-.012)/.045)
restore=np.minimum(q0[:,1]-q1[:,1],0.)*broad
seed[:,1]+=restore
S=design(theta[training],height[training]);w=area[training]*(1-arm[training])**2;w/=np.mean(w)
penalty=[]
for i in range(nu):
    for j in range(1,nv-1):
        r=np.zeros((nu,nv));r[i,j-1:j+2]=[1,-2,1];penalty.append(r.ravel())
for i in range(1,nu-1):
    for j in range(nv):
        r=np.zeros((nu,nv));r[i-1:i+2,j]=[1,-2,1];penalty.append(r.ravel())
D=np.asarray(penalty)
control=np.linalg.solve(S.T@(S*w[:,None])+.020*(D.T@D)+np.eye(nu*nv)*1e-10,S.T@(seed[training]*w[:,None]))
fitted=design(theta,height)@control
gain=smooth((height-vmin)/.045)*smooth((vmax-height)/.035)*smooth((1.60-abs(theta))/.35)*(1-smooth((arm-.20)/.70))
gain[np.arange(N)>=3957]=0;gain[q0[:,2]>=1.425]=0
q=q1+gain[:,None]*(fitted-q1)
q[gain==0]=q1[gain==0]
local=m['q0_local']+(q-q0)@np.linalg.inv(R).T;local[3957:]=m['q0_local'][3957:];local[q0[:,2]>=1.425]=m['q0_local'][q0[:,2]>=1.425]
assert np.array_equal(q[3957:],q0[3957:]) and np.array_equal(q[gain==0],q1[gain==0]) and np.isfinite(local).all()

# Actual continuous fitted-surface derivative audit, separate from final mesh.
ug,vg=np.meshgrid(np.linspace(-1.45,1.45,81),np.linspace(1.15,1.385,101),indexing='ij');ug=ug.ravel();vg=vg.ravel();eps=1e-5
du=(design(ug+eps,vg)@control-design(ug-eps,vg)@control)/(2*eps);dv=(design(ug,vg+eps)@control-design(ug,vg-eps)@control)/(2*eps);normal=np.cross(du,dv);radial=np.column_stack([np.sin(ug),-np.cos(ug),np.zeros(len(ug))]);orient=(normal*radial).sum(1);orient_sign=np.sign(np.median(orient));orient*=orient_sign
report=dict(method='One C2 tensor cubic surface in shared uncompressed posed-core circumferential-angle/ordered-height coordinates, evaluated back at original and refined controls. Smooth C2 boundary transport retains wholebody01 and the open axillary topology.',training_vertices=len(training),spline_control_grid=[nu,nv],parameter_domain=dict(theta=[umin,umax],core_height=[vmin,vmax]),basis_partition_error=float(abs(basis(theta,nu,umin,umax).sum(1)-1).max()),projection_restore='Broad old-baseline profile-depth neighborhood with01 source-supported height/width; no isolated fixed pole points and no oldG Z/volume replay.',maximum_seed_depth_restore_mm=float(-restore.min()*1000),maximum_move_from01_mm=float(np.linalg.norm(q-q1,axis=1).max()*1000),affected_vertices=int((gain>0).sum()),face690_exact=True,head_above1_425_exact=True,body_outside_gain_exact=True,original47_rig_topology_uv_materials_untouched=True,spline_grid_min_dworldZ_dcoreZ=float(dv[:,2].min()),spline_grid_min_oriented_radial_area=float(orient.min()),spline_grid_nonpositive_radial_orientation=int((orient<=0).sum()),baseline01_sha256=hashlib.sha256((O/'target-01.npz').read_bytes()).hexdigest(),status='CPU ordered-surface hypothesis. Final evaluated arcs/normal/source/actual visual judgment required; no anatomy or rig PASS.')
np.savez_compressed(O/'target-03.npz',q0_world=q0,target_world=q,target_local=local,delta_world=q-q0,patch_delta_world=q-q1,parameter_theta=theta,parameter_height=height,patch_gain=gain,spline_control=control.reshape(nu,nv,3),spline_domains=np.array([[umin,umax],[vmin,vmax]]),training_ids=training,seed_profile_restore=restore,control_ids=np.flatnonzero(np.linalg.norm(q-q0,axis=1)>1e-9))
(O/'construction-03.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('POSED_TARGET_03_DATA_DONE',json.dumps(report),flush=True)
