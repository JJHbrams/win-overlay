import bpy,numpy as np,json
from pathlib import Path
from collections import Counter,defaultdict
P=Path(__file__).parent
paths={'wip8':Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v22/integration-wip-8-review/Mia_ReferenceFinish_v22.blend'),'q7':P/'Mia_ConnectedLoft_Q7_SurfaceFit.blend'};arr={};report={}
for label,path in paths.items():
 bpy.ops.wm.open_mainfile(filepath=str(path));o=bpy.data.objects['MIA_V14_SculptedSkin']
 for k in o.data.shape_keys.key_blocks:k.value=0
 bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();a=np.array([v.co[:] for v in me.vertices]);arr[label]=a
 if label=='wip8':
  edges=Counter(tuple(sorted((p.vertices[j],p.vertices[(j+1)%len(p.vertices)]))) for p in me.polygons for j in range(len(p.vertices)));adj=defaultdict(set)
  for (i,j),count in edges.items():
   if count==1:adj[i].add(j);adj[j].add(i)
  seen=set();components=[]
  for i in adj:
   if i in seen:continue
   todo=[i];ids=[]
   while todo:
    j=todo.pop()
    if j in seen:continue
    seen.add(j);ids.append(j);todo.extend(adj[j]-seen)
   components.append(ids)
  report['boundaries']=[{'ids':ids,'center':a[ids].mean(0).tolist(),'min':a[ids].min(0).tolist(),'max':a[ids].max(0).tolist()} for ids in components]
 ev.to_mesh_clear()
for row in report['boundaries']:
 ids=row['ids'];d=arr['q7'][ids]-arr['wip8'][ids];row['q7_minus_wip8_mean_mm']=(d.mean(0)*1000).tolist();row['q7_minus_wip8_z_range_mm']=[float(d[:,2].min()*1000),float(d[:,2].max()*1000)]
np.savez_compressed(P/'mouth-q9-baseline-evaluated.npz',**arr);(P/'mouth-q9-loop-audit.json').write_text(json.dumps(report,indent=2));print([{k:v for k,v in r.items() if k!='ids'} for r in report['boundaries']])
