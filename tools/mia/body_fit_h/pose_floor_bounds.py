"""Whole declared camera-box lower bounds from fixed ellipsoid silhouettes.

Interval arithmetic, not a sampled pose/amplitude grid or a shape solve.
Each fixed primitive is contained in the accumulated union. A certified raw
primitive roof above an observation's upper band obstructs every shared pose.
"""
from pathlib import Path
import sys,math,json,hashlib,importlib.util
import numpy as np
sys.dont_write_bytecode=True
C=Path('D:/MiaWorkCache/mia-reference-work/win-overlay')
A=C/'asset/mia/blender/mia-fit-v003'

def down(x):return float(np.nextafter(x,-np.inf))
def up(x):return float(np.nextafter(x,np.inf))
def iv(x):return (float(x),float(x))
def add(a,b):return down(a[0]+b[0]),up(a[1]+b[1])
def neg(a):return -a[1],-a[0]
def sub(a,b):return add(a,neg(b))
def mul(a,b):
    v=[x*y for x in a for y in b];return down(min(v)),up(max(v))
def div(a,b):
    assert b[0]>0
    return mul(a,(down(1/b[1]),up(1/b[0])))
def sq(a):
    return (0. if a[0]<=0<=a[1] else down(min(a[0]**2,a[1]**2)),up(max(a[0]**2,a[1]**2)))
def root(a):
    assert a[0]>=0
    return down(math.sqrt(a[0])),up(math.sqrt(a[1]))
def trig(a,cosine=False):
    lo,hi=a;values=[math.cos(lo) if cosine else math.sin(lo),math.cos(hi) if cosine else math.sin(hi)]
    offset=0. if cosine else math.pi/2
    for k in range(math.floor((lo-offset)/math.pi)-1,math.ceil((hi-offset)/math.pi)+2):
        t=offset+k*math.pi
        if lo<=t<=hi:values.append((-1.)**k)
    # Explicit libm rounding allowance, separate from source uncertainty.
    return down(min(values)-1e-14),up(max(values)+1e-14)
def dot(a,b):
    out=iv(0.)
    for x,y in zip(a,b):out=add(out,mul(x,y))
    return out
def quadratic(a,Q,b):
    out=iv(0.)
    for i in range(3):
        for j in range(3):out=add(out,mul(mul(a[i],iv(Q[i,j])),b[j]))
    return out

def projected_roof_bound(component,sign,u,yaw,pitch,target=(0.,-.018,.86)):
    th=tuple(math.radians(x) for x in yaw);ph=tuple(math.radians(x) for x in pitch)
    ct,st,cp,sp=trig(th,True),trig(th),trig(ph,True),trig(ph)
    right=[ct,st,iv(0.)];vertical=[neg(mul(st,sp)),mul(ct,sp),cp]
    center=np.array(component['center'],float);center[0]*=sign;delta=[iv(x) for x in center-np.array(target)]
    angle=sign*math.radians(component['angle_y_degrees']);co,si=math.cos(angle),math.sin(angle);R=np.array([[co,0,si],[0,1,0],[-si,0,co]]);Q=R@np.diag(np.square(component['radii']))@R.T
    uc=dot(delta,right);vc=dot(delta,vertical);kuu=quadratic(right,Q,right);kvv=quadratic(vertical,Q,vertical);kuv=quadratic(right,Q,vertical);du=sub(u if isinstance(u,tuple) else iv(u),uc)
    if kuu[0]<=0:return dict(valid_entire_box=False,reason='Unresolved positive projected variance')
    radial=sub(iv(1.),div(sq(du),kuu));conditional=sub(kvv,div(sq(kuv),kuu))
    if radial[0]<=0 or conditional[0]<=0:return dict(valid_entire_box=False,reason='This primitive column is not certified through whole camera box',radial_factor=radial,conditional_variance=conditional)
    roof=add(add(vc,mul(div(kuv,kuu),du)),root(mul(conditional,radial)));roof=add(roof,iv(target[2]))
    # Outward arithmetic above +1micrometre numerical/fixture-encoding margin.
    return dict(valid_entire_box=True,normalized_world_Z_lower=roof[0]-1e-6,normalized_world_Z_upper=roof[1]+1e-6,numerical_margin_m=1e-6,radial_factor_interval=radial,conditional_variance_interval=conditional)

def main():
    path=A/'integration/workspace-storage-20261103/storage_guard.py';spec=importlib.util.spec_from_file_location('H_pose_capacity',path);guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard);capacity=guard.inspect(10*1024*1024)
    if capacity['violations']:raise RuntimeError(json.dumps(capacity))
    p=json.loads((A/'body/shoulder11/parameters.json').read_text(encoding='utf-8'));floor=C/'.mia-cache/body-h/shape/competitor-floor.json';f=json.loads(floor.read_text(encoding='utf-8'));obs=[]
    for record in f['observations']:
        name=record['path'];back=name.startswith('back');axis=935 if back else 239;yaw=[176.,184.] if back else[-4.,4.];pitch=[-6.,6.];u=(record['pixel'][0]-axis)*f['source_registration']['metres_per_pixel'];sigma=record['trace_interval_sigma_m'];u_interval=(u-sigma,u+sigma);target=record['z_world']+sigma;row=dict(path=name,pixel=record['pixel'],panel='back' if back else'front',camera_box_degrees=dict(yaw=yaw,pitch=pitch),source_u_m=u,source_u_trace_interval_m=u_interval,source_upper_Z=target,components={})
        for key in ['upper_arm','anterior_fan','posterior_wall']:
            for sign in [-1,1]:
                b=projected_roof_bound(p[key],sign,u_interval,yaw,pitch)
                if b['valid_entire_box']:b['minimum_excess_over_source_upper_m']=b['normalized_world_Z_lower']-target
                row['components'][key+('_L' if sign<0 else'_R')]=b
        valid=[(k,v) for k,v in row['components'].items() if v['valid_entire_box']]
        witness=max(valid,key=lambda x:x[1]['normalized_world_Z_lower']) if valid else None
        row['certified_union_roof_lower']=None if witness is None else dict(component=witness[0],**witness[1]);obs.append(row)
    failures=[r for r in obs if r['certified_union_roof_lower'] and r['certified_union_roof_lower']['minimum_excess_over_source_upper_m']>0]
    report=dict(status='WHOLE_DECLARED_CAMERA_BOX_AND_2D_TRACE_BOUND_NO_SHAPE_SOLVE',source_floor_sha256=hashlib.sha256(floor.read_bytes()).hexdigest(),camera_model='Orthographic rigid yaw/pitch about frozen target(0,-.018,.86); same original wholeheight uniform registration. No per-point camera, image scale/translation refit or expanded bounds.',trace_uncertainty='Original2px read precision propagated in BOTHsourceu and sourceZ. Independent rectangular bounds conservatively enclose the2px2D trace neighbourhood.',mathematics='Project ellipsoid covarianceQ into camera right/up. At sourceu, roof=vc+Kuv/Kuu*du+sqrt((Kvv-Kuv²/Kuu)*(1-du²/Kuu)). Outward interval arithmetic bounds this expression over ENTIRE panel camera box AND2D trace box. Fixed primitive is contained in every permitted accumulated union, including convex field blends. A positive lower-bound excess therefore rejects every shared pose in the declared box; no pose samples or optimization are used.',bounds_limit='This certifies only the declared camera/trace boxes, not arbitrary unmodeled limb articulation, drawing deformation, or source registration outside its fixed SRT. No uncertainty broadened after seeing residuals.',observation_count=len(obs),certified_conflict_count=len(failures),observations=obs,capacity=capacity,mesh_created=False,GPU_used=False,shape_solve_run=False)
    out=C/'.mia-cache/body-h/shape/fixed-floor-camera-box-2d-trace.json';assert not out.exists();out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print('H_CAMERA_BOX_REPORT',str(out),out.stat().st_size,'certified conflicts',len(failures),flush=True)
    for r in failures:print('CERTIFIED',r['panel'],r['pixel'],r['certified_union_roof_lower']['component'],r['certified_union_roof_lower']['minimum_excess_over_source_upper_m']*1000,'mm',flush=True)

if __name__=='__main__':main()
