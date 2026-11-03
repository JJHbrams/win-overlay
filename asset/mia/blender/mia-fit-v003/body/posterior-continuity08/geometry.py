"""Small actual-triangle geometry helpers; no scene or filesystem mutation."""
import numpy as np

def normals(v,f):
    face=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]])
    vertex=np.zeros_like(v,dtype=float)
    for j in range(3):np.add.at(vertex,f[:,j],face)
    return face/np.maximum(np.linalg.norm(face,axis=1)[:,None],1e-30),vertex/np.maximum(np.linalg.norm(vertex,axis=1)[:,None],1e-30)

def volume(v,f):
    return float(np.einsum('ij,ij->i',v[f[:,0]],np.cross(v[f[:,1]],v[f[:,2]])).sum()/6)

def line_hits(v,f,axis,fixed):
    """Exact triangle/axis line hits. fixed maps the other two axes to metres."""
    other=[i for i in range(3) if i!=axis];t=v[f].astype(float);a=t[:,0];b=t[:,1]-a;c=t[:,2]-a
    i,j=other;det=b[:,i]*c[:,j]-b[:,j]*c[:,i];di=fixed[i]-a[:,i];dj=fixed[j]-a[:,j]
    u=np.divide(di*c[:,j]-dj*c[:,i],det,out=np.zeros_like(det),where=abs(det)>1e-14)
    w=np.divide(b[:,i]*dj-b[:,j]*di,det,out=np.zeros_like(det),where=abs(det)>1e-14)
    ids=np.flatnonzero((abs(det)>1e-14)&(u>=-1e-8)&(w>=-1e-8)&(u+w<=1+1e-8))
    q=a[ids]+u[ids,None]*b[ids]+w[ids,None]*c[ids]
    n=np.cross(b[ids],c[ids]);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-30)
    order=np.argsort(q[:,axis]);rows=[]
    for k in order:
        if rows and abs(q[k,axis]-rows[-1]['world'][axis])<1e-7:continue
        rows.append({'triangle':int(ids[k]),'world':q[k].tolist(),'normal':n[k].tolist()})
    return rows

def roof(v,f,x,y):
    hits=line_hits(v,f,2,{0:x,1:y})
    hits=[h for h in hits if 1.235<h['world'][2]<1.292 and h['normal'][1]>0 and h['normal'][2]<-.05]
    return max(hits,key=lambda h:h['world'][2]) if hits else None

def triangle_intersects(a,b,epsilon=1e-9):
    """Triangle SAT, including in-plane axes for the coplanar case."""
    ea=np.roll(a,-1,axis=0)-a;eb=np.roll(b,-1,axis=0)-b
    na=np.cross(ea[0],ea[1]);nb=np.cross(eb[0],eb[1])
    axes=[na,nb,*[np.cross(x,y) for x in ea for y in eb],*[np.cross(na,x) for x in ea],*[np.cross(nb,x) for x in eb]]
    for axis in axes:
        ll=np.linalg.norm(axis)
        if ll<1e-15:continue
        axis=axis/ll;aa=a@axis;bb=b@axis
        if aa.max()<bb.min()-epsilon or bb.max()<aa.min()-epsilon:return False
    return True

def changed_intersections(v,f,changed_faces):
    """Every changed triangle versus all triangles; shared-vertex pairs excluded."""
    triangles=v[f].astype(float);lo=triangles.min(1);hi=triangles.max(1);seen=set();hits=[];tested=0
    for i in changed_faces:
        candidates=np.flatnonzero(np.all(hi>=lo[i]-1e-9,axis=1)&np.all(lo<=hi[i]+1e-9,axis=1))
        for j in candidates:
            pair=(min(int(i),int(j)),max(int(i),int(j)))
            if i==j or pair in seen or np.intersect1d(f[i],f[j]).size:continue
            seen.add(pair);tested+=1
            if triangle_intersects(triangles[i],triangles[j]):hits.append(pair)
    return hits,tested
