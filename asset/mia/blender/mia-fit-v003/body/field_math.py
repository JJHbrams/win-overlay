"""Pure C2 section interpolation; no scene/data IO. D2 architecture correction."""
import numpy as np

def smooth(t):
    t=np.clip(t,0,1);return t*t*t*(t*(6*t-15)+10)

def cubic_z(nodes,values,query):
    """Natural C2 cubic; linear endpoint continuation retains C2 continuity."""
    nodes=np.asarray(nodes);values=np.asarray(values);query=np.asarray(query);h=np.diff(nodes);N=len(nodes);A=np.zeros((N,N));rhs=np.zeros_like(values);A[0,0]=A[-1,-1]=1
    for i in range(1,N-1):A[i,i-1]=h[i-1];A[i,i]=2*(h[i-1]+h[i]);A[i,i+1]=h[i];rhs[i]=6*((values[i+1]-values[i])/h[i]-(values[i]-values[i-1])/h[i-1])
    M=np.linalg.solve(A,rhs.reshape(N,-1)).reshape(values.shape);ii=np.clip(np.searchsorted(nodes,query),1,N-1);jj=ii-1;ix=np.arange(len(query));q=np.clip(query,nodes[0],nodes[-1]);hh=nodes[ii]-nodes[jj];aa=(nodes[ii]-q)/hh;bb=(q-nodes[jj])/hh
    shape=(len(query),)+(1,)*(values.ndim-2);aa=aa.reshape(shape);bb=bb.reshape(shape);hh=hh.reshape(shape)
    if values.ndim==1:
        lo=values[jj];hi=values[ii];ml=M[jj];mh=M[ii]
    else:lo=values[jj,ix];hi=values[ii,ix];ml=M[jj,ix];mh=M[ii,ix]
    result=aa*lo+bb*hi+((aa**3-aa)*ml+(bb**3-bb)*mh)*hh**2/6
    low=query<nodes[0];high=query>nodes[-1];sl=(values[1]-values[0])/h[0]-h[0]*(2*M[0]+M[1])/6;sh=(values[-1]-values[-2])/h[-1]+h[-1]*(M[-2]+2*M[-1])/6
    if values.ndim==1:result[low]=values[0]+(query[low]-nodes[0])*sl;result[high]=values[-1]+(query[high]-nodes[-1])*sh
    else:result[low]=values[0,low]+(query[low]-nodes[0])[:,None]*sl[low];result[high]=values[-1,high]+(query[high]-nodes[-1])[:,None]*sh[high]
    return result

def periodic_theta(angles,points,query):
    """Periodic C2 interpolation of the actual Blender ring readback."""
    order=np.argsort(angles);a=angles[order];p0=points[order];unique=np.r_[True,np.diff(a)>1e-9];a=a[unique];p0=p0[unique];N=len(a);h=np.diff(np.r_[a,a[0]+2*np.pi]);A=np.zeros((N,N));rhs=np.zeros_like(p0)
    for i in range(N):
        prev=(i-1)%N;nx=(i+1)%N;A[i,prev]=h[prev];A[i,i]=2*(h[prev]+h[i]);A[i,nx]=h[i];rhs[i]=6*((p0[nx]-p0[i])/h[i]-(p0[i]-p0[prev])/h[prev])
    M=np.linalg.solve(A,rhs);q=(query-a[0])%(2*np.pi)+a[0];lo=np.clip(np.searchsorted(a,q)-1,0,N-1);hi=(lo+1)%N;t=(q-a[lo])/h[lo];aa=1-t;return aa[:,None]*p0[lo]+t[:,None]*p0[hi]+(((aa**3-aa)[:,None]*M[lo]+(t**3-t)[:,None]*M[hi])*h[lo,None]**2/6)
