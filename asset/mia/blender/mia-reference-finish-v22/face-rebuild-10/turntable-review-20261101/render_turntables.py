"""Render the frozen current Mia native; never save or alter the source file."""
import argparse, hashlib, json, math, sys
from pathlib import Path
import bpy
from mathutils import Vector

ap=argparse.ArgumentParser()
ap.add_argument('--native',required=True)
ap.add_argument('--output',required=True)
ap.add_argument('--preset',choices=['head','bare','body'],required=True)
ap.add_argument('--frames',type=int,default=72)
ap.add_argument('--preview',action='store_true')
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
native=Path(a.native).resolve();out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=sha(native)
assert before=='e9c8654121307b61fb75d73789c9b2443a3e42c53420dfdfada927d194b475d4'
bpy.ops.wm.open_mainfile(filepath=str(native),use_scripts=False)
s=bpy.context.scene;s.frame_set(1);s.render.engine='BLENDER_EEVEE';s.render.use_freestyle=False
s.render.film_transparent=True;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA'
s.render.resolution_x=720;s.render.resolution_y=840;s.render.resolution_percentage=100
s.render.pixel_aspect_x=s.render.pixel_aspect_y=1
s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
if hasattr(s,'eevee'):s.eevee.taa_render_samples=24
camera=bpy.data.objects.new('EXPORT_Only_Orbit',bpy.data.cameras.new('EXPORT_Only_Orbit'));s.collection.objects.link(camera);s.camera=camera
camera.data.type='ORTHO';camera.data.shift_x=camera.data.shift_y=0;camera.data.clip_start=.001;camera.data.clip_end=100
target=Vector((0,0,.86 if a.preset=='body' else 1.55));scale=1.98 if a.preset=='body' else .49
camera.data.ortho_scale=scale
visible=[o for o in s.objects if o.type=='MESH' and not o.hide_render and not o.hide_viewport]
active_keys={o.name:{k.name:float(k.value) for k in o.data.shape_keys.key_blocks if k.value} for o in visible if o.data.shape_keys}
hidden=[];lamps=[]
if a.preset=='bare':
    members={o.name for c in bpy.data.collections if 'HAIR' in c.name.upper() for o in c.all_objects}
    for o in s.objects:
        if o.type=='MESH' and (o.name in members or any(t in o.name for t in ['Hair','HAIR','PIXAL'])):
            if not o.hide_render:hidden.append(o.name)
            o.hide_render=True
    clay=bpy.data.materials.new('EXPORT_18percent_Clay');clay.use_nodes=True;n=clay.node_tree.nodes;n.clear()
    d=n.new('ShaderNodeBsdfDiffuse');d.inputs['Color'].default_value=(.18,.18,.18,1);m=n.new('ShaderNodeOutputMaterial');clay.node_tree.links.new(d.outputs[0],m.inputs['Surface'])
    for slot in bpy.data.objects['MIA_V27_SharedHeadBody'].material_slots:slot.material=clay
    for o in s.objects:
        if o.type=='LIGHT':o.hide_render=True
    for label,power,size in [('Key',90,1),('Fill',45,1.5),('Rim',50,1)]:
        data=bpy.data.lights.new('EXPORT_'+label,'AREA');data.energy=power;data.shape='DISK';data.size=size
        ob=bpy.data.objects.new(data.name,data);s.collection.objects.link(ob);lamps.append(ob)
records=[]
for i in range(1 if a.preview else a.frames):
    yaw=2*math.pi*i/a.frames;elev=math.radians(0 if a.preset=='bare' else (2 if a.preset=='body' else 5))
    offset=Vector((2*math.sin(yaw)*math.cos(elev),-2*math.cos(yaw)*math.cos(elev),2*math.sin(elev)))
    camera.location=target+offset;camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    if lamps:
        for lamp,(x,y,z) in zip(lamps,[(-.6,-1,2.2),(.8,-.8,1.8),(0,.9,2.05)]):
            lamp.location=(x*math.cos(yaw)-y*math.sin(yaw),x*math.sin(yaw)+y*math.cos(yaw),z)
            lamp.rotation_euler=(target-lamp.location).to_track_quat('-Z','Y').to_euler()
    bpy.context.view_layer.update();p=out/f'{i:03}.png';s.render.filepath=str(p);bpy.ops.render.render(write_still=True)
    records.append({'index':i,'yaw':i*360/a.frames,'elevation':math.degrees(elev),'camera_matrix':[list(r) for r in camera.matrix_world],'ortho_scale':scale,'path':p.name,'sha256':sha(p)})
    print('EXPORT_FRAME',a.preset,i,flush=True)
assert sha(native)==before
(out/'manifest.json').write_text(json.dumps({'native':str(native),'sha256':before,'native_unchanged':True,'preset':a.preset,'projection':'ORTHO','target':list(target),'resolution':[720,840],'active_shape_keys':active_keys,'frame':1,'hidden_hair_owners':hidden,'mode':'18percent diffuse skin, camera-relative white area lights; original eye/ink materials' if a.preset=='bare' else 'Actual native production materials and virtual normal-ramp light; fixed inherited scene lights; only camera orbits','display':'Standard / None / exposure0 / gamma1','frames':records},indent=2),encoding='utf-8')
print('TURNTABLE_COMPLETE',a.preset,flush=True)
