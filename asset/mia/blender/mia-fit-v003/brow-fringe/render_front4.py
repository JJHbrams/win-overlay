"""Root-token-only actual front hairOFF/ON before/after; never saves native."""
from pathlib import Path
import hashlib,json,sys,importlib.util,copy
import bpy,numpy as np
from mathutils import Matrix
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import apply_candidate
CAN=Path(r'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia');ROOT=CAN/'blender/mia-fit-v003'
def load(path):
    spec=importlib.util.spec_from_file_location('fringe_render_'+path.stem,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
native=Path(bpy.data.filepath);expected='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1';assert sha(native)==expected
O=P/'actual-B-front4';O.mkdir(exist_ok=True);assert not (O/'records.json').exists()
composition=load(ROOT/'integration/compose_selected.py').apply(diagnostic_guides=False,provisional_brow_ink=False)
assert not any(o.name.startswith('MiaHair_BrowInkProjection_') for o in bpy.data.objects)
records0=json.loads((CAN/'blender/mia-refinement-v002/review/integrated-R3b/source/render-records.json').read_text());spec=next(r['camera'] for r in records0 if r['id']=='front-hairON');scene=bpy.context.scene
hair_module=load(CAN/'blender/mia-visible-art-v30/component_ownership.py');hair={o.name:o.hide_render for o in scene.objects if o.type=='MESH' and hair_module.is_hair_object(o)}
archived=[o for o in scene.objects if o.type=='LIGHT']
for o in archived:o.hide_render=True
lamps=[]
for i,lamp in enumerate(spec['lighting']['areas']):
    data=bpy.data.lights.new('BrowFringe_SourceLight_'+str(i),'AREA');data.energy=lamp['watts'];data.shape=lamp['shape'];data.size=lamp['size'];data.color=lamp['color'];ob=bpy.data.objects.new(data.name,data);scene.collection.objects.link(ob);ob.matrix_world=Matrix(lamp['matrix']);lamps.append(ob)
world=bpy.data.worlds.new('BrowFringe_SourceWorld');world.use_nodes=True;n=world.node_tree.nodes;n.clear();bg=n.new('ShaderNodeBackground');out=n.new('ShaderNodeOutputWorld');world.node_tree.links.new(bg.outputs[0],out.inputs['Surface']);bg.inputs['Color'].default_value=(*spec['lighting']['world_linear'],1);bg.inputs['Strength'].default_value=spec['lighting']['world_strength'];scene.world=world
camera=bpy.data.objects.new('BrowFringe_ActualCamera',bpy.data.cameras.new('BrowFringe_ActualCamera'));scene.collection.objects.link(camera);camera.data.type='ORTHO';camera.matrix_world=Matrix(spec['matrix']);camera.data.ortho_scale=spec['ortho_scale'];camera.data.shift_x,camera.data.shift_y=spec['lens_shift'];camera.data.clip_start=.1;camera.data.clip_end=10.;scene.camera=camera
scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=scene.render.resolution_y=512;scene.render.resolution_percentage=100;scene.render.pixel_aspect_x=scene.render.pixel_aspect_y=1.;scene.render.use_freestyle=False;scene.render.film_transparent=False;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
for k in ['view_transform','look','exposure','gamma']:setattr(scene.view_settings,k,spec['color_management'][k])
scene.frame_set(1);bpy.context.view_layer.update();rig=bpy.data.objects['MIA_V06_RIG'];pose={b.name:[list(row) for row in b.matrix_basis] for b in rig.pose.bones};master=bpy.data.objects['MIA_V27_Foundation_Face'];values={k.name:k.value for k in master.data.shape_keys.key_blocks};records=[];runtime=None
def shoot(label,hair_on):
    for name,hidden in hair.items():bpy.data.objects[name].hide_render=hidden if hair_on else True
    bpy.context.view_layer.update();assert pose=={b.name:[list(row) for row in b.matrix_basis] for b in rig.pose.bones};assert values=={k.name:k.value for k in master.data.shape_keys.key_blocks}
    active=[o for o in scene.objects if o.type=='LIGHT' and not o.hide_render];assert set(active)==set(lamps);assert [o.data.energy for o in lamps]==[r['watts'] for r in spec['lighting']['areas']]
    file=O/(label+'.png');assert not file.exists();scene.render.filepath=str(file)
    camera_record=copy.deepcopy(spec);camera_record.update(matrix=[list(row) for row in camera.matrix_world],clip_start=camera.data.clip_start,clip_end=camera.data.clip_end,resolution=[512,512],frame=1)
    row={'id':label,'path':str(file),'native_sha256':expected,'variant':'B' if runtime else 'composed-selected-baseline',
         'hair_on':hair_on,'camera':camera_record,'composition':composition,'delta':runtime,
         'fringe_payload_sha256':sha(P/'fringe-B.npz') if runtime else None,'helper_sha256':sha(P/'apply_candidate.py'),
         'provisional_brow_overlay':False,'actual_lights':[{'name':o.name,'energy':o.data.energy,'matrix':[list(r) for r in o.matrix_world]} for o in active],
         'head_pose_basis':pose['J_Bip_C_Head'],'active_face_keys':{k:v for k,v in values.items() if v},'native_saved':False}
    (O/(label+'-pre-render.json')).write_text(json.dumps(row,indent=2)+'\n',encoding='utf-8',newline='\n')
    bpy.ops.render.render(write_still=True);row['sha256']=sha(file);records.append(row);(O/'records.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8',newline='\n');print('BROW_FRINGE_ACTUAL_FRAME '+label,flush=True)
shoot('baseline-front-hairOFF',False);shoot('baseline-front-hairON',True);runtime=apply_candidate.apply('B');shoot('candidate-front-hairOFF',False);shoot('candidate-front-hairON',True)
assert sha(native)==expected;print('BROW_FRINGE_ACTUAL_FRONT4_DONE',flush=True)
