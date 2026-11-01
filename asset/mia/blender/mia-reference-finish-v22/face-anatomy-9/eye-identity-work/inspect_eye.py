import bpy,json,numpy as np
from pathlib import Path
from collections import Counter,defaultdict
from mathutils import Matrix
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).parent;V22=ROOT.parents[1]
SOURCE=Path(r'C:/Users/antio/.codex/worktrees/mia-final-face-v12/win-overlay/asset/mia/blender/mia-face-connected-v26/Mia_Q6b_BakeOnly_Control.blend')
bpy.ops.wm.open_mainfile(filepath=str(SOURCE),use_scripts=False)
skin=bpy.data.objects['MIA_V14_SculptedSkin']
for k in skin.data.shape_keys.key_blocks:k.value=0
bpy.context.view_layer.update();P=np.array([p.co[:] for p in skin.data.shape_keys.key_blocks[0].data]);faces=[list(p.vertices) for p in skin.data.polygons]
edges=Counter(tuple(sorted((f[i],f[(i+1)%len(f)]))) for f in faces for i in range(len(f)))
ad=defaultdict(set)
for (a,b),count in edges.items():
 if count==1:ad[a].add(b);ad[b].add(a)
package=json.loads((V22/'parts/face-finish8-f2-review/reference-review.json').read_text(encoding='utf-8-sig'));camera=next(v for v in package['views'] if v['id']=='front')['baseline_camera'];s=bpy.context.scene
cam=bpy.data.objects.new('InspectEyeCamera',bpy.data.cameras.new('InspectEyeCamera'));s.collection.objects.link(cam);s.camera=cam;cam.matrix_world=Matrix(camera['matrix']);cam.data.type=camera['projection'];cam.data.ortho_scale=camera['ortho_scale'];cam.data.shift_x,cam.data.shift_y=camera['lens_shift'];s.render.resolution_x,s.render.resolution_y=camera['resolution'];s.render.resolution_percentage=100
uvs=defaultdict(list)
for li,loop in enumerate(skin.data.loops):uvs[loop.vertex_index].append(list(skin.data.uv_layers['UVMap'].data[li].uv))
def pp(i):
 q=world_to_camera_view(s,cam,skin.matrix_world@skin.data.vertices[i].co)
 return [q.x*s.render.resolution_x,(1-q.y)*s.render.resolution_y]
remaining=set(ad);loops=[]
while remaining:
 group=set();stack=[min(remaining)]
 while stack:
  i=stack.pop()
  if i in group:continue
  group.add(i);stack.extend(ad[i])
 remaining-=group;center=P[list(group)].mean(0)
 if len(group)>40 and .01<abs(center[0])<.06 and center[1]>.035 and 1.525<center[2]<1.555:
  inner=min(group,key=lambda i:abs(P[i,0]));outer=max(group,key=lambda i:abs(P[i,0]));branches=[]
  for first in ad[inner]:
   path=[inner,first]
   while path[-1]!=outer:
    nx=ad[path[-1]]-{path[-2]};assert len(nx)==1;path.append(next(iter(nx)));assert len(path)<1000
   branches.append(path)
  branches.sort(key=lambda p:P[p,2].mean(),reverse=True)
  entry={'side':int(np.sign(center[0])),'inner':inner,'outer':outer}
  for kind,path in zip(['upper','lower'],branches):entry[kind]=[{'id':i,'local':P[i].tolist(),'uv':uvs[i],'pixel':pp(i)} for i in path]
  loops.append(entry)
assert len(loops)==2
owners={}
for name in ['MIA_V14_EyeSurface','MIA_V14_UpperLash_-1','MIA_V14_UpperLash_1','MIA_V14_OuterWing_-1','MIA_V14_OuterWing_1','MIA_V12_FineLowerLid_-1','MIA_V12_FineLowerLid_1']:
 o=bpy.data.objects.get(name)
 if not o:continue
 pts=np.array([v.co[:] for v in o.data.shape_keys.key_blocks[0].data] if o.data.shape_keys else [v.co[:] for v in o.data.vertices])
 owners[name]={'matrix_world':[list(r) for r in o.matrix_world],'bounds':[pts.min(0).tolist(),pts.max(0).tolist()],'vertices':pts.tolist(),'faces':[list(p.vertices) for p in o.data.polygons],'keys':[k.name for k in o.data.shape_keys.key_blocks] if o.data.shape_keys else [],'hide_render':o.hide_render,'materials':[m.name if m else None for m in o.data.materials]}
(ROOT/'eye-topology.json').write_text(json.dumps({'source':str(SOURCE),'skin_vertices':len(P),'skin_matrix_world':[list(r) for r in skin.matrix_world],'loops':loops,'owners':owners,'camera':camera},indent=2))
for loop in loops:
 for kind in ['upper','lower']:
  rows=loop[kind];ids=np.linspace(0,len(rows)-1,9).astype(int);print(loop['side'],kind,[(rows[i]['id'],np.round(rows[i]['local'],5).tolist(),np.round(rows[i]['pixel'],1).tolist()) for i in ids])
print('OWNERS',[(k,len(v['vertices']),len(v['keys']),v['bounds']) for k,v in owners.items()])
