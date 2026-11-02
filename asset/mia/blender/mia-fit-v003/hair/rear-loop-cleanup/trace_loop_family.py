"""Inventory complete front skins near the topological U backing branch. DATA only."""
from pathlib import Path
import numpy as np,json,collections
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent;d=np.load(P/'source-mesh-input.npz');co=d['co'];T=d['faces'];raw=d['raw_ids'];labels=np.load(P/'global-components.npz')['face_component'];top=np.load(P/'topology-analysis.npz');F=top['physical_faces'];edges=collections.defaultdict(list)
for i,t in enumerate(F):
 for a,b in [(t[0],t[1]),(t[1],t[2]),(t[2],t[0])]:edges[tuple(sorted((int(a),int(b))))].append(i)
adj=[set() for _ in T]
for fs in edges.values():
 for i in fs:adj[i].update(j for j in fs if i!=j)
seed=int(np.flatnonzero(raw==99704)[0]);join=1.4541616439819336;eligible=(labels==488)&(co[T][:,:,2].max(1)<join);seen={seed};queue=[seed]
for i in queue:
 for j in adj[i]:
  if j not in seen and eligible[j]:seen.add(j);queue.append(j)
branch=np.array(sorted(seen),np.int32);np.savez_compressed(P/'backing-branch-DATA.npz',polygon_indices=branch)
bvh=BVHTree.FromPolygons(co.tolist(),T[branch].tolist(),all_triangles=True);report=[]
for k in np.unique(labels):
 if k==488:continue
 rows=np.flatnonzero(labels==k);pts=co[np.unique(T[rows])]
 if pts[:,2].max()<1.30 or pts[:,2].min()>1.46 or pts[:,0].min()>.065 or pts[:,0].max()<-.065 or pts[:,1].max()<.065:continue
 ds=np.array([bvh.find_nearest(Vector(p))[3] for p in pts]);report.append(dict(component=int(k),faces=len(rows),vertices=len(pts),bounds=[pts.min(0).tolist(),pts.max(0).tolist()],nearest_branch_distance_quantiles=np.quantile(ds,[0,.5,.9,1]).tolist(),within_14mm=float(np.mean(ds<.014)),pure_Rear=float(d['semantic_weights'][T[rows],3].min())))
report.sort(key=lambda x:x['nearest_branch_distance_quantiles'][1]);boundary=[];branchset=set(branch.tolist())
for edge,fs in edges.items():
 if any(f in branchset for f in fs) and any(f not in branchset for f in fs):boundary.append(edge)
np.savez_compressed(P/'backing-root-boundary-DATA.npz',physical_vertex_edges=np.array(boundary,np.int32));(P/'loop-family-inventory-DATA.json').write_text(json.dumps(dict(backing=dict(faces=len(branch),first_topological_join_height=join,seed_raw=99704,bounds=[co[np.unique(T[branch])].min(0).tolist(),co[np.unique(T[branch])].max(0).tolist()],attachment_cut_edges=len(boundary)),components=report,limits='Nearest distance inventories whole front skin candidates; it does not authorize a distance or spatial production mask.'),indent=2)+'\n',encoding='utf-8');print('BACKING_BRANCH',len(branch),'ROOT_EDGES',len(boundary));print(json.dumps(report,indent=2))
