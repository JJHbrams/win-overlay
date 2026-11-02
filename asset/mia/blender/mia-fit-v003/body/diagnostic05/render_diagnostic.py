"""Exactly four F2 pose/operator diagnostics. Root GPU token required. No save."""
from pathlib import Path
import sys,json,importlib.util,math
import bpy,numpy as np
from mathutils import Matrix,Vector
O=Path(__file__).resolve().parent;P=O.parent
sys.path.insert(0,str(O));sys.path.insert(0,str(P));sys.path.insert(0,str(P/'inputs'))
import rigged05 as diag,install_posed_target_05,scene_fingerprint as fp
guard=json.loads((O/'cpu-guard.json').read_text());assert guard['status'].startswith('CPU PASS')
assert guard['metadata']['target_sha256']==diag.digest(P/'posed-target/target-05.npz')
d=json.loads((P/'current-body-audit.json').read_text());native=Path(d['native']);assert diag.digest(native)==d['sha256']
record=json.loads((P/'posed-target/actual-05/gray-F2oblique-pre-render.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(native),use_scripts=False)
s=bpy.context.scene;s.frame_set(2);s.frame_set(1);bpy.context.view_layer.update()
originals={ob.name:ob.hide_render for ob in bpy.data.objects}
cache={};fingerprints={name:fp.object_fingerprint(bpy.data.objects[name],cache) for name in originals}
source=bpy.data.objects['MIA_V27_SharedHeadBody'];ctx=diag.build(source)
skin=ctx['object'];static=install_posed_target_05.build();frozen=diag.read_surface(static)
q=diag.read_surface(skin);error=np.linalg.norm(q['world']-frozen['world'],axis=1)
assert error.max()<=2e-6
head=frozen['world'][:,2]>=1.465
assert np.array_equal(q['world'][head],frozen['world'][head])
static.hide_render=True;source.hide_render=True
spec=importlib.util.spec_from_file_location('ownership',r'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-visible-art-v30/component_ownership.py')
own=importlib.util.module_from_spec(spec);spec.loader.exec_module(own)
for ob in s.objects:
    if ob.type=='MESH' and own.is_hair_object(ob):ob.hide_render=True
    if ob.type=='LIGHT':ob.hide_render=True
lights=[]
for i,item in enumerate(q for q in record['actual_all_light_flags_before_render'] if not q['hidden']):
    data=bpy.data.lights.new('Diagnostic05Gray'+str(i),'AREA');data.energy=item['energy'];data.shape='DISK';data.size=item['size'];data.use_shadow=item['use_shadow'];data.color=(1,1,1)
    ob=bpy.data.objects.new(data.name,data);s.collection.objects.link(ob);ob.matrix_world=Matrix(item['matrix']);lights.append(ob)
assert [q.data.energy for q in lights]==[110.,38.,22.]
w=bpy.data.worlds.new('Diagnostic05GrayWorld');w.use_nodes=True;n=w.node_tree.nodes;n.clear()
bg=n.new('ShaderNodeBackground');bg.inputs['Color'].default_value=(.18,.18,.18,1);bg.inputs['Strength'].default_value=.2
out=n.new('ShaderNodeOutputWorld');w.node_tree.links.new(bg.outputs[0],out.inputs['Surface']);s.world=w
mat=bpy.data.materials.new('Diagnostic05PhysicalGray');mat.use_nodes=True;n=mat.node_tree.nodes;n.clear()
bs=n.new('ShaderNodeBsdfPrincipled');bs.inputs['Base Color'].default_value=(.23,.23,.23,1);bs.inputs['Roughness'].default_value=.85
out=n.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(bs.outputs[0],out.inputs['Surface']);skin.data.materials[1]=mat
cam=bpy.data.objects.new('Diagnostic05F2',bpy.data.cameras.new('Diagnostic05F2'));s.collection.objects.link(cam)
c=record['camera'];cam.data.type='ORTHO';cam.data.ortho_scale=c['ortho_scale'];cam.data.clip_start=c['clip_start'];cam.data.clip_end=c['clip_end'];s.camera=cam
# Reconstruct the original camera's authored location/Euler recipe. Assigning
# its matrix invokes a fresh decomposition and introduced measurable roundoff.
source_data=json.loads((P/'source-binding/constraints.json').read_text());mpp=source_data['display_metric']['metres_per_pixel'];center=source_data['cameras']['F2']['body_axis_pixel_x']-887
angle=math.radians(40);elev=math.radians(-8);right=Vector((math.cos(angle),math.sin(angle),0));up=Vector((-math.sin(angle)*math.sin(elev),math.cos(angle)*math.sin(elev),math.cos(elev)))
target=Vector((0,-.018,0))-right*((center-443.5)*mpp);crown=1.692881464958191;target.z=(crown*math.cos(elev)-(443.5-11)*mpp-up.x*target.x-up.y*target.y)/up.z;dist=2.5
cam.location=target+Vector((dist*math.sin(angle)*math.cos(elev),-dist*math.cos(angle)*math.cos(elev),dist*math.sin(elev)));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
s.render.engine='BLENDER_EEVEE';s.render.resolution_percentage=100;s.render.resolution_x,s.render.resolution_y=c['resolution'];s.render.pixel_aspect_x=s.render.pixel_aspect_y=1
s.render.use_freestyle=False;s.render.film_transparent=False;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA'
for name in ['view_transform','look','exposure','gamma']:setattr(s.view_settings,name,record['color_management'][name])
OUT=O/'actual-four';OUT.mkdir(exist_ok=True);records=[]
for pose in ['current','source-like']:
    for smooth_on in [True,False]:
        state=diag.set_state(ctx,pose,smooth_on);state['name']=pose+('-smooth-on' if smooth_on else '-smooth-body-off')
        q=diag.read_surface(skin);assert np.array_equal(q['world'][head],frozen['world'][head])
        active=[ob for ob in s.objects if ob.type=='LIGHT' and not ob.hide_render]
        assert set(active)==set(lights) and len(active)==3
        assert skin.data.materials[1] is mat
        assert np.isfinite(np.array(cam.matrix_world)).all()
        assert [list(r) for r in cam.matrix_world]==c['matrix']
        path=OUT/(state['name']+'.png');assert not path.exists()
        state.update(path=str(path),native_sha256=d['sha256'],target_sha256=diag.digest(P/'posed-target/target-05.npz'),
            diagnostic_module_sha256=diag.digest(O/'rigged05.py'),cpu_guard_sha256=diag.digest(O/'cpu-guard.json'),
            camera=c,camera_exact_existing05_F2=True,hair_off=True,body_material=mat.name,
            actual_lights_before_render=[dict(name=ob.name,hidden=ob.hide_render,energy=ob.data.energy,size=ob.data.size,color=list(ob.data.color),matrix=[list(r) for r in ob.matrix_world]) for ob in s.objects if ob.type=='LIGHT'],
            world=dict(color=[.18,.18,.18],strength=.2),gray=dict(base_color=[.23,.23,.23,1],roughness=.85),
            color_management=record['color_management'],head_evaluated_bitexact=True,
            scope='Rejected05 diagnostic; pose and scoped Smooth changed independently. No anatomical improvement or motion-rig claim.',native_saved=False)
        (OUT/(state['name']+'-pre-render.json')).write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
        s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
        assert skin.data.materials[1] is mat
        state['sha256']=diag.digest(path);records.append(state)
        (OUT/'render-records.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
        print('DIAGNOSTIC05_FRAME_DONE',state['name'],str(path),flush=True)
diag.set_state(ctx,'current',True)
for name,hidden in originals.items():bpy.data.objects[name].hide_render=hidden
cache={}
for name,before in fingerprints.items():assert fp.object_fingerprint(bpy.data.objects[name],cache)==before,('Original mutated',name)
assert len(records)==4 and diag.digest(native)==d['sha256']
(OUT/'completion.json').write_text(json.dumps(dict(frames=4,original_objects_exact=len(fingerprints),original47_rig_rest_and_pose_exact=True,native_unchanged=True,native_saved=False,rejected05_not_selected=True),indent=2)+'\n')
print('REJECTED05_F2_POSE_SMOOTH_ACTUAL4_DONE original data and native unchanged',flush=True)
