"""Static actual evaluated patch contacts and the01-relative normal rotation."""
from pathlib import Path
import json,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent;O=P/'posed-target'

def segment_hit(p,q,tri,eps=1e-9):
    a,b,c=tri;direction=q-p;e1=b-a;e2=c-a;h=np.cross(direction,e2);det=np.dot(e1,h)
    if abs(det)<1e-16:return False
    inv=1/det;s=p-a;u=np.dot(s,h)*inv
    if u<=eps or u>=1-eps:return False
    z=np.cross(s,e1);v=np.dot(direction,z)*inv
    if v<=eps or u+v>=1-eps:return False
    return eps<np.dot(e2,z)*inv<1-eps

def orient(a,b,c):
    u=b-a;v=c-a
    return float(u[0]*v[1]-u[1]*v[0])

def coplanar_overlap(a,b):
    n=np.cross(a[1]-a[0],a[2]-a[0]);length=np.linalg.norm(n)
    if length<1e-14:return False
    n/=length
    if abs(np.dot(b[0]-a[0],n))>1e-8:return False
    nb=np.cross(b[1]-b[0],b[2]-b[0]);nb/=max(np.linalg.norm(nb),1e-30)
    if abs(np.dot(n,nb))<1-1e-8:return False
    axis=int(np.argmax(abs(n)));a=np.delete(a,axis,axis=1);b=np.delete(b,axis,axis=1)
    for aa,ab in zip(a,np.roll(a,-1,axis=0)):
        for ba,bb in zip(b,np.roll(b,-1,axis=0)):
            if orient(aa,ab,ba)*orient(aa,ab,bb)<-1e-18 and orient(ba,bb,aa)*orient(ba,bb,ab)<-1e-18:return True
    for q,t in [(a[0],b),(b[0],a)]:
        values=[orient(x,y,q) for x,y in zip(t,np.roll(t,-1,axis=0))]
        if min(values)>1e-10 or max(values)<-1e-10:return True
    return False

pc=np.array([[-1,0,0],[1,0,0],[0,1,0],[0,.2,-1],[0,.2,1],[.5,.8,0]],float)
positive=any(segment_hit(p,q,pc[3:]) for p,q in zip(pc[:3],np.roll(pc[:3],-1,axis=0))) or any(segment_hit(p,q,pc[:3]) for p,q in zip(pc[3:],np.roll(pc[3:],-1,axis=0)))
assert positive
report=dict(strict_crossing_positive_control=positive)
for role,path in [('baseline4dc1',P/'current-body-limit.npz'),('rejected01',O/'evaluated-01.npz'),('candidate05',O/'evaluated-05.npz')]:
    d=np.load(path);v=d['world'];t=d['triangles'];mi=d['triangle_materials'];cent=v[t].mean(1)
    ids=np.flatnonzero((mi<=1)&(cent[:,2]>1.135)&(cent[:,2]<1.425)&(abs(cent[:,0])<.185)&(cent[:,1]<.035));f=t[ids]
    tree=BVHTree.FromPolygons([Vector(p) for p in v],f.tolist(),all_triangles=True,epsilon=0)
    other=BVHTree.FromPolygons([Vector(p) for p in v],f.tolist(),all_triangles=True,epsilon=0)
    checked=0;hits=[]
    for aa,bb in tree.overlap(other):
        if aa>=bb or set(f[aa]).intersection(f[bb]):continue
        checked+=1;a,b=v[f[aa]],v[f[bb]]
        if any(segment_hit(p,q,b) for p,q in zip(a,np.roll(a,-1,axis=0))) or any(segment_hit(p,q,a) for p,q in zip(b,np.roll(b,-1,axis=0))) or coplanar_overlap(a,b):hits.append([int(ids[aa]),int(ids[bb])])
    report[role]=dict(selected_actual_triangles=len(f),strict_nonadjacent_pairs_tested=checked,strict_intersections=len(hits),first20=hits[:20])

report['limits']='ExpandedSTATICanteriorgeometry only; no ART/motionapproval.'
(O/'contact-05.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('CONTACT05_DONE',json.dumps(report),flush=True)
