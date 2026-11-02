"""Held-C expanded review:3 critical+12 orbit actual frames; no scene save."""
from pathlib import Path
import json,hashlib,types,sys,math
DIAG=Path(__file__).resolve().parent;C=DIAG.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
before={str(f):sha(f) for f in C.rglob('*') if f.is_file() and 'expanded-review' not in f.parts and '__pycache__' not in f.parts}
DIAG_INSTALL=types.ModuleType('sculpt07_C_expanded_install');DIAG_INSTALL.__file__=str(C/'install_design.py');DIAG_INSTALL.DIAG=DIAG
code=(C/'install_design.py').read_text(encoding='utf-8').replace("(P/'preservation.json')","(DIAG/'preservation.json')");exec(compile(code,str(C/'install_design.py'),'exec'),DIAG_INSTALL.__dict__)
recipe=(C/'render_four.py').read_text(encoding='utf-8').split('for fixture in old:')[0].replace('import install_design','install_design=DIAG_INSTALL').replace("(P/'preservation.json')","(DIAG/'preservation.json')")
globals()['__file__']=str(C/'render_four.py');exec(compile(recipe,str(C/'render_four.py'),'exec'),globals())
from mathutils import Vector
DO_RENDER='--render' in sys.argv
OUT=DIAG;shared=dict(native_sha256=NATIVE_SHA,C_parameters_sha256=sha(C/'parameters.json'),C_mesh_sha256=targetsha,actual_design_vertex_array_sha256=fp.digest(design.data.vertices,'co',3),original_owner_fingerprint=original_fingerprint,pose_basis=pose,active_master_keys=keys,actual_mesh_actor_flags=[dict(name=o.name,hide_render=o.hide_render) for o in s.objects if o.type=='MESH'],context_seams='UNVERIFIED; torso-centric framing does not validate whole body or forearm/waist integration.',preservation_sha256=sha(DIAG/'preservation.json'),body_geometry_held=True,head_scale_unchanged=True)
shared_path=OUT/'shared-state.json';shared_path.write_text(json.dumps(shared,indent=2)+'\n',encoding='utf-8');pose_sha=fp.json_digest(pose);keys_sha=fp.json_digest(keys)
jobs=[dict(view='back',yaw=180,pitch=0,resolution=640,scale=.40,target=[0,-.035,1.285],role='v06 corresponding back orientation; covered back inferred; outer contour only'),dict(view='upperoblique',yaw=40,pitch=30,resolution=640,scale=.40,target=[0,-.035,1.285],role='Extra actual upper surface/root inspection; no calibrated source panel'),dict(view='loweropposite',yaw=-40,pitch=-25,resolution=640,scale=.40,target=[0,-.035,1.285],role='Extra actual inferior/root/axilla inspection; no calibrated source panel')]
jobs += [dict(view='orbit-'+str(i).zfill(2),yaw=i*30,pitch=8,resolution=384,scale=.38,target=[0,-.025,1.290],role='Held static design actual orbit; torso-centric, not fullbody/art/animation validation') for i in range(12)]
assert len(jobs)==15;records=[]
for job in jobs:
    target=Vector(job['target']);angle=math.radians(job['yaw']);elev=math.radians(job['pitch']);dist=2.
    cam.location=target+Vector((dist*math.sin(angle)*math.cos(elev),-dist*math.cos(angle)*math.cos(elev),dist*math.sin(elev)));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=job['scale'];s.render.resolution_x=s.render.resolution_y=job['resolution'];bpy.context.view_layer.update()
    assert fp.json_digest({b.name:[list(r) for r in b.matrix_basis] for b in rig.pose.bones})==pose_sha and fp.json_digest({k.name:k.value for k in master.data.shape_keys.key_blocks})==keys_sha
    assert fp.digest(design.data.vertices,'co',3)==shared['actual_design_vertex_array_sha256'] and design.data.materials[0]==gray
    camera=dict(projection=cam.data.type,matrix=[list(r) for r in cam.matrix_world],ortho_scale=cam.data.ortho_scale,clip_start=cam.data.clip_start,clip_end=cam.data.clip_end,resolution=[s.render.resolution_x,s.render.resolution_y],pixel_aspect=[s.render.pixel_aspect_x,s.render.pixel_aspect_y],frame=s.frame_current,yaw=job['yaw'],pitch=job['pitch'])
    lights=[dict(name=o.name,hidden=o.hide_render,matrix=[list(r) for r in o.matrix_world],energy=o.data.energy,size=o.data.size,use_shadow=o.data.use_shadow,shape=o.data.shape,color=list(o.data.color)) for o in s.objects if o.type=='LIGHT'];assert len([l for l in lights if not l['hidden']])==3
    path=OUT/(job['view']+'.png');row=dict(view=job['view'],path=str(path),role=job['role'],camera=camera,shared_state=dict(path=shared_path.name,sha256=sha(shared_path)),actual_pose_sha256=pose_sha,actual_master_keys_sha256=keys_sha,actual_design_vertex_array_sha256=fp.digest(design.data.vertices,'co',3),actual_C_mesh_sha256=targetsha,actual_visible_mesh_actor_names=[o.name for o in s.objects if o.type=='MESH' and not o.hide_render],actual_lights=lights,actual_material_signature=fp.material_signature(gray),actual_transparency_signature=fp.material_signature(transparent),actual_world=dict(color=list(bg.inputs['Color'].default_value),strength=bg.inputs['Strength'].default_value),color_management=old[0]['color_management'],native_saved=False,geometry_changed=False,head_scale_changed=False)
    row['actual_renderer_state_sha256']=fp.json_digest(row)
    if DO_RENDER:
        assert not path.exists();(OUT/(job['view']+'-pre-render.json')).write_text(json.dumps(row,indent=2)+'\n',encoding='utf-8');s.render.filepath=str(path);bpy.ops.render.render(write_still=True);assert row['actual_material_signature']==fp.material_signature(gray);row['sha256']=sha(path)
    records.append(row)
    if DO_RENDER:(OUT/'render-records.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
assert before=={str(f):sha(f) for f in C.rglob('*') if f.is_file() and 'expanded-review' not in f.parts and '__pycache__' not in f.parts} and sha(N)==NATIVE_SHA and install_design.fingerprint(original)==original_fingerprint
if not DO_RENDER:(OUT/'cpu-preparation.json').write_text(json.dumps(dict(planned_frames=15,jobs=jobs,body_geometry_held=True,head_scale_unchanged=True,prior_C_files_unchanged=True,camera_clip=[cam.data.clip_start,cam.data.clip_end],shared_state_sha256=sha(shared_path)),indent=2)+'\n',encoding='utf-8')
print('SCULPT07_C_EXPANDED_ACTUAL15_DONE' if DO_RENDER else 'SCULPT07_C_EXPANDED_CPU15_PREPARED',flush=True)
