"""Matched WIP8/A2 form-only studio renders without source-image registration."""
import bpy, hashlib, json, math
from pathlib import Path
from mathutils import Vector

HERE=Path(__file__).resolve().parent
BASE=Path(r"C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v22/integration-wip-8-review/Mia_ReferenceFinish_v22.blend")
CANDIDATE=HERE/'candidate-a2/Mia_ReferenceFinish_WIP8_AnatomyA2.blend'
OUT=HERE/'candidate-a2/review';OUT.mkdir(parents=True,exist_ok=True)
SKIN='MIA_V14_SculptedSkin'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def aim(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
def render(native,label):
    bpy.ops.wm.open_mainfile(filepath=str(native),use_scripts=False);s=bpy.context.scene
    for o in s.objects:o.hide_render=(o.name!=SKIN)
    skin=bpy.data.objects[SKIN]
    for key in skin.data.shape_keys.key_blocks:key.value=0
    for o in list(s.objects):
        if o.type=='CAMERA':bpy.data.objects.remove(o,do_unlink=True)
    d=bpy.data.cameras.new('ANATOMY_WORKBENCH_CAMERA');cam=bpy.data.objects.new('ANATOMY_WORKBENCH_CAMERA',d);s.collection.objects.link(cam);s.camera=cam;d.type='ORTHO';d.ortho_scale=.225
    s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.studio_light='paint.sl';s.display.shading.color_type='MATERIAL';s.display.shading.background_type='WORLD';s.display.shading.background_color=(.045,.045,.045);s.display.shading.show_shadows=True;s.display.shading.show_cavity=True;s.display.shading.cavity_type='WORLD';s.display.shading.cavity_ridge_factor=1.2;s.display.shading.cavity_valley_factor=1.2
    s.render.resolution_x=700;s.render.resolution_y=700;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='Standard';s.view_settings.look='None'
    target=(0,.025,1.548);records=[]
    for name,yaw,elev in [('front',0,0),('left_oblique',30,0),('right_oblique',-30,0),('profile',90,0),('low_left',30,-12)]:
        a=math.radians(yaw);cam.location=(math.sin(a)*.72,math.cos(a)*.72,target[2]+math.sin(math.radians(elev))*.18);aim(cam,target)
        p=OUT/f'{label}_{name}.png';s.render.filepath=str(p);bpy.ops.render.render(write_still=True);records.append({'view':name,'yaw':yaw,'elevation':elev,'path':p.name,'sha256':sha(p)})
    return records
b=render(BASE,'wip8');a=render(CANDIDATE,'a2')
(OUT/'render-records.json').write_text(json.dumps({'baseline':{'path':str(BASE),'sha256':sha(BASE)},'candidate':{'path':str(CANDIDATE),'sha256':sha(CANDIDATE)},'records':{'baseline':b,'candidate':a},'mode':'actual Blender workbench studio form render; same camera/display per native; no source fit'},indent=2),encoding='utf-8')
print('A2_WORKBENCH_DONE',len(b),len(a))
