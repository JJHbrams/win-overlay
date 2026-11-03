"""Small C1 authoring curves with connected-local-surface projection.

No mesh coordinates, UVs, images or native scenes are edited. C1 describes the
authoring interpolant; its densely projected samples follow a polyhedral mesh
and are not falsely advertised as an exact analytic C1 surface curve.
"""
import numpy as np


def cubic_shape_preserving(x, y, samples):
    x,y,t=map(lambda a:np.asarray(a,float),[x,y,samples])
    scalar=y.ndim==1
    if scalar:y=y[:,None]
    h=np.diff(x)
    if len(x)<2 or np.any(h<=0):raise ValueError('Strict increasing curve parameter required')
    d=np.diff(y,axis=0)/h[:,None];m=np.zeros_like(y)
    if len(x)==2:m[:]=d[0]
    else:
        for i in range(1,len(x)-1):
            same=d[i-1]*d[i]>0;w1=2*h[i]+h[i-1];w2=h[i]+2*h[i-1]
            m[i,same]=(w1+w2)/(w1/d[i-1,same]+w2/d[i,same])
        for i,j,k in [(0,0,1),(-1,-1,-2)]:
            a=((2*h[j]+h[k])*d[j]-h[j]*d[k])/(h[j]+h[k])
            a=np.where(a*d[j]<=0,0,a)
            a=np.where((d[j]*d[k]<0)&(abs(a)>3*abs(d[j])),3*d[j],a)
            m[i]=a
    t=np.clip(t,x[0],x[-1]);i=np.minimum(np.searchsorted(x,t,side='right')-1,len(x)-2)
    u=((t-x[i])/h[i])[:,None];hh=h[i,None]
    result=(2*u**3-3*u**2+1)*y[i]+(u**3-2*u**2+u)*hh*m[i]+(-2*u**3+3*u**2)*y[i+1]+(u**3-u**2)*hh*m[i+1]
    return result[:,0] if scalar else result


def source_curve_c1(points, maximum_step=.35):
    points=np.asarray(points,float)
    arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
    parameter=np.unique(np.r_[np.linspace(0,arc[-1],max(2,int(np.ceil(arc[-1]/maximum_step))+1)),arc])
    return cubic_shape_preserving(arc,points,parameter)


def closest_local(point, triangles):
    """Exact closest point/barycentric among supplied local connected facets."""
    p=np.asarray(point,float);v=np.asarray(triangles,float)
    a,b,c=v[:,0],v[:,1],v[:,2];ab,ac=b-a,c-a;ap=p-a
    aa=np.einsum('ij,ij->i',ab,ab);bb=np.einsum('ij,ij->i',ab,ac);cc=np.einsum('ij,ij->i',ac,ac)
    pa=np.einsum('ij,ij->i',ap,ab);pc=np.einsum('ij,ij->i',ap,ac);den=aa*cc-bb*bb
    u=np.divide(cc*pa-bb*pc,den,out=np.zeros_like(den),where=abs(den)>1e-28)
    w=np.divide(aa*pc-bb*pa,den,out=np.zeros_like(den),where=abs(den)>1e-28)
    bary=np.column_stack((1-u-w,u,w));inside=(bary>=0).all(1)&(abs(den)>1e-28)
    best=np.full(len(v),np.inf);weights=np.zeros_like(bary)
    if inside.any():
        q=np.einsum('ij,ijk->ik',bary[inside],v[inside]);best[inside]=np.sum((q-p)**2,axis=1);weights[inside]=bary[inside]
    for i,j in [(0,1),(1,2),(2,0)]:
        edge=v[:,j]-v[:,i];d=np.einsum('ij,ij->i',edge,edge)
        t=np.clip(np.divide(np.einsum('ij,ij->i',p-v[:,i],edge),d,out=np.zeros_like(d),where=d>1e-30),0,1)
        q=v[:,i]+t[:,None]*edge;dist=np.sum((q-p)**2,axis=1);take=dist<best
        best[take]=dist[take];weights[take]=0;weights[take,i]=1-t[take];weights[take,j]=t[take]
    k=int(np.argmin(best));return k,weights[k]@v[k],weights[k],float(np.sqrt(best[k]))


def fair_surface_strap(surface, allowed_faces, vertex_ids, anchors, width_m):
    world,faces=surface['world'],surface['triangles'];ids=np.asarray(vertex_ids,int)
    raw=np.vstack((anchors[0]['world'],world[ids],anchors[1]['world'])).astype(float)
    raw_ids=np.r_[ids[0],ids,ids[-1]]
    keep=np.r_[True,np.linalg.norm(np.diff(raw,axis=0),axis=1)>1e-10];raw,raw_ids=raw[keep],raw_ids[keep]
    arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(raw,axis=0),axis=1))]
    uniform=np.linspace(0,arc[-1],max(3,int(np.ceil(arc[-1]/.001))+1))
    original=np.column_stack([np.interp(uniform,arc,raw[:,j]) for j in range(3)])
    sigma=.3*width_m;kernel=np.exp(-.5*((uniform[:,None]-uniform[None,:])/sigma)**2);kernel/=kernel.sum(1)[:,None]
    smooth=kernel@original;t=uniform/uniform[-1]
    smooth-=(1-t)[:,None]*(smooth[0]-raw[0])+t[:,None]*(smooth[-1]-raw[-1])
    dense=np.linspace(0,arc[-1],max(3,int(np.ceil(arc[-1]/.0005))+1))
    curve=cubic_shape_preserving(uniform,smooth,dense)
    adjacency={}
    for fi in np.flatnonzero(allowed_faces):
        for vi in faces[fi]:adjacency.setdefault(int(vi),[]).append(int(fi))
    projected=[];bound=[];offset=[]
    for i,(parameter,point) in enumerate(zip(dense,curve)):
        if i==0 or i==len(dense)-1:
            anchor=anchors[0 if i==0 else 1];projected.append(anchor['world']);bound.append(dict(triangle_id=anchor['triangle_id'],barycentric=anchor['barycentric']));offset.append(float(np.linalg.norm(point-np.asarray(anchor['world']))));continue
        j=min(max(int(np.searchsorted(arc,parameter)-1),0),len(raw)-1)
        local=set()
        for vi in raw_ids[max(0,j-2):min(len(raw_ids),j+4)]:local.update(adjacency.get(int(vi),[]))
        neighbours=np.unique(faces[list(local)])
        for vi in neighbours:local.update(adjacency.get(int(vi),[]))
        candidates=np.array(sorted(local),int)
        if not len(candidates):raise ValueError('No semantic connected-local strap patch')
        k,q,b,d=closest_local(point,world[faces[candidates]])
        projected.append(q.tolist());bound.append(dict(triangle_id=int(candidates[k]),barycentric=b.tolist()));offset.append(d)
    projected=np.asarray(projected)
    if max(offset)>width_m/3:raise ValueError('Fair strap left its connected local surface patch')
    reference=np.column_stack([np.interp(dense,arc,raw[:,j]) for j in range(3)])
    displacement=np.linalg.norm(projected-reference,axis=1)
    if displacement.max()>width_m/2:raise ValueError('Fair strap deviates too far from source route')
    return dict(world=projected.tolist(),bindings=bound,width_m=float(width_m),
                authoring_sigma_m=float(sigma),sample_spacing_m=float(arc[-1]/(len(dense)-1)),
                maximum_local_projection_m=float(max(offset)),maximum_route_delta_m=float(displacement.max()),
                exact_source_anchor_endpoints=True,geometry_UV_unchanged=True,
                method='Endpoint-preserved arc Gaussian +C1 shape-preserving author curve; dense projection ONLY into connected semantic vertex-star patches of original route.',
                continuity_limit='C1 authoring interpolant before dense projection; no exact analytic C1 claim on a polyhedral surface.')
