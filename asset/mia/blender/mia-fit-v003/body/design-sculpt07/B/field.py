"""B uses unchanged A arithmetic helpers, independent anatomical field recipe."""
from pathlib import Path
import importlib.util,math
spec=importlib.util.spec_from_file_location('sculpt07_frozen_A_field',Path(__file__).resolve().parent.parent/'field.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
E=base.E;mi=base.mi;ma=base.ma;sqrt=base.sqrt;sm=base.sm;profile=base.profile;ellipsoid=base.ellipsoid;evaluate=base.evaluate;nodes=base.nodes
def make(p):
    x,y,z=[E('POS',i) for i in range(3)];reg={};t=p['thorax'];rx=profile(z,t['x_radius']);ry=profile(z,t['y_radius']);cy=profile(z,t['center_y'])
    radial=(sqrt((x/rx)*(x/rx)+((y-cy)/ry)*((y-cy)/ry))-1.)*.075
    torso=ma(radial,ma(t['z_min']-z,z-t['z_max']));reg['curved_tapered_thorax_neck']=torso
    b=p['breast'];brx=profile(z,b['x_radius']);bry=profile(z,b['y_radius']);bcy=profile(z,b['center_y']);mass=[]
    for sign in [-1,1]:
        qx=(x-sign*b['center_x'])/brx;qy=(y-bcy)/bry
        d=(sqrt(qx*qx+qy*qy)-1.)*.065
        # Primitive closures are internal to the thorax, not subtraction from
        # the union or an artificial skin membrane across an axillary opening.
        d=ma(d,ma(y-b['posterior_cap_y'],ma(b['z_min']-z,z-b['z_max'])))
        mass.append(d)
    breasts=sm(mass[0],mass[1],b['interbreast_blend']);reg['breast_pair']=breasts
    value=sm(torso,breasts,b['thorax_blend'])
    for sign in [-1,1]:
        for key in ['shoulder','upper_arm','anterior_fan','posterior_wall','trapezius']:
            v=p[key];c=v['center'].copy();c[0]*=sign;d=ellipsoid(x,y,z,c,v['radii'],sign*math.radians(v.get('angle_y_degrees',0.)))
            reg[key+('_L' if sign<0 else '_R')]=d;value=sm(value,d,v['blend'])
    return value,reg
