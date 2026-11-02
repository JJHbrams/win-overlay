"""Local actual-surface fairing with anatomical transition handles, not primitives.

Candidate A is a real cage-coordinate edit. Fixed thorax and outside region
stay exact; no scalar volume restoration or cone/ellipse mass remapping.
"""
from pathlib import Path
import json,numpy as np
P=Path(__file__).resolve().parent;d=np.load(P/'current-body-limit.npz');p=d['raw_world'].astype(float);edges=d['raw_edges'];core=d['core'];soft=d['soft_G'];lower=d['lower'];nall=len(p)
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
ax=abs(p[:,0]+.0004777);z=p[:,2];front=p[:,1]<-.025
# Actual soft-mass patch plus two neighboring control rings, bounded on chest.
seed=(np.linalg.norm(soft,axis=1)>.001)&(np.arange(nall)<3957)
adj=[set() for _ in range(nall)]
for i,j in edges:adj[i].add(int(j));adj[j].add(int(i))
patch=set(np.flatnonzero(seed).tolist())
for _ in range(2):patch.update(j for i in list(patch) for j in adj[i])
selected=np.asarray(sorted(i for i in patch if i<3957 and front[i] and ax[i]<.132 and 1.184<z[i]<1.344),dtype=int)
lookup={int(i):j for j,i in enumerate(selected)};n=len(selected)
# Discrete bending of the actual cage position, including fixed neighbors.
L=np.zeros((n,n));boundary=np.zeros((n,3))
for row,i in enumerate(selected):
    L[row,row]=1.;neighbors=sorted(adj[i]);weight=1/np.maximum(np.linalg.norm(p[neighbors]-p[i],axis=1),.003);weight/=weight.sum()
    for j,w in zip(neighbors,weight):
        if j in lookup:L[row,lookup[j]]-=w
        else:boundary[row]-=w*p[j]
# Three independently named surface handles, anchored to actual positions:
# round the projecting pole; soften/fill upper root; unfold inferior attachment.
pole=smooth((np.linalg.norm(soft,axis=1)-.045)/.02)*smooth((z-1.205)/.020)*smooth((1.275-z)/.020)
upper=smooth((z-1.282)/.016)*smooth((1.341-z)/.020)*smooth((ax-.012)/.025)*smooth((.108-ax)/.022)
return_handle=smooth((z-1.184)/.010)*smooth((1.222-z)/.020)*smooth((ax-.008)/.020)*smooth((.103-ax)/.025)
target=p.copy();target[:,1]+=.012*pole-.0045*upper-.0035*return_handle;target[:,2]+=.004*return_handle
W=.8+14*pole+7*upper+9*return_handle
# Protect depth/height landmarks through actual handle regions; fair between.
A=np.diag(W[selected])+4*(L.T@L)
rhs=W[selected,None]*target[selected]-4*(L.T@boundary)
q=p.copy();q[selected]=np.linalg.solve(A,rhs)
# Source front transverse silhouette retained exactly. This is one 3D Y/Z
# correction applied to every view, not a per-camera shape change.
q[:,0]=p[:,0]
delta=q-p
ids=np.flatnonzero(np.linalg.norm(delta,axis=1)>1e-8)
assert ids.max()<3957 and delta[3957:].max()==0
assert np.max(np.linalg.norm(delta,axis=1))<.025
# Core data remains unchanged. The new surface is a soft field over this core.
assert np.isfinite(q).all()
local_delta=delta@np.linalg.inv(d['matrix_world'][:3,:3]).T
np.savez_compressed(P/'form-A-delta.npz',indices=ids,world_delta=delta[ids],local_delta=local_delta[ids].astype(np.float32),baseline_selected=d['raw'][ids],baseline_world=p,selected_world=q,core=core,soft_before=soft,soft_after=soft+delta,lower=lower,patch_indices=selected,handles=np.stack([pole,upper,return_handle],axis=1),key_names=d['key_names'])
report=dict(method='Actual cage bending-energy fairing with separate pole, thin upper root and inferior attachment surface handles. Fixed thorax data and all outside coordinates remain exact. No primitive/volume coefficient/mapping Jacobian is used as art authority.',patch_controls=n,changed_controls=len(ids),maximum_move_mm=float(np.linalg.norm(delta,axis=1).max()*1000),maximum_anterior_retraction_mm=float(delta[:,1].max()*1000),maximum_root_fill_mm=float(-delta[:,1].min()*1000),maximum_vertical_move_mm=float(abs(delta[:,2]).max()*1000),all_X_exact=True,face690_delta_zero=bool(not delta[3957:].any()),thorax_core_unchanged=True,original47_not_rewritten=True,handle_targets_mm=dict(pole_retraction=12.,upper_root_fill=4.5,inferior_return_fill=3.5,inferior_return_lift=4.),source_limit='Handle displacements are bounded engineering/art hypotheses, not calibrated source dimensions. Must judge actual source silhouettes and current/candidate gray views.',status='CPU_CHALLENGER_ONLY')
(P/'form-A-construction.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('V003_BODY_FORM_A_SOLVED',json.dumps(report),flush=True)
