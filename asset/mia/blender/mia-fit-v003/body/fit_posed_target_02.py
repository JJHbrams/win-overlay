"""Connected anterior-surface thin-plate patch, preserving whole-body01.

This fairs FINAL control positions using the original uncompressed core metric,
not the smoothness label of a displacement. No topology, original key, or rig edit.
"""
from pathlib import Path
import json,hashlib
import numpy as np

P=Path(__file__).resolve().parent;O=P/'posed-target'
data=np.load(O/'target-01.npz');cache=np.load(P/'inputs/mapping-frame1.npz')
base=np.load(P/'current-body-limit.npz');topo=np.load(O/'control-topology.npz')
q1=data['target_world'];q0=data['q0_world'];N=len(q1)
R=cache['matrix_world'][:3,:3]
soft_local=base['soft_G']@np.linalg.inv(R).T
soft_world=np.einsum('nij,nj->ni',cache['J_world_from_local'],soft_local)
reference=q0-soft_world
tri=topo['triangles'];mat=topo['triangle_materials'];bodytri=tri[(mat<=1)&(tri.max(1)<3957)]
neighbors=[set() for _ in range(N)]
edge_weights={};areas=np.zeros(N)
for t in bodytri:
    p=reference[t]
    cross=np.linalg.norm(np.cross(p[1]-p[0],p[2]-p[0]))
    if cross<1e-14:continue
    areas[t]+=cross/6
    for k,(a,b) in enumerate([(1,2),(2,0),(0,1)]):
        i,j=int(t[a]),int(t[b]);neighbors[i].add(j);neighbors[j].add(i)
        cot=float(np.dot(p[a]-p[k],p[b]-p[k])/cross)
        edge=tuple(sorted((i,j)));edge_weights[edge]=edge_weights.get(edge,0.)+cot*.5

# Whole connected anterior patch includes old original root AND dense new rows.
# No arm-weight cutoff; the existing open axillary topology is retained.
roi=set(np.flatnonzero((np.arange(N)<3957)&(areas>0)&(abs(q1[:,0])<.160)&(q1[:,1]<.010)&(q1[:,2]>1.145)&(q1[:,2]<1.417)).tolist())
boundary={i for i in roi if any(j not in roi for j in neighbors[i])}
boundary|={j for i in list(boundary) for j in neighbors[i] if j in roi}
free=sorted(roi-boundary)
rows=sorted(roi|{j for i in roi for j in neighbors[i]})
columns=sorted(set(rows)|{j for i in rows for j in neighbors[i]})
col={i:k for k,i in enumerate(columns)};row={i:k for k,i in enumerate(rows)}
L=np.zeros((len(rows),len(columns)))
for (i,j),w in edge_weights.items():
    if i in row:L[row[i],col[i]]+=w;L[row[i],col[j]]-=w
    if j in row:L[row[j],col[j]]+=w;L[row[j],col[i]]-=w
assert np.min(areas[rows])>0
M=np.maximum(areas[rows],1e-10)
B=L.T@(L/M[:,None])

# The observed shelf changes tangent over2–4mm; keep the broad >30mm supported
# form while removing this high-frequency energy. This is a physical length,
# not a scalar breast-volume replacement or a per-triangle boundary fade.
length=.012
A=np.diag(np.maximum(areas[columns],1e-10))+length**4*B
rhs=np.maximum(areas[columns],1e-10)[:,None]*q1[columns]
mass=np.linalg.norm(base['soft_G'],axis=1)
pole=set(np.flatnonzero((mass>.068)&(q1[:,2]>1.24)&(q1[:,2]<1.285)&(np.arange(N)<3957)).tolist())
assert 4<=len(pole)<=40
fixed=set(columns)-set(free)
fixed|=pole
free=sorted(set(free)-pole)
fi=np.asarray([col[i] for i in free]);bi=np.asarray([col[i] for i in sorted(fixed)])
q=q1.copy();anchor=q1.copy()
# Retain the already-substantial baseline profile projection at supported pole
# controls, with01's source-raised height/width. It was lost8–12mm by radial fit.
anchor[list(pole),1]=q0[list(pole),1]
q[list(fixed)]=anchor[list(fixed)]
q[free]=np.linalg.solve(A[np.ix_(fi,fi)],rhs[fi]-A[np.ix_(fi,bi)]@anchor[np.asarray(sorted(fixed))])
delta=q-q1
outside=sorted(set(range(N))-roi)
assert np.array_equal(q[outside],q1[outside])
assert np.array_equal(q[3957:],q0[3957:])
assert np.array_equal(q[q0[:,2]>=1.425],q0[q0[:,2]>=1.425])
assert np.isfinite(q).all()
local=cache['q0_local']+(q-q0)@np.linalg.inv(R).T
local[3957:]=cache['q0_local'][3957:]
local[q0[:,2]>=1.425]=cache['q0_local'][q0[:,2]>=1.425]
np.savez_compressed(O/'target-02.npz',q0_world=q0,target_world=q,target_local=local,delta_world=q-q0,patch_delta_world=delta,patch_free=np.asarray(free,np.int32),patch_boundary=np.asarray(sorted(boundary),np.int32),pole_anchors=np.asarray(sorted(pole),np.int32),control_ids=np.flatnonzero(np.linalg.norm(q-q0,axis=1)>1e-9))
normal0=np.cross(q1[bodytri[:,1]]-q1[bodytri[:,0]],q1[bodytri[:,2]]-q1[bodytri[:,0]])
normal1=np.cross(q[bodytri[:,1]]-q[bodytri[:,0]],q[bodytri[:,2]]-q[bodytri[:,0]])
reversed_ids=np.flatnonzero((normal0*normal1).sum(1)<-1e-15)
def volume(v):
    t=topo['triangles'];p=v[t];return float(np.einsum('ij,ij->i',p[:,0],np.cross(p[:,1],p[:,2])).sum()/6)
report=dict(method='Area-weighted cotangent biharmonic final-position fairing on a connected original+refined anterior patch, with two fixed boundary rings and supported pole anchors. No topology or original data edit.',reference_metric='Exact q0 posed cage minus inherited soft_G transported by empirical current-pose Jacobian; no raw-T/world shortcut.',physical_filter_length_mm=length*1000,roi_vertices=len(roi),free_vertices=len(free),fixed_boundary_vertices=len(boundary),pole_anchors=sorted(pole),patch_bounds_min=q1[sorted(roi)].min(0).tolist(),patch_bounds_max=q1[sorted(roi)].max(0).tolist(),max_patch_move_mm=float(np.linalg.norm(delta,axis=1).max()*1000),outside_patch_bitexact=True,face690_bitexact=True,head_above1_425_bitexact=True,rig_keys_untouched=True,raw_common_triangle_reversals=len(reversed_ids),raw_reversed_body_triangle_ids=reversed_ids.tolist(),signed_raw_volume01_l=volume(q1)*1000,signed_raw_volume02_l=volume(q)*1000,base_target_sha256=hashlib.sha256((O/'target-01.npz').read_bytes()).hexdigest(),status='CPU surface hypothesis; actual evaluated arc/tangent, source and visual gates required. Not ART or motion approval.')
(O/'construction-02.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('POSED_TARGET_02_DATA_DONE',json.dumps(report),flush=True)
