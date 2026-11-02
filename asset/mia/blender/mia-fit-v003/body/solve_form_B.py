"""Broaden the actual inferior return with fixed pole and boundary tangents."""
from pathlib import Path
import numpy as np,json
P=Path(__file__).resolve().parent;d=np.load(P/'current-body-limit.npz');p=d['raw_world'].astype(float);edges=d['raw_edges'];soft=d['soft_G'];nall=len(p)
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
ax=abs(p[:,0]+.0004777);z=p[:,2];adj=[set() for _ in range(nall)]
for i,j in edges:adj[i].add(int(j));adj[j].add(int(i))
seed=(np.linalg.norm(soft,axis=1)>.001)&(np.arange(nall)<3957);patch=set(np.flatnonzero(seed).tolist())
for _ in range(2):patch.update(j for i in list(patch) for j in adj[i])
pole=(np.linalg.norm(soft,axis=1)>.055)&(z>1.220)&(z<1.270)
selected=np.asarray(sorted(i for i in patch if i<3957 and p[i,1]<-.025 and ax[i]<.132 and 1.174<z[i]<1.344 and not pole[i]),dtype=int);lookup={int(i):j for j,i in enumerate(selected)};n=len(selected)
# Include the surrounding fixed ring's Laplacian rows: continuity is checked
# across the patch boundary, not only inside an independent displacement field.
rows=sorted(set(selected.tolist())|set(j for i in selected for j in adj[i]));L=np.zeros((len(rows),n));b=np.zeros((len(rows),3))
for row,i in enumerate(rows):
    if i in lookup:L[row,lookup[i]]=1.
    else:b[row]+=p[i]
    neighbors=sorted(adj[i]);w=1/np.maximum(np.linalg.norm(p[neighbors]-p[i],axis=1),.003);w/=w.sum()
    for j,v in zip(neighbors,w):
        if j in lookup:L[row,lookup[j]]-=v
        else:b[row]-=v*p[j]
upper=smooth((z-1.282)/.016)*smooth((1.341-z)/.020)*smooth((ax-.012)/.025)*smooth((.108-ax)/.022)
lower=smooth((z-1.174)/.014)*smooth((1.255-z)/.052)*smooth((ax-.006)/.018)*smooth((.112-ax)/.025)
target=p.copy();target[:,1]-=.005*upper+.010*lower;target[:,2]+=.008*lower
W=.6+9*upper+15*lower
A=np.diag(W[selected])+8*(L.T@L);rhs=W[selected,None]*target[selected]-8*(L.T@b);q=p.copy();q[selected]=np.linalg.solve(A,rhs);q[:,0]=p[:,0]
delta=q-p;ids=np.flatnonzero(np.linalg.norm(delta,axis=1)>1e-8)
assert not delta[pole].any() and not delta[3957:].any();assert np.linalg.norm(delta,axis=1).max()<.025
local=delta@np.linalg.inv(d['matrix_world'][:3,:3]).T
np.savez_compressed(P/'form-B-delta.npz',indices=ids,world_delta=delta[ids],local_delta=local[ids].astype(np.float32),baseline_selected=d['raw'][ids],baseline_world=p,selected_world=q,pinned_pole_indices=np.flatnonzero(pole),patch_indices=selected,handles=np.stack([upper,lower],axis=1),key_names=d['key_names'])
r=dict(method='Direct actual-surface fairing across inside and fixed outer boundary rows; pole region hard-fixed, broader inferior return filled/lifted, thin upper root supported. No cone/sphere, no volume scalar, no pole shrink.',changed_controls=len(ids),hard_pinned_pole_controls=int(pole.sum()),pole_coordinates_exact=True,source_transverse_X_exact=True,face690_delta_zero=True,maximum_move_mm=float(np.linalg.norm(delta,axis=1).max()*1000),maximum_root_fill_mm=float(-delta[:,1].min()*1000),maximum_lift_mm=float(delta[:,2].max()*1000),actual_boundary_rows=len(rows),fixed_thorax_data_unchanged=True,source_limit='The10mm fill/8mm lift handles are bounded correction hypotheses, not measured anatomy. Actual matte/source4/cup-support correspondence required.',status='CPU_CHALLENGER_ONLY')
(P/'form-B-construction.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print('V003_BODY_FORM_B_SOLVED',json.dumps(r))
