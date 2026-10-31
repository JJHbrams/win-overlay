"""Restore overcut Pixal nape from preserved extraction; keep body-fitted braid."""
import bpy,bmesh,sys,argparse,json,hashlib,math
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools/mia/blender'));import refine_mia_head_v06 as h
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--output-dir',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);SRC=Path(a.source).resolve();OUT=Path(a.output_dir).resolve();OUT.mkdir(parents=True,exist_ok=True);REC=SRC.parent/'Recovered_Pixal_Hair_Source.blend';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();hashes={str(p):sha(p) for p in [SRC,REC]}
bpy.ops.wm.open_mainfile(filepath=str(SRC));old=bpy.data.objects['MIA_V17_PIXAL_DetailedHair'];col=bpy.data.collections['MIA_V17_PIXAL_HAIR'];materials=list(old.data.materials)
# Source polygon plus UV correspondence preserves every already-kept upper strand coordinate.
lookup={};attr=old.data.attributes['MIA_SOURCE_POLYGON'];uv=old.data.uv_layers.active
for po in old.data.polygons:
 for li in po.loop_indices:lookup[(attr.data[po.index].value,tuple(round(v,6) for v in uv.data[li].uv))]=old.data.vertices[old.data.loops[li].vertex_index].co.copy()
with bpy.data.libraries.load(str(REC),link=False) as (av,ld):ld.objects=['MIA_V17_PIXAL_DetailedHair']
hair=ld.objects[0];col.objects.link(hair);hair.hide_render=False;hair.hide_viewport=False;hair.hide_set(False);attr=hair.data.attributes['MIA_SOURCE_POLYGON'];uv=hair.data.uv_layers.active;updated=set()
for po in hair.data.polygons:
 for li in po.loop_indices:
  key=(attr.data[po.index].value,tuple(round(v,6) for v in uv.data[li].uv));vi=hair.data.loops[li].vertex_index
  if key in lookup:hair.data.vertices[vi].co=lookup[key];updated.add(vi)
hair.data.materials.clear()
for m in materials:hair.data.materials.append(m)
for po in hair.data.polygons:po.material_index=0;po.use_smooth=True
bpy.data.objects.remove(old,do_unlink=True);hair.name='MIA_V17_PIXAL_DetailedHair'
# Report connected surface owners without a height-band deletion.
buckets={};centers={}
for po in hair.data.polygons:
 centers[po.index]=sum((hair.data.vertices[i].co for i in po.vertices),Vector())/len(po.vertices)
 for i in po.vertices:buckets.setdefault(tuple(round(v,5) for v in hair.data.vertices[i].co),set()).add(po.index)
remaining=set(range(len(hair.data.polygons)));groups=[]
while remaining:
 first=remaining.pop();stack=[first];group=[first]
 while stack:
  j=stack.pop()
  for vi in hair.data.polygons[j].vertices:
   for k in buckets[tuple(round(v,5) for v in hair.data.vertices[vi].co)]:
    if k in remaining:remaining.remove(k);stack.append(k);group.append(k)
 pts=[centers[i] for i in group];groups.append({'count':len(group),'source_polygons':[attr.data[i].value for i in group],'bounds':[[min(q[j] for q in pts),max(q[j] for q in pts)] for j in range(3)]})
(OUT/'surface-components.json').write_text(json.dumps(groups,indent=2))
# Identify the original braided tube by its measured centerline, not a head-height band.
# Bounds follow the raw braid itself (six sampled stations), preserving adjacent nape waves.
zs=np.array([1.30,1.34,1.38,1.42,1.46,1.49]);xs=np.array([.11,.109,.089,.078,.071,.069]);ys=np.array([-.090,-.080,-.061,-.040,-.022,-.016]);remove=set();reasons={}
for po in hair.data.polygons:
 q=centers[po.index];xx=float(np.interp(q.z,zs,xs));yy=float(np.interp(q.z,zs,ys))
 if 1.285<q.z<1.49 and ((q.x-xx)/.025)**2+((q.y-yy)/.025)**2<1:
  remove.add(po.index);reasons[attr.data[po.index].value]='measured_original_braid_tube'
# Dark cloth is selected through connected original atlas-painted surface pieces.
atlas=materials[0].node_tree.nodes['ORIGINAL_PIXAL_ATLAS'].image;w,hh=atlas.size;pixels=np.array(atlas.pixels[:],np.float32).reshape(hh,w,4);candidates=set()
for po in hair.data.polygons:
 q=centers[po.index]
 if not (.035<q.x<.17 and -.025<q.y<.065 and 1.20<q.z<1.435):continue
 t=sum((uv.data[li].uv for li in po.loop_indices),Vector((0,0)))/len(po.loop_indices);rgb=pixels[min(hh-1,max(0,int(t.y*hh))),min(w-1,max(0,int(t.x*w))),:3]
 if max(rgb)<.115:candidates.add(po.index)
while candidates:
 first=candidates.pop();stack=[first];grp=[first]
 while stack:
  j=stack.pop()
  for vi in hair.data.polygons[j].vertices:
   for k in buckets[tuple(round(v,5) for v in hair.data.vertices[vi].co)]:
    if k in candidates:candidates.remove(k);stack.append(k);grp.append(k)
 if (len(grp)>40 and max(centers[j].z for j in grp)-min(centers[j].z for j in grp)>.025) or max(centers[j].z for j in grp)<1.34:
  for j in grp:remove.add(j);reasons[attr.data[j].value]='connected_dark_cloth_atlas_patch'
(OUT/'removed-source-polygons.json').write_text(json.dumps(reasons,indent=2))
bm=bmesh.new();bm.from_mesh(hair.data);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.faces[i] for i in remove],context='FACES');bm.to_mesh(hair.data);bm.free();hair.data.update()
# Remove only detached residual surfaces wholly inside the former braid/front-cloth corridor.
bm=bmesh.new();bm.from_mesh(hair.data);layer=bm.faces.layers.int['MIA_SOURCE_POLYGON'];vb={}
for f in bm.faces:
 for v in f.verts:vb.setdefault(tuple(round(a,5) for a in v.co),set()).add(f)
left=set(bm.faces);detached=[]
while left:
 f=left.pop();stack=[f];grp={f}
 while stack:
  f=stack.pop()
  for v in f.verts:
   for g in vb[tuple(round(a,5) for a in v.co)]:
    if g in left:left.remove(g);stack.append(g);grp.add(g)
 coords=[v.co for f in grp for v in f.verts]
 if len(grp)<1500 and all(.015<q.x<.17 and q.y<.015 and q.z<1.425 for q in coords):
  detached.extend(grp)
  for f in grp:reasons[f[layer]]='detached_original_braid_or_front_cloth_remnant'
bmesh.ops.delete(bm,geom=detached,context='FACES');bm.to_mesh(hair.data);bm.free();hair.data.update()
(OUT/'removed-source-polygons.json').write_text(json.dumps(reasons,indent=2))

restored_count=len(hair.data.polygons)
scene=bpy.context.scene;cam=scene.camera;cam.data.ortho_scale=.48;h._aim(cam,(0,-2,1.54),(0,0,1.54));native=OUT/'Mia_PixalHead_v17c.blend';bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(native));bpy.ops.wm.open_mainfile(filepath=str(native));scene=bpy.context.scene;cam=scene.camera
for name,loc in [('front',(0,-2,1.54)),('profile',(2,0,1.54)),('back',(0,2,1.54))]:
 h._aim(cam,loc,(0,0,1.54));scene.render.filepath=str(OUT/('beauty_'+name+'.png'));bpy.ops.render.render(write_still=True)
assert all(sha(Path(p))==v for p,v in hashes.items());r={'source_hashes':hashes,'native_sha256':sha(native),'recipe_sha256':sha(Path(__file__)),'restored_faces':restored_count,'preserved_corresponding_vertices':len(updated),'status':'Review restored nape, no broad region deletion; original extraction contamination remains to classify'}
(OUT/'manifest.json').write_text(json.dumps(r,indent=2));print('NATIVE_SHA',r['native_sha256'])
