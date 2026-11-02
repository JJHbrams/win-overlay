from pathlib import Path
import json,hashlib,sys
import bpy
from mathutils.geometry import interpolate_bezier
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import install_neck_supplement
sys.path.insert(0,str(P.parents[1]/'mia-body-underwear-v002/integration-guard-R3'));import scene_fingerprint as h
d=json.loads((P/'current-body-audit.json').read_text());N=Path(d['native']);assert hashlib.sha256(N.read_bytes()).hexdigest()==d['sha256'];bpy.ops.wm.open_mainfile(filepath=str(N),use_scripts=False);s=bpy.context.scene;s.frame_set(2);s.frame_set(1);bpy.context.view_layer.update();before={o.name:h.object_fingerprint(o) for o in bpy.data.objects};envelope=h.snapshot_scene()['scene'];col=install_neck_supplement.install();bpy.context.view_layer.update();assert all(h.object_fingerprint(bpy.data.objects[n])==fp for n,fp in before.items());assert h.snapshot_scene()['scene']==envelope;assert install_neck_supplement.install()==col;curves=[]
for ob in col.objects:
    if ob.type!='CURVE':continue
    sp=ob.data.splines[0];bp=sp.bezier_points;points=[]
    for i in range(len(bp) if sp.use_cyclic_u else len(bp)-1):
        a=bp[i];b=bp[(i+1)%len(bp)];points.extend([list(ob.matrix_world@p) for p in interpolate_bezier(a.co,a.handle_right,b.handle_left,b.co,21)][:-1])
    points.append(points[0] if sp.use_cyclic_u else list(ob.matrix_world@bp[-1].co));curves.append(dict(name=ob.name,points=points))
O=P/'scaffold-fullbody';(O/'neck-actual-Blender.json').write_text(json.dumps(dict(collection=col.name,curves=curves),indent=2)+'\n',encoding='utf-8');report=dict(neck_data_sha256=col['neck_data_sha256'],base_guide_sha256=col['base_fullbody_sha256'],curves=len(curves),net=1,all_original_data_objects_exact=len(before),scene_envelope_exact=True,model_head_keys_unchanged=True,idempotent=True,native_saved=False,gpu_used=False,native_unchanged=hashlib.sha256(N.read_bytes()).hexdigest()==d['sha256']);(O/'neck-fresh-guard.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('NECK_SUPPLEMENT_ACTUAL_CPU_DONE',json.dumps(report),flush=True)
