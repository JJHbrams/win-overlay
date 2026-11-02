"""Quantify potential detailed Main fragments; no cap or source mutation yet."""
from pathlib import Path
import numpy as np,json,collections
P=Path(__file__).resolve().parent;R=P.parent/'rear-loop-cleanup';d=np.load(R/'source-mesh-input.npz');co=d['co'];T=d['faces'];phy=np.load(R/'topology-analysis.npz');F=phy['physical_faces'];points=phy['points'];parts=np.load(P/'detailed-branch-inventory-DATA.npz');result=[]
for name in ['h138_part2','h138_part17','h138_part1','h135_part10','h132_part5']:
 ids=parts[name];edges=collections.Counter(tuple(sorted((int(a),int(b)))) for t in F[ids] for a,b in [(t[0],t[1]),(t[1],t[2]),(t[2],t[0])]);be=[e for e,n in edges.items() if n==1];graph=collections.defaultdict(set)
 for a,b in be:graph[a].add(b);graph[b].add(a)
 visited=set();loops=[]
 for seed in graph:
  if seed in visited:continue
  seen={seed};q=[seed];visited.add(seed)
  for i in q:
   for j in graph[i]:
    if j not in visited:visited.add(j);seen.add(j);q.append(j)
  v=points[sorted(seen)];loops.append(dict(vertices=len(seen),all_degree2=all(len(graph[k])==2 for k in seen),bounds=[v.min(0).tolist(),v.max(0).tolist()],span=(v.max(0)-v.min(0)).tolist()))
 result.append(dict(branch=name,faces=len(ids),boundary_components=loops,nonmanifold_edges=sum(n>2 for n in edges.values())))
(P/'detailed-fragment-boundaries-DATA.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,indent=2))
