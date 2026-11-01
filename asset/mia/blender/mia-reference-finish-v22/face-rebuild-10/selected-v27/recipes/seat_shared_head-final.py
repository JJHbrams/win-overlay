import bpy,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
O=Path(__file__).parent;OUT=O/'face-shared-final';bpy.ops.wm.open_mainfile(filepath=str(OUT/'Mia_Foundation_v27.blend'));master=bpy.data.objects['MIA_V27_Foundation_Face'];skin=bpy.data.objects['MIA_V27_SharedHeadBody'];ks=master.data.shape_keys.key_blocks;ribs=[o for o in bpy.context.scene.objects if o.name.startswith('V27_') and 'Ribbon' in o.name and not o.hide_render];carrier=set(i for p in master.data.polygons if p.material_index in [1,5] for i in p.vertices);records=[]
for ki,key in enumerate(ks):
 for k in ks:k.value=0
 if ki:key.value=1
 bpy.context.view_layer.update();ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();bv=BVHTree.FromPolygons([ev.matrix_world@v.co for v in me.vertices],[list(p.vertices) for p in me.polygons]);cmoves=[];rmoves=[]
 for i in carrier:
  v=key.data[i];q=v.co.copy();hit=bv.ray_cast(Vector((q.x,-.25,q.z)),Vector((0,1,0)))
  if hit[0] is not None and q.y<hit[0].y+.00045:
   d=hit[0].y+.00045-q.y
   if d<.015:v.co.y+=d;cmoves.append(d)
 for ob in ribs:
  rk=ob.data.shape_keys.key_blocks[ki]
  for v in rk.data:
   q=v.co.copy();hit=bv.ray_cast(Vector((q.x,-.25,q.z)),Vector((0,1,0)))
   if hit[0] is not None:v.co.y=min(q.y,hit[0].y-.00022)
   else:
    hit=bv.find_nearest(q)
    if hit[0] is not None and hit[3]<.002:v.co=hit[0]+Vector((0,-.00022,0))
   rmoves.append((v.co-q).length)
  if ki==0:
   for v,c in zip(ob.data.vertices,rk.data):v.co=c.co
 ev.to_mesh_clear();records.append({'key':key.name,'carrier_max_mm':max(cmoves,default=0)*1000,'ribbon_max_mm':max(rmoves,default=0)*1000})
for k in ks:k.value=0
for v,c in zip(master.data.vertices,ks[0].data):v.co=c.co
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Mia_Foundation_v27.blend'));(OUT/'evaluated-contact-audit.json').write_text(json.dumps(records,indent=2));print('R2_CONTACT_SAVED')
