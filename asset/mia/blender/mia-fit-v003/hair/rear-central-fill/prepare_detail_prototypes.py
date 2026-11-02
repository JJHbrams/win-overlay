"""Real detailed Main terminal volumes; new-copy-only root caps and tiny seam separation."""
from pathlib import Path
import numpy as np,json,collections,hashlib
P=Path(__file__).resolve().parent;R=P.parent/'rear-loop-cleanup';d=np.load(R/'source-mesh-input.npz');co=d['co'];T=d['faces'];parts=np.load(P/'detailed-branch-inventory-DATA.npz');out={};reports=[]
for key,label in [('h138_part2','RoundCurl'),('h138_part17','SweptCurl'),('h135_part10','FineTip')]:
 ids=parts[key];original=np.unique(T[ids]);lookup={int(v):i for i,v in enumerate(original)};verts=co[original].astype(float);faces=np.array([[lookup[int(v)] for v in t] for t in T[ids]],np.int32);sourcefaces=ids.tolist();caps=[];sourcepoint=original.tolist();separated=[]
 if label=='RoundCurl':
  # The physical four-way edge is two distinct raw UV-seam edges that touch.
  # Separate ONLY one raw pair in this NEW copy by20micrometres, preserving UV/fields.
  rawpairs=[2273,2276];normal=np.array([-.55,.65,.45]);normal/=np.linalg.norm(normal)
  for raw in rawpairs:
   assert raw in lookup;verts[lookup[raw]]+=normal*.00002;separated.append(raw)
 points,physical=np.unique(np.round(verts,7),axis=0,return_inverse=True);F=physical[faces];edges=collections.defaultdict(list)
 for i,t in enumerate(F):
  for j,(a,b) in enumerate([(t[0],t[1]),(t[1],t[2]),(t[2],t[0])]):edges[tuple(sorted((int(a),int(b))))].append((i,int(a),int(b)))
 assert not any(len(v)>2 for v in edges.values()),label;boundary=[v[0] for v in edges.values() if len(v)==1];graph=collections.defaultdict(list)
 for fi,a,b in boundary:graph[a].append((b,fi))
 visited=set();allfaces=faces.tolist()
 for start in list(graph):
  if start in visited:continue
  loop=[];i=start
  while i not in visited:
   visited.add(i);loop.append(i);assert len(graph[i])==1,(label,i,graph[i]);i=graph[i][0][0]
  assert i==start;rawlocal=[]
  for p in loop:rawlocal.append(int(np.flatnonzero(physical==p)[0]))
  centre=len(verts);verts=np.vstack([verts,verts[rawlocal].mean(0)]);sourcepoint.append(-1);caps.append(dict(new_vertex=centre,interpolate_source_vertices=[int(original[v]) for v in rawlocal],boundary_vertices=rawlocal,scope='Buried root cap' if points[loop,2].mean()>points[:,2].mean() else 'Tiny source opening closure'))
  for a,b in zip(rawlocal,rawlocal[1:]+rawlocal[:1]):allfaces.append([centre,b,a]);sourcefaces.append(-1)
 faces=np.array(allfaces,np.int32);tri=verts[faces];volume=float(np.einsum('ij,ij->i',tri[:,0],np.cross(tri[:,1],tri[:,2])).sum()/6)
 if volume<0:faces=faces[:,[0,2,1]];volume=-volume
 points,iv=np.unique(np.round(verts,7),axis=0,return_inverse=True);counts=collections.Counter(tuple(sorted((int(a),int(b)))) for t in iv[faces] for a,b in [(t[0],t[1]),(t[1],t[2]),(t[2],t[0])]);assert min(counts.values())==max(counts.values())==2,(label,min(counts.values()),max(counts.values()));assert volume>0
 out[label+'_co']=verts.astype(np.float32);out[label+'_faces']=faces;out[label+'_source_vertex']=np.array(sourcepoint,np.int32);out[label+'_source_face']=np.array(sourcefaces,np.int32);reports.append(dict(name=label,source_branch=key,source_faces=len(ids),new_faces=len(faces),new_vertices=len(verts),caps=caps,new_copy_separated_source_vertices=separated,separation_m=.00002 if separated else 0,closed_physical_two_manifold=True,positive_volume_mm3=volume*1e9,bounds=[verts.min(0).tolist(),verts.max(0).tolist()],source_raw_face_ids=d['raw_ids'][ids].tolist()))
np.savez_compressed(P/'detail-prototypes.npz',**out);(P/'detail-prototypes.json').write_text(json.dumps(dict(purpose='Owned NEW mesh prototypes from actual Main fine geometry; Main untouched. Every original corner UV and POINT field will be copied by source IDs at application, caps explicitly interpolate.',payload_sha256=hashlib.sha256((P/'detail-prototypes.npz').read_bytes()).hexdigest(),prototypes=reports,ART=False),indent=2)+'\n',encoding='utf-8');print('DETAILED_PROTOTYPES',[(r['name'],r['source_faces'],r['new_faces'],r['positive_volume_mm3']) for r in reports],flush=True)
