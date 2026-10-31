import bpy,sys,argparse,json,hashlib,math,bmesh
from pathlib import Path
from mathutils import Vector
import numpy as np
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools/mia/blender'));import refine_mia_head_v06 as h
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--output-dir',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);SRC=Path(a.source).resolve();OUT=Path(a.output_dir).resolve();OUT.mkdir(parents=True,exist_ok=True);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();source_sha=sha(SRC)
bpy.ops.wm.open_mainfile(filepath=str(SRC));hair=bpy.data.objects['MIA_V17_PIXAL_DetailedHair'];me=hair.data
scene=bpy.context.scene;cam=scene.camera;scene.render.resolution_x=scene.render.resolution_y=1000;cam.data.ortho_scale=.64
def views(prefix):
 for name,loc in [('front',(0,-2,1.46)),('profile',(2,0,1.46)),('back',(0,2,1.46))]:
  h._aim(cam,loc,(0,0,1.46));scene.render.filepath=str(OUT/(prefix+'_'+name+'.png'));bpy.ops.render.render(write_still=True)
views('before')
# Original coordinates/UV scope evidence. No source image or material writes.
import struct
def mesh_hash(o):
 data=b''.join(struct.pack('<3f',*v.co) for v in o.data.vertices)+b''.join(struct.pack('<2f',*v.uv) for layer in o.data.uv_layers for v in layer.data)
 if o.data.shape_keys:data+=b''.join(struct.pack('<3f',*v.co) for k in o.data.shape_keys.key_blocks for v in k.data)
 return hashlib.sha256(data).hexdigest()
allowed={o.name for o in bpy.data.collections['MIA_V17_PIXAL_HAIR'].objects if 'Knot' in o.name or 'OneClosedKnot' in o.name}|{hair.name};protected={o.name:mesh_hash(o) for o in bpy.data.objects if o.type=='MESH' and o.name not in allowed};original_uv={o.name:hashlib.sha256(b''.join(struct.pack('<2f',*v.uv) for l in o.data.uv_layers for v in l.data)).hexdigest() for o in bpy.data.objects if o.type=='MESH' and o.name in allowed}
# Geometric-connected lower branches, weld correspondence only for grouping (no topology edits).
sel={v.index for v in me.vertices if v.co.z<1.385};buckets={};adj={i:set() for i in sel}
for i in sel:buckets.setdefault(tuple(round(a,5) for a in me.vertices[i].co),[]).append(i)
for ids in buckets.values():
 for i in ids:adj[i].update(ids)
for edge in me.edges:
 i,j=edge.vertices
 if i in sel and j in sel:adj[i].add(j);adj[j].add(i)
left=set(sel);groups=[]
while left:
 i=left.pop();stack=[i];grp=[i]
 while stack:
  for j in adj[stack.pop()]:
   if j in left:left.remove(j);stack.append(j);grp.append(j)
 groups.append(grp)
report=[]
for k,g in enumerate(groups):
 pts=[me.vertices[i].co for i in g]
 if len(g)>70:report.append({'id':k,'count':len(g),'bounds':[[min(q[j] for q in pts),max(q[j] for q in pts)] for j in range(3)]})
print('BRANCHES',json.dumps(report));(OUT/'branch-inspection.json').write_text(json.dumps(report,indent=2))

changed=[]
for g in groups:
 pts=[me.vertices[i].co.copy() for i in g];lo=min(q.z for q in pts);hi=max(q.z for q in pts)
 if len(g)<15 or lo>1.31 or hi<1.335:continue
 tips=[q for q in pts if q.z<lo+.018];center=sum(tips,Vector())/len(tips);sgn=1 if center.x>0 else -1;endshift=.016*math.cos(28*center.x)+.006*math.sin(60*center.x)
 for i,q in zip(g,pts):
  t=max(0,min(1,(1.385-q.z)/(1.385-lo)));fade=t*t*(3-2*t);sx=1-.88*t**2.8;sy=1-.52*t**2
  q.x=center.x+(q.x-center.x)*sx+sgn*.012*math.sin(math.pi*t)*fade-center.x*.045*t*t
  q.y=center.y+(q.y-center.y)*sy+.012*math.sin(math.pi*t)*fade
  q.z+=endshift*fade
  me.vertices[i].co=q
 changed.append({'vertices':len(g),'center':list(center),'tip_z_delta':endshift})
me.update()
# Existing half-up core/wraps: fuller oval loop bundle with recessed center, UV untouched.
for o in bpy.data.collections['MIA_V17_PIXAL_HAIR'].objects:
 if 'Knot' not in o.name:continue
 for v in o.data.vertices:
  q=v.co-Vector((0,.135,1.568));x=q.x*.78;z=q.z*1.38;y=q.y*1.30
  recess=.012*math.exp(-((x/.015)**2+(z/.019)**2))*max(0,min(1,(q.y+.005)/.018))
  y+=.006-recess;ang=.23;v.co=Vector((x*math.cos(ang)+z*math.sin(ang),.135+y,1.568+z*math.cos(ang)-x*math.sin(ang)))
 if 'OneClosedKnot' in o.name:
  for v in o.data.vertices:
   q=v.co-Vector((0,.135,1.568));v.co=Vector((q.x*.60,.123+q.y*.65,1.568+q.z*.60))
 o.data.update()
# Remove isolated front cloth scraps only, not side locks or head-connected pieces.
bm=bmesh.new();bm.from_mesh(me);bucket={}
for f in bm.faces:
 for v in f.verts:bucket.setdefault(tuple(round(a,5) for a in v.co),set()).add(f)
remaining=set(bm.faces);remove=[];sourceids=[];layer=bm.faces.layers.int.get('MIA_SOURCE_POLYGON')
while remaining:
 first=remaining.pop();stack=[first];grp={first}
 while stack:
  for v in stack.pop().verts:
   for f in bucket[tuple(round(a,5) for a in v.co)]:
    if f in remaining:remaining.remove(f);stack.append(f);grp.add(f)
 pts=[v.co for f in grp for v in f.verts]
 if (layer and any(f[layer] in {193147,193570,193146,193281} for f in grp) and len(grp)<3000) or (len(grp)<3000 and all(abs(q.x)<.16 and q.y<.060 and q.z<1.355 for q in pts)):
  remove.extend(grp)
  if layer:sourceids.extend(f[layer] for f in grp)
bmesh.ops.delete(bm,geom=remove,context='FACES');bm.to_mesh(me);bm.free();me.update()
# Non-hair geometry and braid stay byte-identical. All retained UV loops remain copied by bmesh.
assert all(mesh_hash(bpy.data.objects[n])==v for n,v in protected.items())
for image in bpy.data.images:
 if image.packed_file:image.use_fake_user=True
native=OUT/'Mia_HairFinish_v17e.blend';h._aim(cam,(0,-2,1.46),(0,0,1.46));bpy.ops.wm.save_as_mainfile(filepath=str(native));bpy.ops.wm.open_mainfile(filepath=str(native));scene=bpy.context.scene;cam=scene.camera;views('after');assert sha(SRC)==source_sha
r={'source_sha256':source_sha,'native_sha256':sha(native),'recipe_sha256':sha(Path(__file__)),'protected_meshes_unchanged':len(protected),'lower_branch_changes':changed,'removed_detached_source_polygons':sourceids,'changed_owners':sorted(allowed),'state':'Focused shape candidate, inspect actual before/after','original_uv_hashes':original_uv};(OUT/'manifest.json').write_text(json.dumps(r,indent=2));print('NATIVE_SHA',r['native_sha256'])
