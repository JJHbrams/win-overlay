"""Render the actual complete below-head construction guide, never a body PASS.

Run in a private Blender process. Native bytes are read only; no save or live
scene access. The --body-root option allows reviewing a producer checkpoint
before integration. No source illustration is generated or reshaped here.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, json, math, sys
import bpy
from mathutils import Vector

P = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--body-root', type=Path, default=P.parent/'body')
args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
body = args.body_root.resolve()
native = P.parents[1]/'mia-refinement-v002/integrated/Mia_v0.0.2_Review_R3b.blend'
expected = '4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'
sha = lambda f: hashlib.sha256(Path(f).read_bytes()).hexdigest()
assert sha(native) == expected
bpy.ops.wm.open_mainfile(filepath=str(native), use_scripts=False)
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
original_ids = {o.name for o in bpy.data.objects}
for obj in scene.objects:
    obj.hide_render = True

def module(name):
    spec = importlib.util.spec_from_file_location(name, body/(name+'.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

full = module('install_fullbody_scaffold').install()
neck = module('install_neck_supplement').install(full)
full.hide_render = False
neck.hide_render = False
guide = [o for o in full.all_objects if o.type == 'CURVE']
for obj in guide:
    obj.hide_render = False
    obj.data.bevel_resolution = 1
    obj.data.bevel_depth = .00065
assert len(guide) == 207  #191 fullbody +16 explicit neck curves
assert all(o.get('guide_only') for o in guide)
assert all(o.hide_render for o in full.all_objects if o.type == 'MESH')

world = bpy.data.worlds.new('V003_GuideOnlyWorld')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (.011,.017,.025,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = .8
scene.world = world
cam = bpy.data.objects.new('V003_CompleteGuideReview', bpy.data.cameras.new('V003_CompleteGuideReview'))
scene.collection.objects.link(cam)
cam.data.type = 'ORTHO'
cam.data.ortho_scale = 1.63
cam.data.clip_start, cam.data.clip_end = .1, 10.
scene.camera = cam
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = 640, 900
scene.render.resolution_percentage = 100
scene.render.pixel_aspect_x = scene.render.pixel_aspect_y = 1.
scene.render.use_freestyle = False
scene.render.film_transparent = False
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'None'
scene.view_settings.exposure = 0.
scene.view_settings.gamma = 1.
out = P/'actual-R4-neck'
out.mkdir(exist_ok=True)
records = []
for view, yaw, pitch in [('front',0,0), ('oblique',-35,8)]:
    center = Vector((0,0,.735))
    y, p = math.radians(yaw), math.radians(pitch)
    cam.location = center + Vector((4*math.sin(y)*math.cos(p),-4*math.cos(y)*math.cos(p),4*math.sin(p)))
    cam.rotation_euler = (center-cam.location).to_track_quat('-Z','Y').to_euler()
    bpy.context.view_layer.update()
    file = out/(view+'.png')
    assert not file.exists(), 'Evidence is append-only'
    scene.render.filepath = str(file)
    bpy.ops.render.render(write_still=True)
    records.append(dict(view=view, path=str(file), sha256=sha(file), native_sha256=expected,
        guide_data_sha256=sha(body/'scaffold-fullbody/guide-data.json'),
        neck_data_sha256=sha(body/'scaffold-fullbody/neck-supplement.json'),
        curves_rendered=len(guide), construction_meshes_rendered=0,
        camera=dict(projection='ORTHO', matrix=[list(r) for r in cam.matrix_world],
            ortho_scale=cam.data.ortho_scale, clip_start=.1, clip_end=10.,
            resolution=[640,900], pixel_aspect=[1,1], yaw=yaw,pitch=pitch),
        original_objects_rendered=0, native_saved=False,
        limitation='Actual source-constrained inferred3D construction only; no fitted body/anatomy/art or motion-rig approval. Occluded dimensions remain uncertain.'))
    (out/'render-records.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
assert sha(native) == expected
assert original_ids.issubset({o.name for o in bpy.data.objects})
print('COMPLETE_BELOW_HEAD_GUIDE_ACTUAL_DONE',len(records),flush=True)
