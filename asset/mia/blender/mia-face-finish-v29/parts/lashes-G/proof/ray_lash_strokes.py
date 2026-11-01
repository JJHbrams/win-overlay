import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
O=Path(__file__).parent;bpy.ops.wm.open_mainfile(filepath=str(O/'Mia_EyeLash_v29_D.blend'));master=bpy.data.objects['MIA_V27_Foundation_Face']
for k in master.data.shape_keys.key_blocks:k.value=0
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();owners=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render and (o.name in ['MIA_V27_SharedHeadBody','MIA_V27_Foundation_Face'] or o.name.startswith('V28G_') or 'BoundaryRibbon' in o.name or o.name.startswith('V29_'))];bvs=[]
for ob in owners:
 ev=ob.evaluated_get(dg);me=ev.to_mesh();bv=BVHTree.FromPolygons([ev.matrix_world@v.co for v in me.vertices],[list(f.vertices) for f in me.polygons]);mats=[{'slot':f.material_index,'name':me.materials[f.material_index].name if me.materials[f.material_index] else None} for f in me.polygons];bvs.append((ob.name,bv,mats));ev.to_mesh_clear()
r=next(r for r in json.loads((O/'lash-review/D-first/records.json').read_text()) if r['id']=='left_oblique-production');m=Matrix(r['camera_matrix']);rot=m.to_3x3();D=-(rot@Vector((0,0,1)));rows=[]
for x,y in [(455,375),(458,373),(461,372),(428,424),(433,423),(526,385),(548,351)]:
 origin=m.translation+rot@Vector((((x+.5)/768-.5)*.09,(.5-(y+.5)/768)*.09,0));hits=[]
 for name,bv,mats in bvs:
  h,n,idx,dist=bv.ray_cast(origin,D)
  if h is not None:hits.append({'owner':name,'distance':dist,'world_mm':list(h*1000),'polygon':idx,'material':mats[idx]})
 hits.sort(key=lambda h:h['distance']);rows.append({'pixel':[x,y],'hits':hits[:5]})
materials=[]
for i,m in enumerate(master.data.materials):
 out=next((n for n in m.node_tree.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output),None) if m and m.node_tree else None
 materials.append({'slot':i,'name':m.name if m else None,'active_surface':[(l.from_node.name,l.from_node.type) for l in out.inputs['Surface'].links] if out else None})
(O/'lash-D-interior-stroke-withmaster-rays.json').write_text(json.dumps({'rays':rows,'master_active_materials':materials},indent=2));print(json.dumps({'rays':rows,'master_active_materials':materials},indent=2))
