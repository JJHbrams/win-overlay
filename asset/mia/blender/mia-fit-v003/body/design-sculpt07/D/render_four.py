"""Exact four inherited gray fixtures; root GPU token required. No native save."""
from pathlib import Path
import json,hashlib,math,sys,importlib.util
import bpy,numpy as np
from mathutils import Vector
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import install_design
CAN=install_design.CAN;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
fpspec=importlib.util.spec_from_file_location('sculpt07_B_renderer_fingerprint',CAN/'blender/mia-fit-v003/body/inputs/scene_fingerprint.py');fp=importlib.util.module_from_spec(fpspec);fpspec.loader.exec_module(fp)
N=CAN/'blender/mia-refinement-v002/integrated/Mia_v0.0.2_Review_R3b.blend';NATIVE_SHA='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1';assert sha(N)==NATIVE_SHA
targetsha=sha(P/'sculpt07-D.npz');audit=json.loads((P/'cpu-audit.json').read_text());assert audit['mesh_sha256']==targetsha and audit['finite'] and audit['connected_components']==1
old=json.loads((CAN/'blender/mia-fit-v003/body/anatomical-patch06/actual-four/render-records.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(N),use_scripts=False);s=bpy.context.scene;s.frame_set(2);s.frame_set(1);bpy.context.view_layer.update()
gray=bpy.data.materials.new('Sculpt07_PhysicalGray');gray.use_nodes=True;n=gray.node_tree.nodes;n.clear();bs=n.new('ShaderNodeBsdfPrincipled');bs.inputs['Base Color'].default_value=(.23,.23,.23,1);bs.inputs['Roughness'].default_value=.85;out=n.new('ShaderNodeOutputMaterial');gray.node_tree.links.new(bs.outputs[0],out.inputs['Surface'])
transparent=bpy.data.materials.new('Sculpt07_ContextTransparentMask');transparent.use_nodes=True;n=transparent.node_tree.nodes;n.clear();tr=n.new('ShaderNodeBsdfTransparent');out=n.new('ShaderNodeOutputMaterial');transparent.node_tree.links.new(tr.outputs[0],out.inputs['Surface'])
design,context,original_fingerprint=install_design.build(gray,transparent);original=bpy.data.objects['MIA_V27_SharedHeadBody']
# Actual evaluated copy correspondence is checked before any rendering; no
# global evaluated prefix is treated as an original raw vertex ID.
def evaluated(ob):
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();a=install_design.coords(me.vertices);ev.to_mesh_clear();return a
bpy.context.view_layer.update();ev0=evaluated(original);ev1=evaluated(context);assert ev0.shape==ev1.shape and np.array_equal(ev0,ev1)
pres=json.loads((P/'preservation.json').read_text());pres.update(private_context_entire_evaluated_surface_exact=True,evaluated_vertices=len(ev0),evaluated_difference_max_m=0.);(P/'preservation.json').write_text(json.dumps(pres,indent=2)+'\n')
osp=importlib.util.spec_from_file_location('sculpt07_component_ownership',CAN/'blender/mia-visible-art-v30/component_ownership.py');own=importlib.util.module_from_spec(osp);osp.loader.exec_module(own)
hair=[]
for o in s.objects:
    if o.type=='MESH' and own.is_hair_object(o):o.hide_render=True;hair.append(o.name)
    if o.type=='LIGHT':o.hide_render=True
lamps=[]
for i,(loc,energy,size) in enumerate([((-1.2,-1.8,2.1),110.,1.3),((1.4,-1.4,1.7),38.,1.4),((0,1.6,2),22.,1.)]):
    data=bpy.data.lights.new('Sculpt07_Gray_'+str(i),'AREA');data.energy=energy;data.shape='DISK';data.size=size;data.use_shadow=True;ob=bpy.data.objects.new(data.name,data);s.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector((0,-.018,1.2))-ob.location).to_track_quat('-Z','Y').to_euler();lamps.append(ob)
w=bpy.data.worlds.new('Sculpt07_GrayWorld');w.use_nodes=True;n=w.node_tree.nodes;n.clear();bg=n.new('ShaderNodeBackground');bg.inputs['Color'].default_value=(.18,.18,.18,1);bg.inputs['Strength'].default_value=.2;out=n.new('ShaderNodeOutputWorld');w.node_tree.links.new(bg.outputs[0],out.inputs['Surface']);s.world=w
cam=bpy.data.objects.new('Sculpt07_ReviewCamera',bpy.data.cameras.new('Sculpt07_ReviewCamera'));s.collection.objects.link(cam);cam.data.type='ORTHO';cam.data.clip_start=.1;cam.data.clip_end=10.;s.camera=cam;s.render.engine='BLENDER_EEVEE';s.render.resolution_percentage=100;s.render.pixel_aspect_x=s.render.pixel_aspect_y=1.;s.render.use_freestyle=False;s.render.film_transparent=False;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA'
for key,value in old[0]['color_management'].items():setattr(s.view_settings,key,value)
rig=bpy.data.objects['MIA_V06_RIG'];master=bpy.data.objects['MIA_V27_Foundation_Face'];pose={b.name:[list(r) for r in b.matrix_basis] for b in rig.pose.bones};keys={k.name:k.value for k in master.data.shape_keys.key_blocks}
O=P/'actual-four-D';O.mkdir(exist_ok=True);records=[];dry='--cpu-only' in sys.argv
for fixture in old:
    view=fixture['view'];spec=fixture['camera'];yaw,pitch=spec['yaw'],spec['pitch'];target=Vector((0,-.035,1.275));dist=2;angle=math.radians(yaw);elev=math.radians(pitch)
    cam.location=target+Vector((dist*math.sin(angle)*math.cos(elev),-dist*math.cos(angle)*math.cos(elev),dist*math.sin(elev)));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.40;s.render.resolution_x=s.render.resolution_y=640;bpy.context.view_layer.update()
    if view=='F2lowoblique':
        source=json.loads((CAN/'blender/mia-fit-v003/body/source-binding/constraints.json').read_text());mpp=source['display_metric']['metres_per_pixel'];center=source['cameras']['F2']['body_axis_pixel_x']-887
        right=Vector((math.cos(angle),math.sin(angle),0));up=Vector((-math.sin(angle)*math.sin(elev),math.cos(angle)*math.sin(elev),math.cos(elev)))
        target=Vector((0,-.018,0))-right*((center-443.5)*mpp);crown=1.692881464958191;target.z=(crown*math.cos(elev)-(443.5-11)*mpp-up.x*target.x-up.y*target.y)/up.z;dist=2.5
        cam.location=target+Vector((dist*math.sin(angle)*math.cos(elev),-dist*math.cos(angle)*math.cos(elev),dist*math.sin(elev)));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=mpp*887;s.render.resolution_x=s.render.resolution_y=887;bpy.context.view_layer.update()
    camera=dict(projection=cam.data.type,matrix=[list(r) for r in cam.matrix_world],ortho_scale=cam.data.ortho_scale,clip_start=cam.data.clip_start,clip_end=cam.data.clip_end,resolution=[s.render.resolution_x,s.render.resolution_y],pixel_aspect=[1,1],frame=s.frame_current,yaw=yaw,pitch=pitch)
    assert camera==spec,(view,'fixture camera differs')
    light=[dict(name=o.name,hidden=o.hide_render,energy=o.data.energy,matrix=[list(r) for r in o.matrix_world],size=o.data.size,use_shadow=o.data.use_shadow,shape=o.data.shape,color=list(o.data.color)) for o in s.objects if o.type=='LIGHT']
    actual=[x for x in light if not x['hidden']];previous=[x for x in fixture['actual_all_light_flags_before_render'] if not x['hidden']]
    assert len(actual)==3
    for a,b in zip(actual,previous):
        assert all(a[k]==b[k] for k in ['energy','size','use_shadow']) and np.max(abs(np.array(a['matrix'])-b['matrix']))<1e-7
    assert install_design.fingerprint(original)==original_fingerprint and design.data.materials[0]==gray and sha(P/'sculpt07-D.npz')==targetsha
    assert pose=={b.name:[list(r) for r in b.matrix_basis] for b in rig.pose.bones} and keys=={k.name:k.value for k in master.data.shape_keys.key_blocks}
    file=O/('gray-'+view+'.png');row=dict(view=view,path=str(file),camera=camera,color_management=fixture['color_management'],native=str(N),native_sha256=NATIVE_SHA,target_data_sha256=targetsha,parameters_sha256=sha(P/'parameters.json'),actual_all_light_flags_before_render=light,actual_design_material=gray.name,actual_design_material_nodes=[dict(type=x.bl_idname,name=x.name) for x in gray.node_tree.nodes],actual_design_material_basecolor=list(bs.inputs['Base Color'].default_value),actual_design_material_roughness=bs.inputs['Roughness'].default_value,world=dict(color=list(bg.inputs['Color'].default_value),strength=bg.inputs['Strength'].default_value),pose_basis=pose,active_master_keys=keys,hairOFF=hair,native_saved=False,status='UNSELECTED NEW STATIC DESIGN; context seams/retopo/UV/keys/weights UNVERIFIED',preservation_sha256=sha(P/'preservation.json'),cpu_audit_sha256=sha(P/'cpu-audit.json'))
    row['actual_material_signature']=fp.material_signature(gray)
    row['actual_transparent_context_material_signature']=fp.material_signature(transparent)
    row['actual_renderer_state_sha256']=fp.json_digest(dict(camera=camera,lights=light,material=row['actual_material_signature'],transparent=row['actual_transparent_context_material_signature'],world=row['world'],color=row['color_management'],engine=s.render.engine,design_mesh_sha256=targetsha))
    if not dry:
        assert not file.exists();(O/('gray-'+view+'-pre-render.json')).write_text(json.dumps(row,indent=2)+'\n');s.render.filepath=str(file);bpy.ops.render.render(write_still=True);row['sha256']=sha(file);assert row['actual_material_signature']==fp.material_signature(gray) and row['actual_transparent_context_material_signature']==fp.material_signature(transparent)
    records.append(row)
    if not dry:(O/'render-records.json').write_text(json.dumps(records,indent=2)+'\n')
assert sha(N)==NATIVE_SHA and len(records)==4 and install_design.fingerprint(original)==original_fingerprint
if dry:(P/'render-preparation.json').write_text(json.dumps(dict(native_unchanged=True,exact_four_cameras=True,lights_match=True,cpu_only=True,preservation_sha256=sha(P/'preservation.json')),indent=2)+'\n')
print('SCULPT07_D_CPU_PREPARED' if dry else 'SCULPT07_D_ACTUAL_FOUR_DONE',flush=True)
