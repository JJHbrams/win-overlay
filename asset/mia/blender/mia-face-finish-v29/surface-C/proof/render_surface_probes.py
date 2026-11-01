"""Read-only saved-native surface probes. Run only after parent GPU release.

Small first preset precedes response/blink/source expansion. Exact old source
camera/rig metadata are reused; active node links/inputs are recorded, not intent.
"""
import bpy,json,hashlib,argparse,sys,math
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(__file__).parent;ap=argparse.ArgumentParser();ap.add_argument('--native',required=True);ap.add_argument('--preset',choices=['first','features','response','map-controls','blink','headfollow','source'],default='first');ap.add_argument('--hair',choices=['on','off'],default='off');ap.add_argument('--only',default='',help='Comma-separated job IDs for small append-only batches');a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);S=Path(a.native);digest=hashlib.sha256(S.read_bytes()).hexdigest();O=S.parent/('probes-'+a.preset+'-hair-'+a.hair);O.mkdir(exist_ok=True)
REF=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-orbit-thorax-review-v28/reviews/G2L-face/reference-review.json');ref=json.loads(REF.read_text());views={v['id']:v['candidate_camera'] for v in ref['views']}
bpy.ops.wm.open_mainfile(filepath=str(S),use_scripts=False);s=bpy.context.scene;s.frame_set(1);mats=[m for m in bpy.data.materials if m.name.startswith(('V29_Face_MaskedPigment','V29_InnerWall_'))];assert len(mats)==3
if a.hair=='off':
 for o in s.objects:
  if o.type=='MESH' and (any('HAIR' in c.name.upper() for c in o.users_collection) or any(t in o.name for t in ['Hair','HAIR','PIXAL','Braid','Gather','RootLining'])):o.hide_render=True
original_links={m.name:m.node_tree.nodes['방출'].inputs['Color'].links[0].from_socket for m in mats};defaults={m.name:{n.name:n.outputs[0].default_value for n in m.node_tree.nodes if n.type=='VALUE'} for m in mats}
for o in s.objects:
 if o.type=='LIGHT':o.hide_render=True
meta=views['front'];lamps=[]
for item in meta['lighting']['areas']:
 d=bpy.data.lights.new('V29_Probe_'+item['role'],'AREA');d.energy=item['watts'];d.shape=item['shape'];d.size=item['size'];d.color=item['color'];o=bpy.data.objects.new(d.name,d);s.collection.objects.link(o);o.matrix_world=Matrix(item['matrix']);lamps.append(o)
world=bpy.data.worlds.new('V29_Probe_ActualWorld');world.use_nodes=True;wn=world.node_tree.nodes;wn.clear();bg=wn.new('ShaderNodeBackground');bg.inputs['Color'].default_value=(*meta['lighting']['world_linear'],1);bg.inputs['Strength'].default_value=meta['lighting']['world_strength'];wo=wn.new('ShaderNodeOutputWorld');wo.is_active_output=True;world.node_tree.links.new(bg.outputs[0],wo.inputs['Surface']);s.world=world
camera=bpy.data.cameras.new('V29_ActualSourceCamera');cam=bpy.data.objects.new(camera.name,camera);s.collection.objects.link(cam);s.camera=cam;camera.type='ORTHO';camera.ortho_scale=meta['ortho_scale'];camera.shift_x,camera.shift_y=meta['lens_shift'];s.render.engine='BLENDER_EEVEE';s.render.use_freestyle=False;s.render.resolution_x,s.render.resolution_y=meta['resolution'];s.render.resolution_percentage=100;s.render.pixel_aspect_x,s.render.pixel_aspect_y=meta['pixel_aspect'];s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.render.film_transparent=True
cm=meta['color_management'];s.view_settings.view_transform=cm['view_transform'];s.view_settings.look=cm['look'];s.view_settings.exposure=cm['exposure'];s.view_settings.gamma=cm['gamma']
presets={'first':[('before_production','front','production',{'V29_SurfaceEnabled':0.},None,False),('before_color','front','color',{'V29_SurfaceEnabled':0.},None,False),('after_color','front','color',{},None,False),('after_production','front','production',{},None,False)],'response':[('diffuse_original','front','diffuse',{'V29_ShadowEnabled':0.},None,False),('diffuse_control','front','diffuse',{},None,False),('diffuse_moved','front','diffuse',{},None,True),('spec_flat0','front','spec',{'V29_SpecularOverrideFlag':1.,'V29_SpecularOverrideValue':0.},None,False),('spec_flat1','front','spec',{'V29_SpecularOverrideFlag':1.,'V29_SpecularOverrideValue':1.},None,False),('spec_moved','front','spec',{'V29_SpecularOverrideFlag':1.,'V29_SpecularOverrideValue':1.},None,True),('rough_low','front','spec',{'V29_SpecularOverrideFlag':1.,'V29_SpecularOverrideValue':1.,'V29_RoughnessOverrideFlag':1.,'V29_RoughnessOverrideValue':.15},None,False),('rough_high','front','spec',{'V29_SpecularOverrideFlag':1.,'V29_SpecularOverrideValue':1.,'V29_RoughnessOverrideFlag':1.,'V29_RoughnessOverrideValue':.85},None,False)],'blink':[(f'{side}_{value}', 'front' if side=='Close' else 'left_oblique','production',{},(side,value),False) for side in ['Close','Close_R','Close_L'] for value in [.5,1.]],'source':[(name,name,'production',{},None,False) for name in views]}
# Texture-vs-flat comparisons use atlas means, rather than only bypassing maps
# with0/1 extremes. Both spatial specweight and roughness are isolated.
control=mats[0].node_tree.nodes['V29_NATIVE_LightReflectControls'].image
import numpy as np
pixels=np.empty(len(control.pixels),dtype=np.float32);control.pixels.foreach_get(pixels);pixels=pixels.reshape(-1,4);mean_spec=float(pixels[:,1].mean());mean_rough=float(pixels[:,2].mean())
presets['features']=[(f'{feature}_{value}','front','color',{node:value},None,False) for feature,node in [('fatigue','V29_FatigueGain'),('fold','V29_FoldGain'),('makeup','V29_MakeupGain')] for value in [0.,1.]]
presets['map-controls']=[('native_spec_and_roughness','front','spec',{},None,False),('flat_spec_native_roughness','front','spec',{'V29_SpecularOverrideFlag':1.,'V29_SpecularOverrideValue':mean_spec},None,False),('native_spec_flat_roughness','front','spec',{'V29_RoughnessOverrideFlag':1.,'V29_RoughnessOverrideValue':mean_rough},None,False),('flat_spec_and_roughness','front','spec',{'V29_SpecularOverrideFlag':1.,'V29_SpecularOverrideValue':mean_spec,'V29_RoughnessOverrideFlag':1.,'V29_RoughnessOverrideValue':mean_rough},None,False)]
presets['headfollow']=[(f'head_{angle}_{view}',view,'production',{'__head_yaw__':angle},None,False) for angle in [-12.,12.] for view in ['front','left_oblique']]
arm=bpy.data.objects['MIA_V06_RIG'];head=arm.pose.bones['J_Bip_C_Head'];rest_head=head.matrix.copy()
def linear_result(name):
 result=bpy.data.images['Render Result'];values=np.empty(len(result.pixels),dtype=np.float32);result.pixels.foreach_get(values);expected=s.render.resolution_x*s.render.resolution_y*4;source='Actual Render Result float32 RGBA pixels (scene-linear)'
 if values.size!=expected:
  # Some background builds discard the exposed pixel buffer after PNG write.
  # Save that same Render Result as lossless linear32-bit EXR, never infer
  # weak response by decoding an8-bit PNG.
  settings=s.render.image_settings;old=(settings.file_format,settings.color_mode,settings.color_depth,s.view_settings.view_transform);settings.file_format='OPEN_EXR';settings.color_mode='RGBA';settings.color_depth='32';settings.exr_codec='ZIP';s.view_settings.view_transform='Raw';path=O/(name+'-RenderResult-linear.exr');result.save_render(str(path),scene=s);settings.file_format,settings.color_mode,settings.color_depth,s.view_settings.view_transform=old;loaded=bpy.data.images.load(str(path),check_existing=False);loaded.colorspace_settings.name='Non-Color';values=np.empty(len(loaded.pixels),dtype=np.float32);loaded.pixels.foreach_get(values);source='Same actual Render Result, losslessZIP32-bit EXR reload as numeric Non-Color; no PNG decoding'
 assert values.size==expected
 array=values.reshape(s.render.resolution_y,s.render.resolution_x,4);path=O/(name+'-linear.npz');np.savez_compressed(path,linear_rgba=array);return array,{'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'pixel_sha256':hashlib.sha256(array.tobytes()).hexdigest(),'shape':list(array.shape),'dtype':'float32','source':source,'max_rgb':float(array[:,:,:3].max())}
record_path=O/'probe-records.json'
records={}
if record_path.exists():
 previous=json.loads(record_path.read_text());assert previous['native_sha256']==digest;records=previous['records']
linear_frames={}
if a.only:
 selected=set(a.only.split(','));presets[a.preset]=[job for job in presets[a.preset] if job[0] in selected];assert {job[0] for job in presets[a.preset]}==selected
for name,view,mode,overrides,blink,moved in presets[a.preset]:
 head.matrix=rest_head.copy()
 if '__head_yaw__' in overrides:
  pivot=(arm.matrix_world@rest_head).translation;head.matrix=arm.matrix_world.inverted()@Matrix.Translation(pivot)@Matrix.Rotation(math.radians(overrides['__head_yaw__']),4,'Z')@Matrix.Translation(-pivot)@arm.matrix_world@rest_head
 for o in s.objects:
  if o.type=='MESH' and o.data.shape_keys:
   for k in o.data.shape_keys.key_blocks:
    if k.name!='Basis':k.value=0.
   if blink:
    key='Face.M_F00_000_00_Fcl_EYE_'+blink[0]
    if key in o.data.shape_keys.key_blocks:o.data.shape_keys.key_blocks[key].value=blink[1]
 for mat in mats:
  nodes=mat.node_tree.nodes
  for key,v in defaults[mat.name].items():nodes[key].outputs[0].default_value=v
  for key,v in overrides.items():
   if not key.startswith('__'):nodes[key].outputs[0].default_value=v
  socket={'production':original_links[mat.name],'color':nodes['V29_OriginalVsSurfaceBypass'].outputs[0],'diffuse':nodes['V29_ActiveDiffuseShadowControl'].outputs[0],'spec':nodes['V29_WeightedActualSpecular'].outputs[0]}[mode];mat.node_tree.links.new(socket,nodes['방출'].inputs['Color'])
 cam.matrix_world=Matrix(views[view]['matrix']);camera.ortho_scale=views[view]['ortho_scale']
 for lamp,item in zip(lamps,meta['lighting']['areas']):
  lamp.matrix_world=Matrix(item['matrix'])
  if moved:
   pivot=Vector((0,0,1.55));rot=Matrix.Rotation(math.radians(65),4,'Z');lamp.matrix_world=Matrix.Translation(pivot)@rot@Matrix.Translation(-pivot)@lamp.matrix_world
 bpy.context.view_layer.update();s.render.filepath=str(O/(name+'.png'));bpy.ops.render.render(write_still=True);linear_frames[name],linear_meta=linear_result(name)
 records[name]={'path':s.render.filepath,'sha256':hashlib.sha256(Path(s.render.filepath).read_bytes()).hexdigest(),'mode':mode,'hair':a.hair,'scope':'Face slot0 and inner-wall skin only. Other materials keep production shaders; color diagnostic is not whole-head albedo.','view_id':view,'requested_head_yaw_world_degrees':overrides.get('__head_yaw__',0.),'flat_map_comparison':{'definition':'Atlas mean of actual consumed Non-Color response image; no anatomical target claim','spec_weight':mean_spec,'roughness':mean_rough},'camera':{'matrix':[list(r) for r in cam.matrix_world],'ortho_scale':camera.ortho_scale,'resolution':[s.render.resolution_x,s.render.resolution_y],'pixel_aspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'lens_shift':[camera.shift_x,camera.shift_y]},'display':cm,'actual_lights':[{'name':o.name,'matrix':[list(r) for r in o.matrix_world],'watts':o.data.energy,'size':o.data.size} for o in lamps],'actual_world':{'active_output':wo.name,'linked_background':wo.inputs['Surface'].links[0].from_node.name,'color':list(bg.inputs['Color'].default_value),'strength':bg.inputs['Strength'].default_value},'active_keys':{o.name:{k.name:k.value for k in o.data.shape_keys.key_blocks if k.value} for o in s.objects if o.type=='MESH' and o.data.shape_keys},'actual_material_values':{m.name:{n.name:n.outputs[0].default_value for n in m.node_tree.nodes if n.type=='VALUE'} for m in mats},'actual_emission_links':{m.name:m.node_tree.nodes['방출'].inputs['Color'].links[0].from_node.name for m in mats},'frame':s.frame_current,'actual_head_rig':{'matrix':[list(r) for r in bpy.data.objects['MIA_V06_RIG'].matrix_world],'head_matrix_basis':[list(r) for r in bpy.data.objects['MIA_V06_RIG'].pose.bones['J_Bip_C_Head'].matrix_basis]},'native_saved':False}
 records[name]['actual_linear_render_result']=linear_meta
 (O/'probe-records.json').write_text(json.dumps({'native':str(S),'native_sha256':digest,'reference_camera_package':str(REF),'records':records,'status':'Actual controlled probes only; not source/art acceptance'},indent=2),encoding='utf8')
# Load existing actual-linear frames when appending a single controlled job.
for name,record in records.items():
 if name not in linear_frames and 'actual_linear_render_result' in record:linear_frames[name]=np.load(record['actual_linear_render_result']['path'])['linear_rgba']
comparison_pairs=[('before_production','after_production'),('before_color','after_color'),('fatigue_0.0','fatigue_1.0'),('fold_0.0','fold_1.0'),('makeup_0.0','makeup_1.0'),('diffuse_original','diffuse_control'),('diffuse_control','diffuse_moved'),('spec_flat0','spec_flat1'),('spec_flat1','spec_moved'),('rough_low','rough_high'),('native_spec_and_roughness','flat_spec_native_roughness'),('native_spec_and_roughness','native_spec_flat_roughness'),('native_spec_and_roughness','flat_spec_and_roughness')];deltas=[]
for first,second in comparison_pairs:
 if first not in linear_frames or second not in linear_frames:continue
 x,y=linear_frames[first],linear_frames[second];delta=y[:,:,:3]-x[:,:,:3];mask=np.maximum(x[:,:,3],y[:,:,3])>.5;active=delta[mask];deltas.append({'pair':[first,second],'source':'Actual scene-linear Render Result, before8-bit PNG quantization','scope':'All model-covered pixels alpha>.5; other owners are unchanged within a fixed-light pair. Moved-light pairs also affect original scene-lit owners.','max_abs_linear_RGB':float(abs(active).max()),'mean_abs_linear_RGB':float(abs(active).mean()),'rms_linear_RGB':float(np.sqrt(np.mean(active.astype(np.float64)**2))),'pixels_with_delta_above1e-8':int(np.count_nonzero(np.max(abs(active),axis=1)>1e-8))})
(O/'actual-linear-response-deltas.json').write_text(json.dumps({'native_sha256':digest,'preset':a.preset,'comparisons':deltas,'status':'Numerical actual response only; spatial/style/source acceptance remains independent'},indent=2),encoding='utf8')
assert hashlib.sha256(S.read_bytes()).hexdigest()==digest;print('SURFACE_PROBES_DONE',a.preset,len(records),flush=True)
