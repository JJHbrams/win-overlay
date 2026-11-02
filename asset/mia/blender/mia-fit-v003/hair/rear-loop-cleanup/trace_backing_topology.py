"""Diagnostic root-section sweep of the backing U surface; no production mask."""
from pathlib import Path
import numpy as np,json,collections
P=Path(__file__).resolve().parent;d=np.load(P/'source-mesh-input.npz');T=d['faces'];co=d['co'];raw=d['raw_ids'];a=np.load(P/'topology-analysis.npz');F=a['physical_faces'];points=a['points'];edges=collections.defaultdict(list)
for i,t in enumerate(F):
 for v,w in [(t[0],t[1]),(t[1],t[2]),(t[2],t[0])]:edges[tuple(sorted((int(v),int(w))))].append(i)
adj=[set() for _ in T]
for fs in edges.values():
 for i in fs:adj[i].update(j for j in fs if i!=j)
seed=int(np.flatnonzero(raw==99704)[0]);reports=[];payload={}
for h in [1.34,1.36,1.38,1.40,1.42,1.44,1.46]:
 eligible=co[T][:,:,2].max(1)<h
 seen={seed};queue=[seed]
 for i in queue:
  for j in adj[i]:
   if j not in seen and eligible[j]:seen.add(j);queue.append(j)
 ids=np.array(sorted(seen),np.int32);pc=co[np.unique(T[ids])];payload[str(h)+'_faces']=ids;reports.append(dict(root_section_z=h,faces=len(ids),bounds=[pc.min(0).tolist(),pc.max(0).tolist()],semantics=d['semantic_weights'][T[ids]].min((0,1)).tolist()))
np.savez_compressed(P/'backing-root-sections-DATA.npz',**payload);(P/'backing-root-sections-DATA.json').write_text(json.dumps(dict(seed=99704,partitions=reports,limits='Height sweeps diagnose narrow roots only. No threshold partition is approved as a whole logical strand owner.'),indent=2)+'\n',encoding='utf-8');print(json.dumps(reports,indent=2))

# Track the branch's exact sublevel-topology merge, not a camera rectangle.
labels=np.load(P/'global-components.npz')['face_component'];eligible=np.flatnonzero((labels==488)&(co[T][:,:,2].max(1)<1.46));level=co[T][:,:,2].max(1);order=eligible[np.argsort(level[eligible])];active=np.zeros(len(T),bool);parent=np.arange(len(T));count=np.ones(len(T),np.int32);changes=[]
def find(i):
 while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
 return i
last=0
for i in order:
 active[i]=True
 for j in adj[i]:
  if active[j]:
   a,b=find(i),find(j)
   if a!=b:parent[b]=a;count[a]+=count[b]
 if active[seed]:
  size=int(count[find(seed)])
  if size-last>=20:changes.append(dict(level=float(level[i]),size=size,face=int(i),raw=int(raw[i]),jump=size-last));last=size
(P/'backing-merge-events-DATA.json').write_text(json.dumps(changes,indent=2)+'\n',encoding='utf-8');print('MERGE_EVENTS',changes[-15:])
