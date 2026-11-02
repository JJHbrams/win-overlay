"""Root-token-only four actual frames; no native save or image draw-over."""
from pathlib import Path
import bpy,json,hashlib,sys,copy,importlib.util
from mathutils import Matrix
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;CAN=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia');R=CAN/'blender/mia-refinement-v002/review/integrated-R3b';N=R.parents[1]/'integrated/Mia_v0.0.2_Review_R3b.blend';SHA='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert sha(N)==SHA
O=P/'review/A-front-oblique4';O.mkdir(parents=True,exist_ok=True);assert not (O/'render-records.json').exists();bpy.ops.wm.open_mainfile(filepath=str(N),use_scripts=False)
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
delta=load('brow_display_render',P/'partial_brow_display.py');h=load('brow_render_guard',P.parents[2]/'mia-mouth-rig-v002/guard_helpers.py')
old=json.loads((R/'source/render-records.json').read_text(encoding='utf-8'));views={v:next(r['camera'] for r in old if r['id']==v+'-hairON') for v in ['front','left_oblique']};base=views['front'];scene=bpy.context.scene;ctrl=bpy.data.objects['Mia_FacialControls_v002'];master=bpy.data.objects['MIA_V27_Foundation_Face'];rig=next(m.object for m in master.modifiers if m.type=='ARMATURE');head=rig.pose.bones['J_Bip_C_Head']
for n in ctrl.keys():
 if n.startswith('Manual') or (n.startswith('P') and n[:3][1:].isdigit()) or n in ['HeadPitch','HeadYaw','HeadRoll','GazeX','GazeY']:ctrl[n]=0.
ctrl['Strength']=ctrl['HeadPoseStrength']=ctrl['GazeStrength']=1.;ctrl.update_tag();scene.frame_set(1);bpy.context.view_layer.update()
archived=[o for o in scene.objects if o.type=='LIGHT']
for o in archived:o.hide_render=True
lamps=[]
for i,l in enumerate(base['lighting']['areas']):
 data=bpy.data.lights.new('BrowDisplay_Reference_'+str(i),'AREA');data.energy=l['watts'];data.shape=l['shape'];data.size=l['size'];data.color=l['color'];ob=bpy.data.objects.new(data.name,data);scene.collection.objects.link(ob);ob.matrix_world=Matrix(l['matrix']);lamps.append(ob)
w=bpy.data.worlds.new('BrowDisplay_ReferenceWorld');w.use_nodes=True;n=w.node_tree.nodes;n.clear();bg=n.new('ShaderNodeBackground');out=n.new('ShaderNodeOutputWorld');w.node_tree.links.new(bg.outputs[0],out.inputs['Surface']);bg.inputs['Color'].default_value=(*base['lighting']['world_linear'],1);bg.inputs['Strength'].default_value=base['lighting']['world_strength'];scene.world=w
scene.render.engine='BLENDER_EEVEE';scene.render.use_freestyle=False;scene.render.film_transparent=False;scene.render.resolution_percentage=100;scene.render.resolution_x=scene.render.resolution_y=512;scene.render.pixel_aspect_x=scene.render.pixel_aspect_y=1.;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';cm=base['color_management'];scene.view_settings.view_transform=cm['view_transform'];scene.view_settings.look=cm['look'];scene.view_settings.exposure=cm['exposure'];scene.view_settings.gamma=cm['gamma']
cam=bpy.data.objects.new('BrowDisplay_ActualCamera',bpy.data.cameras.new('BrowDisplay_ActualCamera'));scene.collection.objects.link(cam);cam.data.type='ORTHO';cam.data.clip_start=.1;cam.data.clip_end=10.;scene.camera=cam
records=[];runtime=None
def render(label,view):
 v=views[view];cam.matrix_world=Matrix(v['matrix']);cam.data.ortho_scale=v['ortho_scale'];cam.data.shift_x,cam.data.shift_y=v['lens_shift'];scene.frame_set(len(records)+1);bpy.context.view_layer.update();active=[o for o in scene.objects if o.type=='LIGHT' and not o.hide_render];assert set(active)==set(lamps) and all(o.hide_render for o in archived);file=O/(label+'.png');assert not file.exists();scene.render.filepath=str(file)
 before={m:h.jhash(h.graph(bpy.data.materials[m].node_tree)) for m in runtime['materials']} if runtime else None
 bpy.ops.render.render(write_still=True)
 after={m:h.jhash(h.graph(bpy.data.materials[m].node_tree)) for m in runtime['materials']} if runtime else None
 assert before==after
 actual=copy.deepcopy(v);actual.update(matrix=[list(r) for r in cam.matrix_world],ortho_scale=cam.data.ortho_scale,lens_shift=[cam.data.shift_x,cam.data.shift_y],clip_start=cam.data.clip_start,clip_end=cam.data.clip_end,resolution=[512,512],pixel_aspect=[1.,1.],frame=scene.frame_current,head_matrix_basis=[list(r) for r in head.matrix_basis],active_shape_keys={k.name:k.value for k in master.data.shape_keys.key_blocks if k.value});actual['lighting']['areas']=[dict(item,name=o.name,matrix=[list(r) for r in o.matrix_world],watts=o.data.energy,shape=o.data.shape,size=o.data.size,color=list(o.data.color)) for item,o in zip(base['lighting']['areas'],lamps)]
 records.append(dict(id=label,view=view,path=str(file),sha256=sha(file),native=str(N),native_sha256=SHA,camera=actual,runtime_delta=runtime,helper_sha256=sha(P/'partial_brow_display.py') if runtime else None,renderer_sha256=sha(Path(__file__)),active_lights=[o.name for o in active],all_archived_lights_hidden=True,new_material_graphs_before=before,new_material_graphs_after=after,native_saved=False));(O/'render-records.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8');print('BROW_DISPLAY_FRAME_DONE',label,flush=True)
render('baseline-front','front');render('baseline-left_oblique','left_oblique');runtime=delta.apply_to_current_scene(.60);render('candidate-front','front');render('candidate-left_oblique','left_oblique');assert sha(N)==SHA;print('BROW_DISPLAY_ACTUAL4_DONE',str(O/'render-records.json'),flush=True)
