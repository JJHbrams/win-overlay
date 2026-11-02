"""Ephemeral CPU test. No original authored data or native save/render."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,sys
from mathutils import Matrix
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;N=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-refinement-v002/integrated/Mia_v0.0.2_Review_R3b.blend');SHA='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1';assert hashlib.sha256(N.read_bytes()).hexdigest()==SHA;bpy.ops.wm.open_mainfile(filepath=str(N),use_scripts=False)
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
h=load('browguard',P.parents[2]/'mia-mouth-rig-v002/guard_helpers.py') if (P.parents[2]/'mia-mouth-rig-v002/guard_helpers.py').exists() else load('browguard',P.parents[3]/'mia-mouth-rig-v002/guard_helpers.py')
before,_,bm,bi=h.snapshot();controller=bpy.data.objects['Mia_FacialControls_v002'];master=bpy.data.objects['MIA_V27_Foundation_Face'];rig=next(m.object for m in master.modifiers if m.type=='ARMATURE');head=rig.pose.bones['J_Bip_C_Head'];head0=rig.matrix_world@head.matrix
delta=load('partial_brow_display',P/'partial_brow_display.py');report_apply=delta.apply_to_current_scene();metadata=json.loads((P/'fringe-target-A.json').read_text(encoding='utf-8'));payload=np.load(P/metadata['payload']);frame=bpy.data.objects[report_apply['frame']];target=bpy.data.objects[report_apply['target']];main=bpy.data.objects[metadata['main_owner']]
def pose(values):
 for n in controller.keys():
  if n.startswith('Manual') or (n.startswith('P') and n[:3][1:].isdigit()) or n in ['HeadPitch','HeadYaw','HeadRoll','GazeX','GazeY']:controller[n]=0.
 controller['Strength']=controller['HeadPoseStrength']=controller['GazeStrength']=1.
 for n,v in values.items():controller[n]=v
 controller.update_tag();bpy.context.scene.frame_set(bpy.context.scene.frame_current+1);bpy.context.view_layer.update()
def mesh(ob):
 e=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh(preserve_all_data_layers=True,depsgraph=bpy.context.evaluated_depsgraph_get());return e,me
states=[('neutral',{}),('P05',{'P05_downward_irritated':1.}),('P12',{'P12_surprised':1.}),('Close',{'Manual_EYE_Close':1.}),('WinkRhalf',{'Manual_EYE_Close_R':.5}),('Angry1',{'Manual_BRW_Angry':1.}),('BrowSurprise1',{'Manual_BRW_Surprised':1.}),('HeadYaw22',{'HeadYaw':22.}),('HeadYawMinus22',{'HeadYaw':-22.}),('HeadRoll18',{'HeadRoll':18.}),('HeadPitch20',{'HeadPitch':20.}),('HeadPitchMinus20',{'HeadPitch':-20.}),('P04',{'P04_aside_attention':1.})]
rows=[]
for label,values in states:
 pose(values);expected=(rig.matrix_world@head.matrix)@head0.inverted();head_error=float(np.abs(np.array(frame.matrix_world)-np.array(expected)).max())
 em,mm=mesh(main);mt=np.array([em.matrix_world@v.co for v in mm.vertices]);em.to_mesh_clear();et,tm=mesh(target);tq=np.array([et.matrix_world@v.co for v in tm.vertices]);et.to_mesh_clear();target_error=float(np.linalg.norm(tq-mt[payload['main_point_ids']],axis=1).max());row=dict(state=label,controls=values,head_frame_matrix_max_error=head_error,proxy_sample_max_world_error_m=target_error,overlays=[])
 for name in report_apply['overlay_objects']:
  ob=bpy.data.objects[name];ev,me=mesh(ob);side=name.rsplit('_',1)[1];faces=[tuple(p.vertices) for p in me.polygons];used=np.array(sorted({int(i) for f in faces for i in f}),int);q=np.array([v.co[:] for v in me.vertices]);attributes={}
  for n in [delta.COMP,delta.HIT,delta.NORMAL,delta.VALID,delta.DEPTH,delta.SOURCEPOS]:
   at=me.attributes.get(n)
   if at:
    attributes[n]=np.array([tuple(d.vector) if at.data_type=='FLOAT_VECTOR' else d.value for d in at.data])
  details=dict(owner=name,evaluated_vertices=len(me.vertices),rendered_faces=len(faces),used_vertices=len(used),UV_layers=[u.name for u in me.uv_layers],attribute_names=[a.name for a in me.attributes])
  if len(used):
   comp=attributes[delta.COMP];hit=attributes[delta.HIT];norm=attributes[delta.NORMAL];sp=attributes[delta.SOURCEPOS];depth=attributes[delta.DEPTH];valid=attributes[delta.VALID]
   same=all(len(set(comp[list(f)].tolist()))==1 for f in faces);offset=np.linalg.norm(q[used]-hit[used]-norm[used]*.00015,axis=1);xz=np.abs(hit[used][:,[0,2]]-sp[used][:,[0,2]]).max();u=me.uv_layers.get('BrowParamUV');uv=np.array([d.uv[:] for d in u.data]) if u else np.empty((0,2));window=metadata['source_supported_windows'][side]
   details.update(component_ids=sorted(set(comp[used].tolist())),each_face_single_component=same,all_used_hit_valid=bool(valid[used].all()),foreground_depth_m=[float(depth[used].min()),float(depth[used].max())],max_surface_offset_error_m=float(offset.max()),max_ray_XZ_drift_m=float(xz),UV_bounds=[uv.min(0).tolist(),uv.max(0).tolist()] if len(uv) else None,source_window=window)
  row['overlays'].append(details);ev.to_mesh_clear()
 rows.append(row);print('BROW_DISPLAY_CPU_STATE',label,[(o['owner'],o['rendered_faces']) for o in row['overlays']],flush=True)
pose({});delta.set_strength(0.);bpy.context.scene.frame_set(bpy.context.scene.frame_current+1);bpy.context.view_layer.update();strength_zero={n:float(bpy.data.materials[n].node_tree.nodes[delta.PREFIX+'Strength'].outputs[0].default_value) for n in report_apply['materials']};after,_,am,ai=h.snapshot()
checks=dict(all_original_mesh_records_exact=all(after[n]==r for n,r in before.items()),all_original_material_graphs_exact=all(am[n]==v for n,v in bm.items()),all_original_images_exact=all(ai[n]==v for n,v in bi.items()),all_head_frames_follow_expected=max(r['head_frame_matrix_max_error'] for r in rows)<1e-6,all_proxy_vertices_follow_current_Main=max(r['proxy_sample_max_world_error_m'] for r in rows)<1e-6,all_states_both_nonempty=all(o['rendered_faces']>0 for r in rows for o in r['overlays']),no_cross_component_faces=all(o.get('each_face_single_component',False) for r in rows for o in r['overlays']),all_used_hits_valid=all(o.get('all_used_hit_valid',False) for r in rows for o in r['overlays']),offset_errors_below_1um=all(o.get('max_surface_offset_error_m',1.)<1e-6 for r in rows for o in r['overlays']),strength_zero_reaches_both_new_materials=all(v==0. for v in strength_zero.values()),input_native_unchanged=hashlib.sha256(N.read_bytes()).hexdigest()==SHA)
report=dict(input_native=str(N),sha256=SHA,helper_sha256=hashlib.sha256((P/'partial_brow_display.py').read_bytes()).hexdigest(),apply_report=report_apply,checks=checks,states=rows,strength_zero=strength_zero,material_incoming_angle_note='Head-space incoming+Y is intended front direction. Actual shader appearance/angular fade remains unverified until the allocated front/oblique proof. No GPU/native save.',native_saved=False,GPU_used=False)
(P/'CPU-projection-guards-A.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');assert all(checks.values()),checks
print('BROW_DISPLAY_CPU_GUARDS_DONE',json.dumps(checks),flush=True)
