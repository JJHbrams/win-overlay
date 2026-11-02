"""CPU line-of-sight diagnosis of actual atlas-classified teeth, not an ART test."""
from pathlib import Path
import json, math, argparse, sys
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--native',required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.open_mainfile(filepath=str(Path(a.native).resolve()),use_scripts=False)
o=bpy.data.objects['MIA_V27_Foundation_Face'];m=o.data;uv=m.uv_layers.active
teeth=[]
for f in m.polygons:
 if f.material_index!=0:continue
 c=sum((uv.data[i].uv for i in f.loop_indices),Vector((0,0)))/len(f.loop_indices)
 if c.x<.46 and c.y>.52:teeth.append(f.index)
c=bpy.data.objects.get('Mia_FacialControls_v002');cam=bpy.context.scene.camera
direction=cam.matrix_world.to_quaternion() @ Vector((0,0,-1)); results=[]
for suffix,value in [('MTH_Fun',1.),('MTH_Joy',1.),('MTH_I',1.),('MTH_E',1.),('MTH_Up',1.),('MTH_A',.5)]:
 for key in c.keys():
  if key.startswith('Manual_') or (key.startswith('P') and key[:3][1:].isdigit()):c[key]=0.
 c['Manual_'+suffix]=value;c.update_tag();bpy.context.scene.frame_set(len(results)+2);bpy.context.view_layer.update()
 dg=bpy.context.evaluated_depsgraph_get();skin=bpy.data.objects['MIA_V27_SharedHeadBody'];ev=skin.evaluated_get(dg);em=ev.to_mesh()
 vertices=[ev.matrix_world @ v.co for v in em.vertices];polys=[tuple(f.vertices) for f in em.polygons];tree=BVHTree.FromPolygons(vertices,polys)
 mo=o.evaluated_get(dg);me=mo.to_mesh();ws=[mo.matrix_world @ v.co for v in me.vertices]
 # The Mask modifier changes polygon indices; classify teeth by interpolated active UV again.
 mu=me.uv_layers.active;points=[];visible=[]
 for f in me.polygons:
  if f.material_index!=0:continue
  cu=sum((mu.data[i].uv for i in f.loop_indices),Vector((0,0)))/len(f.loop_indices)
  if not (cu.x<.46 and cu.y>.52):continue
  target=sum((ws[i] for i in f.vertices),Vector())/len(f.vertices);origin=target-direction*2
  hit=tree.ray_cast(origin,direction,2.0001);blocked=hit[0] is not None and hit[3]<1.99995
  points.append(list(target));visible.append(not blocked)
 mn=[min(v[i] for v in points) for i in range(3)] if points else None;mx=[max(v[i] for v in points) for i in range(3)] if points else None
 results.append(dict(channel=suffix,value=value,teeth_polygons=len(points),centroids_not_blocked_by_skin=sum(visible),bbox_world=[mn,mx]))
 mo.to_mesh_clear();ev.to_mesh_clear()
(P/'mouth-line-of-sight.json').write_text(json.dumps(dict(results=results,meaning='Centroid line of sight only; transparency/frontfacing/material and source match still require actual render.'),indent=2)+'\n',encoding='utf-8')
print('MOUTH_CPU_VISIBILITY',json.dumps(results),flush=True)
