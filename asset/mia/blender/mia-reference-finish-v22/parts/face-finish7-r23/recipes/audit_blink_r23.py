"""Measure actual evaluated aperture loops throughout the R23 blink."""
import bpy,json,hashlib
import numpy as np
from pathlib import Path
from collections import Counter,defaultdict
HERE=Path(__file__).resolve().parent;OUT=HERE/'candidate-r23';SOURCE=OUT/'Mia_FaceFinish7_BlinkR23_v22.blend'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source_sha=sha(SOURCE);bpy.ops.wm.open_mainfile(filepath=str(SOURCE));skin=bpy.data.objects['MIA_V14_SculptedSkin'];keys=skin.data.shape_keys.key_blocks
for k in keys:k.value=0.
def evaluated():
 bpy.context.view_layer.update();obj=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=obj.to_mesh();p=np.array([tuple(v.co) for v in mesh.vertices]);faces=[list(f.vertices) for f in mesh.polygons];obj.to_mesh_clear();return p,faces
P,F=evaluated();edges=Counter(tuple(sorted((f[i],f[(i+1)%len(f)]))) for f in F for i in range(len(f)));adj=defaultdict(list)
for (i,j),n in edges.items():
 if n==1:adj[i].append(j);adj[j].append(i)
remaining=set(adj);loops=[]
while remaining:
 start=min(remaining);stack=[start];group=set()
 while stack:
  i=stack.pop()
  if i in group:continue
  group.add(i);stack.extend(adj[i])
 remaining-=group;center=P[list(group)].mean(axis=0)
 if len(group)>40 and abs(center[0])>.01 and abs(center[0])<.06 and center[1]>.035 and 1.525<center[2]<1.555:
  assert all(len(adj[i])==2 for i in group)
  inner=min(group,key=lambda i:abs(P[i,0]));outer=max(group,key=lambda i:abs(P[i,0]));paths=[]
  for first in adj[inner]:
   path=[inner,first]
   while path[-1]!=outer:
    nxt=[i for i in adj[path[-1]] if i!=path[-2]][0];assert nxt not in path;path.append(nxt)
   paths.append(path)
  paths.sort(key=lambda path:float(P[path,2].mean()),reverse=True)
  loops.append({'side':int(np.sign(center[0])),'upper':paths[0],'lower':paths[1]})
assert len(loops)==2,len(loops)
records=[]
for value in [0.,.25,.5,.75,1.]:
 keys['Face.M_F00_000_00_Fcl_EYE_Close'].value=value;p,faces=evaluated();assert faces==F;sides=[]
 for loop in loops:
  u=p[loop['upper']];l=p[loop['lower']];u=u[np.argsort(abs(u[:,0]))];l=l[np.argsort(abs(l[:,0]))];lo=max(abs(u[:,0]).min(),abs(l[:,0]).min());hi=min(abs(u[:,0]).max(),abs(l[:,0]).max());xs=np.linspace(lo+.05*(hi-lo),hi-.05*(hi-lo),101)
  uc=np.array([np.interp(xs,abs(u[:,0]),u[:,axis]) for axis in range(3)]).T;lc=np.array([np.interp(xs,abs(l[:,0]),l[:,axis]) for axis in range(3)]).T
  gap=uc[:,2]-lc[:,2];depth=uc[:,1]-lc[:,1]
  sides.append({'side':loop['side'],'signed_vertical_gap_mm':{'min':float(gap.min()*1000),'median':float(np.median(gap)*1000),'max':float(gap.max()*1000)},'depth_difference_mm_max':float(abs(depth).max()*1000),'upper_curve':u.tolist(),'lower_curve':l.tolist()})
 records.append({'actual_close':value,'sides':sides,'actual_followers':{o.name:{k.name:k.value for k in o.data.shape_keys.key_blocks if k.name=='MIA_V20_BlinkFollower'} for o in bpy.data.objects if o.type=='MESH' and o.data.shape_keys and o.name.startswith('MIA_V14_') and any(x in o.name for x in ['UpperLash','OuterWing'])}})
assert sha(SOURCE)==source_sha
report={'source':{'path':str(SOURCE),'sha256':source_sha},'recipe_sha256':sha(__file__),'method':'Actual evaluated boundary edge loops, upper/lower assigned once from neutral, sampled at common absolute local X over interior5..95%. Signed Z gap positive=open, negative=overlap; depth difference is separate. No claim of eyelid contact from raster darkness.','records':records}
(OUT/'evaluated-blink-aperture.json').write_text(json.dumps(report,indent=2));print(json.dumps([{k:v for k,v in r.items() if k!='sides'}|{'sides':[{k:v for k,v in side.items() if 'curve' not in k} for side in r['sides']]} for r in records],indent=2))
