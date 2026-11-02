"""CPU BVH geometry ownership data, not a shaded Blender/art render."""
from pathlib import Path
import numpy as np,json,collections,math
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent;d=np.load(P/'source-mesh-input.npz');co=d['co'].astype(float);T=d['faces'];raw=d['raw_ids'];M=d['world_matrix'];world=co@M[:3,:3].T+M[:3,3];points,iv=np.unique(np.round(world,6),axis=0,return_inverse=True);F=iv[T];edge=collections.defaultdict(list);parent=np.arange(len(T))
def find(i):
 while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
 return i
for i,t in enumerate(F):
 for a,b in [(t[0],t[1]),(t[1],t[2]),(t[2],t[0])]:edge[tuple(sorted((int(a),int(b))))].append(i)
for fs in edge.values():
 for i in fs[1:]:parent[find(i)]=find(fs[0])
roots=sorted({find(i) for i in range(len(T))});lookup={r:i for i,r in enumerate(roots)};labels=np.array([lookup[find(i)] for i in range(len(T))],np.int32);groups=collections.defaultdict(list)
for i,k in enumerate(labels):groups[int(k)].append(i)
report=[]
for k,rows in groups.items():
 p=world[np.unique(T[rows])];report.append(dict(component=k,faces=len(rows),bounds=[p.min(0).tolist(),p.max(0).tolist()],seed_raw_ids=[int(r) for r in [93498,82771] if int(r) in set(raw[rows])]))
report.sort(key=lambda x:x['component']);(P/'global-components.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');np.savez_compressed(P/'global-components.npz',face_component=labels)
bvh=BVHTree.FromPolygons(world.tolist(),T.tolist(),all_triangles=True);configs=[];payload={};size=384
for name,yaw,pitch,target,scale in [('back_full',180,8,[0,.03,1.47],.72),('rear_low_full',180,-20,[0,.03,1.47],.72),('oblique_low_full',135,-20,[0,.03,1.47],.72),('loop_close',180,-20,[0,.12,1.365],.23)]:
 a=math.radians(yaw);p=math.radians(pitch);target=Vector(target);out=Vector((math.sin(a)*math.cos(p),-math.cos(a)*math.cos(p),math.sin(p)));location=target+out*2;cam=(-out).to_track_quat('-Z','Y').to_matrix().to_4x4();cam.translation=location;direction=-out;ids=np.full((size,size),-1,np.int32);normal=np.zeros((size,size,3),np.float32);depth=np.zeros((size,size),np.float32)
 for y in range(size):
  for x in range(size):
   origin=cam@Vector((((x+.5)/size-.5)*scale,(.5-(y+.5)/size)*scale,0));hit,n,fi,dist=bvh.ray_cast(origin,direction)
   if fi is not None:ids[y,x]=fi;normal[y,x]=n;depth[y,x]=dist
 payload[name+'_face']=ids;payload[name+'_normal']=normal;payload[name+'_depth']=depth;configs.append(dict(name=name,matrix=list(map(list,cam)),ortho_scale=scale,resolution=[size,size],target=list(target),yaw_degrees=yaw,pitch_degrees=pitch,clip=[.1,10],purpose='CPU Main-only geometry first-hit ownership DATA; not source-art/shader evidence'));print('CPU_FIRSTHIT_DATA',name,flush=True)
np.savez_compressed(P/'firsthit-data.npz',**payload);(P/'firsthit-views.json').write_text(json.dumps(configs,indent=2)+'\n',encoding='utf-8');print('CPU_MAIN_ONLY_MAP_DONE',len(roots),flush=True)
