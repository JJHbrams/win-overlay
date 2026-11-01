"""Fair actual final facial positions, not a displacement field.

Use R17 only as a soft primary-shape constraint. Aperture and shared-cap edges
are fixed; medial nose/mouth-side bands are free. Cotangent curvature energy
acts on the final coordinates across the whole cheek/central-face region.
"""
import ast,hashlib,json,sys
from pathlib import Path
from collections import Counter
import bpy
import numpy as np
from mathutils import Vector
HERE=Path(__file__).resolve().parent;SOURCE=HERE/'candidate-r17/Mia_FaceFinish7_PrimaryFormR17_v22.blend';ANCHOR=HERE/'candidate-r15/Mia_FaceFinish7_RadialGuideR15_v22.blend';OUT=HERE/'candidate-r19';OUT.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();ah=lambda p:hashlib.sha256(np.asarray(p).tobytes()).hexdigest()
tree=ast.parse((HERE.parent/'finish-6/dependencies/legacy_snapshot_apply_interp.py').read_text(encoding='utf-8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['snapshots','apply']],type_ignores=[]),'frozen-snapshot-apply','exec'))
def points(o):return np.array([tuple(v.co) for v in o.data.shape_keys.key_blocks[0].data])
def normals(p,faces):
 n=np.cross(p[faces[:,1]]-p[faces[:,0]],p[faces[:,2]]-p[faces[:,0]]);return n/np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-20)
EAR_SOURCE=HERE.parent/'finish-6/continuous-candidate/Mia_FaceFinish6_v22.blend';bpy.ops.wm.open_mainfile(filepath=str(EAR_SOURCE));ear_source_sha=sha(EAR_SOURCE);ear_skin=bpy.data.objects['MIA_V14_SculptedSkin'];ear_ids=np.arange(588,728);ear_basis=points(ear_skin)[ear_ids];ear_cache=np.array([tuple(ear_skin.data.vertices[int(i)].co) for i in ear_ids]);ear_keys={k.name:np.array([tuple(k.data[int(i)].co) for i in ear_ids]) for k in ear_skin.data.shape_keys.key_blocks}
assert np.all(ear_basis[:,1]<-.00049) and np.min(np.degrees(np.arctan2(np.abs(ear_basis[:,0]),ear_basis[:,1])))>90.4
bpy.ops.wm.open_mainfile(filepath=str(ANCHOR));anchor_sha=sha(ANCHOR);anchor=points(bpy.data.objects['MIA_V14_SculptedSkin'])
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));source_sha=sha(SOURCE);skin=bpy.data.objects['MIA_V14_SculptedSkin'];P=points(skin);original_P=P.copy();P[ear_ids]=ear_basis;before=snapshots();packed={im.name:hashlib.sha256(im.packed_file.data).hexdigest() for im in bpy.data.images if im.packed_file}
faces=np.array([list(f.vertices[:3]) for f in skin.data.polygons]);edge_count=Counter(tuple(sorted((a,b))) for f in faces for a,b in zip(f,np.roll(f,-1)));boundary={i for edge,count in edge_count.items() if count==1 for i in edge}
adj=[set() for _ in P];cot={}
for f in faces:
 for a,b,c in [tuple(f),tuple(np.roll(f,1)),tuple(np.roll(f,2))]:
  va=P[a]-P[c];vb=P[b]-P[c];weight=float(np.dot(va,vb)/max(np.linalg.norm(np.cross(va,vb)),1e-12));edge=tuple(sorted((int(a),int(b))));cot[edge]=cot.get(edge,0.)+.5*weight;adj[a].add(b);adj[b].add(a)
# Positive cotangents avoid an inherited obtuse triangle creating a negative
# fairness weight. No topology or UV reparameterization is performed here.
cot={e:max(w,.025) for e,w in cot.items()}
region=sorted(i for i,(x,y,z) in enumerate(P) if 1.464<z<1.552 and y>-.008 and abs(x)<.073 and i not in boundary and i<588)
index={i:k for k,i in enumerate(region)};n=len(region);L=np.zeros((n,n));rhs=np.zeros((n,3));weights=np.full(n,.32);targets=P[region].copy();fixed_neighbor_rows=[]
for row,i in enumerate(region):
 ww={j:cot[tuple(sorted((i,j)))] for j in adj[i]};total=sum(ww.values());L[row,row]=1.
 for j,w in ww.items():
  w/=total
  if j in index:L[row,index[j]]-=w
  else:rhs[row]+=w*P[j]
 x,y,z=P[i]
 # Nose/lip/chin are identity constraints with finite stiffness. Their nearby
 # cheek vertices are solve variables, not a pinned central band.
 if abs(x)<.004 and 1.502<z<1.526:weights[row]=5.
 if abs(x)<.009 and 1.486<z<1.500:weights[row]=3.
 if abs(x)<.008 and z<1.478:targets[row]=anchor[i];weights[row]=12.
 if any(j>=588 for j in adj[i]):weights[row]=max(weights[row],3.)
 if any(j in boundary for j in adj[i]):
  weights[row]=max(weights[row],1.5);fixed_neighbor_rows.append(row)
 # Retain the forehead join without letting its fixed boundary force a cheek
 # ridge: data attachment grows gradually above the lower orbital support.
 if z>1.541:weights[row]=max(weights[row],2.5)
fairness=22.
A=np.diag(weights)+fairness*(L.T@L);B=weights[:,None]*targets+fairness*(L.T@rhs)
solved=np.linalg.solve(A,B);delta=np.zeros_like(P);delta[region]=solved-P[region]
# Active constraints preserve only triangles whose actual orientation would
# otherwise collapse. This is primarily tiny lip/nose feature topology; it is
# not a spatially pinned nose-to-cheek band. Re-solve final positions each time.
locked=set();orientation_steps=[]
for attempt in range(10):
 dots=np.sum(normals(P,faces)*normals(P+delta,faces),axis=1);bad=np.where(dots<.15)[0]
 orientation_steps.append({'attempt':attempt,'minimum_dot':float(dots.min()),'failing_faces':bad.tolist()})
 if not len(bad):break
 new={int(i) for f in faces[bad] for i in f if int(i) in index}-locked
 if not new:break
 locked|=new;fixed_rows=sorted(index[i] for i in locked);free_rows=sorted(set(range(n))-set(fixed_rows));fixed_values=P[np.array(region)[fixed_rows]]
 solved[fixed_rows]=fixed_values;solved[free_rows]=np.linalg.solve(A[np.ix_(free_rows,free_rows)],B[free_rows]-A[np.ix_(free_rows,fixed_rows)]@fixed_values)
 delta[:]=0;delta[region]=solved-P[region]
dots=np.sum(normals(P,faces)*normals(P+delta,faces),axis=1);maxdelta=float(np.linalg.norm(delta,axis=1).max());print('POSITION_FAIR',len(region),maxdelta,float(dots.min()),'orientation_locked',sorted(locked),flush=True)
assert maxdelta<.012 and dots.min()>.10,('Bounded fairness failed',maxdelta,float(dots.min()))
errors=apply(skin,delta)
# Exact restoration, not an approximate delta transfer: all source ear keys,
# the Basis and mesh cache match the frozen Face6 ear patch byte for byte.
for key in skin.data.shape_keys.key_blocks:
 for i,p in zip(ear_ids,ear_keys[key.name]):key.data[int(i)].co=p
for i,p in zip(ear_ids,ear_cache):skin.data.vertices[int(i)].co=p
skin.data.update();skin['v22_finish7_position_fair_r19']='Final-position fairness with exact frozen external-ear constraints and a solved preauricular transition; central cheek bands remain free.'
# Boundary features and shared seam are exact. Existing face-owned ink roots
# sit on fixed oral/ocular boundaries; no carrier or lash depth guess is made.
assert np.linalg.norm(delta[list(boundary)],axis=1).max()==0
after=snapshots()
for name in before:
 if name!=skin.name:assert before[name]==after[name],name
 else:
  for key in ['uv','topology','weights','materials','matrix','modifiers']:assert before[name][key]==after[name][key],key
assert max(errors.values())<2e-7
# R17's auxiliary guides are archived explicitly; they are not R19 evidence.
archived_guides=[]
for obj in bpy.context.scene.objects:
 if obj.name.startswith('MIA_R') and 'GUIDE' in obj.name:
  obj.hide_render=True;obj.hide_viewport=True;old=obj.name;obj.name='ARCHIVED_R17_'+old;obj['role']='Archived R17 guide, not an R19 target or rendering surface';archived_guides.append(obj.name)
saved_snapshot=snapshots();native=OUT/'Mia_FaceFinish7_PositionFairR19_v22.blend'
if '--validate-existing' not in sys.argv:
 assert not native.exists();bpy.ops.wm.save_as_mainfile(filepath=str(native))
else:assert native.exists()
native_sha=sha(native)
bpy.ops.wm.open_mainfile(filepath=str(native));assert snapshots()==saved_snapshot;assert packed=={im.name:hashlib.sha256(im.packed_file.data).hexdigest() for im in bpy.data.images if im.packed_file};assert sha(SOURCE)==source_sha and sha(ANCHOR)==anchor_sha
report={'source':{'path':str(SOURCE),'sha256':source_sha},'chin_anchor_source':{'path':str(ANCHOR),'sha256':anchor_sha},'native':{'path':str(native),'sha256':native_sha},'recipe':{'path':str(Path(__file__).resolve()),'sha256':sha(__file__)},'representation':'Actual final positions minimize positive cotangent Laplacian curvature plus soft source-shape constraints. No displacement smoothing or stacked contour offsets.','region_vertices':len(region),'region_ids':region,'fixed_boundary_ids':sorted(boundary),'curvature_weight':fairness,'base_shape_weight':.32,'max_position_delta_m':maxdelta,'minimum_old_new_face_normal_dot':float(dots.min()),'relative_key_errors':errors,'body_entire_mesh_exact':True,'shared_boundary_exact':True,'eye_carrier_lash_exact':True,'archived_hidden_guides':archived_guides,'limits':['New shape proposal; requires actual low/level/high/source review.','Data/key preservation is not an art or motion PASS.']}
report['orientation_feature_constraints']={'locked_vertex_ids':sorted(locked),'iterations':orientation_steps}
restored=bpy.data.objects['MIA_V14_SculptedSkin']
ear_exact=all(np.array_equal(np.array([tuple(k.data[int(i)].co) for i in ear_ids]),ear_keys[k.name]) for k in restored.data.shape_keys.key_blocks) and np.array_equal(np.array([tuple(restored.data.vertices[int(i)].co) for i in ear_ids]),ear_cache)
assert ear_exact and sha(EAR_SOURCE)==ear_source_sha
report['external_ears']={'source':str(EAR_SOURCE),'sha256':ear_source_sha,'ids':ear_ids.tolist(),'cache_and_all_keys_exact':ear_exact,'attachment':'Ear positions participate as fixed coordinates in the solve; adjacent facial vertices remain free with soft data attachment.'}
(OUT/'manifest.json').write_text(json.dumps(report,indent=2,default=lambda v:v.item()));(OUT/'exact-recipe.py').write_bytes(Path(__file__).read_bytes());(OUT/'vertex-deltas.json').write_text(json.dumps([{'id':int(i),'before':P[i].tolist(),'delta':delta[i].tolist()} for i in region],indent=2));print(json.dumps(report,indent=2,default=lambda v:v.item()))

