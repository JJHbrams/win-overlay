"""Articulated source-like upper-lid arc and a thin directional outer wing.

R19 is the frozen primary-surface checkpoint. The actual upper aperture edge,
its neighboring skin support and attached ribbon share one canthus-frame arc.
No iris/carrier scale, carrier depth, or makeup is changed.
"""
import ast,hashlib,json,math
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
HERE=Path(__file__).resolve().parent;SOURCE=HERE/'candidate-r19/Mia_FaceFinish7_PositionFairR19_v22.blend';OUT=HERE/'candidate-r22';OUT.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();ah=lambda p:hashlib.sha256(np.asarray(p).tobytes()).hexdigest()
tree=ast.parse((HERE.parent/'finish-6/dependencies/legacy_snapshot_apply_interp.py').read_text(encoding='utf-8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['snapshots','apply']],type_ignores=[]),'frozen-guards','exec'))
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));source_sha=sha(SOURCE);skin=bpy.data.objects['MIA_V14_SculptedSkin'];P=np.array([tuple(v.co) for v in skin.data.shape_keys.key_blocks[0].data]);before=snapshots();packed={im.name:hashlib.sha256(im.packed_file.data).hexdigest() for im in bpy.data.images if im.packed_file}
raw_upper=[[345,346,347,348,349,350,351,353,356,357],[497,498,499,500,501,502,503,504,506,510]]
raw_lower=[[320,321,326,327,330,331,332,334,336,337,338,344,359,361],[495,509,513,514,517,518,521,522,525,526,528,529,531,533]]
upper={int(np.sign(P[ids,0].mean())):sorted(ids,key=lambda i:abs(P[i,0])) for ids in raw_upper};lower={int(np.sign(P[ids,0].mean())):sorted(ids,key=lambda i:abs(P[i,0])) for ids in raw_lower};arcs={};fixed={}
for sign,ids in upper.items():
 loop=lower[sign];inner=min(loop,key=lambda i:abs(P[i,0]));outer=max(loop,key=lambda i:abs(P[i,0]));x0,x1=abs(P[inner,0]),abs(P[outer,0]);z0,z1=P[inner,2],P[outer,2]
 samples=[inner]+ids+[outer];xs=np.array([abs(P[i,0]) for i in samples]);oldzs=P[samples,2]
 def desired(x):
  t=np.clip((x-x0)/(x1-x0),0,1);return z0+(z1-z0)*t+.0032*4*t*(1-t)*(1-.12*(t-.5))
 dz=np.array([desired(x)-z for x,z in zip(xs,oldzs)]);dz[0]=dz[-1]=0
 for i,d in zip(samples,dz):fixed[i]=np.array([0.,0.,d])
 for i in loop:fixed[i]=np.zeros(3)
 # Inner/outer corner entries were fixed through the lower-arc assignment;
 # the ten movable upper edge samples retain their authored target arc.
 for i,d in zip(ids,dz[1:-1]):fixed[i]=np.array([0.,0.,d])
 arcs[sign]={'upper_ids':ids,'inner':inner,'outer':outer,'x':xs,'dz':dz,'source_z':oldzs,'target_z':oldzs+dz}
adj=[set() for _ in P]
for edge in skin.data.edges:
 i,j=edge.vertices;adj[i].add(j);adj[j].add(i)
seeds={i for ids in upper.values() for i in ids};distance={i:0 for i in seeds};frontier=set(seeds)
for depth in range(1,4):
 nxt={j for i in frontier for j in adj[i] if j not in distance and P[j,2]>1.534 and P[j,1]>.028 and abs(P[j,0])<.067};distance.update({j:depth for j in nxt});frontier=nxt
free=sorted(i for i,d in distance.items() if i not in fixed and d<3);index={i:k for k,i in enumerate(free)};A=np.zeros((len(free),len(free)));B=np.zeros((len(free),3))
for row,i in enumerate(free):
 ws={j:1/max(np.linalg.norm(P[i]-P[j]),.001) for j in adj[i]};total=sum(ws.values());A[row,row]=1.35
 for j,w in ws.items():
  w/=total
  if j in index:A[row,index[j]]-=w
  elif j in fixed:B[row]+=w*fixed[j]
delta=np.zeros_like(P)
for i,d in fixed.items():delta[i]=d
if len(free):delta[free]=np.linalg.solve(A,B)
faces=np.array([list(f.vertices[:3]) for f in skin.data.polygons])
def normals(points):
 n=np.cross(points[faces[:,1]]-points[faces[:,0]],points[faces[:,2]]-points[faces[:,0]]);return n/np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-20)
dots=np.sum(normals(P)*normals(P+delta),axis=1);assert dots.min()>.30;assert np.linalg.norm(delta,axis=1).max()<.0025
errors={skin.name:apply(skin,delta)};owners={skin.name};exports={skin.name:[{'id':int(i),'before':P[i].tolist(),'delta':delta[i].tolist(),'region':'upper_rim' if i in seeds else 'orbital_support'} for i in np.where(np.linalg.norm(delta,axis=1)>1e-10)[0]]}
def arc_delta(point):
 sign=1 if point[0]>=0 else -1;a=arcs[sign];x=abs(point[0]);return float(np.interp(x,a['x'],a['dz'],left=0,right=0))
for obj in bpy.context.scene.objects:
 if obj.type!='MESH' or not obj.name.startswith('MIA_V14_') or not any(t in obj.name for t in ['UpperLash','OuterWing']):continue
 toskin=skin.matrix_world.inverted()@obj.matrix_world;back=toskin.inverted();base=np.array([tuple(v.co) for v in obj.data.shape_keys.key_blocks[0].data]);points=np.array([tuple(toskin@Vector(p)) for p in base]);result=points.copy();pairs=len(points)//2
 for pair in range(pairs):
  i=2*pair;center=(points[i]+points[i+1])/2;half=(points[i+1]-points[i])/2;dz=arc_delta(center)
  if 'OuterWing' in obj.name:
   t=pair/max(pairs-1,1);sign=1 if center[0]>0 else -1
   # Keep the root overlap, taper the ribbon toward one thin directed tip.
   center=center+np.array([sign*.00075*t*t,-.00045*t*t,dz+.00035*t*t]);half*=1-.45*math.sin(math.pi*t/2)
  else:center=center+np.array([0,0,dz])
  result[i]=center-half;result[i+1]=center+half
 local=np.array([tuple(back@Vector(p)) for p in result]);d=local-base;errors[obj.name]=apply(obj,d);owners.add(obj.name);exports[obj.name]=[{'id':i,'before':p.tolist(),'delta':dd.tolist(),'region':'upper_lash' if 'UpperLash' in obj.name else 'outer_wing'} for i,(p,dd) in enumerate(zip(base,d)) if np.linalg.norm(dd)>1e-10]
skin['v22_finish7_eye_arc_r22']='Canthus-frame articulated upper aperture arc, distributed orbital support, linked upper lash and thin directional outer wing; carrier unchanged.'
after=snapshots()
for name in before:
 if name not in owners:assert before[name]==after[name],name
 else:
  for key in ['uv','topology','weights','materials','matrix','modifiers']:assert before[name][key]==after[name][key],(name,key)
assert max(e for values in errors.values() for e in values.values())<2e-7
native=OUT/'Mia_FaceFinish7_EyeArcR22_v22.blend';assert not native.exists();bpy.ops.wm.save_as_mainfile(filepath=str(native));native_sha=sha(native)
bpy.ops.wm.open_mainfile(filepath=str(native));assert snapshots()==after and sha(SOURCE)==source_sha;assert packed=={im.name:hashlib.sha256(im.packed_file.data).hexdigest() for im in bpy.data.images if im.packed_file}
report={'source':{'path':str(SOURCE),'sha256':source_sha},'native':{'path':str(native),'sha256':native_sha},'recipe':{'path':str(Path(__file__).resolve()),'sha256':sha(__file__)},'arcs':{str(k):{n:(v.tolist() if isinstance(v,np.ndarray) else v) for n,v in a.items()} for k,a in arcs.items()},'changed_owners':sorted(owners),'skin_max_delta_m':float(np.linalg.norm(delta,axis=1).max()),'skin_minimum_old_new_face_normal_dot':float(dots.min()),'body_ears_lower_face_carrier_materials_exact':True,'relative_key_errors':errors,'limits':['Neutral arc and actual movement need visual review.','Inherited Close key over-closes at value .5; preserved relative keys are not a motion PASS.','No new makeup or eye/iris scale/depth change.']}
(OUT/'manifest.json').write_text(json.dumps(report,indent=2));(OUT/'owner-vertex-deltas.json').write_text(json.dumps(exports,indent=2));(OUT/'exact-recipe.py').write_bytes(Path(__file__).read_bytes());print(json.dumps(report,indent=2))
