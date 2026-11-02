"""CPU topology/occlusion challenger, no GPU/art render or source mutation."""
from pathlib import Path
import numpy as np,json,sys
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent;d=np.load(P/'source-mesh-input.npz');p=np.load(P/'loop-mask.npz');co=d['co'];T=d['faces'];W=d['world_matrix'];world=co@W[:3,:3].T+W[:3,3];hidden=p['polygon_indices'];tag='masked'
if '--with-backing' in sys.argv:hidden=np.union1d(hidden,np.load(P/'backing-branch-DATA.npz')['polygon_indices']);tag='backing-plus-six'
if '--family' in sys.argv:hidden=np.load(P/'logical-family-DATA.npz')['polygon_indices'];tag='logical-family'
use=np.flatnonzero(~np.isin(np.arange(len(T)),hidden));bvh=BVHTree.FromPolygons(world.tolist(),T[use].tolist(),all_triangles=True);rows=json.loads((P/'firsthit-views.json').read_text());payload={}
for v in rows:
 if v['name'] not in ['back_full','loop_close']:continue
 size=v['resolution'][0];cam=Matrix(v['matrix']);scale=v['ortho_scale'];direction=cam.to_3x3()@Vector((0,0,-1));face=np.full((size,size),-1,np.int32);norm=np.zeros((size,size,3),np.float32)
 for y in range(size):
  for x in range(size):
   origin=cam@Vector((((x+.5)/size-.5)*scale,(.5-(y+.5)/size)*scale,0));hit,n,fi,dist=bvh.ray_cast(origin,direction)
   if fi is not None:face[y,x]=use[fi];norm[y,x]=n
 payload[v['name']+'_face']=face;payload[v['name']+'_normal']=norm;print('CPU_MASKED_DATA',v['name'],flush=True)
np.savez_compressed(P/(tag+'-firsthit-data.npz'),**payload)
