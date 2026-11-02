"""Root-authorized8 gray frames. No native save; exact common fixtures."""
from pathlib import Path
import hashlib,json,math,sys
import bpy,numpy as np
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import apply_form_C as patch;import install_scaffold_D
d=json.loads((P/'current-body-audit.json').read_text());N=Path(d['native']);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert sha(N)==d['sha256']
CAN=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-refinement-v002');r=json.loads((CAN/'review/integrated-R3b/source/render-records.json').read_text())[0];spec=r['camera']
bpy.ops.wm.open_mainfile(filepath=str(N),use_scripts=False);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[patch.OWNER];rig=bpy.data.objects['MIA_V06_RIG'];master=bpy.data.objects['MIA_V27_Foundation_Face']
pose={b.name:[list(x) for x in b.matrix_basis] for b in rig.pose.bones};keys={k.name:k.value for k in master.data.shape_keys.key_blocks}
ownership=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-visible-art-v30/component_ownership.py');import importlib.util
ospec=importlib.util.spec_from_file_location('body_review_ownership',ownership);own=importlib.util.module_from_spec(ospec);ospec.loader.exec_module(own)
hidden=[]
for ob in s.objects:
    if ob.type=='LIGHT':ob.hide_render=True
    if ob.type=='MESH' and own.is_hair_object(ob):ob.hide_render=True;hidden.append(ob.name)
lamps=[]
for i,(loc,watts,size) in enumerate([((-1.2,-1.8,2.1),110.,1.3),((1.4,-1.4,1.7),38.,1.4),((0,1.6,2.),22.,1.)]):
    data=bpy.data.lights.new('V003_BodyGray_'+str(i),'AREA');data.energy=watts;data.shape='DISK';data.size=size;data.color=(1,1,1);ob=bpy.data.objects.new(data.name,data);s.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector((0,-.018,1.2))-ob.location).to_track_quat('-Z','Y').to_euler();lamps.append(ob)
world=bpy.data.worlds.new('V003_BodyGrayWorld');world.use_nodes=True;nodes=world.node_tree.nodes;nodes.clear();bg=nodes.new('ShaderNodeBackground');bg.inputs['Color'].default_value=(.18,.18,.18,1);bg.inputs['Strength'].default_value=.2;wo=nodes.new('ShaderNodeOutputWorld');world.node_tree.links.new(bg.outputs[0],wo.inputs['Surface']);s.world=world
gray=bpy.data.materials.new('V003_Body_ActualGeometryGray');gray.use_nodes=True;nodes=gray.node_tree.nodes;nodes.clear();bs=nodes.new('ShaderNodeBsdfPrincipled');bs.inputs['Base Color'].default_value=(.23,.23,.23,1);bs.inputs['Roughness'].default_value=.85;out=nodes.new('ShaderNodeOutputMaterial');tr=nodes.new('ShaderNodeBsdfTransparent');mix=nodes.new('ShaderNodeMixShader');mix.inputs[0].default_value=.25;gray.node_tree.links.new(tr.outputs[0],mix.inputs[1]);gray.node_tree.links.new(bs.outputs[0],mix.inputs[2]);gray.node_tree.links.new(mix.outputs[0],out.inputs['Surface']);skin.data.materials[1]=gray
camera=bpy.data.objects.new('V003_BodyProofCamera',bpy.data.cameras.new('V003_BodyProofCamera'));s.collection.objects.link(camera);camera.data.type='ORTHO';camera.data.ortho_scale=.40;camera.data.clip_start=.1;camera.data.clip_end=10.;s.camera=camera
s.render.engine='BLENDER_EEVEE';s.render.resolution_x=s.render.resolution_y=640;s.render.resolution_percentage=100;s.render.pixel_aspect_x=s.render.pixel_aspect_y=1.;s.render.film_transparent=False;s.render.use_freestyle=False;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA'
for field in ['view_transform','look','exposure','gamma']:setattr(s.view_settings,field,spec['color_management'][field])
target=Vector((0,-.035,1.275));angles=[('front',0,0),('profile',85,0),('oblique',30,0),('lowoblique',-35,-25)]
O=P/'scaffold-D/actual-ghost-guides';O.mkdir(exist_ok=True);records=[];matched={r['view']:r['camera'] for r in json.loads((P/'renders-form-B/render-records.json').read_text()) if r['variant']=='baseline'}
for variant in ['candidate']:
    if variant=='candidate':
        patch.apply();col=install_scaffold_D.install();col.hide_render=False
        for o in s.objects:
            if o.type=='MESH' and o!=skin and o.name not in col.objects:o.hide_render=True
        for o in col.objects:
            if o.type=='MESH' and any(q in o.name for q in ['fan_web','fold_bridge']):
                o.hide_render=False;mod=o.modifiers.new('Guide edges only; not membrane','WIREFRAME');mod.thickness=.0004;mod.use_replace=True

    for view,yaw,pitch in angles:
        y,p=math.radians(yaw),math.radians(pitch);camera.location=target+Vector((2*math.sin(y)*math.cos(p),-2*math.cos(y)*math.cos(p),2*math.sin(p)));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();bpy.context.view_layer.update()
        active=[o for o in s.objects if o.type=='LIGHT' and not o.hide_render];assert len(active)==3 and set(o.name for o in active)==set(o.name for o in lamps)
        assert [o.data.energy for o in lamps]==[110.,38.,22.]
        assert pose=={b.name:[list(x) for x in b.matrix_basis] for b in rig.pose.bones}
        assert keys=={k.name:k.value for k in master.data.shape_keys.key_blocks}
        cam=dict(projection=camera.data.type,matrix=[list(x) for x in camera.matrix_world],ortho_scale=camera.data.ortho_scale,clip_start=camera.data.clip_start,clip_end=camera.data.clip_end,resolution=[640,640],pixel_aspect=[1,1],lens_shift=[camera.data.shift_x,camera.data.shift_y],frame=s.frame_current,head_basis=pose['J_Bip_C_Head'],active_original_keys={k:v for k,v in keys.items() if v},lighting=[dict(name=o.name,watts=o.data.energy,matrix=[list(x) for x in o.matrix_world],size=o.data.size,color=list(o.data.color)) for o in lamps],world=dict(color=list(bg.inputs['Color'].default_value),strength=bg.inputs['Strength'].default_value),color_management=spec['color_management'])
        if variant=='baseline':matched[view]=cam
        else:pass # diagnostic guide cameras explicitly recorded; no baseline-pixel identity claim
        file=O/(variant+'-'+view+'.png');assert not file.exists()
        row=dict(variant=variant,view=view,native=str(N),native_sha256=d['sha256'],path=str(file),camera=cam,actual_light_flags_before_render=[dict(name=o.name,hidden=o.hide_render,watts=o.data.energy) for o in s.objects if o.type=='LIGHT'],hair_temporarily_hidden=hidden,material_mode='C body25percent ghost physical-gray + real guide curves/branch edge geometry; guide scaffold is inferred, C body still unselected',body_correction=patch.KEY if variant=='candidate' else None,native_saved=False)
        (O/(variant+'-'+view+'-pre-render.json')).write_text(json.dumps(row,indent=2)+'\n',encoding='utf-8');s.render.filepath=str(file);assert skin.data.materials[1]==gray;bpy.ops.render.render(write_still=True);assert skin.data.materials[1]==gray;row['sha256']=sha(file);records.append(row);(O/'render-records.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
assert len(records)==4 and sha(N)==d['sha256'];print('V003_ACTUAL_GHOST_GUIDES4_DONE',len(records),'native unchanged',flush=True)
