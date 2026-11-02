"""Four CURRENT full-height source views, no edits or native save. GPU token required."""
from pathlib import Path
import hashlib,json,math,sys
import bpy,numpy as np
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parent;d=json.loads((P/'current-body-audit.json').read_text());N=Path(d['native']);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert sha(N)==d['sha256']
REF=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/references/received/mia-body-v06-confirmed-20261102.png');assert sha(REF)=='6d88d1bc6b579d1ac53436d9f1fa50f903117ac244e307b8e08a9d1e270080e1'
CAN=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-refinement-v002');spec=json.loads((CAN/'review/integrated-R3b/source/render-records.json').read_text())[0]['camera']
bpy.ops.wm.open_mainfile(filepath=str(N),use_scripts=False);s=bpy.context.scene;s.frame_set(2);s.frame_set(1);bpy.context.view_layer.update();rig=bpy.data.objects['MIA_V06_RIG'];master=bpy.data.objects['MIA_V27_Foundation_Face'];pose={b.name:[list(r) for r in b.matrix_basis] for b in rig.pose.bones};keys={k.name:k.value for k in master.data.shape_keys.key_blocks}
for o in s.objects:
    if o.type=='LIGHT':o.hide_render=True
lamps=[]
for i,(item,watts) in enumerate(zip(spec['lighting']['areas'],[60.,15.,8.])):
    dat=bpy.data.lights.new('V003_CurrentSource_'+str(i),'AREA');dat.energy=watts;dat.shape=item['shape'];dat.size=item['size'];dat.color=item['color'];o=bpy.data.objects.new(dat.name,dat);s.collection.objects.link(o);o.matrix_world=Matrix(item['matrix']);lamps.append(o)
world=bpy.data.worlds.new('V003_CurrentSourceWorld');world.use_nodes=True;n=world.node_tree.nodes;n.clear();bg=n.new('ShaderNodeBackground');bg.inputs['Color'].default_value=(*spec['lighting']['world_linear'],1);bg.inputs['Strength'].default_value=spec['lighting']['world_strength'];out=n.new('ShaderNodeOutputWorld');world.node_tree.links.new(bg.outputs[0],out.inputs['Surface']);s.world=world
cam=bpy.data.objects.new('V003_CurrentFullHeightCamera',bpy.data.cameras.new('V003_CurrentFullHeightCamera'));s.collection.objects.link(cam);cam.data.type='ORTHO';cam.data.ortho_scale=1.85;cam.data.clip_start=.1;cam.data.clip_end=10.;cam.data.shift_x=cam.data.shift_y=0;s.camera=cam
s.render.engine='BLENDER_EEVEE';s.render.resolution_x=800;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.render.pixel_aspect_x=s.render.pixel_aspect_y=1;s.render.film_transparent=True;s.render.use_freestyle=False;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA'
for field in ['view_transform','look','exposure','gamma']:setattr(s.view_settings,field,spec['color_management'][field])
O=P/'current-source4';O.mkdir(exist_ok=True);records=[];target=Vector((0,-.018,.86))
for name,yaw in [('front',0),('profile',90),('back',180),('oblique',30)]:
    angle=math.radians(yaw);cam.location=target+Vector((4*math.sin(angle),-4*math.cos(angle),0));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();bpy.context.view_layer.update()
    active=[o for o in s.objects if o.type=='LIGHT' and not o.hide_render];assert len(active)==3 and set(o.name for o in active)==set(o.name for o in lamps);assert [o.data.energy for o in lamps]==[60.,15.,8.]
    assert pose=={b.name:[list(r) for r in b.matrix_basis] for b in rig.pose.bones};assert keys=={k.name:k.value for k in master.data.shape_keys.key_blocks}
    file=O/(name+'.png');assert not file.exists();row=dict(view=name,path=str(file),native=str(N),sha256_native=d['sha256'],native_saved=False,full_current_head_body_hair_attachments=True,body_unchanged=True,camera=dict(projection=cam.data.type,matrix=[list(r) for r in cam.matrix_world],ortho_scale=cam.data.ortho_scale,clip_start=cam.data.clip_start,clip_end=cam.data.clip_end,resolution=[800,1000],pixel_aspect=[1,1],yaw=yaw,frame=s.frame_current),lighting=dict(actual_all_light_flags_before_render=[dict(name=o.name,hidden=o.hide_render,energy=o.data.energy) for o in s.objects if o.type=='LIGHT'],active_areas=[dict(name=o.name,matrix=[list(r) for r in o.matrix_world],size=o.data.size,shape=o.data.shape,energy=o.data.energy,color=list(o.data.color)) for o in lamps],world_color=list(bg.inputs['Color'].default_value),world_strength=bg.inputs['Strength'].default_value),color_management=spec['color_management'],source_target=dict(path=str(REF),sha256=sha(REF),authority='User reattached and explicitly selected v06 for body target; 2026-11-02',registered_not_warped=True))
    (O/(name+'-pre-render.json')).write_text(json.dumps(row,indent=2)+'\n',encoding='utf-8');s.render.filepath=str(file);bpy.ops.render.render(write_still=True);row['image_sha256']=sha(file);records.append(row);(O/'render-records.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
assert len(records)==4 and sha(N)==d['sha256'];print('V003_CURRENT_SOURCE4_DONE native unchanged',flush=True)
