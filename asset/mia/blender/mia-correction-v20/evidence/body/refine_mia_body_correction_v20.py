"""Localized body cage sculpt. Preserves vertex IDs/topology/UV/weights and headcap."""
import bpy, json, hashlib, math, struct, argparse, sys
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[4]
ap=argparse.ArgumentParser();ap.add_argument('--source',default=r'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v17/integrated-v18/Mia_HeadHair_v18.blend');ap.add_argument('--output-dir',default=str(Path(__file__).resolve().parent));args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
SRC=Path(args.source).resolve();OUT=Path(args.output_dir).resolve();OUT.mkdir(parents=True,exist_ok=True);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();source_sha=sha(SRC)
bpy.ops.wm.open_mainfile(filepath=str(SRC));body=bpy.data.objects['MIA_V06_BODY_SKIN'];mesh=body.data

def signatures():
 result={}
 for o in bpy.data.objects:
  if o.type!='MESH':continue
  m=o.data
  co=b''.join(struct.pack('<3f',*v.co) for v in m.vertices)
  uv=b''.join(struct.pack('<2f',*v.uv) for l in m.uv_layers for v in l.data)
  topo=b''.join(struct.pack('<I',i) for p in m.polygons for i in p.vertices)
  keys=b''.join(struct.pack('<3f',*v.co) for k in m.shape_keys.key_blocks for v in k.data) if m.shape_keys else b''
  weights=b''.join(struct.pack('<If',g.group,g.weight) for v in m.vertices for g in v.groups)
  result[o.name]={'co':hashlib.sha256(co).hexdigest(),'uv':hashlib.sha256(uv).hexdigest(),'topology':hashlib.sha256(topo).hexdigest(),'keys':hashlib.sha256(keys).hexdigest(),'weights':hashlib.sha256(weights).hexdigest(),'materials':[s.material.name if s.material else None for s in o.material_slots]}
 return result
before=signatures();packed={i.name:hashlib.sha256(bytes(i.packed_file.data)).hexdigest() for i in bpy.data.images if i.packed_file}
for i in bpy.data.images:
 if i.packed_file:i.use_fake_user=True
p=np.array([list(body.matrix_world@v.co) for v in mesh.vertices]);orig=p.copy();x=np.abs(p[:,0]);y=p[:,1];z=p[:,2]
def bell(v,c,w):return np.exp(-((v-c)/w)**2)
def smoothstep(a,b,v):
 t=np.clip((v-a)/(b-a),0,1);return t*t*(3-2*t)
# Build seam-aware cage graph without changing actual indices or joining geometry.
neighbors=[set() for _ in p]
for e in mesh.edges:
 a,b=e.vertices;neighbors[a].add(b);neighbors[b].add(a)
from mathutils.kdtree import KDTree
kd=KDTree(len(p))
for i,q in enumerate(p):kd.insert(q,i)
kd.balance()
for i,q in enumerate(p):
 coinc=[j for _,j,d in kd.find_range(q,.00002)]
 merged=set().union(*(neighbors[j] for j in coinc))
 for j in coinc:neighbors[j]|=merged
# Broad localized curvature flow: hips/thigh roots and neck/trapezius only.
hipmask=bell(z,1.025,.105)*(1-smoothstep(.17,.23,x))
neckmask=bell(z,1.397,.037)*(1-smoothstep(.12,.19,x))*(1-smoothstep(1.445,1.46,z))
mask=np.maximum(.68*hipmask,.55*neckmask);mask[z>=1.46]=0
for iteration in range(10):
 d=np.zeros_like(p)
 for i,ns in enumerate(neighbors):
  if mask[i]>.005 and ns:
   ids=list(ns);dist=np.linalg.norm(p[ids]-p[i],axis=1);w=1/np.maximum(dist,.002);avg=np.average(p[ids],axis=0,weights=w);d[i]=(avg-p[i])*.34*mask[i]
 # Keep vertical landmarks, hips width and volume mostly intact; smooth abrupt depth/contour changes.
 d[:,2]*=.25;p+=d
# Breast root sculpt: topology-local depth diffusion spans the whole attachment
# (including side wall), with smooth 3D falloff, rather than a hard front-plane cut.
bmask=bell(z,1.294,.073)*(1-smoothstep(.13,.18,x))*(1-smoothstep(-.035,.035,y))
for iteration in range(14):
 d=np.zeros_like(p)
 for i,ns in enumerate(neighbors):
  if bmask[i]>.002 and ns:
   ids=list(ns);w=1/np.maximum(np.linalg.norm(p[ids]-p[i],axis=1),.003)
   avg=np.average(p[ids],axis=0,weights=w);v=avg-p[i]
   # Preserve protruding volume, preferentially fill surrounding concavity.
   v[1]*=1.0 if v[1]<0 else .18
   v[0]*=.15;v[2]*=.12;d[i]=v*.45*bmask[i]
 p+=d
# Broad upper/lateral root support, smoothly wrapping into the chest wall.
p[:,1]-=.004*bell(x,.097,.045)*bell(z,1.326,.034)*(1-smoothstep(-.04,.03,y))
# Break the closed upper/outer oval: carry the lateral root toward the axilla
# across a broad radial zone; leave lower fold and breast apex in place.
outer=bell(x,.105,.036)*bell(z,1.317,.039)*(1-smoothstep(-.018,.035,y))
p[:,0]+=np.sign(orig[:,0])*.009*outer
p[:,1]-=.006*outer*bell(y,-.035,.055)
p[:,2]+=.003*outer
# Round the high iliac turning point without narrowing the full hip/thigh.
hip_side=smoothstep(.075,.125,x)*(1-smoothstep(.17,.22,x))
p[:,0]+=np.sign(orig[:,0])*hip_side*(-.0055*bell(z,1.067,.023)+.0025*bell(z,1.105,.025))
# Restore broad hip volume lost by curvature flow, with a smooth waist-to-thigh envelope.
p[:,0]+=np.sign(orig[:,0])*.0025*bell(z,1.015,.085)*smoothstep(.06,.13,x)*(1-smoothstep(.17,.22,x))
# Support neck base without changing head/neck upper interface.
p[:,0]+=np.sign(orig[:,0])*.002*bell(z,1.405,.023)*bell(x,.043,.035)
p[z>=1.46]=orig[z>=1.46]
inv=body.matrix_world.inverted();deltas=[]
for i,v in enumerate(mesh.vertices):
 d=p[i]-orig[i]
 if np.linalg.norm(d)>1e-8:
  local=inv.to_3x3()@Vector(d);v.co+=local;deltas.append({'vertex':i,'delta_local':list(local),'delta_world':d.tolist(),'source_world':orig[i].tolist()})
mesh.update();after=signatures();assert all(before[k]==after[k] for k in before if k!=body.name)
assert all(before[body.name][k]==after[body.name][k] for k in ['uv','topology','keys','weights','materials'])
assert np.array_equal(p[z>=1.46],orig[z>=1.46]);body['V20_sculpt']='Localized chest root fill, hip/thigh curvature flow, neckbase continuation; no topology/UV/weights change.'
DST=OUT/'Mia_BodyCorrection_v20.blend';bpy.ops.wm.save_as_mainfile(filepath=str(DST));bpy.ops.wm.open_mainfile(filepath=str(DST));body=bpy.data.objects['MIA_V06_BODY_SKIN'];assert signatures()==after;assert packed=={i.name:hashlib.sha256(bytes(i.packed_file.data)).hexdigest() for i in bpy.data.images if i.packed_file};assert sha(SRC)==source_sha
(OUT/'vertex-delta.json').write_text(json.dumps({'object':body.name,'source_sha256':source_sha,'deltas':deltas},indent=2))
(OUT/'manifest.json').write_text(json.dumps({'source':str(SRC),'source_sha256':source_sha,'native_sha256':sha(DST),'changed_vertices':len(deltas),'max_delta_m':max(np.linalg.norm(v['delta_world']) for v in deltas),'protected_z_min':1.46,'protected_vertices':int(sum(z>=1.46)),'other_meshes_exact':len(before)-1,'packed_images_exact':len(packed),'before':before[body.name],'after':after[body.name],'art_status':'Requires actual four-view review; no automatic PASS'},indent=2));print('NATIVE',sha(DST),'DELTA',len(deltas))
