"""One connected lateral-cheek/upper-jaw section correction from frozen D.
Chin, eye aperture, anterior high apex, outer contour/cap and maps are fixed.
"""
import ast,bpy,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
from collections import Counter
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'shape-e';OUT.mkdir(exist_ok=True);SOURCE=ROOT/'look-d/Mia_FaceFinish8_AuthoredLookD.blend'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();ah=lambda p:hashlib.sha256(np.asarray(p).tobytes()).hexdigest()
t=ast.parse((ROOT.parent/'finish-6/dependencies/legacy_snapshot_apply_interp.py').read_text());exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in ['snapshots','apply']],type_ignores=[]),'frozen-guards','exec'))
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));before=snapshots();skin=bpy.data.objects['MIA_V14_SculptedSkin'];p=np.array([tuple(v.co) for v in skin.data.shape_keys.key_blocks[0].data]);delta=np.zeros_like(p)
# Anatomical section rows, millimeters anterior +localY. These are declared
# inferred 3D targets, not measurements extracted from uncalibrated drawings.
rows={'lateral_malar_turn':{233:2.6,234:6.5,235:1.0},'lateral_buccal_support':{255:2.0,256:4.5,257:5.5,259:4.5},'short_upper_jaw_transition':{260:1.3,261:1.5,264:1.2,265:2.8,266:1.0,276:2.8,277:1.0,278:2.0,279:.5,290:3.0,291:4.0,292:.8,293:.5}}
mapping={};semantic={};used=set()
for region,values in rows.items():
 for i,dy in values.items():
  neg=np.where(p[:,0]<0)[0];j=int(neg[np.argmin(np.linalg.norm(p[neg]-p[i]*[-1,1,1],axis=1))]);assert np.linalg.norm(p[j]-p[i]*[-1,1,1])<.0015
  assert i not in used and j not in used;used.update([i,j]);mapping[i]=j;semantic[i]=semantic[j]=region;delta[i,1]=delta[j,1]=dy/1000
faces=np.array([list(f.vertices[:3]) for f in skin.data.polygons]);ec=Counter(tuple(sorted((int(f[i]),int(f[(i+1)%3])))) for f in faces for i in range(3));boundary={i for e,n in ec.items() if n==1 for i in e}
assert np.max(abs(delta[list(boundary)]))==0;assert np.max(abs(delta[588:]))==0
assert np.max(abs(delta[abs(p[:,0])<.020]))==0
assert np.max(abs(delta[[236,242,247,248,249,250,251,252,253,254,258]]))==0
def aperture():
 bpy.context.view_layer.update();ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();q=np.array([tuple(v.co) for v in m.vertices]);edge=Counter(tuple(sorted((f.vertices[i],f.vertices[(i+1)%len(f.vertices)]))) for f in m.polygons for i in range(len(f.vertices)));ids=sorted({i for e,n in edge.items() if n==1 for i in e if .010<abs(q[i,0])<.061 and q[i,1]>.035 and 1.525<q[i,2]<1.558});ev.to_mesh_clear();return ids,q[ids]
eyeids,eyebefore=aperture();errors=apply(skin,delta);ids,eyeafter=aperture();assert ids==eyeids and np.array_equal(eyebefore,eyeafter)
def normals(q):
 n=np.cross(q[faces[:,1]]-q[faces[:,0]],q[faces[:,2]]-q[faces[:,0]]);return n/np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-20)
dots=np.sum(normals(p)*normals(p+delta),1);assert dots.min()>.8,float(dots.min());after=snapshots()
for name in before:
 for field in before[name]:
  if name==skin.name and field in ['co','keys']:continue
  assert before[name][field]==after[name][field],(name,field)
native=OUT/'Mia_FaceFinish8_ConnectedCheekE.blend';assert not native.exists();bpy.ops.wm.save_as_mainfile(filepath=str(native));bpy.ops.wm.open_mainfile(filepath=str(native));assert snapshots()==after
changes=[{'owner':'MIA_V14_SculptedSkin','id':i,'region':semantic[i],'before':p[i].tolist(),'after':(p[i]+delta[i]).tolist(),'delta':delta[i].tolist()} for i in sorted(used)]
(OUT/'vertex-deltas-from-d.json').write_text(json.dumps(changes,indent=2))
(OUT/'manifest.json').write_text(json.dumps({'status':'ONE BOUNDED E CANDIDATE / ART UNAPPROVED','baseline':{'path':str(SOURCE),'sha256':sha(SOURCE)},'native':{'path':str(native),'sha256':sha(native)},'changed_vertices':len(used),'max_delta_m':float(np.linalg.norm(delta,axis=1).max()),'minimum_old_new_face_normal_dot':float(dots.min()),'section_offsets_mm':rows,'mirror_mapping':mapping,'evaluated_neutral_aperture_exact':True,'all_non_skin_owners_and_all_materials_uv_exact':True,'relative_key_errors':errors,'recipe':{'path':str(Path(__file__)),'sha256':sha(__file__)},'limits':['No new chin shortening/setback: unchanged source comparisons do not justify it numerically.','Anterior high malar depth, outer contour/cap and eye boundary are unchanged; lateral sheet retreat is reduced by broad connected support.','Not a global XY inflation or final art PASS. Source silhouette and both-light continuous volume must be reviewed.']},indent=2));print('SHAPE_E_DONE',len(used),float(dots.min()))
