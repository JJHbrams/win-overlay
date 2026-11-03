"""Explicit actual capture modes; no geometry changes or native saves.

prefly: fresh R3b + selected static component, unsaved provenance.
orbit/diagnostics: must open saved Review12. baseline: must open original R3b.
GPU invocation requires the root's batch grant.
"""
from pathlib import Path
import sys,json
import bpy,numpy as np
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import review_fixture as fixture
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
assert 1<=len(args)<=4 and args[0] in ['prefly','orbit','diagnostics','baseline']
mode=args[0];native=Path(bpy.data.filepath);native_sha=fixture.sha(native);saved=mode in ['orbit','diagnostics'];config=json.loads((P/'selected-review.json').read_text())
outputName=args[1] if len(args)>1 else {'prefly':'material-preflight','orbit':'actual-orbit','diagnostics':'actual-diagnostics','baseline':'actual-baseline4'}[mode]
assert Path(outputName).name==outputName and '..' not in outputName
if len(args)>3:assert mode=='prefly';config['maps']=args[3]
O=P/outputName;O.mkdir(exist_ok=True);assert not (O/'render-records.json').exists(),'Never overwrite frozen actuals'
api=None;bodies={};material_proof=None
surfaceMeta=json.loads((P/config['surface']).with_suffix('.json').read_text());geometrySpec=dict(geometry_file_sha256=config['geometry_sha256'],surface_file_sha256=config['surface_sha256'],world_sha256=surfaceMeta['geometry_world_sha256'],body_triangles_sha256=surfaceMeta['triangles_sha256'],ReviewUV_sha256=surfaceMeta['loop_uv_sha256'])
if mode=='prefly':
    import build_review_native as builder
    scenes,bodies,mats,api,material_proof=builder.build_scenes(config,P/(outputName+'-proof'))
else:
    if saved:
        assert native_sha==json.loads((P/'native/native-save.json').read_text())['sha256'],'Saved-native source mismatch'
        assert (P/'native/reopen-proof.json').exists(),'Fresh reopen verification required'
        scenes={name:bpy.data.scenes[name] for name in ['SkinOnly','Underwear']}
        bodies={name:next(o for o in scenes[name].objects if o.get('MIA12_static_review_body')) for name in scenes}
        import build_review_native as builder
        api=builder.appearance_api(config);mats={name:bodies[name].material_slots[12].material for name in scenes}
    else:
        assert native_sha=='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'
        scenes={'R3bOriginal':bpy.context.scene};fixture.setup(bpy.context.scene);mats={}
jobs=[]
if mode=='orbit':
    for state in ['SkinOnly','Underwear']:
        for k in range(32):jobs.append(dict(name=f'{state}-{k:02d}',state=state,yaw=k*360/32,hair=True,index=k))
elif mode=='baseline':
    for name,yaw in [('front',0),('profile',90),('back',180),('oblique',30)]:jobs.append(dict(name=name,state='R3bOriginal',yaw=yaw,hair=False))
elif mode=='prefly':
    for state in ['SkinOnly','Underwear']:
        for name,yaw in [('front',0),('back',180),('oblique',45)]:jobs.append(dict(name=state+'-'+name,state=state,yaw=yaw,hair=False))
    jobs.extend([dict(name='neck-BODYcolorOnly-clavicleOFF',state='SkinOnly',yaw=35,hair=False,close='neck',color_only=True,clavicle=0),dict(name='clavicle-on',state='Underwear',yaw=0,hair=False,close='clavicle',clavicle=1),dict(name='clavicle-off',state='Underwear',yaw=0,hair=False,close='clavicle',clavicle=0),dict(name='clavicle-moved-light',state='Underwear',yaw=0,hair=False,close='clavicle',clavicle=1,moved_light=True)])
else:
    for name,yaw in [('front',0),('profile',90),('back',180),('oblique',30)]:jobs.append(dict(name='hairOFF-'+name,state='Underwear',yaw=yaw,hair=False))
    jobs.extend([dict(name='clavicle-ON',state='Underwear',yaw=0,hair=False,close='clavicle',clavicle=1),dict(name='clavicle-OFF',state='Underwear',yaw=0,hair=False,close='clavicle',clavicle=0),dict(name='neck-colorOnly-clavicleOFF',state='SkinOnly',yaw=35,hair=False,close='neck',color_only=True,clavicle=0),dict(name='clavicle-moved-light',state='Underwear',yaw=0,hair=False,close='clavicle',clavicle=1,moved_light=True)])
if len(args)>2:
    requested=args[2].split(',');assert set(requested)<=set(j['name'] for j in jobs);jobs=[j for j in jobs if j['name'] in requested];assert len(jobs)==len(requested)
rows=[];baselineGeometry=fixture.original_body_geometry(bpy.context.scene) if mode=='baseline' else None
for job in jobs:
    scene=scenes[job['state']]
    if bpy.context.window:bpy.context.window.scene=scene
    fixture.hair_visibility(scene,job['hair'])
    if api:
        api.set_controls(mats[job['state']],clavicle_strength=job.get('clavicle',1),color_only=job.get('color_only',False))
    if job.get('close'):
        target=(0,-.005,1.43) if job['close']=='neck' else (0,-.02,1.395)
        fixture.aim(scene,job['yaw'],pitch=5,target=target,scale=.26 if job['close']=='neck' else .34,resolution=(800,800))
    else:fixture.aim(scene,job['yaw'])
    key=bpy.data.objects.get(fixture.PREFIX+'Key');old_key=key.matrix_world.copy() if key else None
    if job.get('moved_light'):key.location.x=3;key.rotation_euler=(__import__('mathutils').Vector((0,0,1))-key.location).to_track_quat('-Z','Y').to_euler();bpy.context.view_layer.update()
    if bodies:
        data=np.load(P/config['geometry']);assert np.array_equal(np.asarray([v.co[:] for v in bodies[job['state']].data.vertices],np.float32),data['world']);data.close()
    file=O/(job['name']+'.png');record=dict(job=job,scene=scene.name,actual_source_native=dict(path=str(native),sha256=native_sha),saved_review_native=saved,unsaved_component_payload=None if saved or mode=='baseline' else dict(path=config['geometry'],sha256=config['geometry_sha256']),geometry=baselineGeometry if mode=='baseline' else geometrySpec,fixture=fixture.record(scene),material=api.audit_material(mats[job['state']]) if api else 'Original savedR3b shader routes; same final camera/world/light/pose fixture',diagnostic_scope='BODY ONLY ColorOnly; original face stays lit, not a global pure-pigment comparison' if job.get('color_only') else None,scope='Static fullbody review, no head scaling or production rig claim',path=str(file))
    if api:record['material_image_dimensions']=[dict(role=n.get('mia12_role'),size=list(n.image.size)) for n in mats[job['state']].node_tree.nodes if n.type=='TEX_IMAGE' and n.image]
    scene.render.filepath=str(file);bpy.ops.render.render(write_still=True,scene=scene.name);record['sha256']=fixture.sha(file);rows.append(record);(O/'render-records.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8',newline='\n')
    if key is not None and old_key is not None:key.matrix_world=old_key
    print('REVIEW12_ACTUAL',mode,job['name'],flush=True)
assert fixture.sha(native)==native_sha
print('REVIEW12_CAPTURE_DONE_GPU_RELEASE',mode,len(rows),flush=True)
