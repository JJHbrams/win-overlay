"""D upper-only warp math, C field/mesh lower preservation and buried cap."""
from pathlib import Path
import json,hashlib,sys,importlib.util
import numpy as np
P=Path(__file__).resolve().parent;C=P.parent/'C';sys.path.insert(0,str(P));import field
p=json.loads((P/'parameters.json').read_text(encoding='utf-8'));pc=json.loads((C/'parameters.json').read_text(encoding='utf-8'));b=p['breast'];cz=b['center_z'];w=b['upper_posterior_warp']['width_m'];k=b['upper_posterior_warp']['k'];f,reg=field.make(p)
spec=importlib.util.spec_from_file_location('held_C_field',C/'field.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old);fc,rc=old.make(pc)
pts=np.random.default_rng(12).uniform(p['mesher']['bounds_min'],p['mesher']['bounds_max'],(512,3));low=pts.copy();low[:,2]=np.random.default_rng(13).uniform(1.08,cz,512);dv=field.evaluate(f,low);cv=old.evaluate(fc,low);assert np.array_equal(dv,cv)
components={name:bool(np.array_equal(field.evaluate(expr,pts),old.evaluate(rc[name],pts))) for name,expr in reg.items() if name!='breast_pair'};assert all(components.values())
v=np.load(P/'sculpt07-D.npz')['world'];c=np.load(C/'sculpt07-C.npz')['world'];margin=max(json.loads((P/'build-report.json').read_text())['actual_grid_step_m'])*2
def ordered(a):return a[np.lexsort((a[:,2],a[:,1],a[:,0]))]
vl=ordered(v[v[:,2]<cz-margin]);cl=ordered(c[c[:,2]<cz-margin]);mesh_exact=vl.shape==cl.shape and np.array_equal(vl,cl);assert mesh_exact
allvl=ordered(v[v[:,2]<=cz]);allcl=ordered(c[c[:,2]<=cz]);full_low_exact=allvl.shape==allcl.shape and np.array_equal(allvl,allcl)
uu=np.linspace(0,w,101);vv=uu/w;h=w*(vv**3-.5*vv**4);h1=3*vv**2-2*vv**3;h2=(6*vv-6*vv**2)/w;assert h2.min()>=0
rows=[]
for r in p['source_consumed_before_geometry']['section_support_bands']:
    u=r['world_z']-cz;v0=np.clip(u/w,0,1);hh=w*(v0**3-.5*v0**4)+max(u-w,0);tt=np.clip(u/b['upper_thorax_blend']['ramp_height_m'],0,1);ramp=tt**3*(10-15*tt+6*tt**2);rows.append(dict(z=r['world_z'],upper_posterior_shift_m=k*hh,breast_thorax_blend_m=.016+.018*ramp))
qx=v[(abs(v[:,1]-b['posterior_cap_y'])<.001)&(v[:,2]>cz-b['radii'][2])&(v[:,2]<cz+b['radii'][2])];bv=field.evaluate(reg['breast_pair'],qx);other=np.minimum.reduce([field.evaluate(expr,qx) for name,expr in reg.items() if name!='breast_pair']);exposed=int(((bv<.001)&(other>0)).sum())
r=dict(D_mesh_sha256=hashlib.sha256((P/'sculpt07-D.npz').read_bytes()).hexdigest(),C_mesh_sha256=hashlib.sha256((C/'sculpt07-C.npz').read_bytes()).hexdigest(),C_nonbreast_parameter_arrays_exact={name:p[name]==pc[name] for name in ['thorax','shoulder','upper_arm','anterior_fan','posterior_wall','trapezius','pose','mesher','context_mask_B']},C_nonbreast_11_component_fields_exact_at_512_probes=components,whole_field_below_cz_exact_at_512_probes=True,whole_field_below_cz_max_difference_m=float(abs(dv-cv).max()),lower_mesh_z_margin_m=margin,lower_mesh_vertices_below_cz_minus_two_cells=len(vl),lower_mesh_coordinate_set_bitexact=True,full_mesh_below_cz_coordinate_set_bitexact=bool(full_low_exact),full_low_C_D_counts=[len(allcl),len(allvl)],mesher_limit='A voxel cell crossing cz may react to upper changes; exact analytic field belowcz plus actual lower source stations and lower mesh away from two cells are checked separately.',warp_C2=True,warp_H1_endpoints=[float(h1[0]),float(h1[-1])],warp_H2_min=float(h2.min()),warp_H2_endpoints=[float(h2[0]),float(h2[-1])],front_convexity='Original convex front graph y=Cfront(x,z)+f(z), with fsecond>=0; front-hemisphere Hessian remains positive. D is no longer an affine quadric, no claim that whole union or hidden posterior surface is globally convex.',source_station_warp_and_local_blend=rows,posterior_cap_near_plane_samples=len(qx),exposed_cap_control_samples=exposed,status='CPU bounded upper-root construction/preservation only; actual visible root/axilla review required.')
(P/'upper-root-cpu-audit.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print('D_UPPER_ROOT_CPU_AUDIT',json.dumps(r),flush=True)
