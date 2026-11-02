"""Root-held, continuously tapered distal forelocks; no restored thick tip rings."""
from pathlib import Path
import hashlib,json,numpy as np
P=Path(__file__).resolve().parent;data=np.load(P/'main-logical-inputs.npz');cfg=json.loads((P/'candidate-B.json').read_text());q=data['world'];raw=data['raw'];faces=data['faces'];roots=data['face_component_root'];delta=np.zeros_like(q);logical=[];owned=[]
def smooth(t):
    t=np.clip(t,0,1);return t*t*t*(t*(t*6-15)+10)
tip_factors={'screen_left_outer_forelock':.42,'screen_left_fine_forelock':.28,'screen_left_inner_forelock':.35,'screen_right_inner_fine_forelock':.28,'screen_right_diagonal_forelock':.32}
for old in cfg['logical_clumps']:
    name=old['family'];fi=np.flatnonzero(np.isin(roots,old['complete_component_roots']));ids=np.unique(faces[fi]);v=q[ids];owned.extend(fi.tolist())
    top=v[v[:,2]>=np.percentile(v[:,2],90)].mean(0);tip=v[v[:,2]<=np.percentile(v[:,2],10)].mean(0);axis=(tip-top)[[0,2]];axis/=np.linalg.norm(axis);cross=np.array([-axis[1],axis[0]])
    xz=v[:,[0,2]];center=xz.mean(0);t=(xz-center)@axis;across=(xz-center)@cross;centerline=np.polyval(np.polyfit(t,across,3),t);res=across-centerline
    # One shared longitudinal coordinate per whole family: points across the
    # same slanted crosssection must receive the same positive taper scale.
    u=(t-t.min())/np.ptp(t);u_z=(v[:,2].max()-v[:,2])/np.ptp(v[:,2]);root_gain=smooth((u-.12)/.24);width=old['width_factor']+(tip_factors[name]-old['width_factor'])*smooth((u-.50)/.50)
    field=np.zeros_like(v);field[:,[0,2]]=(-res*(1-width)*root_gain)[:,None]*cross
    field[:,0]+=old['lateral_shift_m']*root_gain*(1-.5*smooth((u-.90)/.10))
    # Keep finite depth, with a gentle coherent distal taper of the full skin/backing bundle.
    depthcenter=np.polyval(np.polyfit(t,v[:,1],3),t);field[:,1]=-(v[:,1]-depthcenter)*.25*smooth((u-.65)/.35)*root_gain
    fixed=(u_z<=.12)|(data['root_locked'][ids]>.5);field[fixed]=0;delta[ids]=field
    bins=[]
    for lo,hi in [(.35,.55),(.55,.75),(.75,.90),(.90,1.00001)]:
        hit=(u>=lo)&(u<hi)
        if hit.sum()<3:continue
        before=v[hit];after=(v+field)[hit];bw=np.ptp((before[:,[0,2]]-center)@cross);aw=np.ptp((after[:,[0,2]]-center)@cross)
        bins.append({'longitudinal_interval':[lo,hi],'samples':int(hit.sum()),'cross_width_before_mm':float(bw*1000),'cross_width_after_mm':float(aw*1000),'depth_before_mm':float(np.ptp(before[:,1])*1000),'depth_after_mm':float(np.ptp(after[:,1])*1000)})
    logical.append(dict(old,fixed_root_ids=ids[fixed].tolist(),fixed_root_or_tip_ids=ids[fixed].tolist(),tip_ring_restored=False,tip_width_factor=tip_factors[name],distal_depth_factor=.75,
        max_move_mm=float(np.linalg.norm(field,axis=1).max()*1000),actual_vertex_section_bounds=bins,
        rationale='One coherent skin/backing field held at true/root caps; narrowing continues through every distal end instead of restoring a wide tip ring. No alpha cut, no brow displacement.'))
indices=np.flatnonzero(np.linalg.norm(delta,axis=1)>1e-9);owned=np.unique(owned)
assert np.all(delta[data['root_locked']>.5]==0)
np.savez_compressed(P/'fringe-C.npz',indices=indices,expected_basis=raw[indices],delta_local=delta[indices].astype(np.float32),owned_face_ids=owned,expected_owned_faces=faces[owned],expected_source_ids=data['source_polygon'][owned])
cfg.update(candidate='C',logical_clumps=logical,changed_points=len(indices),max_move_mm=float(np.linalg.norm(delta,axis=1).max()*1000),
    payload_sha256=hashlib.sha256((P/'fringe-C.npz').read_bytes()).hexdigest(),scope='True Roots_Locked and upper attachments fixed; coherent finite-width/depth taper continues through distal forelock skins/backings. Original Main raw/topology/UV/fields retained.')
(P/'candidate-C.json').write_text(json.dumps(cfg,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps({'candidate':'C','points':len(indices),'maximum_mm':cfg['max_move_mm'],'authored_root_locks_held':True}))
