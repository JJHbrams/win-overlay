"""Linked lower-face section edit. R28 remains immutable; no fairing pass."""
import bpy,ast,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent/'shape-a';OUT.mkdir(exist_ok=True)
ROOT=OUT.parent.parent;SOURCE=ROOT/'finish-7/candidate-r28/Mia_FaceFinish7_MedialTransitionR28_v22.blend'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
ah=lambda a:hashlib.sha256(np.asarray(a).tobytes()).hexdigest()
t=ast.parse((ROOT/'finish-6/dependencies/legacy_snapshot_apply_interp.py').read_text())
exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in ['snapshots','apply']],type_ignores=[]),'frozen-guards','exec'))
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));before=snapshots();rows=[];changes={}
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def section_delta(p):
 x,y,z=p.T;d=np.zeros_like(p)
 front=smooth(-.005,.035,y);bottom=smooth(1.46,1.466,z)
 # One monotone section compression, including mouth/nasal base and jaw.
 t=np.clip((1.530-z)/.064,0,1)
 d[:,2]=.0055*(t*t*(3-2*t))*front*bottom
 # The needle tip becomes a short soft chin; outer cheek width is not inflated.
 chin=smooth(1.500,1.471,z)
 d[:,0]=.0030*np.tanh(x/.005)*np.exp(-(x/.022)**4)*chin*front*bottom
 # Slight lower cheek convergence, continuous into the short jaw section.
 lateral=smooth(.020,.040,np.abs(x))*(1-smooth(.053,.068,np.abs(x)))
 height=smooth(1.480,1.497,z)*(1-smooth(1.510,1.529,z))
 d[:,0]-=np.sign(x)*.0013*lateral*height*front*bottom
 return d
owners=['MIA_V14_SculptedSkin','MIA_V06_BODY_SKIN','MIA_V14_MouthSeam','MIA_V14_SmoothJawInk']
for name in owners:
 o=bpy.data.objects[name];p=np.array([tuple(v.co) for v in (o.data.shape_keys.key_blocks[0].data if o.data.shape_keys else o.data.vertices)])
 d=section_delta(p)
 if name=='MIA_V14_SculptedSkin':d[588:]=0
 if name=='MIA_V06_BODY_SKIN':
  world=np.array([tuple(o.matrix_world@v.co) for v in o.data.vertices]);d[world[:,2]<=1.46]=0
 ids=np.where(np.linalg.norm(d,axis=1)>1e-12)[0]
 if not len(ids):continue
 # Broadcast only the neutral change: original R23 key-specific closure deltas survive.
 errors=apply(o,d);assert max(errors.values(),default=0)<2e-7
 faces=np.array([list(f.vertices[:3]) for f in o.data.polygons]);a=p[faces[:,1]]-p[faces[:,0]];b=p[faces[:,2]]-p[faces[:,0]]
 q=p+d;aa=q[faces[:,1]]-q[faces[:,0]];bb=q[faces[:,2]]-q[faces[:,0]]
 n=np.cross(a,b);nn=np.cross(aa,bb);dot=np.sum(n*nn,1)/np.maximum(np.linalg.norm(n,axis=1)*np.linalg.norm(nn,axis=1),1e-20)
 valid=np.linalg.norm(n,axis=1)>1e-12;assert dot[valid].min()>.65,(name,float(dot[valid].min()))
 changes[name]={'count':len(ids),'maximum_m':float(np.linalg.norm(d,axis=1).max()),'relative_key_error_m':errors,'minimum_normal_dot':float(dot[valid].min())}
 rows.extend({'owner':name,'id':int(i),'before':p[i].tolist(),'after':q[i].tolist(),'delta':d[i].tolist()} for i in ids)
after=snapshots()
for name in before:
 if name not in changes:assert before[name]==after[name],name
 else:
  for k in ['uv','topology','weights','materials','matrix','modifiers']:assert before[name][k]==after[name][k],(name,k)
native=OUT/'Mia_FaceFinish8_CompactSectionsA.blend';assert not native.exists();bpy.ops.wm.save_as_mainfile(filepath=str(native))
bpy.ops.wm.open_mainfile(filepath=str(native));assert snapshots()==after
(OUT/'vertex-deltas.json').write_text(json.dumps(rows,indent=2))
(OUT/'manifest.json').write_text(json.dumps({'status':'WORKING CANDIDATE / ART UNAPPROVED','baseline':{'path':str(SOURCE),'sha256':sha(SOURCE)},'native':{'path':str(native),'sha256':sha(native)},'changes':changes,'recipe':{'path':str(Path(__file__)),'sha256':sha(__file__)},'limits':['Source eye-to-chin registration does not validate absolute face height. Candidate must retain baseline SRT.','No global fairness or new cheek inflation. High malar depth and eyelid/lash owners retained.','All relative key deltas retained; limited motion still requires actual rendering.']},indent=2))
print('SHAPE_A_DONE',json.dumps(changes))
