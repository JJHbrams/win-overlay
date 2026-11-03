"""RAM-only immutable-component floor; no optimizer, mesher or Blender call.

Read canonical inputs directly. Distinguish deleting mutable components from
the finite point-field left by the zero-scale homothety limit at fixed blends.
The narrow thorax is a relaxed radius-profile limit, not a proposed body.
"""
from pathlib import Path
import argparse, json, hashlib, importlib.util, sys
import numpy as np
sys.dont_write_bytecode=True
DEFAULT=Path(__file__).resolve().parents[3]

def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def evaluate(module,expr,points):
    return np.concatenate([np.asarray(module.evaluate(expr,points[i:i+2048])) for i in range(0,len(points),2048)])

def roots_z(module,expr,xy):
    zz=np.linspace(1.20,1.505,123);q=np.column_stack((np.repeat(xy[:,0],len(zz)),np.repeat(xy[:,1],len(zz)),np.tile(zz,len(xy))))
    d=evaluate(module,expr,q).reshape(len(xy),-1);cross=(d[:,:-1]<=0)&(d[:,1:]>=0);valid=cross.any(1);ix=np.maximum(np.where(cross,np.arange(len(zz)-1),-1).max(1),0);lo=zz[ix];hi=zz[ix+1]
    for _ in range(24):
        mid=(lo+hi)/2;v=evaluate(module,expr,np.column_stack((xy,mid)));lo=np.where(v<=0,mid,lo);hi=np.where(v>0,mid,hi)
    result=(lo+hi)/2;result[~valid]=np.nan;return result

def silhouette(module,expr,x):
    yy=np.linspace(-.09,.09,37);xy=np.column_stack((np.repeat(x,len(yy)),np.tile(yy,len(x))));z=roots_z(module,expr,xy).reshape(len(x),len(yy));valid=np.isfinite(z).any(1);i=np.argmax(np.where(np.isfinite(z),z,-np.inf),axis=1);coarse=z[np.arange(len(x)),i]
    fy=yy[i,None]+np.linspace(-.005,.005,21)[None,:];fine=roots_z(module,expr,np.column_stack((np.repeat(x,21),fy.ravel()))).reshape(len(x),21);j=np.argmax(np.where(np.isfinite(fine),fine,-np.inf),axis=1);height=fine[np.arange(len(x)),j];hit_y=fy[np.arange(len(x)),j];height[~valid]=np.nan;hit_y[~valid]=np.nan
    return height,hit_y,float(np.nanmax(abs(height-coarse)))

def profile(module,expr,z):
    yy=np.linspace(-.15,.15,601);q=np.column_stack((np.zeros(len(yy)),yy,np.full(len(yy),z)));d=evaluate(module,expr,q);ii=np.flatnonzero(d[:-1]*d[1:]<0);roots=[]
    for i in ii:
        lo,hi=yy[i],yy[i+1]
        for _ in range(26):
            mid=(lo+hi)/2;v=evaluate(module,expr,np.array([[0,mid,z]]))[0]
            if v*d[i]>0:lo=mid
            else:hi=mid
        roots.append((lo+hi)/2)
    return roots

def primitive_projected_top(component,x):
    """Exact ellipsoid upper Z at fixed X, maximized over Y=centerY."""
    dx=x-component['center'][0];rx,_,rz=component['radii']
    angle=np.radians(component['angle_y_degrees']);co,si=np.cos(angle),np.sin(angle)
    aa=si*si/rx**2+co*co/rz**2
    bb=2*co*si*(1/rz**2-1/rx**2)*dx
    cc=(co*co/rx**2+si*si/rz**2)*dx*dx-1
    discriminant=bb*bb-4*aa*cc
    return None if discriminant<0 else component['center'][2]+(-bb+np.sqrt(discriminant))/(2*aa)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--canonical',type=Path,default=DEFAULT);args=ap.parse_args();canonical=args.canonical
    asset=canonical/'asset/mia/blender/mia-fit-v003';S=asset/'body/shoulder11';E=asset/'body/design-sculpt07/E';review=asset/'body/surface-review12'
    guard=load('H_storage_guard',asset/'integration/workspace-storage-20261103/storage_guard.py');capacity=guard.inspect(10*1024*1024)
    if capacity['violations']:raise RuntimeError(json.dumps(capacity))
    m=load('H_frozen11',S/'field.py');b=m.base;p=json.loads((S/'parameters.json').read_text(encoding='utf-8'));F11,_=m.make(p);_,reg=b.make(p)
    provenance=[]
    for label,path in [('frozen11',S/'field.py'),('actual_transitive_E',Path(b.__file__)),('actual_transitive_base',Path(b.base.__file__)),('canonical_E',E/'field.py'),('canonical_base',E.parent/'field.py'),('parameters',S/'parameters.json'),('source_rails',S/'source-rails.json')]:
        provenance.append(dict(role=label,path=str(path),sha256=digest(path)))
    assert provenance[1]['sha256']==provenance[3]['sha256']=='6bd907200a1ed082daf81fd2abde77e229890ecce405b415e3ca5b8e1e76f20d'
    assert provenance[2]['sha256']==provenance[4]['sha256']=='94ff4d29ec7629de017281aef6fc63e3d681fd2da0dd7d9c6f6583b265f34bd0'
    x,y,z=[b.E('POS',i) for i in range(3)];t=p['thorax'];cy=b.profile(z,t['center_y']);rx_min=min(v for _,v in t['x_radius']);ry_min=min(v for _,v in t['y_radius'])
    # Exact infimum of positive profile-evaluation radii over the existing
    # clamped tables. It is a local roof-domain relaxation: fixed lower/core
    # matching, a finite-gradient transition and the head collar are not built.
    narrow=b.ma((b.sqrt((x/rx_min)*(x/rx_min)+((y-cy)/ry_min)*((y-cy)/ry_min))-1)*.075,b.ma(t['z_min']-z,z-t['z_max']))
    breast=p['breast'];v=b.mi(b.ma((z-breast['center_z'])/breast['upper_thorax_blend']['ramp_height_m'],0),1);v=v*v*v*(10-15*v+6*v*v);k=breast['upper_thorax_blend']['lower_m']+(breast['upper_thorax_blend']['upper_m']-breast['upper_thorax_blend']['lower_m'])*v
    # Same anchors as the rejected G probe, no source fitting or retuning.
    gp=json.loads((review/'proportion-G-probe/RAM-calibration.json').read_text(encoding='utf-8'))['component_nesting'];pointfields={}
    for sign,suffix in [(-1,'_L'),(1,'_R')]:
        for key,record in [('shoulder',gp['cap']),('trapezius',gp['trap'])]:
            q=p[key];aa=np.array(record['anchor_world']);aa[0]*=sign;angle=sign*np.radians(q['angle_y_degrees']);co,si=np.cos(angle),np.sin(angle);dx=x-float(aa[0]);dy=y-float(aa[1]);dz=z-float(aa[2]);qx=(co*dx-si*dz)/q['radii'][0];qz=(si*dx+co*dz)/q['radii'][2]
            pointfields[key+suffix]=b.sqrt(qx*qx+(dy/q['radii'][1])*(dy/q['radii'][1])+qz*qz)*min(q['radii'])
    def accumulated(torso,points=False,omit_fixed=None):
        result=reg['breast_pair'] if torso is None else b.sm(torso,reg['breast_pair'],k)
        for suffix in ['_L','_R']:
            for key in ['shoulder','upper_arm','anterior_fan','posterior_wall','trapezius']:
                if key in ['shoulder','trapezius']:
                    if not points:continue
                    d=pointfields[key+suffix]
                elif key==omit_fixed:continue
                else:d=reg[key+suffix]
                result=b.sm(result,d,p[key]['blend'])
        return result
    cases={'baseline11':F11,'cap_trap_removed_original_thorax':accumulated(reg['curved_tapered_thorax_neck']),'fixed_components_only_optimistic_floor':accumulated(None),'removed_with_profile_limit_thorax':accumulated(narrow),'homothety_zero_scale_with_profile_limit_thorax':accumulated(narrow,True)}
    # Attribution only: a removable immutable-group competitor is NOT a new
    # authorized deformation or source candidate.
    for key in ['upper_arm','anterior_fan','posterior_wall']:cases['fixed_floor_without_'+key]=accumulated(None,omit_fixed=key)
    rails=json.loads((S/'source-rails.json').read_text(encoding='utf-8'));r=rails['registration'];mpp=r['metres_per_pixel'];obs=[]
    for name,points in rails['traces_original_pixels'].items():
        axis=935 if name.startswith('back') else r['front_axis_pixel']
        for px,py in points:
            xx=abs(px-axis)*mpp
            if xx>=.05:obs.append(dict(path=name,pixel=[px,py],x_world=xx,z_world=(r['zero_world_z_pixel']-py)*mpp,trace_interval_sigma_m=2*mpp))
    xx=np.array([a['x_world'] for a in obs]);results={};refinement={}
    for name,expr in cases.items():
        height,hit_y,error=silhouette(m,expr,xx);refinement[name]=error;results[name]=height
        for i,a in enumerate(obs):
            a.setdefault('cases',{})[name]=dict(z=None if not np.isfinite(height[i]) else float(height[i]),maximizing_y=None if not np.isfinite(height[i]) else float(hit_y[i]),excess_over_trace_interval_m=None if not np.isfinite(height[i]) else float(max(height[i]-a['z_world']-2*mpp,0)))
        print('H_FLOOR_CASE',name,'finite',int(np.isfinite(height).sum()),'maxY_refinement_mm',error*1000,flush=True)
    # Headcut is actual joined retained-head boundary, not the guide tube.
    a=np.load(review/'joined-expanded-E.npz');vv=a['world'];ff=a['triangles'][a['source_part']==1];edges=np.sort(np.concatenate([ff[:,[0,1]],ff[:,[1,2]],ff[:,[2,0]]]),axis=1);edges,count=np.unique(edges,axis=0,return_counts=True);edges=edges[count==1];edges=edges[np.all(abs(vv[edges,2]-1.465)<1e-6,axis=1)];ids=np.unique(edges);head=vv[ids].astype(float);bounds=[head.min(0).tolist(),head.max(0).tolist()]
    profiles=[]
    for py,left,right in [[195,574,615],[205,576,618],[215,574,623]]:
        zz=(r['zero_world_z_pixel']-py)*mpp;row=dict(source_pixel_y=py,source_front_back_x=[left,right],z_world=zz,source_width_m=(right-left)*mpp,two_edge_width_uncertainty_m=4*mpp,cases={})
        for name in ['baseline11','fixed_components_only_optimistic_floor','removed_with_profile_limit_thorax','homothety_zero_scale_with_profile_limit_thorax']:row['cases'][name]=profile(m,cases[name],zz)
        profiles.append(row)
    q=np.array([(X,Y,Z) for Z in np.linspace(1.30,1.465,17) for Y in np.linspace(-.075,.075,13) for X in np.linspace(-.2,.2,17)])
    old=evaluate(m,F11,q);lower=evaluate(m,cases['fixed_components_only_optimistic_floor'],q)
    assert np.all(lower>=old-1e-12),'Removed floor must nest inside baseline'
    report=dict(status='RAM_FLOOR_DIAGNOSTIC_NO_SOLVE_NO_CANDIDATE',provenance=provenance,source_reference_sha256=rails['sha256'],source_registration=r,source_uncertainty=rails['uncertainty'],source_camera_estimates=rails['source_camera_estimates'],camera_uncertainty_degrees=rails['camera_uncertainty_degrees'],raw_trace_counts={k:len(v) for k,v in rails['traces_original_pixels'].items()},included_count=len(obs),selection='Same33 prior G observations withabsX>=.05; no silent31-count assumption; smallerX is separately constrained by actual head/neck visibility.',observations=obs,maxY_coarse_fine_height_difference_m=refinement,headcut=dict(edges=len(edges),vertices=len(ids),bounds_world=bounds,X_width_m=bounds[1][0]-bounds[0][0],AP_width_m=bounds[1][1]-bounds[0][1],cut_z=1.465,placeholder_guide_cut_z=1.445,definition='Actual retained-head boundary in immutable E assembly; no position edits.'),profile_neck=profiles,profile_limit=dict(rx=rx_min,ry=ry_min,centerY='Original profile held',meaning='Positive nested upper-thorax profile-value limit; lower matching, finite-gradient connection and head interface not constructed. It is a relaxed roof-domain infimum, not an admissible completed whole body.'),mathematics=dict(fixed_floor='For fixed smoothminimum order, every additional primitive can only lower F. Ffull<=Ffixed, hence zero/inside fixed union is a lower bound on reachable roof. These are actual accumulated zero intersections, not field differences treated as distances.',homothety_limit='For q=Aold^-1(p-anchor), f_s=min(oldr)*(norm(q-s*Aold^-1(c-anchor))-s). At s→0 a finite point-distance remains; fixed blend widths can still move a union zero. Removing the primitive is more optimistic than the exact scale-only limit.',lower_domain='OldZ0/halo/full1.395 were internal gates, not anatomy. No lower halo is imposed in the optimistic floor. A future finite smooth construction must separately preserve protected breast/exposed core and corridor.',attainment='The immutable-component floor is necessary, not proof of feasible smooth body/collar. The profile-limit and point-limit cases quantify the existing family; no solve, parameters or new domain are adopted.'),sampled_nesting_min_fixed_floor_minus_baseline=float((lower-old).min()),capacity_receipt=capacity,mesh_created=False,GPU_used=False,native_saved=False,inputs_copied=False)
    out=canonical/'.mia-cache/body-h/shape';out.mkdir(parents=True,exist_ok=True);path=out/'competitor-floor.json';assert not path.exists(),'Never overwrite a frozen floor report';path.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    print('H_FLOOR_REPORT',str(path),'bytes',path.stat().st_size,flush=True)

if __name__=='__main__':main()
