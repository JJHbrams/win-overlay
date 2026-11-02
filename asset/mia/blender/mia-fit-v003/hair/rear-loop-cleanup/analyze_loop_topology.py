"""Read physical adjacency around loop seeds; diagnostic partitions, no mask."""
from pathlib import Path
import numpy as np,json,collections
P=Path(__file__).resolve().parent;d=np.load(P/'source-mesh-input.npz');co=d['co'];T=d['faces'];raw=d['raw_ids'];sem=d['semantic_weights'];points,first,iv=np.unique(np.round(co,6),axis=0,return_index=True,return_inverse=True);F=iv[T];edge=collections.defaultdict(list)
for i,t in enumerate(F):
 for a,b in [(t[0],t[1]),(t[1],t[2]),(t[2],t[0])]:edge[tuple(sorted((int(a),int(b))))].append(i)
adj=[set() for _ in T]
for fs in edge.values():
 for i in fs:adj[i].update(j for j in fs if i!=j)
seeds=[int(np.flatnonzero(raw==r)[0]) for r in [93498,82771]];rear=(sem[T,3].min(1)>.99)&(sem[T][:,:,[0,1,2,5]].max((1,2))<1e-6);loose=sem[T,4].mean(1)
def component(seed,eligible):
 if not eligible[seed]:return []
 seen={seed};queue=[seed]
 for i in queue:
  for j in adj[i]:
   if j not in seen and eligible[j]:seen.add(j);queue.append(j)
 return sorted(seen)
reports=[];payload=dict(points=points,physical_faces=F,physical_vertex_map=iv)
for tag,eligible in [('all',np.ones(len(T),bool)),('pureRear',rear)]+[('rear_loose_'+str(t),rear&(loose>=t)) for t in [.3,.6,.8,.95,.999]]:
 seen=set()
 for seed in seeds:
  if seed in seen:continue
  faces=component(seed,eligible)
  if not faces:continue
  seen|=set(faces);vertices=np.unique(F[faces]);counts=collections.Counter(tuple(sorted((int(a),int(b)))) for t in F[faces] for a,b in [(t[0],t[1]),(t[1],t[2]),(t[2],t[0])]);boundary=[e for e,c in counts.items() if c==1];real=[];cuts=[]
  for e in boundary:
   if len(edge[e])==1:real.append(e)
   else:cuts.append(e)
  row=dict(partition=tag,seed_raw_id=int(raw[seed]),contains_both_seeds=all(s in faces for s in seeds),faces=len(faces),points=len(vertices),bounds=[points[vertices].min(0).tolist(),points[vertices].max(0).tolist()],natural_boundary_edges=len(real),partition_attachment_edges=len(cuts),nonmanifold_edges=sum(v>2 for v in counts.values()));reports.append(row);payload[tag+'_faces']=np.array(faces,np.int32);payload[tag+'_natural_edges']=np.array(real,np.int32);payload[tag+'_cut_edges']=np.array(cuts,np.int32)
np.savez_compressed(P/'topology-analysis.npz',**payload);(P/'topology-analysis.json').write_text(json.dumps(dict(source='Actual current Main plus A+B, physical edges welded at1micrometre to join UV seam copies',seeds=seeds,partitions=reports,limits='Loose_Tips/spatial semantics diagnose connectivity only. None of these thresholds is a production strand owner or camera paint mask. No model changed.'),indent=2)+'\n',encoding='utf-8');print(json.dumps(reports,indent=2))
