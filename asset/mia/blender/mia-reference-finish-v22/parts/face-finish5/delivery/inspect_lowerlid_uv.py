import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
H=Path(__file__).resolve().parent;source=H.parent/'finish-4/Mia_FaceFinish_v22.blend';bpy.ops.wm.open_mainfile(filepath=str(source));o=bpy.data.objects['MIA_V14_SculptedSkin'];ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();p=np.array([tuple(v.co) for v in m.vertices]);uvs={}
for poly in m.polygons:
 for i in poly.loop_indices:uvs.setdefault(m.loops[i].vertex_index,[]).append(tuple(m.uv_layers.active.data[i].uv))
uses={}
for f in m.polygons:
 ids=list(f.vertices)
 for a,b in zip(ids,ids[1:]+ids[:1]):edge=tuple(sorted((a,b)));uses[edge]=uses.get(edge,0)+1
adj={}
for (a,b),num in uses.items():
 if num==1:adj.setdefault(a,set()).add(b);adj.setdefault(b,set()).add(a)
seen=set();eyes=[]
for start in adj:
 if start in seen:continue
 stack=[start];seen.add(start);ids=[]
 while stack:
  i=stack.pop();ids.append(i)
  for j in adj[i]:
   if j not in seen:seen.add(j);stack.append(j)
 c=p[ids].mean(0)
 if .018<abs(c[0])<.06 and 1.53<c[2]<1.55 and c[1]>.03:
  inner=min(ids,key=lambda i:abs(p[i,0]));outer=max(ids,key=lambda i:abs(p[i,0]));lower=[]
  for i in ids:
   t=(p[i,0]-p[inner,0])/(p[outer,0]-p[inner,0]);line=p[inner,2]+t*(p[outer,2]-p[inner,2])
   if p[i,2]<=line:lower.append(i)
  lower.sort(key=lambda i:np.mean(uvs[i],axis=0)[0]);rows=[{'local':p[i].tolist(),'uv':np.mean(uvs[i],axis=0).tolist()} for i in lower];eyes.append({'center':c.tolist(),'lower':rows})
ev.to_mesh_clear();(H/'lowerlid-uv.json').write_text(json.dumps(eyes,indent=2));print(json.dumps(eyes,indent=2))
