"""CPU full-height/semantic landmark audit, current4dc1; no shape proposal/save."""
from pathlib import Path
import json,hashlib
import bpy,numpy as np
P=Path(__file__).resolve().parent;d=json.loads((P/'current-body-audit.json').read_text());N=Path(d['native']);assert hashlib.sha256(N.read_bytes()).hexdigest()==d['sha256']
bpy.ops.wm.open_mainfile(filepath=str(N),use_scripts=False);s=bpy.context.scene;s.frame_set(2);s.frame_set(1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();ob=bpy.data.objects['MIA_V27_SharedHeadBody'];ev=ob.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles();v=np.asarray([list(ev.matrix_world@p.co) for p in me.vertices]);t=np.asarray([t.vertices[:] for t in me.loop_triangles]);mi=np.asarray([me.polygons[t.polygon_index].material_index for t in me.loop_triangles]);body=v[np.unique(t[mi==1])];head=v[np.unique(t[np.isin(mi,[0,9,10,11])])];ev.to_mesh_clear()
rig=bpy.data.objects['MIA_V06_RIG'];bones={}
for b in rig.pose.bones:
    if any(x in b.name for x in ['Hips','Spine','Chest','UpperChest','Neck','Head','Shoulder','UpperArm','UpperLeg','LowerLeg','Foot']):bones[b.name]=dict(head=list(rig.matrix_world@b.head),tail=list(rig.matrix_world@b.tail))
def section(z,window=.003):
    # Arm samples excluded by a declared central-body window, not a silhouette width.
    pts=body[(abs(body[:,2]-z)<window)&(abs(body[:,0])<.15)]
    return dict(z=z,n=len(pts),central_width_m=float(np.ptp(pts[:,0])) if len(pts) else None,front_y=float(pts[:,1].min()) if len(pts) else None,back_y=float(pts[:,1].max()) if len(pts) else None)
visible_bounds={}
for o in s.objects:
    if o.type=='MESH' and not o.hide_render and o.visible_get():
        e=o.evaluated_get(dg);m=e.to_mesh()
        if m and len(m.vertices):
            p=np.asarray([list(e.matrix_world@q.co) for q in m.vertices]);visible_bounds[o.name]=dict(count=len(p),minimum=p.min(0).tolist(),maximum=p.max(0).tolist())
        e.to_mesh_clear()
report=dict(native=str(N),sha256=d['sha256'],body_bounds=dict(minimum=body.min(0).tolist(),maximum=body.max(0).tolist()),head_material_bounds=dict(minimum=head.min(0).tolist(),maximum=head.max(0).tolist(),limitation='Material region includes neck junction. Chin/head-height must use actual image landmarks, not this bounding box.'),bones=bones,actual_pose_basis={b.name:[list(r) for r in b.matrix_basis] for b in rig.pose.bones},actual_original_key_values={k.name:k.value for k in ob.data.shape_keys.key_blocks},central_sections=[section(z) for z in np.arange(1.10,1.401,.02)],visible_mesh_bounds=visible_bounds,native_saved=False,gpu_used=False,interpretation='Measurement only. Full-height source registration and observed landmarks are required; no direction for head/body ratio inferred yet.')
(P/'current-proportions.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('V003_CURRENT_PROPORTIONS_DONE',len(visible_bounds),flush=True)
