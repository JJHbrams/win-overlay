import bpy,bmesh,json,collections
from pathlib import Path
P=Path(__file__).parent
bpy.ops.wm.open_mainfile(filepath=str(P/'sculpt2/Mia_HairStructure_v24.blend'),use_scripts=False)
o=bpy.data.objects['MIA_V17_PIXAL_DetailedHair'];bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table()
edges=[e for e in bm.edges if e.is_boundary];adj=collections.defaultdict(set)
for e in edges:
 a,b=e.verts;adj[a.index].add(b.index);adj[b.index].add(a.index)
comps=[];seen=set()
for v in adj:
 if v in seen:continue
 todo=[v];comp=[]
 while todo:
  k=todo.pop()
  if k in seen:continue
  seen.add(k);comp.append(k);todo.extend(adj[k]-seen)
 coords=[bm.verts[k].co for k in comp]
 box=[[min(v[k] for v in coords),max(v[k] for v in coords)] for k in range(3)]
 if box[2][1]>1.45 and box[2][0]<1.60 and box[1][0]<.05:
  comps.append({'n':len(comp),'bounds':box,'indices':comp,'branching':sum(len(adj[k])!=2 for k in comp)})
comps.sort(key=lambda c:c['n'],reverse=True)
(P/'boundary-components.json').write_text(json.dumps(comps,indent=2));print(json.dumps([{k:v for k,v in c.items() if k!='indices'} for c in comps[:40]],indent=2));print('total',len(edges),len(comps))
