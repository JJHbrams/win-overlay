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
assert source_sha=='aa02b736452bc876abf6f81a09b94bad71eb15c5ced35834b6fde17b90f8b5a6'
before=signatures();packed={i.name:hashlib.sha256(bytes(i.packed_file.data)).hexdigest() for i in bpy.data.images if i.packed_file}

# Explicitly preserve orphan material/image datablocks during native save.
for mat in bpy.data.materials: mat.use_fake_user=True
for im in bpy.data.images: im.use_fake_user=True
p=np.array([list(body.matrix_world@v.co) for v in mesh.vertices]);orig=p.copy();x=np.abs(p[:,0]);y=p[:,1];z=p[:,2]
def bell(v,c,w):return np.exp(-((v-c)/w)**2)
def smoothstep(a,b,v):
 t=np.clip((v-a)/(b-a),0,1);return t*t*(3-2*t)
# Explicit anatomical sector/spoke cage mapping, verified from actual edges.
# A is the preserved principal volume row; B/C/D are returning lobe rows;
# E/F are actual chest bridge rows. Rows are repositioned along sculpted
# cubic cross sections, not displaced by spatial Gaussian fields.
A=[2003,2002,2062,2063,2064,2065,2069,2070,2071,2072,2073,2074,2075,2076,2077,2078]
B=[2004,2061,2060,2059,2058,2057,2056,2055,2054,2053,2052,2051,2050,2049,2048,2005]
C=[2018,2022,2026,2031,2035,2036,2033,2028,2024,2020,2016,2013,2011,2009,2007,2006]
D=[2019,2023,2027,2030,2034,2037,2032,2029,2025,2021,2017,2014,2012,2010,2008,2015]
E=[2038,283,282,281,280,279,278,2047,2046,2045,2044,2043,2042,2041,2040,2039]
F=[284,52,50,47,44,58,89,88,93,95,97,99,185,184,291,289]
INNER=[2084,2000,2001,2066,2067,2068,2089,2088,2087,2086,2085,2083,2081,2080,2079,2082]
G={0:286,7:91,8:94,9:96,10:96,11:98,12:102,13:190,14:292,15:290}
NEXT={0:288,13:191,14:293,15:288}
# Specific underfold sectors carry onto the lower rib surface; lateral sectors
# wrap to an existing sidewall endpoint. Central/apical row remains untouched.
long_sectors={0,13,14,15}
strength={0:.75,7:.55,8:1.,9:1.,10:1.,11:1.,12:1.,13:1.,14:1.,15:1.}
adj=[set() for _ in p]
for edge in mesh.edges:
 i,j=edge.vertices;adj[i].add(j);adj[j].add(i)
records=[];assigned={}
def bez(q0,q1,q2,q3,t):return (1-t)**3*q0+3*(1-t)**2*t*q1+3*(1-t)*t*t*q2+t**3*q3
for k,w in strength.items():
 chain=[A[k],B[k],C[k],D[k],E[k],F[k]]
 assert all(j in adj[i] for i,j in zip(chain,chain[1:])),(k,chain)
 islong=k in long_sectors
 if islong:assert G[k] in adj[F[k]]
 q0=orig[A[k]].copy();q3=orig[chain[-1]].copy()
 if islong:
  q3[2]-={0:.002,13:.004,14:.004,15:.003}[k]
  q3[1]-=.0015
  assigned[F[k]]=orig[F[k]]+w*(q3-orig[F[k]])
 span=np.linalg.norm(q3-q0)
 incoming=orig[A[k]]-orig[INNER[k]];incoming/=np.linalg.norm(incoming)
 after=orig[G[k]]-q3
 after/=np.linalg.norm(after)
 q1=q0+incoming*span*.30
 q2=q3-after*span*.28
 # Explicit row sampling evens the compressed attachment band. The inferior
 # section has a rounded returning plane, not a duplicated circular rim.
 ts=[.19,.40,.62,.82]
 row_records=[]
 for i,t in zip(chain[1:-1],ts):
  target=bez(q0,q1,q2,q3,t);new=orig[i]+w*(target-orig[i]);assigned[i]=new
  row_records.append({'vertex':i,'t':t,'source_world':orig[i].tolist(),'target_world':new.tolist()})
 records.append({'sector':k,'chain_vertex_ids':chain,'preserved_start':A[k],'end_vertex':chain[-1],'end_repositioned':islong,'end_target_world':q3.tolist(),'inner_tangent_vertex':INNER[k],'strength':w,'bezier_controls':[q0.tolist(),q1.tolist(),q2.tolist(),q3.tolist()],'rows':row_records})
# Mirror each edited cage ID using observed source world correspondence.
# Preserve existing slight asymmetry by reflecting the delta, not coordinates.
mirror=[]
for i,new in assigned.items():
 p[i]=new;goal=orig[i]*np.array([-1,1,1]);dist=np.linalg.norm(orig-goal,axis=1);j=int(np.argmin(dist))
 assert dist[j]<.002,(i,j,float(dist[j]))
 delta=(new-orig[i])*np.array([-1,1,1]);p[j]=orig[j]+delta
 mirror.append({'right_vertex':i,'left_vertex':j,'source_mirror_distance_m':float(dist[j])})
for record in records:
 mirrored=[]
 for i in record['chain_vertex_ids']:
  goal=orig[i]*np.array([-1,1,1]);mirrored.append(int(np.argmin(np.linalg.norm(orig-goal,axis=1))))
 assert all(j in adj[i] for i,j in zip(mirrored,mirrored[1:])),(record['sector'],mirrored)
 record['left_chain_vertex_ids']=mirrored
(OUT/'control-loop-map.json').write_text(json.dumps({'source_sha256':source_sha,'all_ring_ids':{'A_volume':A,'B_return':B,'C_return':C,'D_attachment':D,'E_chest_bridge':E,'F_chest':F},'sectors':records,'mirror_mapping':mirror,'scope':'Preserved topology, selected actual loop-row redistribution; no generic smoothing or Gaussian offset'},indent=2))
p[z>=1.46]=orig[z>=1.46]
p[np.linalg.norm(p-orig,axis=1)<1e-7]=orig[np.linalg.norm(p-orig,axis=1)<1e-7]
inv=body.matrix_world.inverted();deltas=[]
for i,v in enumerate(mesh.vertices):
 d=p[i]-orig[i]
 if np.linalg.norm(d)>1e-8:
  local=inv.to_3x3()@Vector(d);v.co+=local;deltas.append({'vertex':i,'delta_local':list(local),'delta_world':d.tolist(),'source_world':orig[i].tolist()})
mesh.update();after=signatures();assert all(before[k]==after[k] for k in before if k!=body.name)
assert all(before[body.name][k]==after[body.name][k] for k in ['uv','topology','keys','weights','materials'])
assert np.array_equal(p[z>=1.46],orig[z>=1.46]);body['V21_form_sculpt']='Explicit lower/lateral breast loop-row redistribution against observed ribcage anchors; principal volume row preserved.'
DST=OUT/'Mia_BodyForm_v21_candidate2.blend';bpy.ops.wm.save_as_mainfile(filepath=str(DST));bpy.ops.wm.open_mainfile(filepath=str(DST));body=bpy.data.objects['MIA_V06_BODY_SKIN'];assert signatures()==after;assert packed=={i.name:hashlib.sha256(bytes(i.packed_file.data)).hexdigest() for i in bpy.data.images if i.packed_file};assert sha(SRC)==source_sha
(OUT/'vertex-delta.json').write_text(json.dumps({'object':body.name,'source_sha256':source_sha,'deltas':deltas},indent=2))
(OUT/'manifest.json').write_text(json.dumps({'source':str(SRC),'source_sha256':source_sha,'native_sha256':sha(DST),'changed_vertices':len(deltas),'max_delta_m':max(np.linalg.norm(v['delta_world']) for v in deltas),'protected_z_min':1.46,'protected_vertices':int(sum(z>=1.46)),'other_meshes_exact':len(before)-1,'packed_images_exact':len(packed),'all_before':before,'all_after':after,'before':before[body.name],'after':after[body.name],'art_status':'Requires actual four-view review; no automatic PASS'},indent=2));print('NATIVE',sha(DST),'DELTA',len(deltas))
