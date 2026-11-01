"""Rebuild actual blink targets to close at1 and remain partially open at.5.

Neutral R22 geometry is exact. Existing exaggerated Close displacement is
retimed geometrically, then both true aperture curves meet one common closed
curve. Actual carrier ray contacts bound the closed rim depth. The four lash
followers are rebuilt from the same closed upper-rim relation.
"""
import ast,hashlib,json
from pathlib import Path
from collections import deque
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE=Path(__file__).resolve().parent;SOURCE=HERE/'candidate-r22/Mia_FaceFinish7_EyeArcR22_v22.blend';OUT=HERE/'candidate-r23';OUT.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();ah=lambda p:hashlib.sha256(np.asarray(p).tobytes()).hexdigest()
tree=ast.parse((HERE.parent/'finish-6/dependencies/legacy_snapshot_apply_interp.py').read_text(encoding='utf-8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='snapshots'],type_ignores=[]),'frozen-snapshot','exec'))
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));source_sha=sha(SOURCE);skin=bpy.data.objects['MIA_V14_SculptedSkin'];P=np.array([tuple(v.co) for v in skin.data.shape_keys.key_blocks[0].data]);before=snapshots();packed={im.name:hashlib.sha256(im.packed_file.data).hexdigest() for im in bpy.data.images if im.packed_file}
raw_upper=[[345,346,347,348,349,350,351,353,356,357],[497,498,499,500,501,502,503,504,506,510]];raw_lower=[[320,321,326,327,330,331,332,334,336,337,338,344,359,361],[495,509,513,514,517,518,521,522,525,526,528,529,531,533]]
upper={int(np.sign(P[ids,0].mean())):sorted(ids,key=lambda i:abs(P[i,0])) for ids in raw_upper};lower={int(np.sign(P[ids,0].mean())):sorted(ids,key=lambda i:abs(P[i,0])) for ids in raw_lower}
old_full=np.array([tuple(v.co) for v in skin.data.shape_keys.key_blocks['Face.M_F00_000_00_Fcl_EYE_Close'].data]);eyes=bpy.data.objects['MIA_V14_EyeSurface'];toskin=skin.matrix_world.inverted()@eyes.matrix_world;eye_points=[toskin@v.co for v in eyes.data.vertices];eye_faces=[list(p.vertices) for p in eyes.data.polygons if p.material_index in [1,5]];carrier=BVHTree.FromPolygons(eye_points,eye_faces)
def curve(t,ts,points):return np.array([np.interp(t,ts,points[:,axis]) for axis in range(3)])
guides={}
for sign in [-1,1]:
 lo=lower[sign];inner=lo[0];outer=lo[-1];up=[inner]+upper[sign]+[outer];x0,x1=abs(P[inner,0]),abs(P[outer,0]);ut=np.array([(abs(P[i,0])-x0)/(x1-x0) for i in up]);lt=np.array([(abs(P[i,0])-x0)/(x1-x0) for i in lo]);ts=np.linspace(0,1,101);ratios=[];closed=[];contacts=[]
 for t in ts:
  ub=curve(t,ut,P[up]);lb=curve(t,lt,P[lo]);uc=curve(t,ut,old_full[up]);lc=curve(t,lt,old_full[lo]);gap=ub[2]-lb[2];amount=gap-(uc[2]-lc[2]);ratios.append(float(np.clip(gap/amount if amount>1e-6 else .38,.20,.65)))
 ratios=np.array(ratios);ratios[:8]=ratios[8];ratios[-8:]=ratios[-9]
 for t,ratio in zip(ts,ratios):
  ub=curve(t,ut,P[up]);lb=curve(t,lt,P[lo]);uc=ub+ratio*(curve(t,ut,old_full[up])-ub);lc=lb+ratio*(curve(t,lt,old_full[lo])-lb);c=(uc+lc)/2
  # Both rim paths meet this common curve, just in front of the actual
  # static carrier wherever a forward carrier hit exists during the stroke.
  y_needed=c[1]
  for base in [ub,lb]:
   for alpha in [.25,.5,.75,1.]:
    p=(1-alpha)*base+alpha*c;hit=carrier.ray_cast(Vector((p[0],.25,p[2])),Vector((0,-1,0)))[0]
    if hit is not None and hit.y>.035:y_needed=max(y_needed,(hit.y+.00010-(1-alpha)*base[1])/alpha)
  contacts.append(float(y_needed-c[1]));c[1]=y_needed;closed.append(c)
 closed=np.asarray(closed);assert max(contacts)<.004,('Carrier needs excessive lid depth',sign,max(contacts));guides[sign]={'upper':up,'lower':lo,'ut':ut,'lt':lt,'x0':x0,'x1':x1,'t':ts,'ratio':ratios,'closed':closed,'carrier_depth_adjustment':contacts}
adj=[set() for _ in P]
for e in skin.data.edges:i,j=e.vertices;adj[i].add(j);adj[j].add(i)
edits={};changed_owners={skin.name}
for key in skin.data.shape_keys.key_blocks:
 if not key.name.endswith(('Fcl_EYE_Close','Fcl_EYE_Close_R','Fcl_EYE_Close_L')):continue
 old=np.array([tuple(v.co) for v in key.data]);d=old-P;new=old.copy();rim_correction={}
 for sign,g in guides.items():
  rim=set(g['upper']+g['lower'])
  if np.linalg.norm(d[list(rim)],axis=1).max()<1e-6:continue
  ids=np.where(P[:,0]*sign>0)[0]
  for i in ids:
   t=np.clip((abs(P[i,0])-g['x0'])/(g['x1']-g['x0']),0,1);scale=float(np.interp(t,g['t'],g['ratio']));new[i]=P[i]+scale*d[i]
  for i in rim:
   t=np.clip((abs(P[i,0])-g['x0'])/(g['x1']-g['x0']),0,1);target=curve(t,g['t'],g['closed']);rim_correction[i]=target-new[i];new[i]=target
 # Carry only the small closure/contact correction through neighboring lid
 # support. The main stroke is the existing topology-aware key displacement.
 first={j for i in rim_correction for j in adj[i] if j not in rim_correction};second={j for i in first for j in adj[i] if j not in first and j not in rim_correction}
 correction={i:d.copy() for i,d in rim_correction.items()}
 for layer,factor in [(first,.55),(second,.22)]:
  for i in layer:
   samples=[j for j in adj[i] if j in correction]
   if samples:correction[i]=factor*np.mean([correction[j] for j in samples],axis=0);new[i]+=correction[i]
 key.data.foreach_set('co',new.ravel());rows=[{'id':int(i),'before':old[i].tolist(),'after':new[i].tolist(),'delta':(new[i]-old[i]).tolist()} for i in np.where(np.linalg.norm(new-old,axis=1)>1e-10)[0]];edits.setdefault(skin.name,{})[key.name]=rows
skin.data.update()
for obj in bpy.context.scene.objects:
 if obj.type!='MESH' or not obj.name.startswith('MIA_V14_') or not any(n in obj.name for n in ['UpperLash','OuterWing']):continue
 toskin=skin.matrix_world.inverted()@obj.matrix_world;back=toskin.inverted();basis=np.array([tuple(v.co) for v in obj.data.shape_keys.key_blocks[0].data]);old=np.array([tuple(v.co) for v in obj.data.shape_keys.key_blocks['MIA_V20_BlinkFollower'].data]);new=[]
 for p in basis:
  q=np.array(toskin@Vector(p));sign=1 if q[0]>=0 else -1;g=guides[sign];t=np.clip((abs(q[0])-g['x0'])/(g['x1']-g['x0']),0,1);base_rim=curve(t,g['ut'],P[g['upper']]);closed_rim=curve(t,g['t'],g['closed']);new.append(tuple(back@Vector(q+closed_rim-base_rim)))
 new=np.asarray(new);obj.data.shape_keys.key_blocks['MIA_V20_BlinkFollower'].data.foreach_set('co',new.ravel());obj.data.update();changed_owners.add(obj.name);edits.setdefault(obj.name,{})['MIA_V20_BlinkFollower']=[{'id':int(i),'before':old[i].tolist(),'after':new[i].tolist(),'delta':(new[i]-old[i]).tolist()} for i in np.where(np.linalg.norm(new-old,axis=1)>1e-10)[0]]
after=snapshots()
for name in before:
 if name not in changed_owners:assert before[name]==after[name],name
 else:
  for field in ['co','uv','topology','weights','materials','matrix','modifiers']:assert before[name][field]==after[name][field],(name,field)
  for key in before[name]['keys']:
   if key not in edits[name]:assert before[name]['keys'][key]==after[name]['keys'][key],(name,key)
native=OUT/'Mia_FaceFinish7_BlinkR23_v22.blend';assert not native.exists();bpy.ops.wm.save_as_mainfile(filepath=str(native));native_sha=sha(native)
bpy.ops.wm.open_mainfile(filepath=str(native));assert snapshots()==after and sha(SOURCE)==source_sha;assert packed=={im.name:hashlib.sha256(im.packed_file.data).hexdigest() for im in bpy.data.images if im.packed_file}
report={'source':{'path':str(SOURCE),'sha256':source_sha},'native':{'path':str(native),'sha256':native_sha},'recipe':{'path':str(Path(__file__).resolve()),'sha256':sha(__file__)},'neutral_r22_basis_cache_exact':True,'carrier_iris_body_ears_materials_exact':True,'edited_keys':{name:list(keys) for name,keys in edits.items()},'closed_curve':{str(sign):{name:(value.tolist() if isinstance(value,np.ndarray) else value) for name,value in g.items()} for sign,g in guides.items()},'limits':['Actual neutral/.5/1.0 and both-oblique captures are required before motion acceptance.','Only symmetric/asymmetric Close and their four ribbon followers are corrected; all47 expressions are not claimed revalidated.']}
(OUT/'manifest.json').write_text(json.dumps(report,indent=2));(OUT/'owner-key-edits.json').write_text(json.dumps(edits,indent=2));(OUT/'exact-recipe.py').write_bytes(Path(__file__).read_bytes());print(json.dumps(report,indent=2))
