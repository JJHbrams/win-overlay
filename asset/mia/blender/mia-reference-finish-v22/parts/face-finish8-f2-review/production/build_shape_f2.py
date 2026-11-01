"""Connected central+lateral final section curves; F mass retained as anchor.
One bounded correction of F attachment, not another independent row offset.
"""
import bpy,ast,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
from collections import Counter
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'shape-f2';OUT.mkdir(exist_ok=True);SOURCE=ROOT/'shape-f/Mia_FaceFinish8_CentralBuccalF.blend'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();ah=lambda p:hashlib.sha256(np.asarray(p).tobytes()).hexdigest()
tree=ast.parse((ROOT.parent/'finish-6/dependencies/legacy_snapshot_apply_interp.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['snapshots','apply','interp']],type_ignores=[]),'frozen-functions','exec'))
sample=json.loads((ROOT/'shape-f/evaluated-buccal-f-result.json').read_text())['F'];gx=np.array(sample['xs']);gz=np.array(sample['zs']);gy=np.array(sample['depth_y'],float)
heights=np.array([1.490,1.495,1.500,1.505,1.510,1.515,1.520,1.525,1.530])
radii=np.array([.033,.0405,.045,.050,.0545,.058,.061,.064,.066])
exponents=np.array([2.0,2.0,2.0,2.15,2.3,2.4,2.4,2.3,2.2])
anchor_x=.020;anchor_y=np.interp(heights,gz,gy[:,int(np.argmin(abs(gx-anchor_x)))]);front=anchor_y/np.maximum(1-(anchor_x/radii)**exponents,.001)**(1/exponents)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));before=snapshots();skin=bpy.data.objects['MIA_V14_SculptedSkin'];p=np.array([tuple(v.co) for v in skin.data.shape_keys.key_blocks[0].data]);delta=np.zeros_like(p)
faces=np.array([list(f.vertices[:3]) for f in skin.data.polygons]);ec=Counter(tuple(sorted((int(f[i]),int(f[(i+1)%3])))) for f in faces for i in range(3));boundary={i for e,n in ec.items() if n==1 for i in e}
protected={236,242,247,248,249,250,251,252,253}
negative=np.where(p[:,0]<0)[0]
for i in list(protected):protected.add(int(negative[np.argmin(np.linalg.norm(p[negative]-p[i]*[-1,1,1],axis=1))]))
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
targets=[]
for i,(x,y,z) in enumerate(p):
 if i in boundary or i in protected or i>=588 or not(.012<abs(x)<.059 and 1.487<z<1.531 and y>.010):continue
 radius=interp(z,heights,radii);n=interp(z,heights,exponents);depth=interp(z,heights,front)
 if abs(x)>=radius:continue
 guide=depth*(1-(abs(x)/radius)**n)**(1/n)+.0007
 weight=smooth(.012,.022,abs(x))*smooth(.010,.033,y)*smooth(1.487,1.494,z)*(1-smooth(1.520,1.531,z))
 # A small reduction can remove F's local overshoot, but restored central
 # volume is not sacrificed to fix the lateral attachment.
 target=max(guide,y-.0006)
 delta[i,1]=(target-y)*weight
 if abs(delta[i,1])>1e-8:targets.append({'id':i,'guide_y':float(guide),'weight':float(weight),'radius':float(radius),'exponent':float(n)})
def aperture():
 bpy.context.view_layer.update();ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();q=np.array([tuple(v.co) for v in m.vertices]);e=Counter(tuple(sorted((f.vertices[k],f.vertices[(k+1)%len(f.vertices)]))) for f in m.polygons for k in range(len(f.vertices)));ids=sorted({i for edge,c in e.items() if c==1 for i in edge if .010<abs(q[i,0])<.061 and q[i,1]>.035 and 1.525<q[i,2]<1.558});ev.to_mesh_clear();return ids,q[ids]
ids0,eye0=aperture();errors=apply(skin,delta);ids1,eye1=aperture();assert ids0==ids1 and np.array_equal(eye0,eye1)
def normals(q):
 n=np.cross(q[faces[:,1]]-q[faces[:,0]],q[faces[:,2]]-q[faces[:,0]]);return n/np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-20)
dots=np.sum(normals(p)*normals(p+delta),1);assert dots.min()>.6,float(dots.min());after=snapshots()
for name in before:
 for field in before[name]:
  if name==skin.name and field in ['co','keys']:continue
  assert before[name][field]==after[name][field],(name,field)
native=OUT/'Mia_FaceFinish8_ConnectedBuccalF2.blend';assert not native.exists();bpy.ops.wm.save_as_mainfile(filepath=str(native));bpy.ops.wm.open_mainfile(filepath=str(native));assert snapshots()==after
ids=np.where(np.linalg.norm(delta,axis=1)>1e-10)[0];(OUT/'vertex-deltas-from-f.json').write_text(json.dumps([{'owner':'MIA_V14_SculptedSkin','id':int(i),'before':p[i].tolist(),'after':(p[i]+delta[i]).tolist(),'delta':delta[i].tolist()} for i in ids],indent=2))
(OUT/'manifest.json').write_text(json.dumps({'status':'CONNECTED F2 WORKING CANDIDATE / ART UNAPPROVED','baseline':{'path':str(SOURCE),'sha256':sha(SOURCE)},'native':{'path':str(native),'sha256':sha(native)},'section_curve':{'heights':heights.tolist(),'radii':radii.tolist(),'exponents':exponents.tolist(),'anterior_depth':front.tolist(),'central_F_anchor_x':anchor_x,'central_F_anchor_y':anchor_y.tolist(),'interpolation':'Cubic Hermite across height; one convex superellipse per section, continuous central-to-lateral guide. Geometry unchanged outside owned patch.'},'changed_vertices':len(ids),'max_anterior_m':float(delta[:,1].max()),'max_retreat_m':float(-delta[:,1].min()),'minimum_normal_dot':float(dots.min()),'evaluated_neutral_aperture_exact':True,'all_non_skin_owner_uv_material_exact':True,'relative_key_errors':errors,'actual_targets':targets,'recipe':{'path':str(Path(__file__)),'sha256':sha(__file__)},'limits':['Not a spherical cheek/global XY scale. Source-width/chin/outer contour remain fixed.','Central F depth anchors retained; high malar protected. Visual source/continuity judgment still required.']},indent=2));print('F2_DONE',len(ids),float(delta[:,1].max()),float(dots.min()))
