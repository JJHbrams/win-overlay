"""Certify real source edge cycles and the connected replacement domain once."""
from collections import defaultdict,deque
import json
import numpy as np
from scope import load_scope,CACHE

def main():
 s=load_scope();q=s['q'];faces=s['faces'];edgefaces=defaultdict(list)
 for fi,f in enumerate(faces):
  for a,b in zip(f,f[1:]+f[:1]):edgefaces[tuple(sorted((a,b)))].append(fi)
 loops=dict(waist=[979,978,967,966,938,940,961,941,943,955,954,953,962,913,912,895,893,892,905,906,915,914,916,987,986,988],
  neck=[351,346,226,227,225,224,239,26,27,12,9,8,10,122,126,127],
  right_arm=s['arm'].tolist(),left_arm=s['other_arm'].tolist())
 cuts=set()
 for name,loop in loops.items():
  assert len(loop)==len(set(loop))
  for a,b in zip(loop,loop[1:]+loop[:1]):
   edge=tuple(sorted((a,b)));assert len(edgefaces[edge])==2,(name,edge,edgefaces[edge]);cuts.add(edge)
 assert len(cuts)==sum(map(len,loops.values()))
 adj=[set()for f in faces]
 for edge,owners in edgefaces.items():
  if edge in cuts:continue
  for a in owners:
   adj[a].update(set(owners)-{a})
 centroid=np.array([q[f].mean(0)for f in faces]);seed=int(np.argmin(np.linalg.norm(centroid-[0,-.10,1.30],axis=1)))
 component={seed};queue=deque([seed])
 while queue:
  for j in adj[queue.popleft()]:
   if j not in component:component.add(j);queue.append(j)
 boundary={e for e,owners in edgefaces.items()if sum(f in component for f in owners)==1}
 assert boundary==cuts,(len(boundary),len(cuts),sorted(boundary-cuts)[:10])
 vertices=set(v for i in component for v in faces[i]);boundary_ids=set(v for loop in loops.values()for v in loop)
 interior=np.array(sorted(vertices-boundary_ids),np.int32)
 assert max(q[interior,2])<1.469,'True head/scalp leaked into replacement domain'
 assert not set(interior)&set(range(3957,4647))
 # The retained side of all four boundaries is an actual original source
 # surface, not new cap geometry. No low neck/trapezius rail is frozen inside.
 out=CACHE/'design-boundaries.npz';assert not out.exists()
 np.savez_compressed(out,domain_faces=np.array(sorted(component),np.int32),interior=interior,
  domain_vertices=np.array(sorted(vertices),np.int32),**{name:np.array(v,np.int32)for name,v in loops.items()})
 report=dict(scope='Certified original edge cycles for ONE new upperbody DESIGN flow, no target geometry yet',
  loops={name:dict(count=len(v),ids=v,bounds=[q[v].min(0).tolist(),q[v].max(0).tolist()])for name,v in loops.items()},
  replacement_faces=len(component),replacement_interior_controls=len(interior),entire_domain_bounds=[q[list(vertices)].min(0).tolist(),q[list(vertices)].max(0).tolist()],
  boundary_edges_exact=True,all_source_heads_outside=True,
  neck_scope='16-edge collar Z1.445..1.460 frees lower neck/clavicle, instead of fixing the low30 body/material strip. Upper collar and all true head remain retained.',
  design_only=True,ART=False,native_saved=False)
 (CACHE/'design-boundaries.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps(report),flush=True)

if __name__=='__main__':main()
