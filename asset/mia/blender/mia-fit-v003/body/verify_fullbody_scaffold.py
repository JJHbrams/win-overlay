"""Fresh CPU actual Blender3D guide build, original owner guard, no GPU/save."""
from pathlib import Path
import json,hashlib,sys
import bpy
from mathutils.geometry import interpolate_bezier
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import install_fullbody_scaffold
sys.path.insert(0,str(P.parents[1]/'mia-body-underwear-v002/integration-guard-R3'));import scene_fingerprint as h
d=json.loads((P/'current-body-audit.json').read_text());N=Path(d['native']);assert hashlib.sha256(N.read_bytes()).hexdigest()==d['sha256'];bpy.ops.wm.open_mainfile(filepath=str(N),use_scripts=False);s=bpy.context.scene;s.frame_set(2);s.frame_set(1);before=h.snapshot_scene();col=install_fullbody_scaffold.install();bpy.context.view_layer.update();after=h.snapshot_scene();assert before['scene']==after['scene'];assert all(before['objects'][n]==after['objects'][n] for n in before['objects']);assert install_fullbody_scaffold.install()==col
curves=[];meshes=[]
for ob in col.objects:
    if ob.type=='CURVE':
        sp=ob.data.splines[0];bp=sp.bezier_points;points=[];count=len(bp) if sp.use_cyclic_u else len(bp)-1
        for i in range(count):
            a=bp[i];b=bp[(i+1)%len(bp)];points.extend([list(ob.matrix_world@p) for p in interpolate_bezier(a.co,a.handle_right,b.handle_left,b.co,25)][:-1])
        if not sp.use_cyclic_u:points.append(list(ob.matrix_world@bp[-1].co))
        else:points.append(points[0])
        curves.append(dict(name=ob.name,kind=ob['source_kind'],points=points,closed=sp.use_cyclic_u,limitation=ob['limitation'],actual_Blender_curve=True))
    elif ob.type=='MESH':meshes.append(dict(name=ob.name,vertices=[list(ob.matrix_world@v.co) for v in ob.data.vertices],faces=[list(p.vertices) for p in ob.data.polygons],actual_Blender_controlnet=True))
O=P/'scaffold-fullbody';(O/'guide-actual-Blender.json').write_text(json.dumps(dict(curves=curves,meshes=meshes,collection=col.name,default_hide_render=col.hide_render),indent=2)+'\n',encoding='utf-8');report=dict(native_sha256=d['sha256'],source_target_sha256=col['reference_sha256'],actual_curve_objects=len(curves),actual_loft_controlnets=len(meshes),all_existing_owners_exact=len(before['objects']),scene_envelope_exact=True,idempotent=True,new_collection_default_hidden_for_render=True,native_saved=False,gpu_used=False,native_unchanged=hashlib.sha256(N.read_bytes()).hexdigest()==d['sha256'],status='Actual Blender guide geometry created/read back in fresh process; no D body mutation; source/inferred guide awaits root review.')
(O/'fresh-guide-guard.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('ACTUAL_FULLBODY_SCAFFOLD_CPU_DONE',json.dumps(report),flush=True)
