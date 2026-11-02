"""Actual evaluated geometry and ordered tooth/cavity ray diagnosis. No rendering/save."""
from pathlib import Path
import argparse, collections, json, sys, math
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--native',required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);bpy.ops.wm.open_mainfile(filepath=str(Path(a.native).resolve()),use_scripts=False)
master=bpy.data.objects['MIA_V27_Foundation_Face']
for k in master.data.shape_keys.key_blocks[1:]:k.value=1. if k.name.endswith('_MIA_ToothyGrin') else 0.
bpy.context.scene.frame_set(2);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();scene=bpy.context.scene;cam=scene.camera
direction=cam.matrix_world.to_quaternion()@Vector((0,0,-1))
objects={}
for name in [master.name,'MIA_V27_SharedHeadBody']:
 o=bpy.data.objects[name].evaluated_get(dg);m=o.to_mesh();verts=[o.matrix_world@v.co for v in m.vertices]
 faces=[f for f in m.polygons if name!=master.name or f.material_index==0]
 tree=BVHTree.FromPolygons(verts,[tuple(f.vertices) for f in faces])
 objects[name]=(o,m,verts,faces,tree)
o,m,verts,faces,own=objects[master.name];uv=m.uv_layers.active;white=[]
for i,f in enumerate(faces):
 q=sum((uv.data[j].uv for j in f.loop_indices),Vector((0,0)))/len(f.loop_indices)
 white.append(q.x<.46 and q.y>.52)
counts=collections.Counter();normaldots=[];projected=[];examples=[]
for i,f in enumerate(faces):
 if not white[i]:continue
 target=sum((verts[j] for j in f.vertices),Vector())/len(f.vertices);origin=target-direction*2
 first=own.ray_cast(origin,direction,2.0001)
 skinhit=objects['MIA_V27_SharedHeadBody'][4].ray_cast(origin,direction,2.0001)
 blocked_skin=skinhit[0] is not None and skinhit[3]<1.99995
 blocked_self=first[0] is not None and first[3]<1.99995
 label='skin' if blocked_skin else ('other_white' if blocked_self and white[first[2]] else ('pink_cavity' if blocked_self else 'visible_geometry'))
 counts[label]+=1
 normal=(verts[f.vertices[1]]-verts[f.vertices[0]]).cross(verts[f.vertices[2]]-verts[f.vertices[0]]).normalized();normaldots.append(float(normal.dot(-direction)))
 for j in f.vertices:
  p=world_to_camera_view(scene,cam,verts[j]);projected.append([float(p.x*512),float((1-p.y)*512)])
 if label=='pink_cavity' and len(examples)<8:
  blocker=faces[first[2]];q=sum((uv.data[j].uv for j in blocker.loop_indices),Vector((0,0)))/len(blocker.loop_indices)
  examples.append(dict(target_face=f.index,blocking_face=blocker.index,blocking_uv=list(q),target_world=list(target),hit_world=list(first[0])))
report=dict(native=a.native,white_uv_faces=sum(white),first_geometry_counts=dict(counts),front_facing_white_faces=sum(v>0 for v in normaldots),normal_dot_range=[min(normaldots),max(normaldots)],
  projected_bbox_px=[[min(p[j] for p in projected) for j in range(2)],[max(p[j] for p in projected) for j in range(2)]],blocking_examples=examples,
  meaning='Geometry-only rays; actual shader vector/alpha/culling still require the material audit and diagnostic render.')
for o,m,vs,fs,t in objects.values():o.to_mesh_clear()
(P/'grin-C-ordered-occlusion.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('GRIN_ORDERED_GEOMETRY',json.dumps(report),flush=True)
