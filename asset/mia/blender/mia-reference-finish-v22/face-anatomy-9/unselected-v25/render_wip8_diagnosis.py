"""Actual WIP8 neutral-clay diagnosis views; does not save the source native."""
import bpy, hashlib, json, math
from pathlib import Path
from mathutils import Vector

HERE=Path(__file__).resolve().parent
SOURCE=Path(r"C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v22/integration-wip-8-review/Mia_ReferenceFinish_v22.blend")
OUT=HERE/'diagnosis-wip8'; OUT.mkdir(exist_ok=True)
SKIN='MIA_V14_SculptedSkin'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def aim(obj,target): obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()

bpy.ops.wm.open_mainfile(filepath=str(SOURCE),use_scripts=False)
scene=bpy.context.scene
for obj in scene.objects:
    obj.hide_render = obj.name != SKIN
skin=bpy.data.objects[SKIN]
for key in skin.data.shape_keys.key_blocks:key.value=0
skin.data.materials.clear()
mat=bpy.data.materials.new('WIP8_ANATOMY_CLAY');mat.use_nodes=True
node=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');node.inputs['Base Color'].default_value=(.53,.53,.53,1);node.inputs['Roughness'].default_value=.86
skin.data.materials.append(mat)
for obj in list(scene.objects):
    if obj.type in {'CAMERA','LIGHT'}: bpy.data.objects.remove(obj,do_unlink=True)
cam_data=bpy.data.cameras.new('WIP8_ANATOMY_CAMERA');cam=bpy.data.objects.new('WIP8_ANATOMY_CAMERA',cam_data);scene.collection.objects.link(cam);scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.225
world=scene.world or bpy.data.worlds.new('World');scene.world=world;world.use_nodes=True
bg=next((n for n in world.node_tree.nodes if n.type=='BACKGROUND'),None) or world.node_tree.nodes.new('ShaderNodeBackground');bg.inputs['Color'].default_value=(.015,.015,.015,1);bg.inputs['Strength'].default_value=.12
for name,loc,energy,size in [('key',(.32,.40,1.91),650,.36),('fill',(-.28,.25,1.71),180,.5),('rim',(0,-.36,1.82),120,.4)]:
    data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.shape='DISK';data.size=size;lamp=bpy.data.objects.new(name,data);scene.collection.objects.link(lamp);lamp.location=loc;aim(lamp,(0,.025,1.55))
scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=700;scene.render.resolution_y=700;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
target=(0,.025,1.548);records=[]
for name,yaw,elev in [('front',0,0),('left_oblique',30,0),('right_oblique',-30,0),('profile',90,0),('low_left',30,-12)]:
    a=math.radians(yaw);cam.location=(math.sin(a)*.72,math.cos(a)*.72,target[2]+math.sin(math.radians(elev))*.18);aim(cam,target)
    path=OUT/f'wip8_{name}.png';scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);records.append({'view':name,'yaw':yaw,'elevation':elev,'path':path.name,'sha256':sha(path)})
(OUT/'render-records.json').write_text(json.dumps({'native':{'path':str(SOURCE),'sha256':sha(SOURCE)},'records':records,'mode':'actual neutral clay; skin only; fixed WIP8 camera/light for form diagnosis; source native never saved'},indent=2),encoding='utf-8')
assert sha(SOURCE)=='ff2b61b2b2146fc4f73119cf10534571609dff75f6333fbec34d0926068b8bb4'
print('WIP8_DIAGNOSIS_RENDERS',len(records))
