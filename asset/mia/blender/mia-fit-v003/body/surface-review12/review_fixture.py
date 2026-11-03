"""Small shared fixture for saved-native review and truthful original baseline."""
import hashlib,json,math
import bpy
from mathutils import Vector
PREFIX='MIA12_Review_'
FULL_TARGET=(0,-.015,.87)
FULL_SCALE=1.9
FULL_RES=(640,900)
def sha(path):
    from pathlib import Path
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()
def setup(scene):
    for ob in hair_actors(scene):
        if 'MIA12_source_hair_hide_render' not in ob:ob['MIA12_source_hair_hide_render']=bool(ob.hide_render)
    for ob in scene.objects:
        if ob.type=='LIGHT':ob.hide_render=True
    for name,pos,energy,size in [('Key',(-3,-4,4),650,3),('Fill',(3,-2,2.5),280,4),('Rim',(1,3,3.5),450,3)]:
        ob=bpy.data.objects.get(PREFIX+name)
        if ob is None:
            data=bpy.data.lights.new(PREFIX+name,'AREA');ob=bpy.data.objects.new(data.name,data);scene.collection.objects.link(ob)
        ob.data.energy=energy;ob.data.shape='DISK';ob.data.size=size;ob.location=pos;ob.rotation_euler=(Vector((0,0,1))-ob.location).to_track_quat('-Z','Y').to_euler();ob.hide_render=False
    world=bpy.data.worlds.get(PREFIX+'World') or bpy.data.worlds.new(PREFIX+'World');world.use_nodes=True;bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.18,.18,.18,1);bg.inputs['Strength'].default_value=.2;scene.world=world
    cam=bpy.data.objects.get(PREFIX+'Camera')
    if cam is None:
        data=bpy.data.cameras.new(PREFIX+'Camera');cam=bpy.data.objects.new(data.name,data);scene.collection.objects.link(cam)
    cam.data.type='ORTHO';cam.data.clip_start=.1;cam.data.clip_end=10;scene.camera=cam
    scene.render.engine='BLENDER_EEVEE';scene.render.resolution_percentage=100;scene.render.pixel_aspect_x=scene.render.pixel_aspect_y=1;scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False;scene.frame_set(1)
    aim(scene,0)
    return cam
def aim(scene,yaw,pitch=0,target=FULL_TARGET,scale=FULL_SCALE,resolution=FULL_RES):
    target=Vector(target);a,b=math.radians(yaw),math.radians(pitch);cam=scene.camera
    cam.location=target+Vector((3*math.sin(a)*math.cos(b),-3*math.cos(a)*math.cos(b),3*math.sin(b)));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;cam['MIA12_target_world']=list(target);scene.render.resolution_x,scene.render.resolution_y=resolution;bpy.context.view_layer.update()
def hair_actors(scene):
    out=[]
    for ob in scene.objects:
        if ob.type!='MESH':continue
        text=ob.name.lower()+' '+' '.join(m.name.lower() for m in ob.data.materials if m)
        if any(t in text for t in ['hair','braid','crown','gather','rootlining','rimflow']):out.append(ob)
    return out
def hair_visibility(scene,visible):
    for ob in hair_actors(scene):ob.hide_render=bool(ob.get('MIA12_source_hair_hide_render',ob.hide_render)) if visible else True
def pose(scene):
    rig=scene.objects.get('MIA_V06_RIG');owner=scene.objects.get('MIA_V27_SharedHeadBody')
    return dict(bones={b.name:[list(r) for r in b.matrix_basis] for b in rig.pose.bones} if rig else {},keys={k.name:k.value for k in owner.data.shape_keys.key_blocks} if owner and owner.data.shape_keys else {})
def original_body_geometry(scene):
    import numpy as np
    source=scene.objects['MIA_V27_SharedHeadBody'];depsgraph=bpy.context.evaluated_depsgraph_get();evaluated=source.evaluated_get(depsgraph);mesh=evaluated.to_mesh(preserve_all_data_layers=True,depsgraph=depsgraph);mesh.calc_loop_triangles()
    world=np.asarray([evaluated.matrix_world@v.co for v in mesh.vertices],np.float32);triangles=np.asarray([x.vertices[:] for x in mesh.loop_triangles],np.int32)
    result=dict(scope='ACTUAL evaluated original savedR3b owner, post original modifiers at frame1',world_sha256=hashlib.sha256(world.tobytes()).hexdigest(),triangles_sha256=hashlib.sha256(triangles.tobytes()).hexdigest(),vertices=len(world),triangles=len(triangles),object_matrix=[list(r) for r in evaluated.matrix_world],UV_layers=[u.name for u in mesh.uv_layers],materials=[m.name if m else None for m in source.data.materials]);evaluated.to_mesh_clear();return result
def record(scene):
    cam=scene.camera
    p=pose(scene)
    return dict(projection=cam.data.type,camera_matrix=[list(r) for r in cam.matrix_world],view_frame_camera_local=[list(v) for v in cam.data.view_frame(scene=scene)],target_world=list(cam.get('MIA12_target_world',[])),ortho_scale=cam.data.ortho_scale,clip=[cam.data.clip_start,cam.data.clip_end],resolution=[scene.render.resolution_x,scene.render.resolution_y],pixel_aspect=[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y],shift=[cam.data.shift_x,cam.data.shift_y],lens=cam.data.lens,frame=scene.frame_current,active_shape_keys=p['keys'],color_management={k:getattr(scene.view_settings,k) for k in ['view_transform','look','exposure','gamma']},lights=[dict(name=o.name,matrix=[list(r) for r in o.matrix_world],energy=o.data.energy,size=o.data.size) for o in scene.objects if o.type=='LIGHT' and not o.hide_render],world=dict(color=list(next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND').inputs['Color'].default_value),strength=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND').inputs['Strength'].default_value),pose_sha256=digest(p))
