"""Fresh actual render review of one integrated candidate; no native save or art-pass inference."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
import bpy
from mathutils import Vector

p = argparse.ArgumentParser()
p.add_argument('--source', required=True)
p.add_argument('--output-dir', required=True)
a = p.parse_args(sys.argv[sys.argv.index('--')+1:])
src, out = Path(a.source).resolve(), Path(a.output_dir).resolve()
out.mkdir(parents=True, exist_ok=True)
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
original_sha = sha(src)
bpy.ops.wm.open_mainfile(filepath=str(src), use_scripts=False)
s, cam = bpy.context.scene, bpy.context.scene.camera
s.frame_set(1)
s.render.resolution_x = s.render.resolution_y = 896
s.render.resolution_percentage = 100
s.render.pixel_aspect_x = s.render.pixel_aspect_y = 1
cam.data.type, cam.data.shift_x, cam.data.shift_y = 'ORTHO', 0, 0
hair = [o for o in bpy.data.collections['MIA_V17_PIXAL_HAIR'].all_objects if not o.hide_render]
body = bpy.data.objects['MIA_V06_BODY_SKIN']
skin = bpy.data.objects['MIA_V14_SculptedSkin']
records = []
material_mode = 'unchanged production emission-toon; area lights do not define its synthetic shadow'

def aim(obj, point, target):
    obj.location = point
    obj.rotation_euler = (Vector(target)-obj.location).to_track_quat('-Z', 'Y').to_euler()

def render(name, yaw, scale=.48, z=1.555, elevation=0, size=896):
    t, e = math.radians(yaw), math.radians(elevation)
    aim(cam, (2*math.sin(t), -2*math.cos(t), z+2*math.tan(e)), (0,0,z))
    cam.data.ortho_scale = scale
    s.render.resolution_x = s.render.resolution_y = size
    s.render.filepath = str(out/(name+'.png'))
    bpy.ops.render.render(write_still=True)
    records.append({'name':name,'yaw':yaw,'elevation':elevation,'ortho_scale':scale,
                    'target_z':z,'camera_matrix':[list(r) for r in cam.matrix_world],
                    'projection':cam.data.type, 'lens_shift':[cam.data.shift_x,cam.data.shift_y],
                    'pixel_aspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],
                    'resolution':[size,size], 'frame':s.frame_current,
                    'active_shape_keys':{o.name:{k.name:k.value for k in o.data.shape_keys.key_blocks if k.value != 0}
                                         for o in s.objects if o.type=='MESH' and o.data.shape_keys},
                    'material_mode':material_mode,
                    'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,
                               'color':list(o.data.color),'size':getattr(o.data,'size',None),
                               'matrix':[list(r) for r in o.matrix_world]}
                              for o in s.objects if o.type=='LIGHT' and not o.hide_render],
                    'world':s.world.name if s.world else None,
                    'color_management':[s.view_settings.view_transform,s.view_settings.look,s.view_settings.exposure,s.view_settings.gamma]})

for name, yaw in [('front',0),('profile',90),('back',180),('left',45),('right',-45)]:
    render('head_'+name,yaw)
for o in hair: o.hide_render = True
for name, yaw in [('front',0),('profile',90),('left',45),('right',-45)]:
    render('face_'+name,yaw,.29,1.55)

# Neutral geometric inspection: all anatomical skin gets the same diffuse material.
clay = bpy.data.materials.new('V20_DiffuseInspection')
clay.use_nodes = True
nodes = clay.node_tree.nodes
nodes.clear()
diff = nodes.new('ShaderNodeBsdfDiffuse')
diff.inputs['Color'].default_value = (.18,.18,.18,1)
output = nodes.new('ShaderNodeOutputMaterial')
clay.node_tree.links.new(diff.outputs[0],output.inputs['Surface'])
for o in [body,skin]+hair:
    for slot in o.material_slots: slot.material = clay
for o in s.objects:
    if o.type == 'LIGHT': o.hide_render = True
world = bpy.data.worlds.new('V20_InspectionWorld')
world.use_nodes = True
background = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
background.inputs['Color'].default_value = (.18,.18,.18,1)
background.inputs['Strength'].default_value = .1
s.world = world
s.view_settings.view_transform,s.view_settings.look = 'Standard','None'
s.view_settings.exposure,s.view_settings.gamma = 0,1
material_mode = '18% neutral diffuse diagnostic; fixed white area rig, Standard/None, world strength 0.1'
lamps = []
for name in ['Key','Fill','Edge']:
    data = bpy.data.lights.new('V20_'+name,'AREA')
    data.color = (1,1,1)
    data.shape = 'DISK'
    obj = bpy.data.objects.new(data.name,data)
    s.collection.objects.link(obj)
    lamps.append(obj)

def lights(body_mode=False,yaw=0):
    settings = [((-1.8,-3,2.5),200,2.),((2,-2,1.7),70,2.),((0,2,2.3),30,1.8)] if body_mode else [((-.6,-1,2.2),60,1.),((.8,-.8,1.8),15,1.5),((0,.9,2.05),8,.8)]
    t = math.radians(yaw)
    for obj,(loc,energy,size) in zip(lamps,settings):
        x,y,z=loc
        pos=(x*math.cos(t)-y*math.sin(t),x*math.sin(t)+y*math.cos(t),z) if body_mode else loc
        aim(obj,pos,(0,0,.9 if body_mode else 1.555))
        obj.data.energy,obj.data.size=energy,size

lights()
for name,yaw in [('front',0),('left',45),('right',-45),('profile',90)]:
    render('clay_face_'+name,yaw,.29,1.55)
for o in hair: o.hide_render = False
for name,yaw in [('back',180),('profile',90)]:
    render('clay_hair_'+name,yaw,.64,1.46)
for o in hair: o.hide_render = True
for name,yaw in [('front',0),('profile',90),('back',180),('three_quarter',45)]:
    lights(True,yaw)
    render('clay_body_'+name,yaw,1.8894209113,.8397017428,size=1024)
assert sha(src) == original_sha
report={'source':str(src),'source_sha256_before':original_sha,'source_sha256_after':sha(src),
        'native_saved':False,'renders':records,'hair_visible_owners':[o.name for o in hair],
        'body_light_mode':'camera-relative, same v19 whole-body diagnostic powers/sizes',
        'head_light_mode':'fixed world neutral diagnostic rig',
        'limits':'Actual fresh replay only. No image warping; no art or animation approval inferred.'}
(out/'review-evidence.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('V20_FRESH_REVIEW',original_sha,len(records))
