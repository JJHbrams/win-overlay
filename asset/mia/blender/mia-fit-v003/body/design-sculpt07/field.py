"""Fresh positive anatomical implicit field, not an exact signed distance.

The same small expression graph evaluates NumPy probes and Blender nodes.
No previous candidate vertices, control rows, weights or topology enter it.
"""
import math
import numpy as np

class E:
    def __init__(self, op, *a): self.op, self.a = op, a
    def __add__(self, b): return E('ADD', self, b)
    def __radd__(self, b): return E('ADD', b, self)
    def __sub__(self, b): return E('SUBTRACT', self, b)
    def __rsub__(self, b): return E('SUBTRACT', b, self)
    def __mul__(self, b): return E('MULTIPLY', self, b)
    def __rmul__(self, b): return E('MULTIPLY', b, self)
    def __truediv__(self, b): return E('DIVIDE', self, b)
    def __neg__(self): return self * -1.

def mi(a,b): return E('MINIMUM',a,b)
def ma(a,b): return E('MAXIMUM',a,b)
def sqrt(a): return E('SQRT',ma(a,0.))
def sm(a,b,k):
    h=ma(k-E('ABSOLUTE',a-b),0.)/k
    return mi(a,b)-h*h*(k*.25)

def slopes(x,y):
    x=np.asarray(x);y=np.asarray(y);h=np.diff(x);d=np.diff(y)/h;m=np.zeros(len(x))
    m[0]=d[0];m[-1]=d[-1]
    for i in range(1,len(x)-1):
        if d[i-1]*d[i]>0:
            w1=2*h[i]+h[i-1];w2=h[i]+2*h[i-1]
            m[i]=(w1+w2)/(w1/d[i-1]+w2/d[i])
    return m

def profile(z, table):
    x,y=np.asarray(table,float).T;m=slopes(x,y);out=float(y[0])
    for i in range(len(x)-1):
        h=float(x[i+1]-x[i]);t=mi(ma((z-float(x[i]))/h,0.),1.);t2=t*t;t3=t2*t
        # Hermite value minus segment start; completed segments add only dy.
        out=out+(2*t3-3*t2)*(float(y[i])-float(y[i+1]))+(t3-2*t2+t)*float(h*m[i])+(t3-t2)*float(h*m[i+1])
    return out

def ellipsoid(x,y,z,c,r,angle=0.):
    # angle about world Y, used only for shoulder / down-outward upper arm.
    co,si=math.cos(angle),math.sin(angle);dx=x-c[0];dy=y-c[1];dz=z-c[2]
    qx=(co*dx-si*dz)/r[0];qz=(si*dx+co*dz)/r[2]
    return (sqrt(qx*qx+(dy/r[1])*(dy/r[1])+qz*qz)-1.)*min(r)

def make(p):
    x,y,z=[E('POS',i) for i in range(3)];reg={}
    t=p['thorax'];rx=profile(z,t['x_radius']);ry=profile(z,t['y_radius']);cy=profile(z,t['center_y'])
    radial=(sqrt((x/rx)*(x/rx)+((y-cy)/ry)*((y-cy)/ry))-1.)*.075
    torso=ma(radial,ma(t['z_min']-z,z-t['z_max']));reg['curved_tapered_thorax_neck']=torso
    b=p['breast'];r2=profile(z,b['squared_radial_profile']);rr=sqrt(r2);mass=[]
    for sign in [-1,1]:
        qx=(x-sign*b['center_x'])/b['radius_x'];qy=(y-b['center_y'])/b['radius_y']
        d=(sqrt(qx*qx+qy*qy)-rr)*min(b['radius_x'],b['radius_y'])
        mass.append(ma(d,ma(b['z_min']-z,z-b['z_max'])))
    breasts=sm(mass[0],mass[1],b['interbreast_blend']);reg['breast_pair']=breasts
    field=sm(torso,breasts,b['thorax_blend'])
    for sign in [-1,1]:
        for key in ['shoulder','upper_arm','anterior_fan','posterior_wall','trapezius']:
            v=p[key];c=v['center'].copy();c[0]*=sign
            d=ellipsoid(x,y,z,c,v['radii'],sign*math.radians(v.get('angle_y_degrees',0.)))
            reg[key+('_L' if sign<0 else '_R')]=d
            field=sm(field,d,v['blend'])
    return field,reg

def evaluate(e,points,cache=None):
    cache={} if cache is None else cache
    if not isinstance(e,E): return e
    key=id(e)
    if key in cache:return cache[key]
    if e.op=='POS':v=points[:,e.a[0]]
    else:
        a=[evaluate(q,points,cache) for q in e.a]
        v={'ADD':lambda:a[0]+a[1],'SUBTRACT':lambda:a[0]-a[1],
           'MULTIPLY':lambda:a[0]*a[1],'DIVIDE':lambda:a[0]/a[1],
           'MINIMUM':lambda:np.minimum(a[0],a[1]),'MAXIMUM':lambda:np.maximum(a[0],a[1]),
           'SQRT':lambda:np.sqrt(a[0]),'ABSOLUTE':lambda:np.abs(a[0])}[e.op]()
    cache[key]=v;return v

def nodes(tree,e):
    n=tree.nodes;l=tree.links;pos=n.new('GeometryNodeInputPosition');sep=n.new('ShaderNodeSeparateXYZ');l.new(pos.outputs['Position'],sep.inputs[0]);cache={}
    def emit(q):
        if not isinstance(q,E):return q
        key=id(q)
        if key in cache:return cache[key]
        if q.op=='POS':out=sep.outputs[q.a[0]]
        else:
            nn=n.new('ShaderNodeMath');nn.operation=q.op
            for i,a in enumerate(q.a):
                v=emit(a)
                if isinstance(v,(float,int,np.floating)):nn.inputs[i].default_value=float(v)
                else:l.new(v,nn.inputs[i])
            out=nn.outputs[0]
        cache[key]=out;return out
    return emit(e)
