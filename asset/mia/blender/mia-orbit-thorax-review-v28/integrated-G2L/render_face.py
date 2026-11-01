import bpy,json,sys,math,hashlib
from pathlib import Path
from mathutils import Matrix,Vector
O=Path(__file__).parent
BASE=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v22/face-rebuild-10/selected-v27')
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
native=Path(args[0]) if args else BASE/'native/e9c865412130-Mia_Foundation_v27.blend'
tag=args[1] if len(args)>1 else 'baseline'
mode=args[2] if len(args)>2 else 'source4'
OUT=O/'renders'/tag;OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(native));NATIVE_SHA=hashlib.sha256(native.read_bytes()).hexdigest()
sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=768;sc.render.resolution_y=768;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.film_transparent=False
sc.render.use_freestyle=False;sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
sc.world=bpy.data.worlds.new('V28_ReviewWorld');sc.world.use_nodes=True;nt=sc.world.node_tree;nt.nodes.clear();bg=nt.nodes.new('ShaderNodeBackground');wo=nt.nodes.new('ShaderNodeOutputWorld');wo.is_active_output=True;nt.links.new(bg.outputs[0],wo.inputs[0]);bg.inputs[0].default_value=(.18,.18,.18,1);bg.inputs[1].default_value=.1
pkg=json.loads((BASE/'reference-review.json').read_text());spec=pkg['views'][0]['candidate_camera']
for o in sc.objects:
 if o.type=='LIGHT':o.hide_render=True
for k,l in enumerate(spec['lighting']['areas']):
 ld=bpy.data.lights.new('V28_Review_'+str(k),'AREA');ld.energy=l['watts'];ld.shape=l['shape'];ld.size=l['size'];ld.color=l['color'];ob=bpy.data.objects.new(ld.name,ld);sc.collection.objects.link(ob);ob.matrix_world=Matrix(l['matrix'])
cam=bpy.data.objects.new('V28_ReviewCamera',bpy.data.cameras.new('V28_ReviewCamera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
master=bpy.data.objects['MIA_V27_Foundation_Face']
for k in master.data.shape_keys.key_blocks:k.value=0
hair=[o for o in sc.objects if o.type=='MESH' and any(t in o.name for t in ['Hair','Braid','RootLining','Crown','Gather']) and not o.hide_render]
matte=bpy.data.materials.new('V28_NEUTRAL_MATTE');matte.use_nodes=True;matte.node_tree.nodes.clear();bs=matte.node_tree.nodes.new('ShaderNodeBsdfPrincipled');mo=matte.node_tree.nodes.new('ShaderNodeOutputMaterial');mo.is_active_output=True;matte.node_tree.links.new(bs.outputs[0],mo.inputs[0]);bs.inputs['Base Color'].default_value=(.23,.23,.23,1);bs.inputs['Roughness'].default_value=.85
skin=bpy.data.objects['MIA_V27_SharedHeadBody'];original=list(skin.data.materials)
extra_skin=[o for o in sc.objects if o.type=='MESH' and o.name.startswith('V28G_InnerLid') and not o.hide_render];extra_original={o.name:list(o.data.materials) for o in extra_skin}
records=[]
def render(name,view,hideoff=False,mat=False):
 cam.matrix_world=Matrix(view['matrix']);cam.data.ortho_scale=view['ortho_scale'];cam.data.shift_x=0;cam.data.shift_y=0
 for o in hair:o.hide_render=hideoff
 for i,m in enumerate(original):skin.data.materials[i]=matte if mat else m
 for ob in extra_skin:
  for i,m in enumerate(extra_original[ob.name]):ob.data.materials[i]=matte if mat else m
 bpy.context.view_layer.update();sc.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
 actual=json.loads(json.dumps(view));actual['resolution']=[sc.render.resolution_x,sc.render.resolution_y];actual['lighting']['areas']=[dict(l,watts=bpy.data.lights['V28_Review_'+str(i)].energy) for i,l in enumerate(actual['lighting']['areas'])];actual['lighting']['world_linear']=list(bg.inputs[0].default_value)[:3];actual['lighting']['world_strength']=bg.inputs[1].default_value;actual['frame']=sc.frame_current;actual['active_shape_keys']={k.name:k.value for k in master.data.shape_keys.key_blocks if k.value};rig=next(m.object for m in master.modifiers if m.type=='ARMATURE');hb=rig.pose.bones['J_Bip_C_Head'];actual['head_eye_pose']={'armature':rig.name,'head_bone':hb.name,'head_matrix_basis':[list(r) for r in hb.matrix_basis],'eye_pose':'rest; master shape keys recorded above'}
 records.append({'id':name,'native_path':str(native),'native_sha256':NATIVE_SHA,'camera':actual,'hair_temporarily_hidden':[o.name for o in hair] if hideoff else [],'material':'neutral matte all skin slots,linear BaseColor.23 roughness.85' if mat else 'production','master_keys':actual['active_shape_keys']})
if mode=='quick':
 for vi,kind in [(0,'toon'),(0,'matte'),(2,'matte'),(1,'matte')]:
  v=pkg['views'][vi];render(v['id']+'-'+kind+'-quick',v['candidate_camera'],True,kind=='matte')
elif mode=='source4':
 for v in pkg['views']:
  sp=v['candidate_camera'];render(v['id']+'-hairON',sp);render(v['id']+'-hairOFF',sp,True);render(v['id']+'-matte',sp,True,True)
elif mode=='unilateral':
 for side in ['R','L']:
  for k in master.data.shape_keys.key_blocks:k.value=1 if k.name.endswith('Fcl_EYE_Close_'+side) else 0
  for vi in [0,2]:
   v=pkg['views'][vi];render(v['id']+'-Close_'+side,v['candidate_camera'],True)
elif mode=='blink':
 for v in [pkg['views'][0],pkg['views'][2],pkg['views'][3],pkg['views'][1]]:
  for value in [0,.5,1]:
   for k in master.data.shape_keys.key_blocks:k.value=value if k.name.endswith('Fcl_EYE_Close') else 0
   render(v['id']+'-blink'+str(value),v['candidate_camera'],True)
elif mode=='close_materials':
 for k in master.data.shape_keys.key_blocks:k.value=1 if k.name.endswith('Fcl_EYE_Close') else 0
 for o in sc.objects:
  if 'BoundaryRibbon' in o.name or o.name.startswith('V28_LashFan_'):o.hide_render=True
 clear=bpy.data.materials.new('V28_TEMP_CLEAR');clear.use_nodes=True;nn=clear.node_tree.nodes;nn.clear();tt=nn.new('ShaderNodeBsdfTransparent');oo=nn.new('ShaderNodeOutputMaterial');oo.is_active_output=True;clear.node_tree.links.new(tt.outputs[0],oo.inputs[0]);mats=list(master.data.materials);sp=dict(pkg['views'][1]['candidate_camera']);sp['ortho_scale']=.14
 for name,slots in [('NOsclera',[1]),('NOiris',[5]),('NOlegacy',[6,8])]:
  for j,m in enumerate(mats):master.data.materials[j]=clear if j in slots else m
  render('profile-closed-'+name,sp,True)
elif mode=='close_owner':
 for k in master.data.shape_keys.key_blocks:k.value=1 if k.name.endswith('Fcl_EYE_Close') else 0
 for vi in [1,2]:
  v=pkg['views'][vi];sp=dict(v['candidate_camera']);sp['ortho_scale']=.14;master.hide_render=True;render(v['id']+'-closed-NOmaster',sp,True);master.hide_render=False
  bands=[o for o in sc.objects if ('BoundaryRibbon' in o.name and not o.hide_render) or o.name.startswith('V28_LashFan_')]
  for o in bands:o.hide_render=True
  render(v['id']+'-closed-NObands',sp,True)
  for o in bands:o.hide_render=False
elif mode=='isolate':
 feature=[o for o in sc.objects if o.type=='MESH' and (o==master or 'BoundaryRibbon' in o.name or o.name.startswith('V28_LashFan_')) and not o.hide_render]
 for o in feature:o.hide_render=True
 for vi in [0,2,1]:
  v=pkg['views'][vi];sp=dict(v['candidate_camera']);sp['ortho_scale']=.14;render(v['id']+'-skinONLY-macro',sp,True,True)
 for o in feature:o.hide_render=False
 sp=dict(pkg['views'][0]['candidate_camera']);sp['ortho_scale']=.14;render('front-orbit-macro',sp,True,True)
 bpy.context.view_layer.update();ev=master.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();verts=[ev.matrix_world@v.co for v in me.vertices];faces=[list(f.vertices) for f in me.polygons if f.material_index in [1,5]];mesh=bpy.data.meshes.new('V28_IsolatedGlobe');mesh.from_pydata(verts,[],faces)
 for m in me.materials:mesh.materials.append(m)
 for f,src in zip(mesh.polygons,[f for f in me.polygons if f.material_index in [1,5]]):f.material_index=src.material_index
 globe=bpy.data.objects.new('V28_IsolatedGlobe',mesh);sc.collection.objects.link(globe);ev.to_mesh_clear();skin.hide_render=True
 for o in feature:o.hide_render=True
 for vi in [0,1]:
  sp=dict(pkg['views'][vi]['candidate_camera']);sp['ortho_scale']=.14;render(pkg['views'][vi]['id']+'-globeONLY-macro',sp,True)
elif mode=='follow':
 rig=next(m.object for m in master.modifiers if m.type=='ARMATURE');bone=rig.pose.bones['J_Bip_C_Head'];bone.rotation_mode='XYZ'
 for yaw in [-12,12]:
  bone.rotation_euler[1]=math.radians(yaw);bpy.context.view_layer.update();render('head-follow'+str(yaw),pkg['views'][0]['candidate_camera'],True)
elif mode=='extra':
 for yaw,pitch,label in [(0,-18,'lowfront'),(-35,0,'opposite35'),(45,0,'oblique45'),(90,0,'profile90')]:
  y=math.radians(yaw);p=math.radians(pitch);target=Vector((0,0,1.55));loc=target+Vector((2*math.sin(y)*math.cos(p),-2*math.cos(y)*math.cos(p),2*math.sin(p)));cam.location=loc;cam.rotation_euler=(target-loc).to_track_quat('-Z','Y').to_euler();bpy.context.view_layer.update()
  sp=dict(spec);sp['matrix']=[list(r) for r in cam.matrix_world];sp['ortho_scale']=.29
  render(label+'-matte',sp,True,True)
(OUT/(mode+'-records.json')).write_text(json.dumps(records,indent=2));print('RENDERS_DONE',tag,mode)
