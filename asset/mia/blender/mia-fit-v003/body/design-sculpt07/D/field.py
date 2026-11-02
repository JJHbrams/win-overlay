"""D upper-only C2 posterior warp; lower C bowl and11 other fields held."""
from pathlib import Path
import importlib.util,math
spec=importlib.util.spec_from_file_location('sculpt07_frozen_A_field',Path(__file__).resolve().parent.parent/'field.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
E=base.E;mi=base.mi;ma=base.ma;sqrt=base.sqrt;sm=base.sm;profile=base.profile;ellipsoid=base.ellipsoid;evaluate=base.evaluate;nodes=base.nodes
def make(p):
    x,y,z=[E('POS',i) for i in range(3)];reg={};t=p['thorax'];rx=profile(z,t['x_radius']);ry=profile(z,t['y_radius']);cy=profile(z,t['center_y'])
    radial=(sqrt((x/rx)*(x/rx)+((y-cy)/ry)*((y-cy)/ry))-1.)*.075
    torso=ma(radial,ma(t['z_min']-z,z-t['z_max']));reg['curved_tapered_thorax_neck']=torso
    b=p['breast'];brx,bry,brz=b['radii'];dz=z-b['center_z'];w=b['upper_posterior_warp']['width_m'];v=mi(ma(dz/w,0.),1.);h=w*(v*v*v-.5*v*v*v*v)+ma(dz-w,0.);warp=b['upper_posterior_warp']['k']*h
    blend=b['upper_thorax_blend'];tt=mi(ma(dz/blend['ramp_height_m'],0.),1.);ramp=tt*tt*tt*(10.-15.*tt+6.*tt*tt);localblend=blend['lower_m']+(blend['upper_m']-blend['lower_m'])*ramp
    mass=[]
    for sign in [-1,1]:
        qx=(x-sign*b['center_x'])/brx;qy=(y-warp-b['center_y']-b['yz_shear']*dz)/bry;qz=dz/brz
        d=(sqrt(qx*qx+qy*qy+qz*qz)-1.)*min(b['radii']);mass.append(ma(d,y-b['posterior_cap_y']))
    breasts=sm(mass[0],mass[1],b['interbreast_blend']);reg['breast_pair']=breasts;value=sm(torso,breasts,localblend)
    for sign in [-1,1]:
        for key in ['shoulder','upper_arm','anterior_fan','posterior_wall','trapezius']:
            q=p[key];c=q['center'].copy();c[0]*=sign;d=ellipsoid(x,y,z,c,q['radii'],sign*math.radians(q.get('angle_y_degrees',0.)))
            reg[key+('_L' if sign<0 else '_R')]=d;value=sm(value,d,q['blend'])
    return value,reg
