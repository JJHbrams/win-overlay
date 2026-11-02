"""Actual source-band-driven ordered torso surface + separate3D branch field.

No q0/q1 breast-depth restoration seed. Originalv06 controls global stations;
reaffirmed E2/F2 measured exterior/axillary bands control the broad local form.
"""
from pathlib import Path
import json,hashlib
import numpy as np
from field_math import smooth,cubic_z,periodic_theta
P=Path(__file__).resolve().parent;O=P/'posed-target';C=P/'source-binding'
source=json.loads((C/'constraints.json').read_text());g=json.loads((P/'scaffold-D/guide-data.json').read_text());a=np.load(O/'target-01.npz');m=np.load(P/'inputs/mapping-frame1.npz');old=np.load(P/'current-body-limit.npz');W=np.load(P/'current-body-weights.npz');q0=a['q0_world'];q1=a['target_world'];N=len(q0);R=m['matrix_world'][:3,:3];core=q0-np.einsum('nij,nj->ni',m['J_world_from_local'],old['soft_G']@np.linalg.inv(R).T);theta=np.arctan2(core[:,0],-(core[:,1]+.018));height=core[:,2];arm=W['arm_sum']
gs=sorted(g['stations'],key=lambda s:s['z']);gz=np.array([s['z'] for s in gs]);hz=lambda key,z:float(np.interp(z,gz,[s[key] for s in gs]));bands=source['section_support_bands'];heights=sorted(set([s['z'] for s in gs]+[s['world_z'] for s in bands]));angles=np.array([-np.pi,-2.3,-1.75,-1.40,-1.05,-.65,-.35,0,.35,.65,1.05,1.40,1.75,2.3]);rings=[];ring_records=[]
for z in heights:
    hx=hz('outer_half_width',z);yc=hz('front_core_y',z);back=hz('back_y',z);pole=hz('front_outer_y',z);lateral=.75*pole+.25*(-.004);latx=.9*hx;peakx=.60*hx;band=next((s for s in bands if abs(s['world_z']-z)<1e-8),None)
    if band:
        pole=band['chosen_broad_pole_y'];lateral=band['chosen_lateral_y'];latx=band['inferred_lateral_x'];peakx=band['inferred_peak_x']
    coords={0:(0,yc),.35:(.30*hx,yc+.72*(pole-yc)),.65:(peakx,pole),1.05:(latx,lateral),1.40:(1.02*hx,.65*lateral+.35*(-.004)),1.75:(.98*hx,.035),2.3:(.64*hx,back*.90),np.pi:(0,back)}
    r=[]
    for u in angles:
        xx,yy=coords[abs(u)];r.append([np.sign(u)*xx,yy,z])
    rings.append(r);ring_records.append(dict(z=z,kind='observed-envelope-constrained' if band else 'inferred-continuous-thorax/root',band_station=band['station'] if band else None,points=r))
def torso_target(u,v):
    vals=np.asarray([periodic_theta(angles,np.asarray(r),u) for r in rings]);return cubic_z(np.asarray(heights),vals,v)
F=torso_target(theta,height);dF=F-q1

# The torso cylinder is used only on the injective inner chart. Fold/humeral
# branches use unique 3D core positions and explicit source fold bands instead.
obs={};roles={}
def add(i,value,role):
    obs.setdefault(int(i),[]).append(np.asarray(value));roles.setdefault(int(i),set()).add(role)
inner=np.flatnonzero((abs(theta)>.72)&(abs(theta)<1.05)&(height>1.165)&(height<1.355)&(np.arange(N)<3957)&(arm<.60))
for i in inner:add(i,dF[i],'source_surface_interface')
fold_matches=[]
for sign in [-1,1]:
    eligible=np.flatnonzero((np.sign(core[:,0])==sign)&(abs(core[:,0])>.085)&(abs(core[:,0])<.21)&(height>1.26)&(height<1.375)&(q1[:,1]<.045)&(arm>.025)&(arm<.95)&(np.arange(N)<3957))
    for band in source['anterior_fold_bands']:
        target=np.array([sign*band['inferred_x'],band['inferred_y'],band['world_z']]);i=int(eligible[np.linalg.norm(q1[eligible]-target,axis=1).argmin()]);distance=np.linalg.norm(q1[i]-target);within=band['uncertainty_m'];value=(target-q1[i])*max(0,1-within/max(distance,1e-12));add(i,value,'observed_fold_band');fold_matches.append(dict(raw_id=i,target=target.tolist(),current_distance_m=float(distance),allowed_band_m=within,required_displacement=value.tolist(),arm_weight=float(arm[i])))
zero=np.flatnonzero((np.arange(N)<3957)&(abs(core[:,0])>.07)&(abs(core[:,0])<.27)&(height>1.10)&(height<1.42)&((core[:,1]>.035)|(abs(core[:,0])>.205)|(height>1.38)|(height<1.15)))
for i in zero[::2]:add(i,np.zeros(3),'posterior_or_outer_transport_boundary')
ids=np.asarray(sorted(obs));pos=core[ids];values=np.asarray([np.mean(obs[int(i)],axis=0) for i in ids]);sigma=.045;K=np.exp(-((pos[:,None]-pos[None,:])**2).sum(2)/sigma**2);coef=np.linalg.solve(K+np.eye(len(K))*.003,values);dB=np.exp(-((core[:,None]-pos[None,:])**2).sum(2)/sigma**2)@coef
zGain=smooth((height-1.105)/.045)*smooth((1.385-height)/.035);chart=smooth((1.10-abs(theta))/.20);branch=smooth((2.15-abs(theta))/.30)*smooth((.25-abs(core[:,0]))/.04)*smooth((.075-core[:,1])/.03);delta=zGain[:,None]*(chart[:,None]*dF+(1-chart)[:,None]*branch[:,None]*dB);delta[np.arange(N)>=3957]=0;delta[q0[:,2]>=1.425]=0;q=q1+delta;local=m['q0_local']+(q-q0)@np.linalg.inv(R).T;local[3957:]=m['q0_local'][3957:];local[q0[:,2]>=1.425]=m['q0_local'][q0[:,2]>=1.425]
assert np.array_equal(q[3957:],q0[3957:]) and np.array_equal(q[q0[:,2]>=1.425],q0[q0[:,2]>=1.425]) and np.isfinite(q).all()
np.savez_compressed(O/'target-04.npz',q0_world=q0,target_world=q,target_local=local,delta_world=q-q0,patch_delta_world=delta,parameter_theta=theta,parameter_height=height,torso_chart_weight=chart,branch_displacement=dB,source_section_angles=angles,source_section_heights=np.asarray(heights),source_section_points=np.asarray(rings),branch_observation_ids=ids,branch_observation_values=values,control_ids=np.flatnonzero(np.linalg.norm(q-q0,axis=1)>1e-9))
(C/'source-3D-sections-04.json').write_text(json.dumps(dict(constraints_sha256=hashlib.sha256((C/'constraints.json').read_bytes()).hexdigest(),angles=angles.tolist(),sections=ring_records,fold_matches=fold_matches,limits='Real3D target sections for the supported envelope. Observed exterior support and inferred core/attachment are separate. Source height/pose conflicts remain in constraints.json. No posterior membrane or isolated breast objects.'),indent=2)+'\n',encoding='utf-8')
report=dict(method='Direct source-constrained continuous ordered sections + independent3D Gaussian branch transport. No old q0/q1 Y-shape seed, no10hardpoleanchors, no cylindrical chart on folded axilla.',source_constraint_sha256=hashlib.sha256((C/'constraints.json').read_bytes()).hexdigest(),source_used=str(source['source']),source_sections=len(bands),section_knots=len(heights),branch_observations=len(ids),source_fold_observations=fold_matches,branch_fit_max_residual_mm=float(np.linalg.norm(K@coef-values,axis=1).max()*1000),max_patch_move_mm=float(np.linalg.norm(delta,axis=1).max()*1000),face690_exact=True,head_above1_425_exact=True,neck_branch='Torso field closes below1.385; actualneck/chart remains current and separate, notdiscarded from totalbody scope.',original47_rig_uv_materials_untouched=True,status='CPU source-bound hypothesis; final evaluated sections/contact/source-lowviews required. No anatomy/ART/rig approval.')
(O/'construction-04.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('SOURCE_BOUND_TARGET_04_DATA_DONE',json.dumps(report),flush=True)
