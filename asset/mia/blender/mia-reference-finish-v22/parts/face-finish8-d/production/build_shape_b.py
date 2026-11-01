"""Connected nose-wing/upper-buccal target; no topology or fairing solver."""
import ast,bpy,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'shape-b';OUT.mkdir(exist_ok=True)
SOURCE=ROOT/'shape-a/Mia_FaceFinish8_CompactSectionsA.blend'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();ah=lambda p:hashlib.sha256(np.asarray(p).tobytes()).hexdigest()
t=ast.parse((ROOT.parent/'finish-6/dependencies/legacy_snapshot_apply_interp.py').read_text());exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in ['snapshots','apply']],type_ignores=[]),'guards','exec'))
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));before=snapshots();o=bpy.data.objects['MIA_V14_SculptedSkin'];p=np.array([tuple(v.co) for v in o.data.shape_keys.key_blocks[0].data]);d=np.zeros_like(p);regions={}
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
# Rounded profile wedge, with existing underside branch preserved. This is a
# bounded compression of the excessively projecting nose, not a frontal sheet.
for i,(x,y,z) in enumerate(p):
 if abs(x)<.007 and 1.511<z<1.528 and y>.080:
  w=smooth(.080,.090,y);d[i,1]=-.0026*w;d[i,0]=.22*x*w;regions[i]='rounded_nasal_wedge'
# Explicit adjacent rows around alar and upper-lip support, forward/anterior +Y.
targets={299:.0008,300:.0006,296:.0012,298:.0020,297:.0017,303:.0010,302:.0018,293:.0013,433:.0011,436:.0007,437:.0004,294:.0006,295:.0005}
mapping={}
for i,dy in targets.items():
 neg=np.where(p[:,0]<0)[0];j=int(neg[np.argmin(np.linalg.norm(p[neg]-p[i]*[-1,1,1],axis=1))]);assert np.linalg.norm(p[j]-p[i]*[-1,1,1])<.002
 d[i,1]+=dy;d[j,1]+=dy;regions[i]=regions[j]='connected_alar_upper_buccal_support';mapping[i]=j
assert np.max(abs(d[588:]))==0
faces=np.array([list(f.vertices[:3]) for f in o.data.polygons]);q=p+d
def normals(v):
 n=np.cross(v[faces[:,1]]-v[faces[:,0]],v[faces[:,2]]-v[faces[:,0]]);return n/np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-20)
dots=np.sum(normals(p)*normals(q),1);assert dots.min()>.8,float(dots.min())
errors=apply(o,d);assert max(errors.values())<2e-7;after=snapshots()
for n in before:
 if n!=o.name:assert before[n]==after[n],n
 else:
  for k in ['uv','topology','weights','materials','matrix','modifiers']:assert before[n][k]==after[n][k],k
native=OUT/'Mia_FaceFinish8_NasalBuccalB.blend';assert not native.exists();bpy.ops.wm.save_as_mainfile(filepath=str(native));bpy.ops.wm.open_mainfile(filepath=str(native));assert snapshots()==after
ids=np.where(np.linalg.norm(d,axis=1)>1e-12)[0]
(OUT/'vertex-deltas.json').write_text(json.dumps([{'owner':'MIA_V14_SculptedSkin','id':int(i),'region':regions[int(i)],'before':p[i].tolist(),'after':q[i].tolist(),'delta':d[i].tolist()} for i in ids],indent=2))
(OUT/'manifest.json').write_text(json.dumps({'status':'WORKING CANDIDATE / ART UNAPPROVED','source':{'path':str(SOURCE),'sha256':sha(SOURCE)},'native':{'path':str(native),'sha256':sha(native)},'changes':{'skin_vertices':len(ids),'maximum_m':float(np.linalg.norm(d,axis=1).max()),'minimum_normal_dot':float(dots.min()),'relative_key_errors':errors,'mirror_mapping':mapping},'recipe':{'path':str(Path(__file__)),'sha256':sha(__file__)},'limits':['Existing cage valence does not establish topology incapacity. Direct semantic positions tested first.','Aperture, outer apex, ears, jaw/cap and all non-skin owners exact from ShapeA.','Limited motion/source review required; no whole-art PASS.']},indent=2));print('SHAPE_B_DONE',len(ids))
