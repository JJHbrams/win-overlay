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
# Primary form rebuild: explicit 16-spoke control surface, whole mass included.
# Not an offset field. No A/apex lock. Parameterized artist cross-sections
# distribute every existing breast row between a lower apex and chest roots.
A=[2003,2002,2062,2063,2064,2065,2069,2070,2071,2072,2073,2074,2075,2076,2077,2078]
B=[2004,2061,2060,2059,2058,2057,2056,2055,2054,2053,2052,2051,2050,2049,2048,2005]
C=[2018,2022,2026,2031,2035,2036,2033,2028,2024,2020,2016,2013,2011,2009,2007,2006]
D=[2019,2023,2027,2030,2034,2037,2032,2029,2025,2021,2017,2014,2012,2010,2008,2015]
E=[2038,283,282,281,280,279,278,2047,2046,2045,2044,2043,2042,2041,2040,2039]
F=[284,52,50,47,44,58,57,89,93,95,97,99,185,184,291,289]
R2=[2084,2000,2001,2066,2067,2068,2089,2088,2087,2086,2085,2083,2081,2080,2079,2082]
R1=[1991,1992,1993,1994,1995,1996,1997,1998,1999,1984,1985,1986,1987,1988,1989,1990]
G=[286,285,49,45,43,42,56,77,94,96,96,98,102,190,292,290]
rows=[R1,R2,A,B,C,D,E,F];ts=[.24,.40,.56,.70,.81,.90,.96,1.0]
adj=[set() for _ in p]
for edge in mesh.edges:
 i,j=edge.vertices;adj[i].add(j);adj[j].add(i)
source_center=orig[1973].copy();center=source_center.copy();center[1]=-.139;center[2]=1.272
root_deltas={4:(0,.003,.005),5:(0,.005,.007),6:(0,.003,.006),7:(0,.004,.007),8:(0,-.002,.006),9:(.003,-.004,0),10:(.003,-.004,0),11:(.002,-.003,0),12:(.001,-.002,0)}
assigned={};records=[]
def hermite(v0,v1,d0,d1,t):
 return (2*t**3-3*t*t+1)*v0+(t**3-2*t*t+t)*d0+(-2*t**3+3*t*t)*v1+(t**3-t*t)*d1
for k in range(16):
 chain=[r[k] for r in rows]
 assert all(j in adj[i] for i,j in zip(chain,chain[1:])),(k,chain)
 root=orig[F[k]]+np.array(root_deltas.get(k,(0,0,0)))
 dz=root[2]-center[2]
 # Centre has a sloped tangent plane, rather than an isolated flat disc.
 # Upper spoke rises in depth gently over a longer vertical distance.
 dx0=(orig[R1[k],0]-center[0])/.24
 start_dy=.15*dx0
 nextpoint=orig[G[k]]
 span=np.linalg.norm(root-center);edge=max(np.linalg.norm(nextpoint-root),.008)
 end_dy=(nextpoint[1]-root[1])*span/edge*.72
 end_dy=float(np.clip(end_dy,-.025,.095))
 rec=[]
 for ids,t in zip(rows,ts):
  i=ids[k];target=orig[i].copy()
  target[0]+=root_deltas.get(k,(0,0,0))[0]*t*t
  target[2]=center[2]+dz*t
  upper_y=hermite(center[1],root[1],start_dy,end_dy,t)
  lower_fraction=1-math.sqrt(max(0,1-t*t))
  lower_y=center[1]+(root[1]-center[1])*lower_fraction
  lower_strength={0:.85,1:.30,11:.35,12:.80,13:1.,14:1.,15:1.}.get(k,0.)
  target[1]=(1-lower_strength)*upper_y+lower_strength*lower_y
  assigned[i]=target
  rec.append({'vertex':i,'row_t':t,'source_world':orig[i].tolist(),'target_world':target.tolist()})
 records.append({'sector':k,'right_chain_vertex_ids':chain,'chest_continuation_vertex':G[k],'root_target_world':root.tolist(),'depth_curve_hermite':[float(center[1]),float(root[1]),float(start_dy),float(end_dy)],'rows':rec})
# Rebuild the dense central patch continuously inside its observed R1 border.
# The patch uses the same shifted center/tangent plane, not inherited pad detail.
angles=np.array([math.atan2((orig[i,2]-source_center[2])/.020,(orig[i,0]-source_center[0])/.016) for i in R1]);order=np.argsort(angles);angles=angles[order]
angles_ext=np.r_[angles[-1]-2*math.pi,angles,angles[0]+2*math.pi];indices=[int(order[-1])]+[int(k) for k in order]+[int(order[0])]
for i in range(1951,1984):
 q=orig[i];theta=math.atan2((q[2]-source_center[2])/.020,(q[0]-source_center[0])/.016)
 n=int(np.searchsorted(angles_ext,theta)-1);u=(theta-angles_ext[n])/(angles_ext[n+1]-angles_ext[n])
 b0=orig[R1[indices[n]]]*(1-u)+orig[R1[indices[n+1]]]*u
 b1=assigned[R1[indices[n]]]*(1-u)+assigned[R1[indices[n+1]]]*u
 r=np.linalg.norm((q-source_center)[[0,2]])/max(np.linalg.norm((b0-source_center)[[0,2]]),1e-8);r=min(r,1.)
 target=center+r*(b1-center)
 plane=.15*(target[0]-center[0])
 boundary_plane=.15*(b1[0]-center[0])
 target[1]=center[1]+plane+r*r*(b1[1]-center[1]-boundary_plane)
 assigned[i]=target
# Apply explicit IDs and reflect source deltas to actual mirrored graph mates.
# Infer actual symmetry plane from widely spaced ring correspondences.
coarse_pairs=[]
for i in R1:
 j=int(np.argmin(np.linalg.norm(orig-orig[i]*[-1,1,1],axis=1)))
 coarse_pairs.append((i,j))
plane_x=float(np.median([(orig[i,0]+orig[j,0])/2 for i,j in coarse_pairs]))
def mirror_id(i):
 goal=orig[i].copy();goal[0]=2*plane_x-goal[0]
 return int(np.argmin(np.linalg.norm(orig-goal,axis=1)))
mirrored_ids=[mirror_id(i) for i in assigned]
assert len(set(mirrored_ids))==len(mirrored_ids),'Mirror mapping must be bijective'
for i in assigned:
 for j in adj[i]&set(assigned):
  assert mirror_id(j) in adj[mirror_id(i)],('Mirror edge mismatch',i,j)
mirror=[]
for i,new in assigned.items():
 p[i]=new;goal=orig[i].copy();goal[0]=2*plane_x-goal[0];dist=np.linalg.norm(orig-goal,axis=1);j=mirror_id(i)
 assert dist[j]<.002,(i,j,float(dist[j]))
 delta=(new-orig[i])*np.array([-1,1,1]);p[j]=orig[j]+delta
 mirror.append({'right_vertex':i,'left_vertex':j,'source_mirror_distance_m':float(dist[j])})
for rec in records:
 ids=[mirror_id(i) for i in rec['right_chain_vertex_ids']]
 assert all(j in adj[i] for i,j in zip(ids,ids[1:])),ids
 rec['left_chain_vertex_ids']=ids
(OUT/'primary-control-map.json').write_text(json.dumps({'source_sha256':source_sha,'mirror_plane_x_m':plane_x,'mirror_bijective':True,'central_and_all_owned_edges_verified':True,'lower_curve':'quarter-ellipse depth with horizontal apex tangent; angular transition only lower sectors','source_center_world':source_center.tolist(),'new_center_world':center.tolist(),'row_ids':{'R1':R1,'R2':R2,'A':A,'B':B,'C':C,'D':D,'E':E,'F':F},'sectors':records,'center_patch_ids':list(range(1951,1984)),'mirrors':mirror,'intent':'Whole primary form: long upper transition, lower weighted rounded mass, side root wrapping to ribcage; no clothing-switch functionality'},indent=2))
p[z>=1.46]=orig[z>=1.46]
p[np.linalg.norm(p-orig,axis=1)<1e-7]=orig[np.linalg.norm(p-orig,axis=1)<1e-7]
inv=body.matrix_world.inverted();deltas=[]
for i,v in enumerate(mesh.vertices):
 d=p[i]-orig[i]
 if np.linalg.norm(d)>1e-8:
  local=inv.to_3x3()@Vector(d);v.co+=local;deltas.append({'vertex':i,'delta_local':list(local),'delta_world':d.tolist(),'source_world':orig[i].tolist()})
mesh.update();after=signatures();assert all(before[k]==after[k] for k in before if k!=body.name)
assert all(before[body.name][k]==after[body.name][k] for k in ['uv','topology','keys','weights','materials'])
assert np.array_equal(p[z>=1.46],orig[z>=1.46]);body['V21_primary_sculpt']='Whole breast and upper chest primary surface rebuilt on explicit spoke rows; no apex lock; anatomical WIP.'
DST=OUT/'Mia_BodyPrimary_v21_corrected.blend';bpy.ops.wm.save_as_mainfile(filepath=str(DST));bpy.ops.wm.open_mainfile(filepath=str(DST));body=bpy.data.objects['MIA_V06_BODY_SKIN'];assert signatures()==after;assert packed=={i.name:hashlib.sha256(bytes(i.packed_file.data)).hexdigest() for i in bpy.data.images if i.packed_file};assert sha(SRC)==source_sha
(OUT/'vertex-delta.json').write_text(json.dumps({'object':body.name,'source_sha256':source_sha,'deltas':deltas},indent=2))
(OUT/'manifest.json').write_text(json.dumps({'source':str(SRC),'source_sha256':source_sha,'native_sha256':sha(DST),'changed_vertices':len(deltas),'max_delta_m':max(np.linalg.norm(v['delta_world']) for v in deltas),'protected_z_min':1.46,'protected_vertices':int(sum(z>=1.46)),'other_meshes_exact':len(before)-1,'packed_images_exact':len(packed),'all_before':before,'all_after':after,'before':before[body.name],'after':after[body.name],'art_status':'Requires actual four-view review; no automatic PASS'},indent=2));print('NATIVE',sha(DST),'DELTA',len(deltas))
