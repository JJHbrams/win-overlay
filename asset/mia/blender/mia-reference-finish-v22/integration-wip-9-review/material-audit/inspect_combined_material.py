"""Read-only saved WIP8/WIP9 shader and UV audit. No rendering or native save."""
import bpy,hashlib,json,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parent;V22=ROOT.parents[1]
SOURCES={'wip8':V22/'integration-wip-8-review/Mia_ReferenceFinish_v22.blend','wip9':V22/'integration-wip-9-review/Mia_FaceReview_v22_WIP9.blend'}
EXPECTED9='fb85468a623e1befc590176a24636548b944491ce4ae19decaece625304945b2'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert sha(SOURCES['wip9'])==EXPECTED9
def image_info(im):return {'name':im.name,'size':list(im.size),'colorspace':im.colorspace_settings.name,'packed_sha256':hashlib.sha256(im.packed_file.data).hexdigest() if im.packed_file else None}
def reachable(mat):
 nodes=mat.node_tree.nodes;outs=[n for n in nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output];seen=set();stack=outs[:]
 while stack:
  n=stack.pop()
  if n.name in seen:continue
  seen.add(n.name)
  for s in n.inputs:
   for link in s.links:stack.append(link.from_node)
 return seen
reports={}
for role,path in SOURCES.items():
 bpy.ops.wm.open_mainfile(filepath=str(path),use_scripts=False);skin=bpy.data.objects['MIA_V14_SculptedSkin'];mat=skin.data.materials[7];seen=reachable(mat)
 # Compare evaluated neutral UVs because WIP8 still has Subsurf while WIP9 is
 # the verified equivalent dense bake. Raw loop counts are not comparable.
 for k in skin.data.shape_keys.key_blocks:k.value=0
 bpy.context.view_layer.update();ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();uv={l.name:np.array([p.uv[:] for p in l.data],np.float32) for l in mesh.uv_layers};uvhash={n:hashlib.sha256(a.tobytes()).hexdigest() for n,a in uv.items()};ev.to_mesh_clear()
 maps={n.name:image_info(n.image) for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and n.name in seen}
 uvnodes={n.name:n.uv_map for n in mat.node_tree.nodes if n.type=='UVMAP' and n.name in seen};invalid=[name for name,layer in uvnodes.items() if layer not in skin.data.uv_layers]
 report={'source':{'path':str(path),'sha256':sha(path)},'material':mat.name,'render_visible_skin':not skin.hide_render,'raw_vertices':len(skin.data.vertices),'evaluated_uv_loop_counts':{n:len(a) for n,a in uv.items()},'evaluated_uv_hashes':uvhash,'uv_nodes':uvnodes,'invalid_uv_nodes':invalid,'actual_reachable_nodes':sorted(seen),'actual_consumed_image_maps':maps,'actual_consumed_links':[[[l.from_node.name,l.from_socket.name],[l.to_node.name,l.to_socket.name]] for l in mat.node_tree.links if l.from_node.name in seen and l.to_node.name in seen],'note':'No native save. Connected maps are technical evidence only; actual combined-geometry appearance requires the separate render review.'}
 assert not invalid
 reports[role]=report
assert reports['wip8']['evaluated_uv_hashes']==reports['wip9']['evaluated_uv_hashes'],'evaluated UV changed'
for name in ['FINISH8_BasePigment','FINISH8_FatigueMask','FINISH8_FineLineMask']:
 assert reports['wip8']['actual_consumed_image_maps'][name]==reports['wip9']['actual_consumed_image_maps'][name],name
assert 'IDENTITY9_SecondaryFoldPigment' in reports['wip9']['actual_reachable_nodes']
assert 'IDENTITY9_MeasuredLowerLidUVCurve' in reports['wip9']['actual_reachable_nodes']
reports['checks']={'evaluated_uv_exact':True,'three_original_packed_maps_exact_and_consumed':True,'m4_procedural_fold_reaches_actual_output':True,'m4_shifted_mask_node_not_used': 'IDENTITY9_SecondaryFoldExistingMask' not in reports['wip9']['actual_reachable_nodes'],'native_hashes_unchanged':all(sha(p)==reports[r]['source']['sha256'] for r,p in SOURCES.items()),'art_pass':False}
(ROOT/'packed-map-uv-audit.json').write_text(json.dumps(reports,indent=2));print('COMBINED_MATERIAL_AUDIT_DONE',reports['checks'])
