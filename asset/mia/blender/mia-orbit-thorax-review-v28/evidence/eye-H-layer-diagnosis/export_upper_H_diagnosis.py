"""Read-only G2 aperture/ink projections. No camera or canthal-chord normalization."""
import bpy, json, collections, numpy as np
from pathlib import Path
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view
O=Path(__file__).parent
bpy.ops.wm.open_mainfile(filepath=str(O/'Mia_Orbit_v28_G2.blend'))
sc=bpy.context.scene
master=bpy.data.objects['MIA_V27_Foundation_Face']
skin=bpy.data.objects['MIA_V27_SharedHeadBody']
for k in master.data.shape_keys.key_blocks:k.value=0
bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get()
ev=skin.evaluated_get(dg);me=ev.to_mesh()
ep=np.array([ev.matrix_world@v.co for v in me.vertices])
counts=collections.Counter(tuple(sorted((a,b))) for f in me.polygons for a,b in zip(f.vertices,list(f.vertices[1:])+[f.vertices[0]]))
adj=collections.defaultdict(set)
for (a,b),n in counts.items():
 if n==1:adj[a].add(b);adj[b].add(a)
seen=set();paths={}
for root in adj:
 if root in seen:continue
 comp={root};todo=[root];seen.add(root)
 while todo:
  for j in adj[todo.pop()]:
   if j not in seen:seen.add(j);comp.add(j);todo.append(j)
 q=ep[list(comp)]
 if not (1.52<q[:,2].mean()<1.56 and q[:,1].mean()<-.035 and .01<abs(q[:,0].mean())<.07):continue
 side=int(np.sign(q[:,0].mean()));start=min(comp,key=lambda j:abs(ep[j,0]));end=max(comp,key=lambda j:abs(ep[j,0]));two=[]
 for nxt in adj[start]:
  ids=[start,nxt];prev,now=start,nxt
  while now!=end:
   nxt=next(j for j in adj[now] if j!=prev);ids.append(nxt);prev,now=now,nxt
  two.append(ids)
 two.sort(key=lambda ii:ep[ii,2].mean(),reverse=True)
 paths[str(side)]={'upper':ep[two[0]].tolist(),'lower':ep[two[1]].tolist(),'upper_indices':two[0],'lower_indices':two[1]}
ev.to_mesh_clear()
feature={}
for ob in sc.objects:
 if ob.type!='MESH' or ob.hide_render or not ('BoundaryRibbon' in ob.name or ob.name.startswith('V28_LashFan_')):continue
 # Raw key mesh intentionally distinguishes authored root/ink path from Solidify shell.
 q=np.array([ob.matrix_world@v.co for v in ob.data.shape_keys.key_blocks[0].data])
 feature[ob.name]={'world':q.tolist(),'root':q[::5].tolist() if 'BoundaryRibbon' in ob.name else None,'ink_edge':q[4::5].tolist() if 'BoundaryRibbon' in ob.name else None}
pkg=json.loads((O/'reference-review-G2.json').read_text());views={}
cam=bpy.data.objects.new('H_DIAG_CAMERA',bpy.data.cameras.new('H_DIAG_CAMERA'));sc.collection.objects.link(cam);cam.data.type='ORTHO';sc.render.resolution_x=sc.render.resolution_y=768;sc.render.resolution_percentage=100
for v in pkg['views']:
 cam.matrix_world=Matrix(v['candidate_camera']['matrix']);cam.data.ortho_scale=v['candidate_camera']['ortho_scale'];cam.data.shift_x=cam.data.shift_y=0;bpy.context.view_layer.update()
 def proj(points):
  qq=[world_to_camera_view(sc,cam,Vector(p)) for p in points]
  return [[float(p.x*768),float((1-p.y)*768)] for p in qq]
 p={s:{key:proj(d[key]) for key in ['upper','lower']} for s,d in paths.items()}
 f={n:{key:proj(d[key]) for key in ['root','ink_edge'] if d[key] is not None} for n,d in feature.items()}
 views[v['id']]={'skin':p,'features':f,'camera':v['candidate_camera']}
(O/'upper-H-G2-projections.json').write_text(json.dumps({'native':'Mia_Orbit_v28_G2.blend','world_skin':paths,'world_features':feature,'views':views,'limits':'Unrotated native camera pixel axes. No canthal chord alignment or fitted eye rotation.'},indent=2))
print('H_DIAG_PROJECTIONS_SAVED')
