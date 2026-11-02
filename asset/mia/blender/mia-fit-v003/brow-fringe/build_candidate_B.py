"""Coherent complete-forelock skin/backing narrowing from actual depth traces."""
from pathlib import Path
import hashlib,json
import numpy as np
P=Path(__file__).resolve().parent;data=np.load(P/'main-logical-inputs.npz');old=json.loads((P/'candidate-A.json').read_text());q=data['world'];raw=data['raw'];faces=data['faces'];roots=data['face_component_root'];delta=np.zeros_like(q)
groups=[
    ('screen_left_outer_forelock',[34013,37707,39972,42926,46927,35163],.90,-.0030),
    ('screen_left_fine_forelock',[47790,47982,48443],.65,-.0005),
    ('screen_left_inner_forelock',[48868,48535,41036,49058,48600],.80,.0028),
    ('screen_right_inner_fine_forelock',[56539,58044],.75,-.0012),
    ('screen_right_diagonal_forelock',[60079,56676,59915,59480,60595,60217,60696,61608,60299],.72,.0028)]
logical=[];owned=[]
def smooth(t):
    t=np.clip(t,0,1);return t*t*t*(t*(t*6-15)+10)
for name,component_roots,factor,shift in groups:
    fi=np.flatnonzero(np.isin(roots,component_roots));ids=np.unique(faces[fi]);v=q[ids];owned.extend(fi.tolist())
    top=v[v[:,2]>=np.percentile(v[:,2],90)].mean(0);tip=v[v[:,2]<=np.percentile(v[:,2],10)].mean(0)
    axis=(tip-top)[[0,2]];axis/=np.linalg.norm(axis);cross=np.array([-axis[1],axis[0]]);xz=v[:,[0,2]];center=xz.mean(0)
    t=(xz-center)@axis;across=(xz-center)@cross;centerline=np.polyval(np.polyfit(t,across,3),t);res=across-centerline
    zrange=np.ptp(v[:,2]);u=(v[:,2].max()-v[:,2])/zrange
    weight=smooth((u-.12)/.24)*smooth((.94-u)/.20)
    field=np.zeros_like(v);field[:,[0,2]]=(-res*(1-factor)*weight)[:,None]*cross;field[:,0]+=shift*weight
    root_or_tip=(u<=.12)|(u>=.94);field[root_or_tip]=0
    delta[ids]=field
    logical.append({'family':name,'complete_component_roots':component_roots,'faces':len(fi),'point_ids':ids.tolist(),
        'root_world':top.tolist(),'tip_world':tip.tolist(),'fixed_root_or_tip_ids':ids[root_or_tip].tolist(),
        'source_polygon_ids':data['source_polygon'][fi].tolist(),'width_factor':factor,'lateral_shift_m':shift,
        'max_move_mm':float(np.linalg.norm(field,axis=1).max()*1000),
        'selection_evidence':'Actual source-window Main first-hit plus successively uncovered backing components; complete disconnected forelock islands, not a spatial cap stripe.',
        'source_limit':'Coherent narrower clumps preserve root/tip caps and depth spacing. Fine source-gap correspondence and silhouette require actual paired images.'})
indices=np.flatnonzero(np.linalg.norm(delta,axis=1)>1e-9);owned=np.unique(owned)
assert np.max(np.linalg.norm(q-raw,axis=1))<1e-6,'Neutral head-local conversion must be remeasured'
np.savez_compressed(P/'fringe-B.npz',indices=indices,expected_basis=raw[indices],delta_local=delta[indices].astype(np.float32),
    owned_face_ids=owned,expected_owned_faces=faces[owned],expected_source_ids=data['source_polygon'][owned])
cfg=dict(old);cfg.update(candidate='B',logical_clumps=logical,changed_points=len(indices),max_move_mm=float(np.linalg.norm(delta,axis=1).max()*1000),
    fixed_semantic_boundary_points='Replaced strict semantic-subset boundary by complete-island fixed root/tip caps',
    payload_sha256=hashlib.sha256((P/'fringe-B.npz').read_bytes()).hexdigest(),
    scope='Coherent complete source-supported forelock skin+backing sparse key; fixed root/tip caps; original Main data and depth spacing retained. No new cap stripes or transparency.')
(P/'candidate-B.json').write_text(json.dumps(cfg,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'candidate':'B','points':len(indices),'owned_faces':len(owned),'max_move_mm':cfg['max_move_mm']}))
