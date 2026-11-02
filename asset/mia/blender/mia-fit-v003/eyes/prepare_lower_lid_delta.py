"""Small right lower-rim balance, depth-seated to actual sclera. No scene save."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,heapq,collections
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent;C=P.parents[1];V=C/'mia-refinement-v002'
N=V/'integrated/Mia_v0.0.2_Review_R3b.blend';SHA='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'
assert hashlib.sha256(N.read_bytes()).hexdigest()==SHA
bpy.ops.wm.open_mainfile(filepath=str(N),use_scripts=False)
skin=bpy.data.objects['MIA_V27_SharedHeadBody'];ctrl=bpy.data.objects['Mia_FacialControls_v002'];dg=bpy.context.evaluated_depsgraph_get()
meta=json.loads((V/'parts/eye-A/payload/surprise-A.json').read_text())
rim=json.loads((C/'mia-face-finish-v29/parts/medial-C2/proof/medial-baseline-inspection.json').read_text())
lash=json.loads(Path('C:/Users/antio/.codex/worktrees/mia-final-face-v12/win-overlay/asset/mia/blender/mia-eye-visible-v30/lash-M-audit.json').read_text())
def arr(c):
 a=np.empty(len(c)*3,np.float32);c.foreach_get('co',a);return a.reshape(-1,3)
def ev(o):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();q=np.array([e.matrix_world@v.co for v in m.vertices]);nn=np.array([e.matrix_world.to_3x3()@v.normal for v in m.vertices]);f=[p.vertices[:] for p in m.polygons];e.to_mesh_clear();return q,nn,f
def unit(v):return v/max(np.linalg.norm(v),1e-12)
def frame(q,n,t):
 v=t*(len(q)-1);i=min(len(q)-2,max(0,int(v)));f=v-i;p=q[i]*(1-f)+q[i+1]*f;normal=unit(n[i]*(1-f)+n[i+1]*f);tan=q[min(len(q)-1,i+2)]-q[max(0,i-1)];tan=unit(tan-normal*np.dot(tan,normal));return p,np.column_stack([tan,unit(np.cross(normal,tan)),normal])
base=arr(skin.data.shape_keys.key_blocks[0].data);world=base@np.array(skin.matrix_world.to_3x3()).T+np.array(skin.matrix_world.translation)
paths={r['side']:r for r in meta['construction']};profiles={}
for side,row in paths.items():
 ids=row['lower_raw_path'];q=world[ids];axis=unit(q[-1]-q[0]);up=unit(np.array([0.,0.,1.])-axis*axis[2]);width=np.linalg.norm(q[-1]-q[0]);t=(q-q[0])@axis/width;h=(q-q[0])@up
 profiles[side]=(t,h,width,up)
t,h,width,up=profiles[1];lt,lh,lw,_=profiles[-1]
desired=np.interp(t,lt,lh)*(width/lw)
shift=np.clip(.4*(desired-h),-.0011,.00025);shift[0]=shift[-1]=0.
row=paths[1];boundary={int(i):np.zeros(3) for i in row['boundary_ids']}
sq,_,sf=ev(bpy.data.objects['V28G_Sclera_1']);tree=BVHTree.FromPolygons(sq,sf)
depth=[]
for vi,amount in zip(row['lower_raw_path'],shift):
 vi=int(vi);v=up*amount
 def front(p):
  hit=tree.ray_cast(Vector((float(p[0]),-.2,float(p[2]))),Vector((0,1,0)),.3)[0];return hit.y if hit is not None else None
 a=front(world[vi]);b=front(world[vi]+v)
 if a is not None and b is not None:v[1]=b-a
 boundary[vi]=v;depth.append(dict(vertex=vi,delta_mm=(v*1000).tolist(),sclera_hit_before=a is not None,after=b is not None))
adj=collections.defaultdict(set)
for e in skin.data.edges:a,b=e.vertices;adj[a].add(b);adj[b].add(a)
distance={i:0. for i in row['boundary_ids']};heap=[(0.,i) for i in distance];heapq.heapify(heap);radius=.0075
while heap:
 d,i=heapq.heappop(heap)
 if d!=distance[i]:continue
 for j in adj[i]:
  nd=d+np.linalg.norm(world[i]-world[j])
  if j>=3957 and nd<radius and nd<distance.get(j,float('inf')):distance[j]=nd;heapq.heappush(heap,(nd,j))
free=sorted(set(distance)-set(boundary));ix={v:i for i,v in enumerate(free)};A=np.zeros((len(free),len(free)));b=np.zeros((len(free),3))
for vi,i in ix.items():
 for ni in adj[vi]:
  w=1/max(np.linalg.norm(world[vi]-world[ni]),1e-5);A[i,i]+=w
  if ni in ix:A[i,ix[ni]]-=w
  elif ni in boundary:b[i]+=w*boundary[ni]
sol=np.linalg.solve(A,b);dw=np.zeros_like(base,dtype=float)
for i,v in boundary.items():dw[i]=v
for i,v in zip(free,sol):dw[i]=v
local=dw@np.array(skin.matrix_world.inverted().to_3x3()).T
oldq,oldn,_=ev(skin);payload={};entries=[]
def add(o,delta):
 delta=np.asarray(delta,np.float32);ids=np.flatnonzero(np.linalg.norm(delta,axis=1)>1e-9);prefix='d'+str(len(entries));payload[prefix+'_ids']=ids.astype(np.int32);payload[prefix+'_delta']=delta[ids]
 original={k.name:hashlib.sha256(arr(k.data)[ids].tobytes()).hexdigest() for k in o.data.shape_keys.key_blocks}
 k=o.shape_key_add(name='Mia.v003.NeutralLowerLidBalance.1',from_mix=False);k.data.foreach_set('co',(arr(o.data.shape_keys.key_blocks[0].data)+delta).ravel());k.value=1.
 entries.append(dict(owner=o.name,prefix=prefix,key=k.name,vertices=len(ids),maximum_delta_mm=float(np.linalg.norm(delta,axis=1).max()*1000),vertex_count=len(delta),original_key_ROI_hashes=original))
add(skin,local);bpy.context.view_layer.update();newq,newn,_=ev(skin)
curves={}
for kind in ['upper','lower']:
 ids=rim['evaluated_openings']['1'][kind+'_evaluated_indices'];curves[kind]=((oldq[ids],oldn[ids]),(newq[ids],newn[ids]))
wall=bpy.data.objects['V28G_InnerLid_1'];wq,_,_=ev(wall);target=wq.copy();bindings=[]
for station in range(96):
 match=[]
 for kind,(old,new) in curves.items():
  ds=np.linalg.norm(old[0]-wq[station],axis=1);i=int(ds.argmin());match.append((float(ds[i]),kind,i/(len(ds)-1)))
 dist,kind,t=min(match)
 if kind!='lower' or t<.001 or t>.999:continue
 a,F=frame(*curves[kind][0],t);b,G=frame(*curves[kind][1],t);ids=np.arange(6)*96+station;target[ids]=b+(wq[ids]-a)@(G@F.T).T;bindings.append(dict(station=station,t=t,old_root_distance_mm=dist*1000))
add(wall,(target-wq)@np.array(wall.matrix_world.inverted().to_3x3()).T)
for info in lash['created']:
 if info['owner']!='V30_LowerLashes_1':continue
 o=bpy.data.objects[info['owner']];oq,_,_=ev(o);tq=oq.copy()
 for station in info['station_bindings']:
  ids=np.array(station['vertex_indices']);t=station['t']
  if t<.001 or t>.999:continue
  a,F=frame(*curves['lower'][0],t);b,G=frame(*curves['lower'][1],t);tq[ids]=b+(oq[ids]-a)@(G@F.T).T
 add(o,(tq-oq)@np.array(o.matrix_world.inverted().to_3x3()).T)
np.savez_compressed(P/'lower-lid-balance.npz',**payload)
report=dict(baseline_sha256=SHA,side=1,screen='right',entries=entries,depth_samples=depth,wall_bindings=bindings,geodesic_radius_mm=7.5,method='40% bounded lower-rim profile blend toward the other canthus-local lower curve at retained own width; maximum1.1mm. Corners/upperpath anchored. Depth follows same actual sclera shell. Lowerwall/lashes transported from evaluated skin frames. Original arrays remain unchanged.',activation='Neutral correction fades under matching Close/Joy, half under Surprise,80percent under Angry. Other-side iris/sclera/face contour unchanged.',payload_sha256=hashlib.sha256((P/'lower-lid-balance.npz').read_bytes()).hexdigest(),native_saved=False)
(P/'lower-lid-balance.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');assert hashlib.sha256(N.read_bytes()).hexdigest()==SHA
print('LOWER_LID_BALANCE_PAYLOAD_READY',[(r['owner'],r['vertices'],r['maximum_delta_mm']) for r in entries],flush=True)
