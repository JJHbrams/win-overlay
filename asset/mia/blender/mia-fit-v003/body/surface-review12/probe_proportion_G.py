"""Bounded RAM-only G source calibration. No Blender, mesh or native writes.

One source-residual calibration, no mesh/amplitude grid. Input components and
the11 accumulation are immutable; output contains parameter deltas and probes.
"""
from pathlib import Path
import sys, json, copy, hashlib, importlib.util
import numpy as np
sys.dont_write_bytecode = True
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
from capacity_gate import check
O=P/'proportion-G-probe'
S=P.parent/'shoulder11'
spec=importlib.util.spec_from_file_location('G_frozen11_field',S/'field.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
b=m.base
par=json.loads((S/'parameters.json').read_text())
F11,reg11=m.make(par)
Fhom,rhom=b.make(par)
sha=lambda q:hashlib.sha256(Path(q).read_bytes()).hexdigest()
Z0=par['shoulder11']['gate_zero_z'];ZFULL=1.395;ZHEAD=1.465

def evaluate(expr,points):
    return np.concatenate([np.asarray(m.evaluate(expr,points[i:i+2048])) for i in range(0,len(points),2048)])

def smooth(t):
    t=np.clip(t,0,1);return t*t*t*(10-15*t+6*t*t)

def window(z):
    return smooth((z-Z0)/(ZFULL-Z0))*(1-smooth((z-ZFULL)/(ZHEAD-ZFULL)))

def prof(z,table):
    z=np.atleast_1d(z);q=np.column_stack((np.zeros_like(z),np.zeros_like(z),z))
    return evaluate(b.profile(b.E('POS',2),table),q)

def inverse_profile(value,table):
    z=np.linspace(Z0,ZHEAD,4097);r=prof(z,table)
    assert np.all(np.diff(r)<=1e-14)
    return float(np.interp(value,r[::-1],z[::-1]))

def anchor(key):
    q=par[key];a=np.radians(q['angle_y_degrees']);co,si=np.cos(a),np.sin(a)
    R=np.array([[co,0,si],[0,1,0],[-si,0,co]])
    u=np.array([-1/np.sqrt(2),0,-1/np.sqrt(2)])*.95 if key=='shoulder' else np.array([0,0,-.95])
    A=R@np.diag(q['radii']);point=np.array(q['center'])+A@u
    top=float(q['center'][2]+np.linalg.norm(A[2]))
    return point,u,top

def contract(key,scale):
    q=copy.deepcopy(par[key]);point,u,top=anchor(key)
    q['center']=(point+scale*(np.array(q['center'])-point)).tolist()
    q['radii']=(np.array(q['radii'])*scale).tolist()
    return q,dict(anchor_world=point.tolist(),old_local_normalized_anchor=u.tolist(),anchor_norm=float(np.linalg.norm(u)),scale=scale,new_center=q['center'],new_radii=q['radii'],old_top_z=top,primitive_top_retraction_m=(1-scale)*(top-point[2]),nesting_proof='fnew-fold >= min(oldr)*(1-s)*(1-norm(anchor_local)) >=0 by reverse triangle; fixed smoothminimum is coordinatewise monotone. All3radii shrink, not height only.')

def build_g(values):
    x,y,z=[b.E('POS',i) for i in range(3)]
    lower=b.smooth01((z-Z0)/(ZFULL-Z0))
    w=lower*(1-b.smooth01((z-ZFULL)/(ZHEAD-ZFULL)))
    t=par['thorax'];rx=b.profile(z+values['rx_profile_shift_m']*w,t['x_radius']);ry=b.profile(z+values['ry_profile_shift_m']*w,t['y_radius']);cy=b.profile(z,t['center_y'])
    torso=b.ma((b.sqrt((x/rx)*(x/rx)+((y-cy)/ry)*((y-cy)/ry))-1)*.075,b.ma(t['z_min']-z,z-t['z_max']))
    regs=dict(rhom);regs['curved_tapered_thorax_neck']=torso
    ccap,pcap=contract('shoulder',values['cap_scale']);ctrap,ptrap=contract('trapezius',values['trap_scale'])
    breast=par['breast'];blend=breast['upper_thorax_blend'];tt=b.mi(b.ma((z-breast['center_z'])/blend['ramp_height_m'],0),1);ramp=tt*tt*tt*(10-15*tt+6*tt*tt);k=blend['lower_m']+(blend['upper_m']-blend['lower_m'])*ramp
    f=b.sm(torso,rhom['breast_pair'],k)
    for sign,suffix in [(-1,'_L'),(1,'_R')]:
        for key in ['shoulder','upper_arm','anterior_fan','posterior_wall','trapezius']:
            if key in ['shoulder','trapezius']:
                q=ccap if key=='shoulder' else ctrap;center=q['center'].copy();center[0]*=sign
                d=b.ellipsoid(x,y,z,center,q['radii'],sign*np.radians(q['angle_y_degrees']))
            else:d=rhom[key+suffix]
            regs[key+suffix]=d;f=b.sm(f,d,par[key]['blend'])
    return F11+lower*(f-Fhom),regs,dict(cap=pcap,trap=ptrap)

def roots_z(expr,xy,low=1.30,high=1.505):
    z=np.linspace(low,high,83);q=np.column_stack((np.repeat(xy[:,0],len(z)),np.repeat(xy[:,1],len(z)),np.tile(z,len(xy))))
    d=evaluate(expr,q).reshape(len(xy),-1);cross=(d[:,:-1]<=0)&(d[:,1:]>=0);valid=cross.any(1)
    ix=np.maximum(np.where(cross,np.arange(len(z)-1),-1).max(1),0);lo=z[ix].copy();hi=z[ix+1].copy()
    for _ in range(22):
        mid=(lo+hi)*.5;dd=evaluate(expr,np.column_stack((xy,mid)));lo=np.where(dd<=0,mid,lo);hi=np.where(dd>0,mid,hi)
    result=(lo+hi)/2;result[~valid]=np.nan;return result

def projected_roofs(expr,x):
    ys=np.linspace(-.075,.075,25);xy=np.column_stack((np.repeat(x,len(ys)),np.tile(ys,len(x))))
    r=roots_z(expr,xy).reshape(len(x),len(ys));i=np.nanargmax(r,axis=1);coarse=r[np.arange(len(x)),i]
    fine_y=ys[i,None]+np.linspace(-.00625,.00625,13)[None,:]
    xy=np.column_stack((np.repeat(x,13),fine_y.ravel()));rf=roots_z(expr,xy).reshape(len(x),13);j=np.nanargmax(rf,axis=1)
    return rf[np.arange(len(x)),j],fine_y[np.arange(len(x)),j],float(np.nanmax(np.abs(np.nanmax(rf,axis=1)-coarse)))

def gradients(expr,q):
    h=2e-5;g=[]
    for k in range(3):
        delta=np.zeros_like(q);delta[:,k]=h;g.append((evaluate(expr,q+delta)-evaluate(expr,q-delta))/(2*h))
    return np.column_stack(g)

def main():
    receipt=check(10)
    assert not O.exists(),'Keep the one RAM calibration immutable'
    rails=json.loads((S/'source-rails.json').read_text());r=rails['registration'];mpp=r['metres_per_pixel'];zero=r['zero_world_z_pixel'];observed=[]
    for name,points in rails['traces_original_pixels'].items():
        axis=935 if name.startswith('back') else r['front_axis_pixel']
        for px,py in points:
            xx=abs(px-axis)*mpp
            if xx>=.05:observed.append(dict(path=name,pixel=[px,py],x=xx,z=(zero-py)*mpp))
    xx=np.array([a['x'] for a in observed]);oldroof,oldy,err=projected_roofs(F11,xx);srcz=np.array([a['z'] for a in observed]);residual=oldroof-srcz
    capmask=(xx>=.125)&(xx<=.17);trapmask=(xx>=.07)&(xx<=.11);neckmask=(xx>=.05)&(xx<=.075)
    # One conservative partial source correction outside the observed 2px rail
    # uncertainty; no full fit to an illustrated/pose-uncertain silhouette.
    target_cap=.5*max(float(np.median(residual[capmask]))-2*mpp,0)
    target_trap=.5*max(float(np.median(residual[trapmask]))-2*mpp,0)
    scales={}
    for key,target in [('shoulder',target_cap),('trapezius',target_trap)]:
        aa,uu,top=anchor(key);scales[key]=1-target/(top-aa[2]);assert .4<scales[key]<1,(key,scales[key])
    rx_shifts=[]
    for i in np.flatnonzero(neckmask):
        target=oldroof[i]-.5*max(residual[i]-2*mpp,0);phi=inverse_profile(xx[i],par['thorax']['x_radius']);ww=float(window(target))
        if ww>.1:rx_shifts.append(max((phi-target)/ww,0))
    rx_raw=float(np.median(rx_shifts));monotone_limit=.9*(ZHEAD-ZFULL)/1.875
    # Independently observed profile neck widths; only width is used, not
    # guessed AP centre. Original pixels, approximately +/-2px per edge.
    profile_pixels=[[195,576,613],[205,575,617],[215,571,622]];ry_shifts=[];profile_records=[]
    for py,front,back in profile_pixels:
        zz=(zero-py)*mpp;oldry=float(prof([zz],par['thorax']['y_radius'])[0]);source_width=(back-front)*mpp
        target_width=2*oldry-.5*max(2*oldry-source_width-4*mpp,0);phi=inverse_profile(target_width/2,par['thorax']['y_radius']);ww=float(window(zz));shift=max((phi-zz)/ww,0)
        ry_shifts.append(shift);profile_records.append(dict(pixel_y=py,front_x=front,back_x=back,z=zz,source_AP_width_m=source_width,old_thorax_AP_width_m=2*oldry,derived_shift_m=shift))
    values=dict(cap_scale=scales['shoulder'],trap_scale=scales['trapezius'],rx_profile_shift_m=min(rx_raw,monotone_limit),ry_profile_shift_m=min(float(np.median(ry_shifts)),monotone_limit))
    G,regs,proof=build_g(values);newroof,newy,newerr=projected_roofs(G,xx)
    for i,a in enumerate(observed):a.update(old_roof_z=float(oldroof[i]),G_roof_z=float(newroof[i]),old_maximizing_y=float(oldy[i]),G_maximizing_y=float(newy[i]),old_source_residual_m=float(residual[i]),G_source_residual_m=float(newroof[i]-srcz[i]))
    # Actual fixed-physical-plane vertical intersections across front/mid/back.
    xy=np.array([(x,y) for y in [-.035,0,.035] for x in [.04,.06,.08,.10,.12,.14,.16,.18]])
    rz0=roots_z(F11,xy);rz1=roots_z(G,xy);valid=np.isfinite(rz0)&np.isfinite(rz1);q0=np.column_stack((xy[valid],rz0[valid]));q1=np.column_stack((xy[valid],rz1[valid]));n0=gradients(F11,q0);n1=gradients(G,q1);cos=np.sum(n0*n1,axis=1)/(np.linalg.norm(n0,axis=1)*np.linalg.norm(n1,axis=1));turn=np.degrees(np.arccos(np.clip(cos,-1,1)))
    root_records=[];j=0
    for i,p in enumerate(xy):
        row=dict(x=float(p[0]),y=float(p[1]),old_z=None if not np.isfinite(rz0[i]) else float(rz0[i]),G_z=None if not np.isfinite(rz1[i]) else float(rz1[i]))
        if valid[i]:row.update(normal_turn_degrees=float(turn[j]),old_gradient_norm=float(np.linalg.norm(n0[j])),G_gradient_norm=float(np.linalg.norm(n1[j])));j+=1
        root_records.append(row)
    # Complete old guide surface equality/prediction. These are field and true
    # ray probes; final remeshed physical triangle matching is still required.
    guide=np.load(S/'shoulder11-canonical.npz');v=guide['world'].astype(float);dv=evaluate(G,v)-evaluate(F11,v)
    q=np.array([(x,y,z) for z in np.linspace(1.03,1.525,31) for y in np.linspace(-.18,.13,13) for x in np.linspace(-.29,.29,17)])
    diff=evaluate(G,q)-evaluate(F11,q)
    lower=v[:,2]<=1.36;halo=v[:,2]<=Z0;upper=v[:,2]>=ZHEAD;breast=(abs(v[:,0])<=.125)&(v[:,1]<=-.03)&(v[:,2]>=1.18)&(v[:,2]<=1.35)
    # Same-plane main and posterior openings: solve actual x-zero crossings.
    gaps=[]
    for yy,zz in [(0,1.26),(.020,1.26),(.025,1.265),(.035,1.28)]:
        xs=np.linspace(.09,.23,1401);pts=np.column_stack((xs,np.full(len(xs),yy),np.full(len(xs),zz)));entries=[]
        for label,expr in [('11',F11),('G',G)]:
            d=evaluate(expr,pts);ii=np.flatnonzero(d[:-1]*d[1:]<0);roots=[]
            for k in ii:
                lo,hi=xs[k],xs[k+1]
                for _ in range(24):
                    mid=(lo+hi)/2;val=evaluate(expr,np.array([[mid,yy,zz]]))[0]
                    if val*d[k]>0:lo=mid
                    else:hi=mid
                roots.append((lo+hi)/2)
            positive=[]
            for aa,bb in zip(roots[:-1],roots[1:]):
                if evaluate(expr,np.array([[(aa+bb)/2,yy,zz]]))[0]>0:positive.append([aa,bb,bb-aa])
            entries.append(dict(state=label,roots_x=roots,air_intervals=positive))
        gaps.append(dict(y=yy,z=zz,actual_intersections=entries))
    zz=np.linspace(Z0,ZHEAD,2001);w=window(zz);dw=np.gradient(w,zz);profile_bound={}
    for key in ['rx','ry']:
        shift=values[key+'_profile_shift_m'];profile_bound[key]=dict(shift_m=shift,numerical_min_evaluation_coordinate_derivative=float(np.min(1+shift*dw)),conservative_lower_bound=1-shift*1.875/(ZHEAD-ZFULL))
    report=dict(status='RAM_ONLY_UNSELECTED_NO_MESH',sources={str(S/'parameters.json'):sha(S/'parameters.json'),str(S/'field.py'):sha(S/'field.py'),'tied_hair_reference_sha256':rails['sha256'],'E_joined_sha256':sha(P/'joined-expanded-E.npz')},parameters=values,component_nesting=proof,profile_shift=dict(formula='rX(z+deltaX*w),rY(z+deltaY*w); original centerY; w=lower quintic*(1-upper quintic)',zero_z=Z0,full_peak_z=ZFULL,identity_head_z=ZHEAD,bounds=profile_bound,raw_source_RX_shift_m=rx_raw,source_profile_widths=profile_records),source_calibration=dict(rule='One half of median observed roof residual beyond2px contour uncertainty; source-profile AP width uses half excess beyond4px two-edge uncertainty. Component analytic support span gives each scale; no parameter grid/mesh.',registration=rails['registration'],limits=rails['uncertainty']+' Profile edge readings approx+/-2px; width only, pose/camera85+/-8deg remains uncertain. MaxY silhouette is numerically maximized over~1mmY steps, not a single midplane.',coarse_to_fine_max_height_change_m=max(err,newerr),rails=observed),nesting_grid=dict(samples=len(q),minimum_G_minus11=float(diff.min()),negative_below_1e_12=int((diff < -1e-12).sum())),complete_old_guide_surface_prediction=dict(vertices=len(v),lower_count=int(lower.sum()),lower_field_bit_exact=bool(np.array_equal(evaluate(G,v[lower]),evaluate(F11,v[lower]))),halo_count=int(halo.sum()),halo_max_absolute_field_delta=float(abs(dv[halo]).max()),upper_count=int(upper.sum()),upper_max_absolute_field_delta=float(abs(dv[upper]).max()),breast_core_count=int(breast.sum()),breast_core_max_absolute_field_delta=float(abs(dv[breast]).max()),upper_allowed_changed_count=int((abs(dv)>1e-12).sum()),maximum_field_delta_not_distance=float(dv.max())),halo=dict(json_path=str(S/'mesher-halo.json'),details=json.loads((S/'mesher-halo.json').read_text()),warning='Same conservative3sample collar retained; analytic identity is not an actual VDB stencil proof. One future mesh must match protected physical triangles or STOP.'),true_vertical_roots=root_records,corridor=gaps,capacity=receipt,mesh_created=False,GPU_used=False,native_saved=False,texture_baked=False)
    O.mkdir();(O/'RAM-calibration.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    print('G_RAM_ONLY',json.dumps({k:report[k] for k in ['parameters','profile_shift','nesting_grid','complete_old_guide_surface_prediction','corridor']}),flush=True)
    print('REPORT',str(O/'RAM-calibration.json'),'bytes',(O/'RAM-calibration.json').stat().st_size,flush=True)

if __name__=='__main__':main()
