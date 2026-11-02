"""Current-scene source-fit torso/bust challenger; no old scene/shape replay.

Source selected transverse cup/ribcage size and supported height drive the field.
The inherited soft-decomposition identifies the actual down-compressed rows;
its sag is reduced rather than preserving a known hooked return. No sphere,
cone, volume coefficient or new topology. Shoulder rest proposal is separate.
"""
from pathlib import Path
import json,hashlib
import numpy as np
P=Path(__file__).resolve().parent;d=np.load(P/'current-body-limit.npz');p=d['raw_world'].copy();core=d['core'];soft=d['soft_G'];n=len(p);center=-.0004777
def smooth(t):
    t=np.clip(t,0,1);return t*t*(3-2*t)
x=abs(core[:,0]-center);z=core[:,2];y=core[:,1];mass=np.linalg.norm(soft,axis=1);weights=np.load(P/'current-body-weights.npz');arm_mask=1-smooth((weights['arm_sum']-.05)/.45)
# Actual thorax-sized envelope. Hips/legs and the neck/head are excluded.
vertical=smooth((z-1.125)/.085)*smooth((1.345-z)/.040)
lateral=smooth((.170-x)/.045)
torso=vertical*lateral*arm_mask*(np.arange(n)<3957)
# 30% more transverse ribcage support near the cup; pole X is an observed
# source landmark, so the soft surface there stays centered rather than
# moving both breasts apart merely to increase width.
core_dx=(core[:,0]-center)*.30*torso
pole_seat=smooth((mass-.045)/.025)*np.exp(-((z-1.256)/.045)**4)
dx=core_dx*(1-pole_seat)
# Round the thorax profile modestly. Relative soft projection is retained.
dy=(y+.010)*.10*torso
# Fill upper/lateral supported mass; its upper edge still tapers into skin.
upper=smooth(mass/.018)*np.exp(-((z-1.286)/.030)**2)*smooth((1.345-z)/.015)*arm_mask
dy-=.007*upper
# The actual inherited sag compressed neighboring lower rows to z~1.197.
# Reopen that material flow and raise the pole by about19mm, with no vertex
# reorder or whole-mass volume scalar. Current raw data remain untouched.
dz=-.80*soft[:,2]*smooth((1.345-z)/.015)*arm_mask
delta=np.column_stack([dx,dy,dz]);delta[np.arange(n)>=3957]=0
# Protect true head and every body region outside the declared torso envelope.
assert np.max(abs(delta[3957:]))==0
assert np.max(abs(delta[z<1.12]))==0
assert np.max(abs(delta[z>1.345]))==0
assert np.max(abs(delta[weights['arm_sum']>=.5]))==0
q=p+delta;ids=np.flatnonzero(np.linalg.norm(delta,axis=1)>1e-9);local=delta@np.linalg.inv(d['matrix_world'][:3,:3]).T
assert np.linalg.norm(delta,axis=1).max()<.045
np.savez_compressed(P/'form-C-delta.npz',indices=ids,world_delta=delta[ids],local_delta=local[ids].astype(np.float32),baseline_selected=d['raw'][ids],baseline_world=p,selected_world=q,key_names=d['key_names'],core_delta=np.column_stack([core_dx,(y+.010)*.10*torso,np.zeros(n)]),source_surface_delta=delta,semantic_soft_indices=np.flatnonzero(mass>1e-6))
pole=[3697];lower=[3570,3586,3603,3624,3648,3672]
report=dict(method='Source-fit transverse thorax + upper/lateral support, actual inherited down-compression reopened. Additive current-body field; no G replay, cone/sphere, volume scalar or original-key rewrite.',source_authority='User-confirmed v06 received20261102',source_sha256='6d88d1bc6b579d1ac53436d9f1fa50f903117ac244e307b8e08a9d1e270080e1',changed_controls=len(ids),max_move_mm=float(np.linalg.norm(delta,axis=1).max()*1000),max_transverse_mm=float(abs(dx).max()*1000),max_profile_mm=float(abs(dy).max()*1000),max_up_mm=float(dz.max()*1000),pole_control=[dict(index=i,current=p[i].tolist(),candidate=q[i].tolist(),delta_mm=(delta[i]*1000).tolist()) for i in pole],lower_material_rows=[dict(index=i,core_z=float(core[i,2]),current_z=float(p[i,2]),candidate_z=float(q[i,2])) for i in lower],shoulders='No shoulder rest relocation in this torso/breast challenger; separately gated paired surface/rest strategy follows actual skin measurement.',head_face690_exact=True,hips_legs_exact=True,keys47_not_rewritten=True,material_UV_weights_exact=True,status='CPU_CHALLENGER_ONLY; actual neutral/source front/profile/oblique required before selection')
(P/'form-C-construction.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('V003_FORM_C_FIELD_DONE',json.dumps(report),flush=True)
