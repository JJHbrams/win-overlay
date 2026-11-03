"""Ordered front meridians, including under-bowl return; not a Y(Z) chart."""
from collections import defaultdict, deque
import numpy as np


class Sections:
    def __init__(self, vertices, triangles):
        self.v=np.asarray(vertices,float);self.f=np.asarray(triangles,np.int32)
        e=np.concatenate([self.f[:,[0,1]],self.f[:,[1,2]],self.f[:,[2,0]]])
        self.edges,inv=np.unique(np.sort(e,axis=1),axis=0,return_inverse=True)
        self.face_edges=inv.reshape(3,len(self.f)).T

    def front(self, theta, zlo=1.11, zhi=1.355):
        normal=np.array([np.cos(theta),np.sin(theta),0.])
        outward=np.array([np.sin(theta),-np.cos(theta),0.])
        return self._section(normal,outward,0.,zlo,zhi,theta)

    def front_x(self, x, zlo=1.11, zhi=1.355):
        """Direct Cartesian target chart; no old-cage radial correspondence."""
        return self._section(np.array([1.,0.,0.]),np.array([0.,-1.,0.]),float(x),zlo,zhi,('X',x))

    def _section(self, normal, outward, offset, zlo, zhi, label):
        value=self.v@normal-offset;e=self.edges
        selected=np.flatnonzero(value[e[:,0]]*value[e[:,1]]<0)
        t=value[e[selected,0]]/(value[e[selected,0]]-value[e[selected,1]])
        points=self.v[e[selected,0]]+t[:,None]*(self.v[e[selected,1]]-self.v[e[selected,0]])
        table=np.full(len(e),-1,np.int32);table[selected]=np.arange(len(selected))
        hits=table[self.face_edges];hits=hits[(hits>=0).sum(1)==2]
        nodes=[];lookup={};adj=defaultdict(set)
        def node(p):
            key=tuple(np.round(p,9))
            if key not in lookup:lookup[key]=len(nodes);nodes.append(p)
            return lookup[key]
        for row in hits:
            a,b=points[row[row>=0]];lo,hi=0.,1.;delta=b-a
            for va,vb in [(a[2]-zlo,b[2]-zlo),(zhi-a[2],zhi-b[2]),(a@outward-.005,b@outward-.005)]:
                if va<0 and vb<0:lo,hi=1.,0.;break
                if va<0:lo=max(lo,-va/(vb-va))
                elif vb<0:hi=min(hi,va/(va-vb))
            if hi-lo<1e-9:continue
            i,j=node(a+lo*delta),node(a+hi*delta)
            if i!=j:adj[i].add(j);adj[j].add(i)
        nodes=np.array(nodes);seen=set();paths=[]
        for seed in adj:
            if seed in seen:continue
            comp={seed};queue=deque([seed]);seen.add(seed)
            while queue:
                for j in adj[queue.popleft()]:
                    if j not in seen:seen.add(j);comp.add(j);queue.append(j)
            ends=[i for i in comp if len(adj[i])==1]
            if len(ends)!=2 or any(len(adj[i])>2 for i in comp):continue
            if np.ptp(nodes[list(comp),2]) < .8*(zhi-zlo):continue
            current=max(ends,key=lambda i:nodes[i,2]);old=None;path=[]
            while True:
                path.append(current);nexts=adj[current]-({old} if old is not None else set())
                if not nexts:break
                old,current=current,next(iter(nexts))
                if len(path)>len(comp):raise RuntimeError('Meridian traversal loop')
            pp=nodes[path]
            if pp[0,2]>zhi-.001 and pp[-1,2]<zlo+.001:paths.append(pp)
        assert paths,('No front body section',label)
        curve=min(paths,key=lambda p:np.median(p@outward))
        radius=curve@outward
        candidates=np.flatnonzero((curve[:,2]>1.19)&(curve[:,2]<1.32))
        assert len(candidates)
        pole=int(candidates[np.argmax(radius[candidates])])
        assert 0<pole<len(curve)-1
        def sample(p,count):
            s=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
            assert s[-1]>.01
            return np.column_stack([np.interp(np.linspace(0,s[-1],count),s,p[:,k])for k in range(3)])
        return np.vstack([sample(curve[:pole+1],65)[:-1],sample(curve[pole:],65)])
