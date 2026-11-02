"""Small standalone construction-only .blend, not a production native copy."""
from pathlib import Path
import hashlib, importlib.util, json, math
import bpy
from mathutils import Vector, Quaternion

P=Path(__file__).resolve().parent
out=P/'Mia_v003_BelowHead_Scaffold_R4.blend'
assert not out.exists(), 'Do not overwrite construction evidence'
assert bpy.data.filepath == '', 'Run only factory-startup in a private process'
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj,do_unlink=True)
def module(name):
    spec=importlib.util.spec_from_file_location(name,P.parent/'body'/(name+'.py'))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
full=module('install_fullbody_scaffold').install()
neck=module('install_neck_supplement').install(full)
full.hide_render=neck.hide_render=False
curves=[o for o in full.all_objects if o.type=='CURVE']
nets=[o for o in full.all_objects if o.type=='MESH']
assert len(curves)==207 and len(nets)==17
for obj in curves:
    obj.hide_render=False
    obj.data.bevel_depth=.00065
    obj.data.bevel_resolution=1
for obj in nets:
    obj.hide_render=True
    obj.hide_set(True)  # Avoid filled guide nets masquerading as skin in Solid.
scene=bpy.context.scene
scene['MiaStage']='CONSTRUCTION GUIDE ONLY; no production body, rig or ART approval'
scene['Reference']='User-confirmed body v06; original aspect; hidden anatomy inferred'
scene['Colors']='cyan observed skin constraints; gold garment envelope; pink inferred; gray occluded; blue structural/current-neck'
scene['Pending']='Continuous fitted surface, source4, neck fit, UV/garments and pose validation. Target01 surface rejected.'
world=bpy.data.worlds.new('Mia_ConstructionWorld');world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.011,.017,.025,1)
scene.world=world
camera=bpy.data.objects.new('Mia_ConstructionCamera',bpy.data.cameras.new('Mia_ConstructionCamera'))
scene.collection.objects.link(camera);camera.data.type='ORTHO';camera.data.ortho_scale=1.63
camera.data.clip_start,camera.data.clip_end=.1,10.
center=Vector((0,0,.735));y,p=math.radians(-35),math.radians(8)
camera.location=center+Vector((4*math.sin(y)*math.cos(p),-4*math.cos(y)*math.cos(p),4*math.sin(p)))
camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler();scene.camera=camera
scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x,scene.render.resolution_y=640,900
scene.render.resolution_percentage=100
scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type!='VIEW_3D':continue
        sp=area.spaces.active;sp.clip_start=.01;sp.clip_end=10.
        sp.shading.type='SOLID';sp.shading.color_type='MATERIAL'
        sp.overlay.show_floor=False;sp.overlay.show_axis_x=False;sp.overlay.show_axis_y=False
        region=sp.region_3d;region.view_location=center;region.view_distance=1.8
        region.view_rotation=camera.rotation_euler.to_quaternion();region.view_perspective='ORTHO'
        sp.camera=camera
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True,check_existing=False)
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
report=dict(path=str(out),sha256=sha(out),bytes=out.stat().st_size,curves=207,control_nets=17,
    production_bodies=0,armatures=0,guide_data_sha256=sha(P.parent/'body/scaffold-fullbody/guide-data.json'),
    neck_data_sha256=sha(P.parent/'body/scaffold-fullbody/neck-supplement.json'),
    selected_production_native_changed=False,art_approved=False)
bpy.ops.wm.open_mainfile(filepath=str(out),use_scripts=False)
assert len([o for o in bpy.data.objects if o.type=='CURVE'])==207
assert len([o for o in bpy.data.objects if o.type=='MESH'])==17
assert not any(o.type=='ARMATURE' for o in bpy.data.objects)
assert all(o.hide_render for o in bpy.data.objects if o.type=='MESH')
assert sha(out)==report['sha256']
report['fresh_reopen_counts_exact']=True
(P/'guide-scene.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('STANDALONE_BELOW_HEAD_GUIDE_SAVED_AND_REOPENED',json.dumps(report),flush=True)
