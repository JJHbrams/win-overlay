"""Read Main's real detailed terminal branches at topology joins. DATA, not a mask."""
from pathlib import Path
import numpy as np,json,collections
P=Path(__file__).resolve().parent;R=P.parent/'rear-loop-cleanup';d=np.load(R/'source-mesh-input.npz');co=d['co'];T=d['faces'];top=np.load(R/'topology-analysis.npz');F=top['physical_faces'];labels=np.load(R/'global-components.npz')['face_component'];edges=collections.defaultdict(list)
for i,t in enumerate(F):
 for a,b in [(t[0],t[1]),(t[1],t[2]),(t[2],t[0])]:edges[tuple(sorted((int(a),int(b))))].append(i)
adj=[set() for _ in T]
for fs in edges.values():
 for i in fs:adj[i].update(j for j in fs if i!=j)
arrays={};rows=[];hidden=set(np.load(R/'loop-mask.npz')['polygon_indices'].tolist())
for h in [1.32,1.35,1.38,1.41,1.44]:
 eligible=(labels==488)&(co[T][:,:,2].max(1)<h);eligible[list(hidden)]=False;visited=set();parts=[]
 for i in np.flatnonzero(eligible):
  if i in visited:continue
  seen={int(i)};queue=[int(i)];visited.add(int(i))
  for f in queue:
   for j in adj[f]:
    if eligible[j] and j not in visited:visited.add(j);seen.add(j);queue.append(j)
  if len(seen)<60:continue
  ids=np.array(sorted(seen),np.int32);pts=co[np.unique(T[ids])];span=pts.max(0)-pts.min(0)
  if span[2]<.025:continue
  key='h'+str(round(h*100))+'_part'+str(len(parts));arrays[key]=ids;counts=collections.Counter(tuple(sorted((int(a),int(b)))) for t in F[ids] for a,b in [(t[0],t[1]),(t[1],t[2]),(t[2],t[0])]);boundary=[e for e,c in counts.items() if c==1];real=[e for e in boundary if len(edges[e])==1];cuts=[e for e in boundary if len(edges[e])>1];row=dict(key=key,faces=len(ids),bounds=[pts.min(0).tolist(),pts.max(0).tolist()],span=span.tolist(),natural_edges=len(real),root_cut_edges=len(cuts),seed_raw=int(d['raw_ids'][ids[np.argmin(co[T[ids]].mean(1)[:,2])]]),mean_semantic=d['semantic_weights'][T[ids]].mean((0,1)).tolist());rows.append(row);parts.append(row)
np.savez_compressed(P/'detailed-branch-inventory-DATA.npz',**arrays);(P/'detailed-branch-inventory-DATA.json').write_text(json.dumps(dict(purpose='Real topology branch candidates for new detailed layer copies; no Main mutation or automatic donor acceptance',branches=rows),indent=2)+'\n',encoding='utf-8');print('DETAIL_BRANCH_INVENTORY',len(rows));print(json.dumps(rows,indent=2))
