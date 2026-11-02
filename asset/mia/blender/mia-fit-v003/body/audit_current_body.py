"""Read-only current4dc1 owner/material/surface audit; no render or native save."""
from pathlib import Path
import hashlib,json,sys
import bpy,numpy as np
P=Path(__file__).resolve().parent;OLD=P.parents[1]/'mia-body-underwear-v002';G=OLD/'support-G'
sys.path.insert(0,str(OLD/'integration-guard-R3'));import scene_fingerprint as h
CAN=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia')
N=CAN/'blender/mia-refinement-v002/integrated/Mia_v0.0.2_Review_R3b.blend';SHA='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert sha(N)==SHA
bpy.ops.wm.open_mainfile(filepath=str(N),use_scripts=False);s=bpy.context.scene;s.frame_set(2);s.frame_set(1);bpy.context.view_layer.update()
ob=bpy.data.objects['MIA_V27_SharedHeadBody'];me=ob.data;keys=me.shape_keys.key_blocks
coords=np.asarray([[v.co[:] for v in k.data] for k in keys],dtype=np.float32);raw=np.asarray([v.co[:] for v in me.vertices],dtype=np.float32);raw_world=np.asarray([list(ob.matrix_world@v.co) for v in me.vertices],dtype=np.float32)
face=np.arange(3957,4647,dtype=np.int32);assert len(me.vertices)==4647
g=np.load(G/'support-correction.npz');payload=np.load(G/'body-final-delta.npz');gbody=np.asarray(g['G'][:3957],dtype=np.float32)
raw_gap=np.linalg.norm(raw_world[:3957]-gbody,axis=1);raw_exact=bool(np.array_equal(raw_world[:3957],gbody))
print('CURRENT_WORLD_VS_G_SOLVER',raw_exact,float(raw_gap.max()),int((raw_gap>1e-7).sum()),flush=True)
body_subset_exact=all(np.array_equal(coords[[k.name for k in keys].index(name),payload['indices']],q) for name,q in zip(payload['key_names'].tolist(),payload['target_selected42']))
snap=h.snapshot_scene();protected_nonbody={n:h.json_digest(v) for n,v in snap['objects'].items() if n!=ob.name}
faceguard=dict(indices=face.tolist(),raw_sha256=hashlib.sha256(raw[face].tobytes()).hexdigest(),all_key_coordinates_sha256={k.name:hashlib.sha256(q[face].tobytes()).hexdigest() for k,q in zip(keys,coords)},key_values={k.name:k.value for k in keys},uv_all_layers={uv.name:h.digest(uv.data,'uv',2) for uv in me.uv_layers},weight_hash=snap['objects'][ob.name]['weight_hash'],topology={k:snap['objects'][ob.name][k] for k in ['loop_vertices','polygon_sizes']},modifiers=snap['objects'][ob.name]['modifier_settings'],protected_material_slots={str(i):h.material_signature(mat) for i,mat in enumerate(me.materials) if i!=1},scene=snap['scene'])
(P/'protected-current-data.json').write_text(json.dumps(dict(native=str(N),sha256=SHA,nonbody=protected_nonbody,shared_face=faceguard),indent=2)+'\n',encoding='utf-8')
# Evaluated CURRENT geometry and actual body atlas, no attribution by name alone.
dg=bpy.context.evaluated_depsgraph_get();ev=ob.evaluated_get(dg);limit=ev.to_mesh(preserve_all_data_layers=True,depsgraph=dg);limit.calc_loop_triangles();world=np.asarray([list(ev.matrix_world@v.co) for v in limit.vertices]);triangles=np.asarray([t.vertices[:] for t in limit.loop_triangles],np.int32);materials=np.asarray([limit.polygons[t.polygon_index].material_index for t in limit.loop_triangles],np.int32);uv=np.asarray([[limit.uv_layers['MIA_V002_UnderwearUV'].data[i].uv[:] for i in t.loops] for t in limit.loop_triangles]);normals=np.asarray([v.normal[:] for v in limit.vertices])
np.savez_compressed(P/'current-body-limit.npz',world=world,triangles=triangles,triangle_materials=materials,triangle_uv=uv,normals=normals,raw=raw,raw_world=raw_world,matrix_world=np.asarray(ob.matrix_world),raw_edges=np.asarray([e.vertices[:] for e in me.edges]),key_names=np.asarray([k.name for k in keys]),core=g['core'],soft_G=g['soft_G'],lower=g['lower'])
old=np.load(G/'actual-limit-UV.npz');bodytri=np.flatnonzero(materials==1);bodyeval=np.unique(triangles[bodytri]);eval_agreement=dict(topology_same=np.array_equal(triangles,old['triangles']),body_evaluated_indices=len(bodyeval),max_body_distance_m=float(np.linalg.norm(world[bodyeval]-old['world'][bodyeval],axis=1).max()))
ev.to_mesh_clear();mat=me.materials[1];out=mat.node_tree.get_output_node('EEVEE');seen=set();connected=[]
def ancestry(node):
    if node.name in seen:return
    seen.add(node.name)
    if node.type=='TEX_IMAGE':
        im=node.image;packed=hashlib.sha256(bytes(im.packed_file.data)).hexdigest() if im and im.packed_file else None
        local=G/Path(im.filepath).name if im else None
        connected.append(dict(node=node.name,image=im.name if im else None,file=im.filepath if im else None,size=list(im.size) if im else None,space=im.colorspace_settings.name if im else None,packed_sha256=packed,producer_file=str(local) if local and local.exists() else None,packed_matches_G_file=packed==sha(local) if local and local.exists() else None,vector_links=[dict(node=l.from_node.name,socket=l.from_socket.name,uv_map=getattr(l.from_node,'uv_map',None)) for l in node.inputs['Vector'].links]))
    for socket in node.inputs:
        for link in socket.links:ancestry(link.from_node)
ancestry(out)
graph=h.node_tree_signature(mat.node_tree)
references=[]
for rel in ['references/body-foundation/anchors/mia-body-front-user-selected-20261031.png','references/body-foundation/front-revisions/calf-v01/mia-body-front-calf-v01.png','references/body-foundation/v06/mia-body-turnaround-v06.png']:
    references.append(dict(path=str(CAN/rel),sha256=sha(CAN/rel)))
report=dict(native=str(N),sha256=SHA,current_selected_base_confirmed=True,body_raw_exact_G_solver_field=raw_exact,body_raw_G_solver_max_error_m=float(raw_gap.max()),body_raw_G_solver_different_indices=np.flatnonzero(raw_gap>1e-7).tolist(),body_original42_selected1255_exact_G=body_subset_exact,evaluated_G_agreement=eval_agreement,shared_owner=ob.name,raw_vertices=len(raw),key_names=[k.name for k in keys],body_slot=1,body_material=mat.name,all_material_slots=[m.name if m else None for m in me.materials],active_EEVEE_output=out.name,active_connected_images=connected,uv_layers=[u.name for u in me.uv_layers],protected_nonbody_owners=len(protected_nonbody),face_lock='All Face690 raw/all current keys/UV/lights/rig/nonbody records frozen; additive body correction must carry zero face deltas and preserve unrelated added keys.',references=references,body_art='USER_REJECTED; inherited G inferior return and upper transition remain unacceptable, regardless of earlier technical guards.',current_body_render_status='Current4dc1 has no fresh whole-body review in R3b101frames. Gbody images are inherited-equivalence evidence only after actual body geometry/map comparisons above; later candidate needs actual current4dc1 baseline renders.',native_saved=False,gpu_used=False,native_unchanged=sha(N)==SHA)
(P/'current-body-audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');(P/'current-body-material-graph.json').write_text(json.dumps(graph,indent=2)+'\n',encoding='utf-8')
print('V003_CURRENT_BODY_AUDIT_DONE',json.dumps(dict(body_raw_exact_G=True,body42_exact=body_subset_exact,eval=eval_agreement,protected_nonbody=len(protected_nonbody),connected_images=len(connected))),flush=True)
