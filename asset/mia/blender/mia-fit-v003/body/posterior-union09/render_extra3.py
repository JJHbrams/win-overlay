"""Root's verification increase: EXACTLY3 frozen E front-root views, same09."""
from pathlib import Path
import sys,json,hashlib,math
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent;EXTRA=ROOT/'actual-extra3';EXTRA.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
held8={str(p):sha(p) for p in (ROOT/'actual8').rglob('*') if p.is_file()}
for name in ['actual8.log','render_actual8.py','render-preparation.json','preservation.json','posterior09.npz']:held8[str(ROOT/name)]=sha(ROOT/name)
prefix=(ROOT/'render_actual8.py').read_text(encoding='utf-8').split('prior_audit=')[0]
prefix=prefix.replace('INSTALL.OUT=OUT','INSTALL.OUT=OUT;INSTALL.EXTRA=EXTRA')
prefix=prefix.replace("install_code=(OUT/'install_design.py').read_text(encoding='utf-8')","install_code=(OUT/'install_design.py').read_text(encoding='utf-8').replace(\"(P/'preservation.json')\",\"(EXTRA/'preservation.json')\")")
prefix=prefix.replace("(OUT/'preservation.json')","(EXTRA/'preservation.json')").replace("O=OUT/'actual8'","O=EXTRA").replace("'OUT':OUT,'__name__'","'OUT':OUT,'EXTRA':EXTRA,'__name__'")
exec(compile(prefix,str(ROOT/'render_actual8.py'),'exec'),globals())
prior=json.loads((E/'actual-E/render-records.json').read_text(encoding='utf-8'));jobs=['F2lowoblique','upperoblique','loweropposite'];records=[];dry='--cpu-only' in sys.argv
if not dry:assert not (EXTRA/'render-records.json').exists()
for view in jobs:
    previous=next(r for r in prior if r['view']==view);spec=previous['camera'];yaw,pitch=spec['yaw'],spec['pitch'];angle=math.radians(yaw);elev=math.radians(pitch)
    target=Vector((0,-.035,1.285 if view in ['upperoblique','loweropposite'] else 1.275));dist=2
    cam.location=target+Vector((dist*math.sin(angle)*math.cos(elev),-dist*math.cos(angle)*math.cos(elev),dist*math.sin(elev)));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.40;s.render.resolution_x=s.render.resolution_y=640;bpy.context.view_layer.update()
    if view=='F2lowoblique':
        source=json.loads((CANONICAL/'blender/mia-fit-v003/body/source-binding/constraints.json').read_text(encoding='utf-8'));mpp=source['display_metric']['metres_per_pixel'];center=source['cameras']['F2']['body_axis_pixel_x']-887
        right=Vector((math.cos(angle),math.sin(angle),0));up=Vector((-math.sin(angle)*math.sin(elev),math.cos(angle)*math.sin(elev),math.cos(elev)))
        target=Vector((0,-.018,0))-right*((center-443.5)*mpp);crown=1.692881464958191;target.z=(crown*math.cos(elev)-(443.5-11)*mpp-up.x*target.x-up.y*target.y)/up.z;dist=2.5
        cam.location=target+Vector((dist*math.sin(angle)*math.cos(elev),-dist*math.cos(angle)*math.cos(elev),dist*math.sin(elev)));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=mpp*887;s.render.resolution_x=s.render.resolution_y=887
    design.data.materials[0]=gray
    for i in range(len(context.data.materials)-1):context.data.materials[i]=gray
    bpy.context.view_layer.update();camera=dict(projection=cam.data.type,matrix=[list(r) for r in cam.matrix_world],ortho_scale=cam.data.ortho_scale,clip_start=cam.data.clip_start,clip_end=cam.data.clip_end,resolution=[s.render.resolution_x,s.render.resolution_y],pixel_aspect=[1,1],frame=s.frame_current,yaw=yaw,pitch=pitch)
    assert camera==spec,(view,'camera differs');actual=np.asarray([v.co[:] for v in design.data.vertices],np.float32)
    assert np.array_equal(actual,data['world']) and np.array_equal(evaluated(design),data['world'])
    assert fp.material_signature(gray)==previous['actual_material_signature']
    assert INSTALL.fingerprint(original)==original_fingerprint and np.array_equal(evaluated(original),evaluated(context))
    assert pose=={b.name:[list(r) for r in b.matrix_basis] for b in rig.pose.bones} and keys=={k.name:k.value for k in master.data.shape_keys.key_blocks}
    lights=[dict(name=o.name,hidden=o.hide_render,energy=o.data.energy,size=o.data.size,use_shadow=o.data.use_shadow,matrix=[list(r) for r in o.matrix_world]) for o in s.objects if o.type=='LIGHT']
    for a,b in zip(lights,previous['actual_all_light_flags_before_render']):assert all(a[k]==b[k] for k in ['hidden','energy','size','use_shadow']) and np.max(abs(np.array(a['matrix'])-b['matrix']))<1e-7
    path=EXTRA/('09-gray-'+view+'.png');row=dict(state='09_UNSELECTED_coupled_front_verification',view=view,mode='gray',path=str(path),camera=camera,
        baseline_E_render=dict(path=previous['path'],sha256=previous['sha256']),payload_sha256=payload_sha,actual_private_vertex_sha256=hashlib.sha256(actual.tobytes()).hexdigest(),
        actual_evaluated_private_vertex_sha256=hashlib.sha256(evaluated(design).tobytes()).hexdigest(),actual_material_signature=fp.material_signature(gray),actual_transparency_signature=fp.material_signature(transparent),actual_lights=lights,
        actual_pose_sha256=fp.json_digest(pose),actual_keys_sha256=fp.json_digest(keys),world=dict(color=list(bg.inputs['Color'].default_value),strength=bg.inputs['Strength'].default_value),color_management=previous['color_management'],native_sha256=NATIVE_SHA,
        original47_and_Face690_exact=True,entire_evaluated_original_context_exact=True,native_saved=False,head_scale_changed=False,renderer_sha256=sha(ROOT/'render_extra3.py'),initial_eight_unchanged=True)
    if not dry:
        assert not path.exists();(EXTRA/(path.stem+'-pre-render.json')).write_text(json.dumps(row,indent=2)+'\n',encoding='utf-8',newline='\n');s.render.filepath=str(path);bpy.ops.render.render(write_still=True);row['sha256']=sha(path)
        assert np.array_equal(evaluated(design),data['world']) and fp.material_signature(gray)==row['actual_material_signature']
        records.append(row);(EXTRA/'render-records.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8',newline='\n');print('POSTERIOR09_EXTRA_ACTUAL '+view,flush=True)
    else:records.append(row)
for path,h in held8.items():assert sha(path)==h,('Initial8 file changed',path)
for path,h in protected.items():assert sha(path)==h
assert sha(N)==NATIVE_SHA and sha(payload)==payload_sha and len(records)==3
if dry:(EXTRA/'render-preparation.json').write_text(json.dumps(dict(status='CPU exact3 camera/material/light/mesh/context PASS',jobs=records,initial8_hashes=held8,render_called=False),indent=2)+'\n',encoding='utf-8',newline='\n')
print('POSTERIOR09_EXTRA3_CPU_PASS' if dry else 'POSTERIOR09_EXTRA3_DONE_GPU_RELEASE',flush=True)
