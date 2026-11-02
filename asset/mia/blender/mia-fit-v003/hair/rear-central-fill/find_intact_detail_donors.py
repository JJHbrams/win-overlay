"""Find closed terminal volumes with exactly one logical root contour. Read-only."""
from pathlib import Path
import numpy as np,json,collections
P=Path(__file__).resolve().parent;R=P.parent/'rear-loop-cleanup';d=np.load(R/'source-mesh-input.npz');co=d['co'];T=d['faces'];top=np.load(R/'topology-analysis.npz');F=top['physical_faces'];lab=np.load(R/'global-components.npz')['face_component'];ed=collections.defaultdict(list)
for i,t in enumerate(F):
 for a,b in [(t[0],t[1]),(t[1],t[2]),(t[2],t[0])]:ed[tuple(sorted((int(a),int(b))))].append(i)
adj=[set() for _ in T]
for fs in ed.values():
 for i in fs:adj[i].update(j for j in fs if i!=j)
hidden=np.load(R/'loop-mask.npz')['polygon_indices'];rows=[];payload={}
for hi in range(1340,1501,5):
 h=hi/1000;ok=(lab==488)&(co[T][:,:,2].max(1)<h);ok[hidden]=False;visited=set()
 for seed in np.flatnonzero(ok):
  if seed in visited:continue
  seen={int(seed)};q=[int(seed)];visited.add(int(seed))
  for i in q:
   for j in adj[i]:
    if ok[j] and j not in visited:visited.add(j);seen.add(j);q.append(j)
  if not 150<=len(seen)<=2500:continue
  ids=np.array(sorted(seen),np.int32);edges=collections.Counter(tuple(sorted((int(a),int(b)))) for t in F[ids] for a,b in [(t[0],t[1]),(t[1],t[2]),(t[2],t[0])]);boundary=[e for e,v in edges.items() if v==1];natural=[e for e in boundary if len(ed[e])==1]
  if natural:continue
  rootgraph=collections.defaultdict(set)
  for a,b in boundary:rootgraph[a].add(b);rootgraph[b].add(a)
  if any(len(v)!=2 for v in rootgraph.values()):continue
  rootseen=set();queue=[next(iter(rootgraph))]
  for i in queue:
   if i in rootseen:continue
   rootseen.add(i);queue.extend(j for j in rootgraph[i] if j not in rootseen)
  if len(rootseen)!=len(rootgraph):continue
  points=co[np.unique(T[ids])];span=points.max(0)-points.min(0)
  if span[2]<.04:continue
  key='Donor_'+str(len(rows));payload[key+'_faces']=ids;payload[key+'_root_physical_edges']=np.array(boundary,np.int32);row=dict(name=key,root_z=h,faces=len(ids),natural_boundary_edges=0,single_root_cycle_edges=len(boundary),bounds=[points.min(0).tolist(),points.max(0).tolist()],mean_semantics=d['semantic_weights'][T[ids]].mean((0,1)).tolist(),source_raw_ids=d['raw_ids'][ids].tolist());rows.append(row)
np.savez_compressed(P/'intact-detail-donors-DATA.npz',**payload);(P/'intact-detail-donors-DATA.json').write_text(json.dumps(dict(candidates=rows,scope='Read-only real connected terminal volumes; root contour cap will be concealed. Same-tip nested levels are alternatives, not distinct source shapes.'),indent=2)+'\n',encoding='utf-8');print('INTACT_DETAIL_DONORS',[(r['name'],r['root_z'],r['faces'],r['single_root_cycle_edges'],r['bounds']) for r in rows],flush=True)
