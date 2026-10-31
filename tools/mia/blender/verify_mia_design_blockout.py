"""Independent saved-file data audit; never saves or modifies the loaded model."""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
import bpy

out=Path(sys.argv[sys.argv.index('--')+1]).resolve()
report=json.loads((out/'report.json').read_text(encoding='utf-8'))
checks=[];coverage={}
for ob in bpy.data.objects:
 if ob.type!='MESH' or 'source_object' not in ob: continue
 source=bpy.data.objects[ob['source_object']];vertices=list(ob['source_vertex_indices']);polys=list(ob['source_poly_indices'])
 coerr=max((abs(ob.data.vertices[i].co[k]-source.data.vertices[v].co[k]) for i,v in enumerate(vertices) for k in range(3)),default=0)
 uverr=0.0;loop_count=0
 for layer in ob.data.uv_layers:
  original=source.data.uv_layers[layer.name]
  for i,p in enumerate(polys):
   a=ob.data.polygons[i];b=source.data.polygons[p]
   assert a.loop_total==b.loop_total
   for j in range(a.loop_total):
    uverr=max(uverr,*(abs(layer.data[a.loop_start+j].uv[k]-original.data[b.loop_start+j].uv[k]) for k in (0,1)))
    loop_count+=1
 coverage.setdefault(source.name,[]).extend(polys)
 checks.append({'part':ob.name,'vertices_compared':len(vertices),'uv_loops_compared':loop_count,'position_max_error':coerr,'uv_max_error':uverr})
 assert coerr==0 and uverr==0 and vertices and loop_count
coverage_checks=[]
for name,ids in coverage.items():
 source=bpy.data.objects[name];counter=Counter(ids);missing=set(range(len(source.data.polygons)))-set(ids);overlap=sum(n-1 for n in counter.values() if n>1)
 assert not missing and not overlap
 coverage_checks.append({'source':name,'imported_faces':len(source.data.polygons),'assigned_faces':len(ids),'missing':len(missing),'overlap':overlap})
face=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Mia_Face_AnimeTopology') and o.data.shape_keys)
assert len(face.data.shape_keys.key_blocks)==42
visible=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render]
assert visible and bpy.context.scene.camera and bpy.context.scene.view_layers[0].material_override is None
assert not any(m.name.startswith('ID_') for o in visible for m in o.data.materials if m)
linked=[d.name for blocks in (bpy.data.objects,bpy.data.meshes,bpy.data.node_groups,bpy.data.materials,bpy.data.images,bpy.data.armatures) for d in blocks if d.library]
assert not linked
image_checks=[{'name':im.name,'packed':bool(im.packed_file)} for im in bpy.data.images if im.source=='FILE']
assert all(im['packed'] for im in image_checks)
result={'status':'PASS_DATA_PRESERVATION_ONLY','saved_native':bpy.data.filepath,'part_checks':checks,'coverage':coverage_checks,'preserved_original_face_keys':42,'visible_meshes':len(visible),'active_linked_datablocks':linked,'images':image_checks,'final_likeness_or_animation_approval':False}
(out/'native-data-audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('NATIVE_AUDIT_OK',len(checks),'partitions;',len(visible),'visible meshes; Face42; exact UV/coordinates')
