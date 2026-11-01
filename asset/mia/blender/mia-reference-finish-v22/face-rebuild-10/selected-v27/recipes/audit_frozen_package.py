import bpy,numpy as np,json,hashlib
from pathlib import Path
O=Path(__file__).parent;S=O/'face-shared-final/Mia_Foundation_v27.blend';R=O/'replay-verification-final/Mia_Foundation_v27_Replayed.blend'
def owners():return [o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render and (o.name.startswith('MIA_V27_') or o.name.startswith('V27_'))]
def evaluated():
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();result={};arrays={}
 for o in owners():
  e=o.evaluated_get(dg);m=e.to_mesh();co=np.array([e.matrix_world@v.co for v in m.vertices],dtype='<f4');uv=np.array([d.uv[:] for d in m.uv_layers['UVMap'].data],dtype='<f4') if m.uv_layers.get('UVMap') else np.zeros((0,2),dtype='<f4');arrays[o.name]=uv.copy();result[o.name]={'coordinates_sha':hashlib.sha256(co.tobytes()).hexdigest(),'loop_uv_sha':hashlib.sha256(uv.tobytes()).hexdigest(),'vertices':len(m.vertices),'polygons':len(m.polygons)};e.to_mesh_clear()
 return result,arrays
bpy.ops.wm.open_mainfile(filepath=str(S));expected,expected_uv=evaluated();used=set();visited=set()
def visit(node):
 token=node.as_pointer()
 if token in visited:return
 visited.add(token)
 if node.type=='TEX_IMAGE' and node.image:used.add(node.image)
 if node.type=='GROUP' and node.node_tree:
  for out in node.node_tree.nodes:
   if out.type=='GROUP_OUTPUT':visit(out)
 for socket in node.inputs:
  for link in socket.links:visit(link.from_node)
materials={s.material for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render for s in o.material_slots if s.material}
for m in materials:
 if m.use_nodes:
  for n in m.node_tree.nodes:
   if n.type=='OUTPUT_MATERIAL' and n.is_active_output:visit(n)
imageinfo=lambda im:{'name':im.name,'packed':bool(im.packed_file or im.packed_files),'filepath':im.filepath,'source':im.source,'size':list(im.size)}
report={'native_sha256':hashlib.sha256(S.read_bytes()).hexdigest(),'visible_material_consumed_images':[imageinfo(i) for i in sorted(used,key=lambda i:i.name)],'unpacked_consumed_images':[imageinfo(i) for i in used if not(i.packed_file or i.packed_files) and i.source!='GENERATED'],'unused_archive_images_count':len(set(bpy.data.images)-used),'unused_archive_images_unpacked':[imageinfo(i) for i in set(bpy.data.images)-used if not(i.packed_file or i.packed_files)],'scope':'Visible materials active output dependency walk including node groups. Unused archived image paths do not determine the visible result.'}
(S.parent/'packed-image-audit.json').write_text(json.dumps(report,indent=2));meta_path=O/'replay-package/manifest.json';meta=json.loads(meta_path.read_text());meta['scene']={'render_engine':bpy.context.scene.render.engine,'use_freestyle':bpy.context.scene.render.use_freestyle,'view_transform':bpy.context.scene.view_settings.view_transform,'look':bpy.context.scene.view_settings.look,'exposure':bpy.context.scene.view_settings.exposure,'gamma':bpy.context.scene.view_settings.gamma};meta_path.write_text(json.dumps(meta,indent=2))
bpy.ops.wm.open_mainfile(filepath=str(R));actual,actual_uv=evaluated();diff={n:{k:[v,actual.get(n,{}).get(k)] for k,v in r.items() if actual.get(n,{}).get(k)!=v} for n,r in expected.items()};diff={n:v for n,v in diff.items() if v};(O/'replay-verification-final/evaluated-equivalence.json').write_text(json.dumps({'reference_sha256':report['native_sha256'],'all_six_evaluated_coordinate_arrays_and_uv_exact':not diff,'differences':diff,'evaluated_uv_max_abs_error':{n:float(abs(expected_uv[n]-actual_uv[n]).max()) if expected_uv[n].size else 0. for n in expected_uv},'all_six_evaluated_coordinate_arrays_exact':all(expected[n]['coordinates_sha']==actual[n]['coordinates_sha'] for n in expected),'owners':expected},indent=2));print('PACKED',len(used),'UNPACKED',len(report['unpacked_consumed_images']),'EVAL_EQUIVALENT',not diff)
