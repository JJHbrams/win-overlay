"""C2 support-map Jacobian/field scope and actual rail/front measurements."""
from pathlib import Path
import json,hashlib,sys,importlib.util
import numpy as np
P=Path(__file__).resolve().parent;D=P.parent/'D';sys.path.insert(0,str(P));import field
p=json.loads((P/'parameters.json').read_text());c=p['breast']['support_map'];b=np.load(P/'breast-step.npz');d=np.load(D/'sculpt07-D.npz');f,reg=field.make(p);sp=importlib.util.spec_from_file_location('frozenD',D/'field.py');old=importlib.util.module_from_spec(sp);sp.loader.exec_module(old);fd,rd=old.make(json.loads((D/'parameters.json').read_text()))
def sm(t):t=np.clip(t,0,1);return t**3*(10-15*t+6*t*t)
def mapping(q,sign):
    x,y,z=q.T;w=(1-sm((abs(x)-c['x_full'])/(c['x_zero']-c['x_full'])))*(1-sm((y-c['y_full'])/(c['y_zero']-c['y_full'])))*sm((z-c['z0'])/(c['z_full']-c['z0']));r=q.copy();r[:,0]+=sign*c['medial_gather_m']*w;r[:,2]-=w*(z-c['z0'])*(1-1/c['height_scale']);return r,w
points=np.random.default_rng(19).uniform([-.15,-.18,1.18],[.15,.025,1.38],(2048,3));jac=[]
for sign in [-1,1]:
    J=np.empty((len(points),3,3));h=1e-6
    for axis in range(3):
        qq=points.copy();qq[:,axis]+=h;rr=points.copy();rr[:,axis]-=h;J[:,:,axis]=(mapping(qq,sign)[0]-mapping(rr,sign)[0])/(2*h)
    det=np.linalg.det(J);assert det.min()>0;jac.append(dict(sign=sign,min_determinant=float(det.min()),min_singular_value=float(np.linalg.svd(J,compute_uv=False).min())))
w=mapping(points,1)[1];outside=w==0;ev=field.evaluate(f,points[outside]);dv=old.evaluate(fd,points[outside]);assert np.array_equal(ev,dv)
def section(mesh,z):
    xyz=mesh['world'][mesh['triangles']];delta=xyz[:,:,2]-z;xyz=xyz[(delta.min(1)<0)&(delta.max(1)>0)];out=[]
    for aa,bb in [(0,1),(1,2),(2,0)]:
        x,y=xyz[:,aa],xyz[:,bb];ok=(x[:,2]-z)*(y[:,2]-z)<0;x,y=x[ok],y[ok];out.append(x+(y-x)*((z-x[:,2])/(y[:,2]-x[:,2]))[:,None])
    return np.concatenate(out)
def front(mesh,x,z):
    xyz=mesh['world'][mesh['triangles']];dd=xyz[:,:,0]-x;xyz=xyz[(dd.min(1)<0)&(dd.max(1)>0)];seg=[]
    for face in xyz:
        pp=[]
        for aa,bb in [(0,1),(1,2),(2,0)]:
            if (face[aa,0]-x)*(face[bb,0]-x)<0:pp.append(face[aa]+(face[bb]-face[aa])*((x-face[aa,0])/(face[bb,0]-face[aa,0])))
        if len(pp)==2 and (pp[0][2]-z)*(pp[1][2]-z)<=0 and abs(pp[1][2]-pp[0][2])>1e-12:seg.append(pp[0][1]+(pp[1][1]-pp[0][1])*(z-pp[0][2])/(pp[1][2]-pp[0][2]))
    return float(min(seg))
rows=[]
for z in [1.200,1.205,1.215,1.225,1.240,1.2572377274,1.280,1.300,1.320]:
    sections=[]
    for mesh in [d,b]:
        q=section(mesh,z);q=q[(q[:,1]<-.05)&(abs(q[:,0])<.18)];sections.append([float(q[:,0].min()),float(q[:,0].max())])
    rows.append(dict(z=z,D_outer_front_X_interval=sections[0],breast_step_outer_front_X_interval=sections[1],common_plane_front_samples=[dict(x=x,D_y=front(d,x,z),breast_step_y=front(b,x,z)) for x in [0.,.015,.030,.0621,.09,.115]]))
def peak(mesh):
    v=mesh['world'];q=v[(abs(v[:,0])<.12)&(v[:,2]>1.20)&(v[:,2]<1.36)];return q[q[:,1].argmin()].tolist()
r=dict(breast_mesh_sha256=hashlib.sha256((P/'breast-step.npz').read_bytes()).hexdigest(),map_Jacobian_samples_per_side=len(points),map_Jacobian=jac,whole_field_outside_ROI_exact_samples=int(outside.sum()),actual_D_frontmost=peak(d),actual_breast_step_frontmost=peak(b),actual_sections=rows,limits='Inferior anchors/field outsideROI are held. Lower bowl ABOVE1.205 changes, including lateral movement; C2/Jacobian do not guarantee convex visible shape or no knife. Upper source cup width is not a naked root target. Posterior fair checked separately.')
(P/'support-map-audit.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print('E_SUPPORT_MAP_AUDIT',json.dumps({k:v for k,v in r.items() if k!='actual_sections'}),flush=True)
