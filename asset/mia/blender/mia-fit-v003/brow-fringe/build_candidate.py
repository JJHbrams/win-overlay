"""Build a sparse logical-Fringe narrowing field from current CPU readback."""
from pathlib import Path
from collections import deque
import hashlib,json
import numpy as np

P=Path(__file__).resolve().parent;a=np.load(P/'current-inputs.npz');meta=json.loads((P/'current-inputs.json').read_text())
ids=a['fringe_point_ids'];q=a['fringe_world'];raw=a['fringe_raw_local'];faces=a['fringe_faces'];comp=a['fringe_component_ids'];anchors=set(map(int,a['fringe_anchor_point_ids']))
lookup={int(v):i for i,v in enumerate(ids)};world_delta=np.zeros_like(q);logical=[]
# Existing asymmetrical source part and large central diagonal lock remain.
# Only actually foreground-intersecting fine/front-sheet families are narrowed.
factors={44:.70,57:.60,67:.60,68:.86,71:.88,81:.76,106:.72,117:.62,127:.58,132:.68,135:.72}
for cid,factor in factors.items():
    fs=faces[comp==cid];vids=np.unique(fs);ix=np.array([lookup[int(v)] for v in vids]);v=q[ix]
    top=v[v[:,2]>=np.percentile(v[:,2],85)].mean(0);bottom=v[v[:,2]<=np.percentile(v[:,2],15)].mean(0)
    direction=(bottom-top)[[0,2]];direction/=max(np.linalg.norm(direction),1e-12);cross=np.array([-direction[1],direction[0]])
    xz=v[:,[0,2]];center=xz.mean(0);t=(xz-center)@direction;across=(xz-center)@cross
    fit=np.polyfit(t,across,2);center_across=np.polyval(fit,t);residual=across-center_across
    local={int(v):i for i,v in enumerate(vids)};adj=[set() for _ in vids]
    for f in fs:
        for x,y in [(f[0],f[1]),(f[1],f[2]),(f[2],f[0])]:
            adj[local[int(x)]].add(local[int(y)]);adj[local[int(y)]].add(local[int(x)])
    root_mask=np.array([int(v) in anchors for v in vids])|(v[:,2]>=np.percentile(v[:,2],90))
    distance=np.full(len(v),1000.);queue=deque(np.flatnonzero(root_mask).tolist());distance[root_mask]=0
    while queue:
        i=queue.popleft()
        for j in adj[i]:
            if distance[j]>distance[i]+1:distance[j]=distance[i]+1;queue.append(j)
    w=np.clip(distance/3,0,1);w=w*w*w*(w*(w*6-15)+10)
    axial=np.clip((v[:,2].max()-v[:,2])/(max(np.ptp(v[:,2]),1e-9)*.45),0,1)
    axial=axial*axial*axial*(axial*(axial*6-15)+10);w*=axial
    delta=np.zeros_like(v);delta[:,[0,2]]=(-residual*(1-factor)*w)[:,None]*cross
    for _ in range(2):
        smoothed=delta.copy()
        for i,neighbours in enumerate(adj):
            if neighbours and not root_mask[i]:smoothed[i]=.75*delta[i]+.25*np.mean(delta[list(neighbours)],axis=0)
        delta=smoothed;delta[root_mask]=0
    world_delta[ix]+=delta
    logical.append({'component':cid,'width_factor':factor,'source_polygon_ids':a['fringe_source_polygon_ids'][comp==cid].tolist(),
                    'point_ids':vids.tolist(),'fixed_root_or_boundary_ids':vids[root_mask].tolist(),
                    'root_world':top.tolist(),'tip_world':bottom.tolist(),'maximum_move_mm':float(np.linalg.norm(delta,axis=1).max()*1000),
                    'rationale':'Existing foreground Fringe family; narrow its cross-strand width along its own root-to-tip centerline, without moving its centerline or alpha-cutting a gap.'})
world_delta[np.array([int(i) in anchors for i in ids])]=0
move=np.linalg.norm(world_delta,axis=1)>1e-9;selected=ids[move]
matrix=np.asarray(meta['main_matrix_world']);local_delta=world_delta[move]@np.linalg.inv(matrix[:3,:3]).T
assert np.max(np.linalg.norm(q-(raw@matrix[:3,:3].T+matrix[:3,3]),axis=1))<1e-6,'Fringe pose must be freshly mapped if neutral Head transform differs'
np.savez_compressed(P/'fringe-A.npz',indices=selected,expected_basis=raw[move],delta_local=local_delta.astype(np.float32),
                    owned_face_ids=a['fringe_face_ids'],expected_owned_faces=a['fringe_faces'],expected_source_ids=a['fringe_source_polygon_ids'])
report={'candidate':'A','owner':meta['owner'],'baseline_native_sha256':meta['sha256'],'base_raw_sha256':meta['main_raw_sha256'],
        'original_vertices':meta['main_vertices'],'original_faces':meta['main_faces'],'original_six_UV_hashes':meta['UV_hashes'],
        'base_topology_sha256':meta['main_topology_sha256'],
        'logical_clumps':logical,'changed_points':int(move.sum()),'max_move_mm':float(np.linalg.norm(local_delta,axis=1).max()*1000),
        'fixed_semantic_boundary_points':len(anchors),'payload_sha256':hashlib.sha256((P/'fringe-A.npz').read_bytes()).hexdigest(),
        'brow_width_case':{'-1':{'observed_u':list(meta['source_supported_windows']['-1'][k] for k in ['u_min','u_max']),'factor':1.04},
                           '1':{'observed_u':list(meta['source_supported_windows']['1'][k] for k in ['u_min','u_max']),'factor':.84}},
        'brow_ink_linear_rgba':[.026,.019,.023,1],
        'source_limit':'Visible source bar thickness differs between sides and hair occlusion. Hidden full tails remain inferred; no brow centerline lift or symmetrization.',
        'scope':'Actual sparse additive Main key; separate dynamic brow strip-width modifier before final Shrinkwrap; no source/face/head/body/topology/UV edits.',
        'native_saved':False,'gpu_used':False,'ART':'UNVERIFIED until actual source paired images'}
(P/'candidate-A.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({k:report[k] for k in ['candidate','changed_points','max_move_mm','fixed_semantic_boundary_points']}))
