"""Root-token eight UNSAVED component gray/seam actuals, originalsavedR3b actors."""
from pathlib import Path
import sys,json,hashlib,math
import bpy,numpy as np
from mathutils import Vector
sys.dont_write_bytecode=True;P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import install_review
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();digest=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()
assert json.loads((P/'CPU-static-C-proof.json').read_text())['new_open_or_nonmanifold_edges']==0
control=json.loads((P/'head-normal-roundtrip-control-C.json').read_text());assert control['max_angle_degrees']<.05 and control['max_vector_error']<8e-4
O=P/'seam-preflight-C4';O.mkdir(exist_ok=True);assert not (O/'render-records.json').exists(),'Do not overwriteactualpreflight'
body,proof=install_review.apply(proof_path=O/'installed-source-proof.json',geometry_path=P/'joined-geometric-C.npz',packing_path=O/'head-normal-packing.json');scene=bpy.context.scene;original=bpy.data.objects['MIA_V27_SharedHeadBody'];rig=bpy.data.objects['MIA_V06_RIG'];pose={b.name:[list(r) for r in b.matrix_basis] for b in rig.pose.bones};keys={k.name:k.value for k in original.data.shape_keys.key_blocks}
for o in scene.objects:
    if o.type=='LIGHT':o.hide_render=True
for name,pos,energy,size in [('Review12_Key',(-3,-4,4),650,3),('Review12_Fill',(3,-2,2.5),280,4),('Review12_Rim',(1,3,3.5),450,3)]:
    data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.shape='DISK';data.size=size;o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,1.0))-o.location).to_track_quat('-Z','Y').to_euler()
world=bpy.data.worlds.new('Review12_GrayWorld');world.use_nodes=True;bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.18,.18,.18,1);bg.inputs['Strength'].default_value=.2;scene.world=world
camera=bpy.data.cameras.new('Review12_ActualCamera');camera.type='ORTHO';camera.clip_start=.1;camera.clip_end=10;cam=bpy.data.objects.new(camera.name,camera);scene.collection.objects.link(cam);scene.camera=cam
scene.render.engine='BLENDER_EEVEE';scene.render.resolution_percentage=100;scene.render.pixel_aspect_x=scene.render.pixel_aspect_y=1;scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False;scene.frame_set(1)
hair=[]
for ob in scene.objects:
    if ob.type!='MESH' or ob.hide_render:continue
    text=ob.name.lower()+' '+' '.join(m.name.lower() for m in ob.data.materials if m)
    if any(t in text for t in ['hair','braid','crown','gather','rootlining','rimflow']):hair.append(ob)
hairflags={ob.name:ob.hide_render for ob in hair}
jobs=[('neck-oblique',40,10,(0,-.005,1.43),.24,(800,800),False),('waist-profile',85,0,(0,-.015,1.075),.26,(800,800),False),('arm-rear',140,0,(.235,-.005,1.15),.20,(800,800),False),('full-oblique',40,0,(0,-.015,.87),1.9,(640,900),True)]
rows=[];worlddata=np.load(P/'joined-geometric-C.npz')['world'];tri=np.load(P/'joined-geometric-C.npz')['triangles'];nativehash=sha(bpy.data.filepath)
for view,yaw,pitch,target,scale,res,hairOn in jobs:
    for ob in hair:ob.hide_render=hairflags[ob.name] if hairOn else True
    target=Vector(target);a,b=math.radians(yaw),math.radians(pitch);cam.location=target+Vector((3*math.sin(a)*math.cos(b),-3*math.cos(a)*math.cos(b),3*math.sin(b)));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();camera.ortho_scale=scale;scene.render.resolution_x,scene.render.resolution_y=res;bpy.context.view_layer.update()
    assert original.hide_render and np.array_equal(np.asarray([v.co[:] for v in body.data.vertices],np.float32),worlddata)
    assert pose=={b.name:[list(r) for r in b.matrix_basis] for b in rig.pose.bones} and keys=={k.name:k.value for k in original.data.shape_keys.key_blocks}
    lights=[dict(name=o.name,energy=o.data.energy,size=o.data.size,matrix=[list(r) for r in o.matrix_world]) for o in scene.objects if o.type=='LIGHT' and not o.hide_render]
    spec=dict(projection='ORTHO',matrix=[list(r) for r in cam.matrix_world],ortho_scale=camera.ortho_scale,clip_start=camera.clip_start,clip_end=camera.clip_end,frame=scene.frame_current,resolution=list(res),pixel_aspect=[1,1],lens_shift=[camera.shift_x,camera.shift_y],yaw=yaw,pitch=pitch,active_shape_keys=keys,lighting=lights,color_management={k:getattr(scene.view_settings,k) for k in ['view_transform','look','exposure','gamma']})
    file=O/(view+'.png');row=dict(view=view,path=str(file),source_native=dict(path=bpy.data.filepath,sha256=nativehash),unsaved_component_payload=dict(path=str(P/'joined-geometric-C.npz'),sha256=sha(P/'joined-geometric-C.npz')),world_sha256=install_review.ah(worlddata),triangles_sha256=install_review.ah(tri),camera=spec,
        material='ActualPrincipledgray.23/roughness.85 BODYONLY; savedR3b head/face/hair materialroutes retained.',hair_visible=hairOn,hidden_hair_actor_names=[] if hairOn else [o.name for o in hair],pose_sha256=digest(pose),head_source_preservation=proof['status'],
        head_normal_API_precision=control,original_source_torso_hidden=True,no_transparency_body_mask=True,native_saved=False,provenance='UNSAVEDstaticcomponent seam preflight onfreshR3b; never relabelasfinalReview12native render.')
    (O/(view+'-pre-render.json')).write_text(json.dumps(row,indent=2)+'\n',encoding='utf-8',newline='\n');scene.render.filepath=str(file);bpy.ops.render.render(write_still=True);row['sha256']=sha(file);rows.append(row);(O/'render-records.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8',newline='\n');print('REVIEW12_C4_ACTUAL '+view,flush=True)
assert len(rows)==4 and sha(bpy.data.filepath)==nativehash
print('REVIEW12_C4_DONE_GPU_RELEASE',flush=True)
