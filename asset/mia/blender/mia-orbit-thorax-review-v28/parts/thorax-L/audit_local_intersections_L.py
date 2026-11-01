"""Strict nonadjacent triangle intersection checks in actual breast/lower-return region."""
import numpy as np,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).parent;O=P/'source-soft-L'
def segment_hit(p,q,tri,eps=1e-9):
 a,b,c=tri;direction=q-p;e1=b-a;e2=c-a;h=np.cross(direction,e2);det=np.dot(e1,h)
 if abs(det)<1e-16:return False
 inv=1/det;s=p-a;u=np.dot(s,h)*inv
 if u<=eps or u>=1-eps:return False
 z=np.cross(s,e1);v=np.dot(direction,z)*inv
 if v<=eps or u+v>=1-eps:return False
 t=np.dot(e2,z)*inv
 return eps<t<1-eps
def orient(a,b,c):return np.cross(b-a,c-a).item()
def coplanar_overlap(a,b):
 n=np.cross(a[1]-a[0],a[2]-a[0]);length=np.linalg.norm(n)
 if length<1e-14:return False
 n/=length
 if abs(np.dot(b[0]-a[0],n))>1e-8:return False
 nb=np.cross(b[1]-b[0],b[2]-b[0]);nb/=max(np.linalg.norm(nb),1e-30)
 if abs(np.dot(n,nb))<1-1e-8:return False
 axis=int(np.argmax(abs(n)));a=np.delete(a,axis,axis=1);b=np.delete(b,axis,axis=1)
 for aa,ab in zip(a,np.roll(a,-1,axis=0)):
  for ba,bb in zip(b,np.roll(b,-1,axis=0)):
   if orient(aa,ab,ba)*orient(aa,ab,bb)<-1e-18 and orient(ba,bb,aa)*orient(ba,bb,ab)<-1e-18:return True
 for q,t in [(a[0],b),(b[0],a)]:
  vals=[orient(x,y,q) for x,y in zip(t,np.roll(t,-1,axis=0))]
  if min(vals)>1e-10 or max(vals)<-1e-10:return True
 return False
pc=np.array([[-1,0,0],[1,0,0],[0,1,0],[0,.2,-1],[0,.2,1],[.5,.8,0]],dtype=float);pcf=[[0,1,2],[3,4,5]];pca=BVHTree.FromPolygons([Vector(p) for p in pc],pcf,all_triangles=True);pcb=BVHTree.FromPolygons([Vector(p) for p in pc],pcf,all_triangles=True);pcpairs=pca.overlap(pcb);pchit=any(segment_hit(p,q,pc[pcf[1]]) for p,q in zip(pc[pcf[0]],np.roll(pc[pcf[0]],-1,axis=0))) or any(segment_hit(p,q,pc[pcf[0]]) for p,q in zip(pc[pcf[1]],np.roll(pc[pcf[1]],-1,axis=0)));assert pcpairs and pchit
reports={'positive_control':{'bvh_crossing_pairs':pcpairs,'strict_segment_triangle_detected':pchit}}
for role,path in [('I',P/'source-soft-I/evaluated-skin.npz'),('L',O/'evaluated-skin.npz')]:
 d=np.load(path);v=d['vertices'];allf=d['triangles'];t=v[allf];center=t.mean(1);mask=(center[:,2]>1.205)&(center[:,2]<1.34)&(abs(center[:,0])<.145)&(center[:,1]<.005);ids=np.flatnonzero(mask);f=allf[ids];tree=BVHTree.FromPolygons([Vector(p) for p in v],f.tolist(),all_triangles=True,epsilon=0.)
 other=BVHTree.FromPolygons([Vector(p) for p in v],f.tolist(),all_triangles=True,epsilon=0.);candidates=tree.overlap(other);checked=set();hits=[]
 for aa,bb in candidates:
  if aa>=bb:continue
  key=(aa,bb)
  if key in checked:continue
  checked.add(key)
  if set(f[aa]).intersection(f[bb]):continue
  a,b=v[f[aa]],v[f[bb]]
  if any(segment_hit(p,q,b) for p,q in zip(a,np.roll(a,-1,axis=0))) or any(segment_hit(p,q,a) for p,q in zip(b,np.roll(b,-1,axis=0))) or coplanar_overlap(a,b):hits.append({'triangle_indices':[int(ids[aa]),int(ids[bb])],'vertex_indices':[f[aa].tolist(),f[bb].tolist()],'centers':[a.mean(0).tolist(),b.mean(0).tolist()]})
 reports[role]={'selected_evaluated_triangles':len(f),'bvh_candidate_pairs':len(checked),'strict_nonadjacent_intersections':len(hits),'hits_first30':hits[:30]}
reports['limits']='Strict interior intersections only, selected static breast/return region. Shared-vertex neighbors excluded; this is not all-pose/whole-model collision acceptance.'
(O/'local-intersection-audit.json').write_text(json.dumps(reports,indent=2),encoding='utf8');print('LOCAL_INTERSECTIONS',json.dumps(reports),flush=True)
