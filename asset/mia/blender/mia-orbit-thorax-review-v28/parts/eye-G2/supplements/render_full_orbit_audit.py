import bpy,json,math,sys,hashlib
from pathlib import Path
from mathutils import Vector
O=Path(__file__).parent;OUT=O/'full-orbit-audit';OUT.mkdir(exist_ok=True);args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['critical'];mode=args[0];native=O/(args[1] if len(args)>1 else 'Mia_Orbit_v28_F.blend');tag=native.stem.rsplit('_',1)[-1];sha=hashlib.sha256(native.read_bytes()).hexdigest();assert tag!='F' or sha=='bdee6f4558fe05a870bf85ec4d188bebfcf2f483e9a407f3411704dcedd0cd26';bpy.ops.wm.open_mainfile(filepath=str(native));sc=bpy.context.scene;master=bpy.data.objects['MIA_V27_Foundation_Face'];skin=bpy.data.objects['MIA_V27_SharedHeadBody'];keys=master.data.shape_keys.key_blocks;ocular=[o for o in sc.objects if o.type=='MESH' and (o.name.startswith('V28G_Sclera_') or o.name.startswith('V28G_Iris_')) and not o.hide_render];walls=[o for o in sc.objects if o.type=='MESH' and o.name.startswith('V28G_InnerLid_') and not o.hide_render]
for k in keys:k.value=0
sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=640 if mode in ['critical','visible','focus','trial','deform','wallproof'] else 512;sc.render.resolution_y=sc.render.resolution_x;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.use_freestyle=False;sc.render.film_transparent=False;sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
world=bpy.data.worlds.new('V28_OrbitalAuditWorld');world.use_nodes=True;n=world.node_tree.nodes;n.clear();bg=n.new('ShaderNodeBackground');wo=n.new('ShaderNodeOutputWorld');wo.is_active_output=True;world.node_tree.links.new(bg.outputs[0],wo.inputs[0]);bg.inputs[0].default_value=(.12,.12,.12,1);bg.inputs[1].default_value=.15;sc.world=world
for o in sc.objects:
 if o.type=='LIGHT':o.hide_render=True
lights=[]
for name,pos,power,size in [('Key',(-.6,-1,2.2),60,1),('Fill',(.8,-.8,1.8),15,1.5),('Rim',(0,.9,2),8,.8)]:
 d=bpy.data.lights.new('V28_Orbital_'+name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(d.name,d);sc.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,1.54))-o.location).to_track_quat('-Z','Y').to_euler();lights.append({'name':name,'power_W':power,'size_m':size,'position':pos})
def physical(name,c):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;n.clear();p=n.new('ShaderNodeBsdfPrincipled');o=n.new('ShaderNodeOutputMaterial');o.is_active_output=True;m.node_tree.links.new(p.outputs[0],o.inputs[0]);p.inputs['Base Color'].default_value=(c,c,c,1);p.inputs['Roughness'].default_value=.8;return m
gray=physical('V28_PhysicalSkin',.23);white=physical('V28_PhysicalSclera',.52);iris=physical('V28_PhysicalIris',.14);white.use_backface_culling=True
if mode in ['visible','sweep','focus','trial','deform','wallproof']:
 iris=(next(o for o in ocular if 'Iris_' in o.name).data.materials[0] if ocular else master.data.materials[5]).copy();iris.name='V28_PhysicalIris_PreserveActualUVAlpha';ip=iris.node_tree.nodes.new('ShaderNodeBsdfPrincipled');ip.inputs['Base Color'].default_value=(.14,.14,.14,1);ip.inputs['Roughness'].default_value=.8
 for em in [n for n in iris.node_tree.nodes if n.type=='EMISSION']:
  for link in list(em.outputs[0].links):iris.node_tree.links.new(ip.outputs[0],link.to_socket)
clear=bpy.data.materials.new('V28_AuditTransparent');clear.use_nodes=True;clear.node_tree.nodes.clear();t=clear.node_tree.nodes.new('ShaderNodeBsdfTransparent');oo=clear.node_tree.nodes.new('ShaderNodeOutputMaterial');oo.is_active_output=True;clear.node_tree.links.new(t.outputs[0],oo.inputs[0])
wire=physical('V28_WallPhysicalWire',.23);nn=wire.node_tree.nodes;ll=wire.node_tree.links;out=next(n for n in nn if n.type=='OUTPUT_MATERIAL' and n.is_active_output);prior=out.inputs[0].links[0].from_socket;wf=nn.new('ShaderNodeWireframe');wf.use_pixel_size=True;wf.inputs[0].default_value=.75;ink=nn.new('ShaderNodeEmission');ink.inputs[0].default_value=(.005,.005,.005,1);mix=nn.new('ShaderNodeMixShader');ll.new(wf.outputs[0],mix.inputs[0]);ll.new(prior,mix.inputs[1]);ll.new(ink.outputs[0],mix.inputs[2]);ll.new(mix.outputs[0],out.inputs[0])
normalmat=bpy.data.materials.new('V28_ActualWorldNormalDiagnostic');normalmat.use_nodes=True;nn=normalmat.node_tree.nodes;nn.clear();gg=nn.new('ShaderNodeNewGeometry');scal=nn.new('ShaderNodeVectorMath');scal.operation='MULTIPLY';scal.inputs[1].default_value=(.5,.5,.5);add=nn.new('ShaderNodeVectorMath');add.operation='ADD';add.inputs[1].default_value=(.5,.5,.5);em=nn.new('ShaderNodeEmission');out=nn.new('ShaderNodeOutputMaterial');out.is_active_output=True;ll=normalmat.node_tree.links;ll.new(gg.outputs['Normal'],scal.inputs[0]);ll.new(scal.outputs[0],add.inputs[0]);ll.new(add.outputs[0],em.inputs[0]);ll.new(em.outputs[0],out.inputs[0])
skinm=list(skin.data.materials);masterm=list(master.data.materials);extra={o.name:list(o.data.materials) for o in ocular+walls};visible=[o for o in sc.objects if o.type=='MESH' and not o.hide_render];hair=[o for o in visible if any(t in o.name for t in ['Hair','Braid','RootLining','Crown','Gather'])];lash=[o for o in visible if 'BoundaryRibbon' in o.name or o.name.startswith('V28_LashFan_')];cam=bpy.data.objects.new('V28_OrbitalAuditCamera',bpy.data.cameras.new('V28_OrbitalAuditCamera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.20;target=Vector((0,-.01,1.54));records=[]
def render(name,yaw,pitch,which='geometry'):
 for o in visible:o.hide_render=True
 if which in ['geometry','production','skinONLY','normal']:skin.hide_render=False
 if which in ['geometry','production','globeONLY']:master.hide_render=False
 if which in ['geometry','production','skinONLY','normal','wallONLY','wallWIRE']:
  for ob in walls:ob.hide_render=False
 if which in ['geometry','production','globeONLY']:
  for ob in ocular:ob.hide_render=False
 if which=='globeONLY' and ocular:master.hide_render=True
 if which in ['geometry','production','lashONLY']:
  for o in lash:o.hide_render=False
 for i,m in enumerate(skinm):skin.data.materials[i]=m if which=='production' else (normalmat if which=='normal' else gray)
 for ob in walls:
  for i,m in enumerate(extra[ob.name]):ob.data.materials[i]=m if which=='production' else (wire if which=='wallWIRE' else normalmat if which=='normal' else gray)
 for ob in ocular:
  for i,m in enumerate(extra[ob.name]):ob.data.materials[i]=m if which=='production' else (iris if 'Iris_' in ob.name else white)
 for i,m in enumerate(masterm):master.data.materials[i]=m if which in ['production','geometry'] else clear
 if which in ['geometry','globeONLY'] and not ocular:master.data.materials[1]=white;master.data.materials[5]=iris
 y=math.radians(yaw);p=math.radians(pitch);cam.location=target+Vector((2*math.sin(y)*math.cos(p),-2*math.cos(y)*math.cos(p),2*math.sin(p)));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();bpy.context.view_layer.update();folder=OUT/(mode if tag=='F' else mode+'-'+tag);folder.mkdir(exist_ok=True);sc.render.filepath=str(folder/(name+'.png'));bpy.ops.render.render(write_still=True);records.append({'id':name,'native_sha256':sha,'surface_mode':which,'visible_owners':[o.name for o in visible if not o.hide_render],'hair_hidden':[o.name for o in hair],'projection':'ORTHO','ortho_scale':cam.data.ortho_scale,'yaw_pitch_roll_deg':[yaw,pitch,0],'camera_matrix':[list(r) for r in cam.matrix_world],'resolution':[sc.render.resolution_x,sc.render.resolution_y],'pose':'actualkeysrecorded,restHead','actual_shape_keys':{k.name:k.value for k in keys if k.value},'lights':lights,'world':{'linear':.12,'strength':.15},'display':'Standard/None exposure0 gamma1','geometry_shader':'Active Physical Principled gray23%skin/52%sclera/14%iris roughness.8; whitebackfaceculling and actualirisUVradialalpha preserved' if which!='production' else 'Native production shaders'})
if mode=='wallproof':
 target=Vector((.036,-.060,1.540));cam.data.ortho_scale=.070
 for label,y,p in [('HIGH',30,35),('LOW',30,-30),('SIDE',80,0)]:
  for kind in ['skinONLY','wallONLY','wallWIRE','normal']:render(label+'-'+kind,y,p,kind)
elif mode=='deform':
 for value in [.5,1]:
  for k in keys:k.value=value if k.name.endswith('Fcl_EYE_Close') else 0
  for label,y,p in [('frontHIGH',0,50),('frontLOW',0,-35),('lowRIGHT',35,-30)]:render(label+'-Close'+str(value),y,p,'production')
elif mode=='trial':
 for label,y,p in [('front',0,0),('profile',80,0),('frontHIGH',0,50),('frontLOW',0,-35),('lowRIGHT',35,-30)]:
  render(label+'-geometry',y,p);render(label+'-production',y,p,'production')
  if label in ['profile','frontHIGH','lowRIGHT']:render(label+'-skinONLY',y,p,'skinONLY')
 for label,y,p in [('front',0,0),('profile90',90,0)]:render(label+'-globeONLY',y,p,'globeONLY')
 render('profile90-lashONLY',90,0,'lashONLY')
elif mode in ['critical','visible','focus']:
 views=[('front',0,0),('obliqueR',35,0),('obliqueL',-35,0),('profile',80,0),('frontHIGH',0,50),('frontLOW',0,-35),('lowRIGHT',35,-30),('lowLEFT',-35,-30),('highRIGHT',35,45),('topDOWN',0,75),('bottomUP',0,-55),('profileLOW',80,-30)]
 if mode in ['visible','focus']:views=[views[j] for j in ([0,3,4,5,6] if mode=='focus' else [0,3,4,5,6,8])]
 for label,y,p in views:
  render(label+'-geometry',y,p);render(label+'-skinONLY',y,p,'skinONLY')
 if mode!='focus':
  for label,y,p in (views if mode=='visible' else [views[j] for j in [3,4,5,6,8,10]]):render(label+'-production',y,p,'production')
 for label,y,p in ([('front',0,0),('profile90',90,0)] if mode=='focus' else [('front',0,0),('oblique',35,0),('profile80',80,0),('profile90',90,0),('lowRIGHT',35,-30),('highRIGHT',35,45)]):render(label+'-lashONLY',y,p,'lashONLY')
 for label,y,p in ([('front',0,0),('profile90',90,0)] if mode=='focus' else [('front',0,0),('profile90',90,0),('frontHIGH',0,50),('frontLOW',0,-35)]):render(label+'-globeONLY',y,p,'globeONLY')
else:
 for i in range(73):
  yaw=i*5;pitch=5+40*math.sin(math.radians(yaw*2));render(f'{i:03}',yaw,pitch,'production' if mode=='sweep_prod' else 'geometry')
(OUT/((mode if tag=='F' else mode+'-'+tag)+'-records.json')).write_text(json.dumps(records,indent=2));print('FULL_ORBIT_DONE',mode,tag,len(records))
