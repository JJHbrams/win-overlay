"""Render the F2 baseline and A1 candidate with a neutral clay rig.

The images are for form reading only.  No source-art projection, camera fitting or
texture painting is used here.
"""
import bpy
import hashlib
import json
import math
import sys
from pathlib import Path
from mathutils import Vector

HERE = Path(__file__).resolve().parent
BASELINE = Path(r"C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v22/parts/face-finish8-f2-review/native/6d0672ae12ea-Mia_FaceFinish8_ConnectedBuccalF2.blend")
CANDIDATE = HERE / "candidate-a1/Mia_FaceAnatomy25_OrbitalMalarBridgeA1.blend"
OUTPUT = HERE / "candidate-a1/review"
OUTPUT.mkdir(parents=True, exist_ok=True)
SKIN = "MIA_V14_SculptedSkin"

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def aim(obj, target): obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z','Y').to_euler()
def clear_scene(scene):
    for obj in scene.objects:
        if obj.type in {'LIGHT','CAMERA'} or obj.name != SKIN:
            obj.hide_render = True
    for obj in list(scene.objects):
        if obj.type in {'LIGHT','CAMERA'}:
            bpy.data.objects.remove(obj, do_unlink=True)
def setup(scene):
    clear_scene(scene)
    skin = bpy.data.objects[SKIN]
    for key in skin.data.shape_keys.key_blocks: key.value = 0.0
    clay = bpy.data.materials.new("ANATOMY_NEUTRAL_CLAY")
    clay.diffuse_color = (0.54,0.54,0.54,1)
    clay.use_nodes=True
    bsdf=next((node for node in clay.node_tree.nodes if node.type=='BSDF_PRINCIPLED'),None); bsdf.inputs['Base Color'].default_value=(0.54,0.54,0.54,1); bsdf.inputs['Roughness'].default_value=.82
    skin.data.materials.clear(); skin.data.materials.append(clay)
    cam_data=bpy.data.cameras.new('ANATOMY_REVIEW_CAMERA'); cam=bpy.data.objects.new('ANATOMY_REVIEW_CAMERA',cam_data); scene.collection.objects.link(cam); scene.camera=cam
    cam.data.type='ORTHO'; cam.data.ortho_scale=.225
    world=scene.world or bpy.data.worlds.new('World'); scene.world=world; world.use_nodes=True
    background=next((node for node in world.node_tree.nodes if node.type=='BACKGROUND'),None)
    if background is None: background=world.node_tree.nodes.new('ShaderNodeBackground')
    background.inputs['Color'].default_value=(0.018,0.018,0.018,1); background.inputs['Strength'].default_value=.18
    for name,loc,energy,size in [('key',(0.32,0.38,1.92),650,.36),('fill',(-.28,.25,1.72),200,.5),('rim',(0,-.36,1.82),160,.4)]:
        data=bpy.data.lights.new(name,'AREA'); data.energy=energy; data.shape='DISK'; data.size=size; lamp=bpy.data.objects.new(name,data); scene.collection.objects.link(lamp); lamp.location=loc; aim(lamp,(0,.02,1.55))
    scene.render.engine='BLENDER_EEVEE'; scene.render.resolution_x=700; scene.render.resolution_y=700; scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'; scene.render.film_transparent=False
    scene.view_settings.look='None'; scene.view_settings.view_transform='Standard'
    return cam
def render(native,label):
    bpy.ops.wm.open_mainfile(filepath=str(native)); scene=bpy.context.scene; cam=setup(scene); target=(0,.026,1.548); records=[]
    for name,yaw,elev in [('front',0,0),('left_oblique',30,0),('right_oblique',-30,0),('profile',90,0),('low_front',0,-12),('low_left',30,-12)]:
        r=.72; a=math.radians(yaw); cam.location=(math.sin(a)*r, math.cos(a)*r, target[2]+math.sin(math.radians(elev))*.18); aim(cam,target)
        path=OUTPUT/f'{label}_{name}.png'; scene.render.filepath=str(path); bpy.ops.render.render(write_still=True)
        records.append({'view':name,'yaw':yaw,'elevation':elev,'path':path.name,'sha256':sha(path)})
    return records
base=render(BASELINE,'f2'); candidate=render(CANDIDATE,'a1')
(OUTPUT/'render-records.json').write_text(json.dumps({'baseline':{'path':str(BASELINE),'sha256':sha(BASELINE)},'candidate':{'path':str(CANDIDATE),'sha256':sha(CANDIDATE)},'records':{'baseline':base,'candidate':candidate},'scope':'Actual Blender neutral-clay render. Fixed camera/light setup per native; no source registration or per-view mesh fit.'},indent=2),encoding='utf-8')
print('ANATOMY_REVIEW_DONE',len(base),len(candidate))
