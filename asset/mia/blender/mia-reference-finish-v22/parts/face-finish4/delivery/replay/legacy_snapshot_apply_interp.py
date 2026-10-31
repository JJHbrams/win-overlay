"""Anatomical rim-to-cheek guide on actual Basis; no width or cranial scaling."""
import bpy,sys,math,json,hashlib,argparse,ast
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=Path(r'C:/Users/antio/.codex/worktrees/mia-final-face-v12/win-overlay');sys.path.insert(0,str(ROOT/'tools/mia/blender'));import refine_mia_head_v06 as h
ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--output-dir',required=True);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);SOURCE=Path(a.source).resolve();OUT=Path(a.output_dir).resolve();OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();ah=lambda p:hashlib.sha256(np.asarray(p).tobytes()).hexdigest()
def snapshots():
 d={}
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  m=o.data;d[o.name]={'co':ah([tuple(v.co) for v in m.vertices]),'keys':{k.name:ah([tuple(v.co) for v in k.data]) for k in m.shape_keys.key_blocks} if m.shape_keys else {},'uv':{l.name:ah([tuple(v.uv) for v in l.data]) for l in m.uv_layers},'topology':ah([v for p in m.polygons for v in [len(p.vertices),*p.vertices]]),'weights':ah([(v.index,g.group,g.weight) for v in m.vertices for g in v.groups]),'materials':[s.material.name if s.material else None for s in o.material_slots],'matrix':str(o.matrix_world),'modifiers':[(m.name,m.type,m.show_render) for m in o.modifiers]}
 return d
def apply(o,ds):
 old={k.name:np.array([tuple(v.co) for v in k.data]) for k in o.data.shape_keys.key_blocks} if o.data.shape_keys else {}
 for k in o.data.shape_keys.key_blocks if o.data.shape_keys else []:
  for v,d in zip(k.data,ds):v.co+=Vector(d)
 for v,d in zip(o.data.vertices,ds):v.co+=Vector(d)
 o.data.update();error={}
 for k in o.data.shape_keys.key_blocks if o.data.shape_keys else []:
  d=np.array([tuple(v.co) for v in k.data])-np.array([tuple(v.co) for v in k.relative_key.data]);error[k.name]=float(np.max(np.abs(d-(old[k.name]-old[k.relative_key.name]))))
 return error
def interp(t,x,y,zero_ends=False):
 if t<=x[0]:return y[0]
 if t>=x[-1]:return y[-1]
 x=np.array(x);y=np.array(y);slopes=np.zeros_like(y);slopes[1:-1]=(y[2:]-y[:-2])/(x[2:]-x[:-2]);slopes[0]=0 if zero_ends else (y[1]-y[0])/(x[1]-x[0]);slopes[-1]=0 if zero_ends else (y[-1]-y[-2])/(x[-1]-x[-2]);k=int(np.searchsorted(x,t)-1);span=x[k+1]-x[k];u=(t-x[k])/span
 return (2*u**3-3*u*u+1)*y[k]+(u**3-2*u*u+u)*span*slopes[k]+(-2*u**3+3*u*u)*y[k+1]+(u**3-u*u)*span*slopes[k+1]
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;skin=bpy.data.objects['MIA_V14_SculptedSkin'];eyes=bpy.data.objects['MIA_V14_EyeSurface'];assert not skin.get('v21_orbital_guide')
source_sha=sha(SOURCE);before=snapshots();packed={im.name:hashlib.sha256(im.packed_file.data).hexdigest() for im in bpy.data.images if im.packed_file}
for im in bpy.data.images:
 if im.packed_file:im.use_fake_user=True
bpy.context.view_layer.update();ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();points=np.array([tuple(v.co) for v in me.vertices]);faces=[list(p.vertices) for p in me.polygons];bvh=BVHTree.FromPolygons([Vector(p) for p in points],faces);uses={}
for f in faces:
 for i,j in zip(f,f[1:]+f[:1]):e=tuple(sorted((i,j)));uses[e]=uses.get(e,0)+1
adj={}
for (i,j),n in uses.items():
 if n==1:adj.setdefault(i,set()).add(j);adj.setdefault(j,set()).add(i)
seen=set();loops=[]
for start in adj:
 if start in seen:continue
 stack=[start];ids=[];seen.add(start)
 while stack:
  i=stack.pop();ids.append(i)
  for j in adj[i]:
   if j not in seen:seen.add(j);stack.append(j)
 c=points[ids].mean(0)
 if .018<abs(c[0])<.060 and 1.53<c[2]<1.55 and c[1]>.03:loops.append(points[ids])
ev.to_mesh_clear();assert len(loops)==2
guides={};guide_reports=[]
for loop in loops:
 sign=1 if loop[:,0].mean()>0 else -1;outer=max(loop,key=lambda p:abs(p[0]));inner=min(loop,key=lambda p:abs(p[0]));lower=[]
 for p in loop:
  t=(p[0]-inner[0])/(outer[0]-inner[0]);line=inner[2]+t*(outer[2]-inner[2])
  if p[2]<=line:lower.append(p)
 lower=np.array(sorted(lower,key=lambda p:abs(p[0])));p0=min(lower,key=lambda p:abs(abs(p[0])-(abs(outer[0])-.004)))
 x1=sign*(abs(outer[0])-.007);z1=p0[2]-.016;x2=sign*(abs(outer[0])-.018);z2=p0[2]-.040
 p1=np.array(bvh.ray_cast(Vector((x1,.3,z1)),Vector((0,-1,0)))[0]);p2=np.array(bvh.ray_cast(Vector((x2,.3,z2)),Vector((0,-1,0)))[0]);anchors=np.array([p0,p1,p2]);ts=np.linspace(0,1,65)
 path=np.array([[interp(t,[0,.42,1],abs(anchors[:,0])),interp(t,[0,.42,1],anchors[:,2])] for t in ts]);guides[sign]={'outer':outer,'lower':lower,'path':path,'ts':ts,'anchors':anchors};guide_reports.append({'side':sign,'outer':outer.tolist(),'rim_apex_lowercheek':anchors.tolist(),'path_xz':path.tolist()})
def field(p):
 x,y,z=map(float,p);g=guides[1 if x>0 else -1];q=np.array([abs(x),z]);path=g['path'];best=None
 for i,(aa,bb) in enumerate(zip(path,path[1:])):
  ab=bb-aa;t=np.clip(np.dot(q-aa,ab)/np.dot(ab,ab),0,1);pt=aa+t*ab;dist=np.linalg.norm(q-pt)
  if best is None or dist<best[0]:best=(dist,i,t,pt,ab/np.linalg.norm(ab))
 dist,i,t,pt,tangent=best;u=np.dot(q-pt,np.array([-tangent[1],tangent[0]]));s=(i+t)/64
 before_start=np.dot(q-path[0],(path[1]-path[0])/np.linalg.norm(path[1]-path[0]));w=h._smooth((before_start+.006)/.006)*h._smooth((u+.018)/.014)*(1-h._smooth((u-.012)/.016))*h._smooth((y-.008)/.020)
 depth=interp(s,[0,.15,.45,.73,1],[-.0004,.0012,.0030,.0024,0],True)
 depth*=float(np.interp(u,[-.018,-.006,0,.010,.028],[.15,.55,1,1.5,1.0]))
 if depth>0:
  lower=g['lower'];cap=float(np.interp(abs(x),abs(lower[:,0]),lower[:,1]))-.0003;room=max(0,cap-y)
  depth=(room*math.tanh(depth/max(room,1e-10))*h._smooth(room/.001)) if room>0 else 0
 return np.array([0,depth*w,0])
base=np.array([tuple(v.co) for v in skin.data.shape_keys.key_blocks[0].data]);ds=np.array([field(p) for p in base]);errors={skin.name:apply(skin,ds)};skin['v21_orbital_guide']=True;changed={skin.name}
# Keep the existing iris shape; retreat its complete curved carrier very slightly.
toskin=skin.matrix_world.inverted()@eyes.matrix_world;back=toskin.inverted().to_3x3();iris={i for p in eyes.data.polygons if p.material_index==5 for i in p.vertices};ed=[]
for v in eyes.data.vertices:
 q=toskin@v.co;d=np.array([0,-.00035,0]) if v.index in iris else field(q);ed.append(back@Vector(d))
errors[eyes.name]=apply(eyes,ed);changed.add(eyes.name)
bpy.context.view_layer.update();ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();surface=BVHTree.FromPolygons([v.co for v in me.vertices],[list(p.vertices) for p in me.polygons]);ev.to_mesh_clear()
for o in scene.objects:
 if o.type!='MESH' or o.hide_render or not any(t in o.name for t in ['UpperLash','OuterWing']):continue
 toskin=skin.matrix_world.inverted()@o.matrix_world;back=toskin.inverted();dd=[]
 for v in o.data.shape_keys.key_blocks[0].data if o.data.shape_keys else o.data.vertices:
  q=toskin@v.co;q+=Vector(field(q));hit=surface.ray_cast(Vector((q.x,.3,q.z)),Vector((0,-1,0)))[0]
  if hit is not None:q.y=hit.y+.00045
  dd.append(back@q-v.co)
 errors[o.name]=apply(o,dd);changed.add(o.name)
after=snapshots()
for n in before:
 if n not in changed:assert before[n]==after[n],n
 else:
  for f in ['uv','topology','weights','materials','matrix','modifiers']:assert before[n][f]==after[n][f],(n,f)
assert max(v for e in errors.values() for v in e.values())<2e-7
native=OUT/'Mia_OrbitalGuide_v21.blend';assert not native.exists();bpy.ops.wm.save_as_mainfile(filepath=str(native));native_sha=sha(native)
bpy.ops.wm.open_mainfile(filepath=str(native));assert snapshots()==after;assert {im.name:hashlib.sha256(im.packed_file.data).hexdigest() for im in bpy.data.images if im.packed_file}==packed
report={'source':str(SOURCE),'source_sha256':source_sha,'native':str(native),'native_sha256':native_sha,'recipe_sha256':sha(__file__),'coordinate_definition':'Actual neutral Basis fields; landmarks from evaluated lower orbital rim and surface ray sampled cheek apex/lower cheek; same local offsets to all keys and cache.','guides':guide_reports,'before':before,'after':after,'changed_owners':sorted(changed),'key_relative_errors':errors,'max_skin_delta_m':float(np.linalg.norm(ds,axis=1).max()),'all59_packed_exact':len(packed)==59,'packed_images':packed,'body_cap_hair_unchanged':True,'no_x_or_z_skin_delta':bool(np.all(ds[:,[0,2]]==0)),'status':'Candidate pending actual curve/eye/blink review; no art pass.'}
(OUT/'manifest.json').write_text(json.dumps(report,indent=2));(OUT/'vertex-deltas.json').write_text(json.dumps([{'vertex':i,'delta_local_m':d.tolist()} for i,d in enumerate(ds) if np.linalg.norm(d)>1e-8],indent=2));(OUT/'exact-recipe.py').write_bytes(Path(__file__).read_bytes())
# Read-only previews from the saved native, with the established fixed neutral rig.
helper=ROOT/'asset/mia/blender/mia-face-correction-v20/verify_v20.py';tree=ast.parse(helper.read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),str(helper),'exec'))
s=load(native)
for label,yaw in [('front',0),('left45',45),('profile90',90)]:render(s,'after_beauty_'+label,yaw)
neutral(s)
for label,yaw in [('front',0),('yaw20',20),('left45',45),('right45',-45),('profile90',90)]:render(s,'after_neutral_'+label,yaw)
s=load(native);k=next(k for k in bpy.data.objects['MIA_V14_SculptedSkin'].data.shape_keys.key_blocks if k.name.endswith('Fcl_EYE_Close'));k.value=.5;bpy.context.view_layer.update();render(s,'blink_half_front',0)
assert sha(native)==native_sha and sha(SOURCE)==source_sha;print('ORBITAL_GUIDE_DONE',native_sha)
