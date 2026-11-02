"""A local animated mouth correction; keep the original42 shapes and neutral exact.

The source10 grin has a broad curved tooth band. Existing Fun closes over the teeth;
existing E opens the lip but gives only a thin tooth edge. This candidate controls the
actual32-vertex aperture, its connected soft tissue, and existing upper/lower teeth.
It is a source-informed deformation hypothesis requiring actual multi-angle review.
"""
from pathlib import Path
import argparse, hashlib, json, sys, collections
import bpy, numpy as np
from mathutils import Vector
P=Path(__file__).resolve().parent
NAME='Face.M_F00_000_00_Fcl_MIA_ToothyGrin'
def apply_to_current_scene():
 skin=bpy.data.objects['MIA_V27_SharedHeadBody'];mouth=bpy.data.objects['MIA_V27_Foundation_Face']
 assert NAME not in skin.data.shape_keys.key_blocks and NAME not in mouth.data.shape_keys.key_blocks
 def coords(o,key):return np.array([o.matrix_world @ v.co for v in o.data.shape_keys.key_blocks[key].data],dtype=float)
 def put(o,points):
  inv=o.matrix_world.inverted();k=o.shape_key_add(name=NAME,from_mix=False)
  for i,v in enumerate(points):k.data[i].co=inv@Vector(v)
  k.value=0.
  return k
 sk=skin.data.shape_keys.key_blocks;basis=coords(skin,'Basis');e=coords(skin,'Face.M_F00_000_00_Fcl_MTH_E')
 edge_counts=collections.Counter(pair for f in skin.data.polygons for pair in f.edge_keys)
 ring_edges=[pair for pair,n in edge_counts.items() if n==1 and all(abs(basis[i,0])<.045 and basis[i,1]<-.05 and 1.47<basis[i,2]<1.52 for i in pair)]
 ring_ids=sorted(set(i for pair in ring_edges for i in pair));assert len(ring_ids)==32
 radj={i:[] for i in ring_ids}
 for a,b in ring_edges:radj[a].append(b);radj[b].append(a)
 assert all(len(v)==2 for v in radj.values())
 left=min(ring_ids,key=lambda i:e[i,0]);right=max(ring_ids,key=lambda i:e[i,0]);paths=[]
 for first in radj[left]:
  path=[left,first]
  while path[-1]!=right:
   nxt=next(i for i in radj[path[-1]] if i!=path[-2]);path.append(nxt);assert len(path)<=32
  paths.append(path)
 upper=max(paths,key=lambda p:np.mean(e[p,2]));lower=min(paths,key=lambda p:np.mean(e[p,2]))
 cx=(e[left,0]+e[right,0])/2;half=(e[right,0]-e[left,0])/2
 def heights(u):return 1.498+.003*u*u+.00035*u,1.4925+.0085*u*u+.00035*u
 targets={}
 for path,side in [(upper,0),(lower,1)]:
  for i in path:
   u=float(np.clip((e[i,0]-cx)/half,-1,1));z=heights(u)[side]
   targets[i]=np.array([cx+1.08*(e[i,0]-cx),e[i,1],z])
 adj={i:set() for i in range(len(basis))}
 # Access Blender Edge.vertices explicitly rather than guessing an iterable edge layout.
 for edge in skin.data.edges:
  a,b=edge.vertices;adj[a].add(b);adj[b].add(a)
 domain={i for i,v in enumerate(basis) if abs(v[0])<.047 and v[1]<-.040 and 1.455<v[2]<1.529}
 connected=set();stack=list(ring_ids)
 while stack:
  i=stack.pop()
  if i in connected or i not in domain:continue
  connected.add(i);stack.extend(adj[i]-connected)
 domain=connected
 outer={i for i in domain if any(j not in domain for j in adj[i])}
 fixed={i:np.zeros(3) for i in outer};fixed.update({i:targets[i]-basis[i] for i in ring_ids})
 unknown=sorted(domain-set(fixed));index={i:j for j,i in enumerate(unknown)};A=np.zeros((len(unknown),len(unknown)));B=np.zeros((len(unknown),3))
 for i,row in index.items():
  for j in adj[i]:
   w=1/max(float(np.linalg.norm(basis[i]-basis[j])),1e-5);A[row,row]+=w
   if j in index:A[row,index[j]]-=w
   elif j in fixed:B[row]+=w*fixed[j]
 solved=np.linalg.solve(A,B);target=basis.copy()
 for i,d in fixed.items():target[i]+=d
 for i,row in index.items():target[i]+=solved[row]
 key=put(skin,target)
 # The original atlas and known Joy response identify actual teeth; no new painted teeth.
 mb=coords(mouth,'Basis');me=coords(mouth,'Face.M_F00_000_00_Fcl_MTH_E');mj=coords(mouth,'Face.M_F00_000_00_Fcl_MTH_Joy');mt=mb.copy()
 visible_ids=set(i for f in mouth.data.polygons if f.material_index==0 for i in f.vertices)
 uv=mouth.data.uv_layers.active;white=set()
 for f in mouth.data.polygons:
  if f.material_index!=0:continue
  q=sum((uv.data[i].uv for i in f.loop_indices),Vector((0,0)))/len(f.loop_indices)
  if q.x<.46 and q.y>.52:white.update(f.vertices)
 upper_teeth={i for i in white if mj[i,2]-mb[i,2]>.0005};lower_teeth={i for i in white if mj[i,2]-mb[i,2]<-.0005}
 assert len(upper_teeth)==120 and len(lower_teeth)==112
 def interp(path,u,axis):
  ordered=sorted(path,key=lambda i:e[i,0]);xs=np.array([(e[i,0]-cx)/half for i in ordered]);vs=e[ordered,axis]
  return float(np.interp(u,xs,vs))
 tmin=me[list(upper_teeth),2].min();tmax=me[list(upper_teeth),2].max()
 for i in visible_ids:
  u=float(np.clip((me[i,0]-cx)/half,-1,1));up,low=heights(u);old_up=interp(upper,u,2);old_low=interp(lower,u,2)
  v=(me[i,2]-old_low)/max(old_up-old_low,.0003)
  mt[i]=[cx+1.08*(me[i,0]-cx),me[i,1],low+v*(up-low)]
  if i in upper_teeth:
   t=float(np.clip((me[i,2]-tmin)/(tmax-tmin),0,1));bottom=low+.0006;top=max(bottom+.0002,up-.00025)
   mt[i,2]=bottom+t*(top-bottom)
   mt[i,1]=max(mt[i,1],interp(upper,u,1)+.001)
  elif i in lower_teeth:
   mt[i,2]=min(mt[i,2],low-.0007);mt[i,1]+=.0015
 # The inherited cavity/tongue can sit ahead of the tooth band after widening.
 # Keep exact shared lip-root positions; retract only the interior behind teeth.
 matched_roots=0
 for i in visible_ids-white:
  distance=np.linalg.norm(basis[ring_ids]-mb[i],axis=1);j=int(np.argmin(distance));nearest=ring_ids[j]
  if distance[j]<.00001:
   mt[i]=targets[nearest];matched_roots+=1
  else:
   u=float(np.clip((me[i,0]-cx)/half,-1,1));blend=float(np.clip(distance[j]/.004,0,1))
   back=max(mt[i,1],interp(upper,u,1)+.004)
   mt[i,1]=mt[i,1]*(1-blend)+back*blend
 put(mouth,mt)
 f=key.driver_add('value');f.driver.type='AVERAGE';v=f.driver.variables.new();v.name='source_grin';v.type='SINGLE_PROP';v.targets[0].id_type='KEY';v.targets[0].id=mouth.data.shape_keys;v.targets[0].data_path='key_blocks["'+NAME+'"].value'
 return dict(name=NAME,skin_domain=len(domain),matched_cavity_lip_roots=matched_roots,mouth_aperture_controls=ring_ids,skin_changed=int(np.sum(np.linalg.norm(target-basis,axis=1)>1e-8)),upper_teeth=sorted(upper_teeth),lower_teeth=sorted(lower_teeth),
   source_panel=10,original42_arrays_unchanged=True,neutral_unchanged=True,art_approved=False,
   mechanism='Continuous harmonic lip/soft-tissue field and existing teeth/cavity deformation. New key only; original coordinates/keys/UV/maps/weights remain intact.')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--native',required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--output',required=True)
 a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);p=Path(a.native);out=Path(a.output);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 assert sha(p)==a.sha256 and not out.exists();bpy.ops.wm.open_mainfile(filepath=str(p.resolve()),use_scripts=False)
 report=apply_to_current_scene();out.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()))
 report.update(native=str(out),sha256=sha(out),input_sha256=a.sha256)
 report['new_key_default_values']={n:bpy.data.objects[n].data.shape_keys.key_blocks[NAME].value for n in ['MIA_V27_SharedHeadBody','MIA_V27_Foundation_Face']}
 assert all(v==0 for v in report['new_key_default_values'].values())
 out.with_suffix('.build.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('SOURCE_GRIN_KEY_BUILT',sha(out),flush=True)
