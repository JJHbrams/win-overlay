"""Check camera covariance/tangency against actual frozen primitive fields.

Deterministic mathematical verification; no source fit, shape trials or mesh.
The interval proof is analytic; random samples only catch implementation bugs.
"""
from pathlib import Path
import sys,json,math,hashlib,importlib.util
import numpy as np
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pose_floor_bounds as bounds
from competitor_floor import primitive_projected_top
C=bounds.C;A=bounds.A

def main():
    path=A/'integration/workspace-storage-20261103/storage_guard.py';spec=importlib.util.spec_from_file_location('H_math_capacity',path);guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
    receipt=guard.inspect(10*1024*1024)
    if receipt['violations']:raise RuntimeError(json.dumps(receipt))
    path=A/'body/shoulder11/field.py';spec=importlib.util.spec_from_file_location('H_math_frozen11',path);f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f);p=json.loads((path.parent/'parameters.json').read_text(encoding='utf-8'));_,reg=f.base.make(p)
    raw=C/'.mia-cache/body-h/shape/fixed-floor-camera-box-2d-trace.json';report=json.loads(raw.read_text(encoding='utf-8'));rng=np.random.default_rng(20261103);maxfield=0.;maxtangent=0.;samples=0;enclosure_checks=0
    for record in report['observations']:
        if record['pixel'] not in [[323,235],[328,238],[865,226]]:continue
        box=record['camera_box_degrees'];u0,u1=record['source_u_trace_interval_m'];component=p['anterior_fan'];sign=1;center=np.array(component['center'],float);angle=math.radians(component['angle_y_degrees']);co,si=math.cos(angle),math.sin(angle);R=np.array([[co,0,si],[0,1,0],[-si,0,co]]);Q=R@np.diag(np.square(component['radii']))@R.T;target=np.array([0.,-.018,.86]);bound=record['components']['anterior_fan_R'];assert bound['valid_entire_box']
        for _ in range(256):
            yaw,pitch=np.radians([rng.uniform(*box['yaw']),rng.uniform(*box['pitch'])]);u=rng.uniform(u0,u1);ct,st,cp,sp=np.cos(yaw),np.sin(yaw),np.cos(pitch),np.sin(pitch);right=np.array([ct,st,0.]);vertical=np.array([-st*sp,ct*sp,cp]);depth=np.cross(right,vertical);U=np.stack([right,vertical]);K=U@Q@U.T;c=U@(center-target);du=u-c[0];h=1-du*du/K[0,0];assert h>0;v=c[1]+K[0,1]/K[0,0]*du+np.sqrt((K[1,1]-K[0,1]**2/K[0,0])*h);z=v+target[2]
            assert bound['normalized_world_Z_lower']<=z<=bound['normalized_world_Z_upper'];enclosure_checks+=1
            # Minimum-norm lifted ellipse boundary is on the3D ellipsoid and
            # tangent to the viewing depth. Verify actual frozen expression.
            residual=np.array([u,v])-c;point=center+Q@U.T@np.linalg.solve(K,residual);value=float(f.evaluate(reg['anterior_fan_R'],point[None,:])[0]);normal=np.linalg.solve(Q,point-center);tangent=abs(float(normal@depth))/np.linalg.norm(normal);maxfield=max(maxfield,abs(value));maxtangent=max(maxtangent,tangent);samples+=1
    assert maxfield<1e-10 and maxtangent<1e-10
    # Independent fixed-X formula check at nominal roof witnesses.
    for key in ['upper_arm','anterior_fan','posterior_wall']:
        for x in [.155053125,.16428247767857146]:
            z=primitive_projected_top(p[key],x)
            if z is not None:assert abs(float(f.evaluate(reg[key+'_R'],np.array([[x,p[key]['center'][1],z]]))[0]))<1e-10
    assert not bounds.projected_roof_bound(p['anterior_fan'],1,(.34,.35),[-4,4],[-6,6])['valid_entire_box']
    result=dict(status='MATH_IMPLEMENTATION_CHECK_PASS_NOT_ART',projected_ellipse_samples=samples,interval_enclosure_checks=enclosure_checks,maximum_actual_frozen_field_absolute_residual=maxfield,maximum_normal_dot_view_depth=maxtangent,negative_outside_column_refused=True,meaning='Checks covariance signs, orthographic camera basis, analytic lift and exact frozen field. Sampling is only implementation QA; whole-box certificate comes from interval arithmetic.',source_interval_report_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),actual_C_E_field_sha256=hashlib.sha256(Path(f.base.__file__).read_bytes()).hexdigest(),actual_C_base_field_sha256=hashlib.sha256(Path(f.base.base.__file__).read_bytes()).hexdigest(),mesh_created=False,shape_optimization_run=False,GPU_used=False)
    out=C/'.mia-cache/body-h/shape/floor-math-verification.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(result),flush=True)

if __name__=='__main__':main()
