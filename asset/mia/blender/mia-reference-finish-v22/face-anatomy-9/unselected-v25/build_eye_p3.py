import bpy, json
from pathlib import Path
import numpy as np
from mathutils import Vector

H=Path(__file__).resolve().parent; S=H/'proportion-p2'/'Mia_ReferenceFinish_WIP8_ProportionP2.blend'; O=H/'eye-midface-p3'; O.mkdir(exist_ok=True); N=O/'Mia_ReferenceFinish_P2_EyeMidfaceP3.blend'; assert not N.exists()
bpy.ops.wm.open_mainfile(filepath=str(S),use_scripts=False)
skin=bpy.data.objects['MIA_V14_SculptedSkin']; P=np.array([tuple(v.co) for v in skin.data.shape_keys.key_blocks[0].data])
# Actual pre-existing base aperture loop IDs (validated again in P2 evaluated topology).
upper=[[345,346,347,348,349,350,351,353,356,357],[497,498,499,500,501,502,503,504,506,510]]
lower=[[320,321,326,327,330,331,332,334,336,337,338,344,359,361],[495,509,513,514,517,518,521,522,525,526,528,529,531,533]]
d=np.zeros_like(P)
for ids in upper:
 ids=sorted(ids,key=lambda i:abs(P[i,0])); n=len(ids)
 for j,i in enumerate(ids):
  t=j/(n-1); d[i,2]-=.00055*(1-.25*t) # flatter shallow upper stroke
  d[i,1]+=.00018
for ids in lower:
 ids=sorted(ids,key=lambda i:abs(P[i,0])); n=len(ids)
 for j,i in enumerate(ids):
  t=j/(n-1); d[i,2]+=.00042*(.55+.45*t) # independent shallow rising lower arc
  d[i,1]+=.00010
# carry two rings of support by edge-neighbour averaging, avoiding an isolated rim crease
adj=[set() for _ in P]
for e in skin.data.edges: adj[e.vertices[0]].add(e.vertices[1]);adj[e.vertices[1]].add(e.vertices[0])
rim=set(sum(upper+lower,[])); one=set().union(*(adj[i] for i in rim))-rim; two=set().union(*(adj[i] for i in one))-rim-one
for group,f in [(one,.42),(two,.16)]:
 for i in group:
  ns=[j for j in adj[i] if np.linalg.norm(d[j])>0]
  if ns:d[i]=f*np.mean([d[j] for j in ns],axis=0)
for k in skin.data.shape_keys.key_blocks:
 for i in np.where(np.linalg.norm(d,axis=1)>1e-9)[0]: k.data[i].co+=Vector(d[i])
# eye surface: reduce vertical displayed sclera while preserving horizontal/iris placement.
eye=bpy.data.objects['MIA_V14_EyeSurface']; zc=1.543
for v in eye.data.vertices: v.co.z=zc+(v.co.z-zc)*.90
# lash and wing follow the upper-rim's small downward change in their lower range.
for name in ['MIA_V14_UpperLash_-1','MIA_V14_UpperLash_1','MIA_V14_OuterWing_-1','MIA_V14_OuterWing_1']:
 o=bpy.data.objects[name]
 for k in o.data.shape_keys.key_blocks:
  for v in k.data:
   if 1.535<v.co.z<1.555:v.co.z-=.00045
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(N))
(O/'manifest.json').write_text(json.dumps({'status':'WORKING/ART UNAPPROVED','base':str(S),'native':str(N),'skin_changed':int(np.sum(np.linalg.norm(d,axis=1)>1e-9)),'max_skin_delta_m':float(np.linalg.norm(d,axis=1).max()),'method':'Actual validated aperture paths with two support rings; smaller vertical eye surface; lash/wing follower. Midface remains P2 for later connected pass.'},indent=2))
print('P3_DONE',int(np.sum(np.linalg.norm(d,axis=1)>1e-9)))
