"""Private static surface clipping/ordered loops/tangent-aware collars. CPU."""
import numpy as np

class Mesh:
    def __init__(self,world,weights,normals):
        self.xyz=list(np.asarray(world,float));self.weights=list(np.asarray(weights,float));self.normals=list(np.asarray(normals,float));self.cache={}
        self.faces=[];self.attrs=[];self.material=[];self.part=[];self.sourceface=[];self.inherited_boundary=set();self.inherited_nonmanifold={}
    def sign(self,vid,plane):
        name,n,c,weight=plane
        return (self.weights[vid][weight]-c) if weight is not None else np.dot(self.xyz[vid],n)+c
    def intersection(self,a,b,plane,da,db):
        ia,aa=a;ib,ab=b;t=da/(da-db);key=(plane[0],min(ia,ib),max(ia,ib))
        if key not in self.cache:
            if ia<ib:i,j,tt=ia,ib,t
            else:i,j,tt=ib,ia,1-t
            self.cache[key]=len(self.xyz);self.xyz.append(self.xyz[i]+tt*(self.xyz[j]-self.xyz[i]));self.weights.append(self.weights[i]+tt*(self.weights[j]-self.weights[i]));nn=self.normals[i]+tt*(self.normals[j]-self.normals[i]);self.normals.append(nn/max(np.linalg.norm(nn),1e-20))
        return self.cache[key],aa+t*(ab-aa)
    def add(self,face,attrs,mat,part,source):
        if len(set(face))<3:return
        self.faces.append(face);self.attrs.append(attrs);self.material.append(mat);self.part.append(part);self.sourceface.append(source)
    def clipped(self,faces,attrs,mats,part,planes,source_offset=0):
        # Fast retain/reject before processing the narrow actual cut bands.
        q=np.array(self.xyz);ww=np.array(self.weights);inside=np.ones(len(faces),bool);outside=np.zeros(len(faces),bool)
        for name,n,c,w in planes:
            vals=ww[faces,w]-c if w is not None else q[faces]@n+c
            inside&=(vals>=-1e-12).all(1);outside|=(vals<-1e-12).all(1)
        for fi in np.flatnonzero(inside):self.add(faces[fi].tolist(),attrs[fi].copy(),int(mats[fi]),part,int(fi+source_offset))
        for fi in np.flatnonzero(~inside&~outside):
            poly=[(int(i),a.copy()) for i,a in zip(faces[fi],attrs[fi])]
            for plane in planes:
                output=[]
                for j,a in enumerate(poly):
                    b=poly[(j+1)%len(poly)];da=self.sign(a[0],plane);db=self.sign(b[0],plane);ina=da>=-1e-12;inb=db>=-1e-12
                    if ina:output.append(a)
                    if ina!=inb:output.append(self.intersection(a,b,plane,da,db))
                poly=output
                if len(poly)<3:break
            for j in range(1,len(poly)-1):self.add([poly[0][0],poly[j][0],poly[j+1][0]],np.array([poly[0][1],poly[j][1],poly[j+1][1]]),int(mats[fi]),part,int(fi+source_offset))
    def boundary_loops(self):
        f=np.asarray(self.faces,np.int32);edges=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1);ee,counts=np.unique(edges,axis=0,return_counts=True)
        bad=[(tuple(map(int,e)),int(c)) for e,c in zip(ee[counts>2],counts[counts>2]) if self.inherited_nonmanifold.get(tuple(map(int,e)))!=c];assert not bad,('NEWnonmanifold',bad[:10])
        boundary=ee[counts==1];boundary=np.asarray([e for e in boundary if tuple(map(int,e)) not in self.inherited_boundary],np.int32).reshape(-1,2);adj={}
        for a,b in boundary:adj.setdefault(int(a),[]).append(int(b));adj.setdefault(int(b),[]).append(int(a))
        bad={k:v for k,v in adj.items() if len(v)!=2};assert not bad,('branched openboundary',list(bad.items())[:10])
        seen=set();loops=[]
        for seed in adj:
            if seed in seen:continue
            loop=[];old=None;cur=seed
            while cur not in seen:
                seen.add(cur);loop.append(cur);nxt=adj[cur][0] if adj[cur][0]!=old else adj[cur][1];old,cur=cur,nxt
            assert cur==seed;loops.append(loop)
        return loops,boundary
    def ordered(self,loop,axis):
        points=np.array([self.xyz[i] for i in loop]);center=points.mean(0);axis=np.asarray(axis,float);axis/=np.linalg.norm(axis)
        u=np.array([1.,0,0]) if abs(axis[2])>.99 else np.array([0.,1,0]);v=np.cross(axis,u);v/=np.linalg.norm(v);u=np.cross(v,axis)
        theta=np.mod(np.arctan2((points-center)@v,(points-center)@u),2*np.pi);order=np.argsort(theta);ids=np.asarray(loop)[order];ang=theta[order]
        oldedges={tuple(sorted((loop[i],loop[(i+1)%len(loop)]))) for i in range(len(loop))};newedges={tuple(sorted((int(ids[i]),int(ids[(i+1)%len(ids)])))) for i in range(len(ids))}
        assert oldedges==newedges,'Boundary not star-shaped in declaredlimb/neck/waist plane'
        return ids,ang,center,u,v,axis
    def resample(self,ordered,angles):
        ids,theta,*_=ordered;tt=np.r_[theta[-1]-2*np.pi,theta,theta[0]+2*np.pi];ii=np.r_[ids[-1],ids,ids[0]];j=np.searchsorted(tt,angles,side='right')-1;t=(angles-tt[j])/(tt[j+1]-tt[j]);a=np.array(self.xyz)[ii[j]];b=np.array(self.xyz)[ii[j+1]];q=a+t[:,None]*(b-a)
        n=np.array(self.normals)[ii[j]]+t[:,None]*(np.array(self.normals)[ii[j+1]]-np.array(self.normals)[ii[j]]);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-20)
        return q,n
    def oriented(self,face,center,axis,mat,part):
        q=np.array([self.xyz[i] for i in face]);r=q.mean(0)-center;r-=axis*np.dot(r,axis);n=np.cross(q[1]-q[0],q[2]-q[0])
        if np.dot(n,r)<0:face=[face[0],face[2],face[1]]
        attrs=np.zeros((3,12),float);self.add(face,attrs,mat,part,-1)
    def zipper(self,idsA,angA,idsB,angB,center,axis,mat,part):
        na,nb=len(idsA),len(idsB);i=j=0
        while i<na or j<nb:
            ai=int(idsA[i%na]);bj=int(idsB[j%nb]);aNext=angA[(i+1)%na]+2*np.pi*((i+1)//na) if i<na else np.inf;bNext=angB[(j+1)%nb]+2*np.pi*((j+1)//nb) if j<nb else np.inf
            if aNext<=bNext:
                self.oriented([ai,int(idsA[(i+1)%na]),bj],center,axis,mat,part);i+=1
            else:self.oriented([ai,int(idsB[(j+1)%nb]),bj],center,axis,mat,part);j+=1
    def collar(self,loop0,loop1,axis,mat,part,bands=12,section_provider=None,discrete_provider=None):
        a=self.ordered(loop0,axis);b=self.ordered(loop1,axis);N=int(np.ceil(max(len(loop0),len(loop1),96)/8)*8);angles=np.arange(N)*2*np.pi/N
        p0,n0=self.resample(a,angles);p1,n1=self.resample(b,angles);d=p1-p0;t0=d-n0*(d*n0).sum(1)[:,None];t1=d-n1*(d*n1).sum(1)[:,None]
        geometric=None
        if section_provider is not None:
            inner0,inner1,geometric=section_provider(a,b,angles)
            # CubicBezier handles equal ONE measured adjacentsection chord.
            # Direction is actualgeometricG1; do not claim parameterC1 continuity.
            t0=3.*(p0-inner0);t1=3.*(inner1-p1)
        discrete_rows=None
        if discrete_provider is not None:
            discrete_rows,geometric=discrete_provider(a,b,angles,p0,p1,bands)
        rowids=[]
        oldIds,oldAng=a[0],a[1];axis=a[-1];center=(a[2]+b[2])*.5
        for k in range(1,bands):
            t=k/bands;q=discrete_rows[k] if discrete_rows is not None else (2*t**3-3*t*t+1)*p0+(t**3-2*t*t+t)*t0+(-2*t**3+3*t*t)*p1+(t**3-t*t)*t1
            ids=np.arange(len(self.xyz),len(self.xyz)+N);self.xyz.extend(q);self.weights.extend(np.zeros((N,4)));nn=(1-t)*n0+t*n1;nn/=np.maximum(np.linalg.norm(nn,axis=1)[:,None],1e-20);self.normals.extend(nn)
            self.zipper(oldIds,oldAng,ids,angles,center,axis,mat,part);oldIds,oldAng=ids,angles;rowids.append(ids.tolist())
        self.zipper(oldIds,oldAng,b[0],b[1],center,axis,mat,part)
        return dict(first_loop=len(loop0),second_loop=len(loop1),resample_count=N,bands=bands,bounds=[np.minimum(p0.min(0),p1.min(0)).tolist(),np.maximum(p0.max(0),p1.max(0)).tolist()],row_vertex_ids=rowids,geometric_section_tangents=geometric)

def minimum_bending_rows(p0,p1,inside0,inside1,bands,axis,*,fixed_end_rows=1,angular_sigma=None):
    """One discrete solve, with two finite endpoint secants from actual sections.

    Neighbor sections are one and two *collar row spacings* inside each retained
    surface. A quadratic through those observations supplies the first exterior
    row. All remaining rows minimize the sum of squared second
    differences. This is a finite-row constraint, not an analytic C1 claim.
    """
    assert bands>=8
    q=np.zeros((bands+1,)+p0.shape,float);q[0]=p0;q[-1]=p1
    i01,i02=inside0;i11,i12=inside1
    q[1]=3*p0-3*i01+i02;q[2]=6*p0-8*i01+3*i02
    q[-2]=3*p1-3*i11+i12;q[-3]=6*p1-8*i11+3*i12
    smoothing=None
    if angular_sigma is not None:
        def smooth_displacement(points,delta,sigma):
            lengths=np.linalg.norm(np.roll(points,-1,axis=0)-points,axis=1);arc=np.r_[0,np.cumsum(lengths[:-1])];perimeter=lengths.sum()
            distance=abs(arc[:,None]-arc[None,:]);distance=np.minimum(distance,perimeter-distance)
            weight=np.exp(-.5*(distance/sigma)**2);weight[distance>3*sigma]=0;weight/=weight.sum(1)[:,None]
            return weight@delta
        before0=q[1]-p0;before1=p1-q[-2]
        after0=smooth_displacement(p0,before0,angular_sigma);after1=smooth_displacement(p1,before1,angular_sigma)
        q[1]=p0+after0;q[-2]=p1-after1
        smoothing=dict(field='ONLY Q1-P0 and Pm-Qm-1 derivative/displacement, not absolute ring coordinates',sigma_m=angular_sigma,kernel='Gaussian actual periodic physical ring-arc distance; truncated at3sigma',maximum_displacement_field_change_m=float(max(np.linalg.norm(after0-before0,axis=1).max(),np.linalg.norm(after1-before1,axis=1).max())))
    assert fixed_end_rows in (1,2)
    fixed=np.array([0,1,bands-1,bands] if fixed_end_rows==1 else [0,1,2,bands-2,bands-1,bands]);free=np.setdiff1d(np.arange(bands+1),fixed)
    D=np.zeros((bands-1,bands+1))
    for j in range(bands-1):D[j,j:j+3]=[1,-2,1]
    A=D[:,free];rhs=-D[:,fixed]@q[fixed].reshape(len(fixed),-1)
    q[free]=np.linalg.solve(A.T@A,A.T@rhs).reshape((len(free),)+p0.shape)
    # Rows remain on equally spaced physical planes, preventing axial bunching.
    axis=np.asarray(axis,float);axis/=np.linalg.norm(axis)
    for k in range(1,bands):
        target=((1-k/bands)*p0+(k/bands)*p1)@axis
        q[k]+=(target-q[k]@axis)[:,None]*axis
    return q,dict(method='One constrained minimum discrete bending solve; no handle/grid sweep',fixed_rows=fixed.tolist(),free_rows=free.tolist(),objective='sum squared physical row second differences',endpoint_rule='Quadratic extrapolation of endpoint plus actual retained sections at one/two collar physical row spacings',angular_regularization=smoothing,continuity='Actual finite-row secants audited separately; no analytic or discrete C1 guarantee')

class SectionSource:
    """Actual triangle/plane contours, sampled in endpoint's geometricframe."""
    def __init__(self,v,f):
        self.v=np.asarray(v,float);self.f=f
        edges=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);self.edges,inv=np.unique(np.sort(edges,axis=1),axis=0,return_inverse=True);self.face_edges=inv.reshape(3,len(f)).T
    def row_step(self,frame):
        ids,theta,c,u,w,axis=frame;v=self.v;e=self.edges;mid=v[e].mean(1);radius=max(np.linalg.norm(vv-c) for vv in [np.asarray(c)+.03*u])
        step=abs((v[e[:,1]]-v[e[:,0]])@axis);near=(abs((mid-c)@axis)<.006)&(np.linalg.norm(mid-c,axis=1)<.18)&(step>1e-5)&(step<.01)
        return float(np.clip(np.median(step[near]),.001,.003))
    def loop_points(self,frame,delta):
        ids,theta,center,u,w,axis=frame;origin=center+delta*axis;value=(self.v-origin)@axis;e=self.edges;cross=(value[e[:,0]]*value[e[:,1]]<0);eid=np.flatnonzero(cross);t=value[e[eid,0]]/(value[e[eid,0]]-value[e[eid,1]]);points=self.v[e[eid,0]]+t[:,None]*(self.v[e[eid,1]]-self.v[e[eid,0]])
        table=np.full(len(e),-1,np.int32);table[eid]=np.arange(len(eid));facehits=table[self.face_edges];adj={}
        for row in facehits[(facehits>=0).sum(1)==2]:
            a,b=row[row>=0];adj.setdefault(int(a),[]).append(int(b));adj.setdefault(int(b),[]).append(int(a))
        seen=set();loops=[]
        for seed in adj:
            if seed in seen:continue
            cur=seed;old=None;loop=[]
            while cur not in seen:
                seen.add(cur);loop.append(cur);nexts=adj[cur]
                if len(nexts)!=2:break
                nxt=nexts[0] if nexts[0]!=old else nexts[1];old,cur=cur,nxt
            if cur==seed and len(loop)>5:loops.append(loop)
        assert loops,'Noactualadjacentsectionloop'
        loop=min(loops,key=lambda ids:np.linalg.norm(points[ids].mean(0)-origin));return points[loop]
    def sample(self,frame,delta,angles):
        ids,theta,center,u,w,axis=frame;origin=center+delta*axis;q=self.loop_points(frame,delta)
        ang=np.mod(np.arctan2((q-origin)@w,(q-origin)@u),2*np.pi);order=np.argsort(ang);diff=(np.roll(order,-1)-order)%len(order)
        assert np.all(diff==1) or np.all(diff==len(order)-1),'Adjacent source section not star-shaped around endpoint-follow frame; do not invent ray order'
        ang=ang[order];q=q[order];tt=np.r_[ang[-1]-2*np.pi,ang,ang[0]+2*np.pi];qq=np.vstack([q[-1],q,q[0]]);j=np.searchsorted(tt,angles,side='right')-1;s=(angles-tt[j])/(tt[j+1]-tt[j]);return qq[j]+s[:,None]*(qq[j+1]-qq[j])
