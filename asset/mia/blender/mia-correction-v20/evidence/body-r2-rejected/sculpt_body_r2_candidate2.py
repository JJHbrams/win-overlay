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
# R2 lower breast attachment: extend the inframammary root into the
# anterior ribs, preserving the apex. The 3D support extends below/outside
# the lobe instead of shrinking its projection through global smoothing.
front=1-smoothstep(-.045,.015,y)
root=bell(x,.065,.047)*bell(z,1.237,.047)*front
p[:,1]-=.024*root*smoothstep(-.124,-.072,y)
# Broaden the inferolateral contact. A soft local shoulder under the lobe
# distributes the return into chest wall across the vertical/radial section.
side=bell(x,.087,.030)*bell(z,1.246,.040)*bell(y,-.065,.040)
p[:,0]+=np.sign(orig[:,0])*.0045*side
p[:,1]-=.0090*side
# Inferior breast rim is eased toward the rib support, leaving apex z~1.285.
p[:,2]-=.0008*bell(x,.062,.040)*bell(z,1.241,.022)*bell(y,-.109,.022)
# Pelvic turning point: coordinated depth+width redistribution across
# flank/iliac/upper-thigh rather than changing one frontal outline alone.
flank=smoothstep(.065,.12,x)*(1-smoothstep(.17,.21,x))
p[:,0]+=np.sign(orig[:,0])*flank*(-.0035*bell(z,1.045,.028)+.0028*bell(z,1.005,.050)+.0020*bell(z,1.092,.030))
# Fill anterolateral hollow at femoral origin and blend it down the thigh.
p[:,1]-=.0038*bell(x,.097,.048)*bell(z,.995,.066)*bell(y,-.053,.038)
p[:,1]+=.004*bell(x,.055,.050)*bell(z,1.045,.031)*bell(y,-.083,.030)
p[:,1]-=.0025*bell(x,.060,.050)*bell(z,1.090,.040)*bell(y,-.083,.030)
# Softly round central inguinal transition through anterior support;
# do not introduce an illustrated underwear V or close the leg gap.
p[:,1]-=.0025*bell(x,.036,.026)*bell(z,.987,.043)*bell(y,-.058,.029)
# Tangential local relaxation distributes the section edits in sparse cage
# while retaining original vertical landmarks and explicit volume support.
mask=bell(z,1.025,.074)*smoothstep(.045,.10,x)*(1-smoothstep(.17,.21,x))
for iteration in range(6):
 d=np.zeros_like(p)
 for i,ns in enumerate(neighbors):
  if mask[i]>.005 and ns:
   ids=list(ns); w=1/np.maximum(np.linalg.norm(p[ids]-p[i],axis=1),.003)
   v=np.average(p[ids],axis=0,weights=w)-p[i]
   d[i]=v*.20*mask[i]
 d[:,2]*=.15
 p+=d
p[z>=1.46]=orig[z>=1.46]
p[np.linalg.norm(p-orig,axis=1)<1e-7]=orig[np.linalg.norm(p-orig,axis=1)<1e-7]
inv=body.matrix_world.inverted();deltas=[]
for i,v in enumerate(mesh.vertices):
 d=p[i]-orig[i]
 if np.linalg.norm(d)>1e-8:
  local=inv.to_3x3()@Vector(d);v.co+=local;deltas.append({'vertex':i,'delta_local':list(local),'delta_world':d.tolist(),'source_world':orig[i].tolist()})
mesh.update();after=signatures();assert all(before[k]==after[k] for k in before if k!=body.name)
assert all(before[body.name][k]==after[body.name][k] for k in ['uv','topology','keys','weights','materials'])
assert np.array_equal(p[z>=1.46],orig[z>=1.46]);body['V20_R2_sculpt']='Lower breast rib support and coordinated pelvic/thigh surface redistribution; volume/apex retained.'
DST=OUT/'Mia_BodySurface_v20_r2_candidate2.blend';bpy.ops.wm.save_as_mainfile(filepath=str(DST));bpy.ops.wm.open_mainfile(filepath=str(DST));body=bpy.data.objects['MIA_V06_BODY_SKIN'];assert signatures()==after;assert packed=={i.name:hashlib.sha256(bytes(i.packed_file.data)).hexdigest() for i in bpy.data.images if i.packed_file};assert sha(SRC)==source_sha
(OUT/'vertex-delta.json').write_text(json.dumps({'object':body.name,'source_sha256':source_sha,'deltas':deltas},indent=2))
(OUT/'manifest.json').write_text(json.dumps({'source':str(SRC),'source_sha256':source_sha,'native_sha256':sha(DST),'changed_vertices':len(deltas),'max_delta_m':max(np.linalg.norm(v['delta_world']) for v in deltas),'protected_z_min':1.46,'protected_vertices':int(sum(z>=1.46)),'other_meshes_exact':len(before)-1,'packed_images_exact':len(packed),'all_before':before,'all_after':after,'before':before[body.name],'after':after[body.name],'art_status':'Requires actual four-view review; no automatic PASS'},indent=2));print('NATIVE',sha(DST),'DELTA',len(deltas))
