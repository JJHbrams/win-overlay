"""Standalone read-only integrated review. No native save, GUI, geometry edits or art approval."""
import argparse,sys,json,hashlib,math,shutil
from pathlib import Path
import bpy
from mathutils import Vector,Matrix

ap=argparse.ArgumentParser()
for name in ['baseline','candidate','face-package','body-package','hair-package','output-dir']:ap.add_argument('--'+name,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);OUT=Path(a.output_dir).resolve();OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
artifact=lambda p:{'path':str(Path(p).resolve()),'sha256':sha(p)}
sources={role:Path(getattr(a,role)).resolve() for role in ['baseline','candidate']};source_art={k:artifact(v) for k,v in sources.items()}
packages={part:Path(getattr(a,part+'_package')).resolve() for part in ['face','body','hair']};data={k:json.loads(v.read_text(encoding='utf-8-sig')) for k,v in packages.items()}
deps=OUT/'dependencies';deps.mkdir(exist_ok=True);shutil.copyfile(__file__,deps/Path(__file__).name)
for part,p in packages.items():shutil.copyfile(p,deps/(part+'-source-package.json'))

def render_visible():
 ids=set()
 def walk(lc,hidden=False):
  hidden=hidden or lc.exclude or lc.collection.hide_render
  if not hidden:ids.update(o.as_pointer() for o in lc.collection.objects)
  for ch in lc.children:walk(ch,hidden)
 walk(bpy.context.view_layer.layer_collection)
 return [o for o in bpy.context.scene.objects if o.type=='MESH' and o.as_pointer() in ids and not o.hide_render]

def keys():
 return {o.name:{k.name:float(k.value) for k in o.data.shape_keys.key_blocks[1:] if abs(k.value)>1e-8} for o in render_visible() if o.data.shape_keys and any(abs(k.value)>1e-8 for k in o.data.shape_keys.key_blocks[1:])}

def hair_hide():
 members={o.as_pointer() for c in bpy.data.collections if 'HAIR' in c.name.upper() for o in c.all_objects}
 for o in bpy.context.scene.objects:
  if o.type=='MESH' and (o.as_pointer() in members or any(x in o.name for x in ['Hair','HAIR','PIXAL'])):o.hide_render=True

def material(kind):
 m=bpy.data.materials.new('IntegratedReview_'+kind);m.use_nodes=True;n=m.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial')
 if kind=='clay':node=n.new('ShaderNodeBsdfDiffuse');node.inputs['Color'].default_value=(.18,.18,.18,1)
 else:
  node=n.new('ShaderNodeEmission');uv=n.new('ShaderNodeTexCoord');c=n.new('ShaderNodeTexChecker');c.inputs['Scale'].default_value=40;m.node_tree.links.new(uv.outputs['UV'],c.inputs['Vector']);m.node_tree.links.new(c.outputs['Color'],node.inputs['Color'])
 m.node_tree.links.new(node.outputs[0],out.inputs['Surface']);return m

def aim(obj,pos,target):obj.location=pos;obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()

def setup(path,part):
 bpy.ops.wm.open_mainfile(filepath=str(path),use_scripts=False);s=bpy.context.scene;s.frame_set(1)
 for o in render_visible():
  if o.data.shape_keys:
   for k in o.data.shape_keys.key_blocks[1:]:k.value=0
 bpy.context.view_layer.update()
 s.render.engine='BLENDER_EEVEE';s.render.use_freestyle=False;s.render.film_transparent=True;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.render.resolution_percentage=100
 s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
 world=bpy.data.worlds.new('IntegratedReview_World');world.use_nodes=True;bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.18,.18,.18,1);bg.inputs['Strength'].default_value=.1;s.world=world
 for o in s.objects:
  if o.type=='LIGHT':o.hide_render=True
 lamps=[]
 for role in ['Key','Fill','Rim']:
  light=bpy.data.lights.new('IntegratedReview_'+role,'AREA');light.shape='DISK';light.color=(1,1,1);o=bpy.data.objects.new(light.name,light);s.collection.objects.link(o);lamps.append(o)
 c=bpy.data.cameras.new('IntegratedReview_Camera');cam=bpy.data.objects.new(c.name,c);s.collection.objects.link(cam);s.camera=cam
 if part=='body':
  hair_hide();clay=material('clay')
  for name in ['MIA_V06_BODY_SKIN','MIA_V14_SculptedSkin']:
   for slot in bpy.data.objects[name].material_slots:slot.material=clay
 return s,lamps

def camera_and_lights(s,lamps,source,part):
 cam=s.camera;cam.matrix_world=Matrix(source['matrix']);cam.data.type=source['projection'];cam.data.ortho_scale=source['ortho_scale'];cam.data.shift_x,cam.data.shift_y=source['lens_shift'];s.render.resolution_x,s.render.resolution_y=source['resolution'];s.render.pixel_aspect_x,s.render.pixel_aspect_y=source['pixel_aspect'];s.frame_set(source['frame'])
 body=part=='body';yaw=math.atan2(cam.location.x,-cam.location.y);settings=[((-1.8,-3,2.5),200,2),((2,-2,1.7),70,2),((0,2,2.3),30,1.8)] if body else [((-.6,-1,2.2),60,1),((.8,-.8,1.8),15,1.5),((0,.9,2.05),8,.8)]
 for o,(loc,power,size) in zip(lamps,settings):
  x,y,z=loc;pos=(x*math.cos(yaw)-y*math.sin(yaw),x*math.sin(yaw)+y*math.cos(yaw),z) if body else loc;aim(o,pos,(0,0,.9 if body else 1.55));o.data.energy=power;o.data.size=size
 bpy.context.view_layer.update()

def record(s,lamps):
 c=s.camera
 return {'projection':c.data.type,'matrix':[list(x) for x in c.matrix_world],'ortho_scale':c.data.ortho_scale,'frame':s.frame_current,'active_shape_keys':keys(),'lighting':{'areas':[{'role':role,'matrix':[list(x) for x in o.matrix_world],'watts':o.data.energy,'size':o.data.size,'shape':o.data.shape,'color':list(o.data.color)} for role,o in zip(['Key','Fill','Rim'],lamps)],'world_linear':[.18,.18,.18],'world_strength':.1,'other_lights_disabled':True},'color_management':{'view_transform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma},'resolution':[s.render.resolution_x,s.render.resolution_y],'pixel_aspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'lens_shift':[c.data.shift_x,c.data.shift_y],'freestyle':s.render.use_freestyle,'engine':s.render.engine}

def routes():
 mats={}
 for o in render_visible():
  for slot in o.material_slots:
   m=slot.material
   if not m or m.name in mats:continue
   mats[m.name]={'owners':[ob.name for ob in render_visible() if any(sl.material==m for sl in ob.material_slots)],'use_backface_culling':m.use_backface_culling,'nodes':[],'links':[]}
   if not m.use_nodes:continue
   for n in m.node_tree.nodes:
    item={'name':n.name,'type':n.bl_idname}
    if n.type=='TEX_IMAGE' and n.image:item['image']={'name':n.image.name,'colorspace':n.image.colorspace_settings.name,'packed_sha256':hashlib.sha256(n.image.packed_file.data).hexdigest() if n.image.packed_file else None}
    if n.type=='UVMAP':item['uv_map']=n.uv_map
    mats[m.name]['nodes'].append(item)
   mats[m.name]['links']=[[[l.from_node.name,l.from_socket.name],[l.to_node.name,l.to_socket.name]] for l in m.node_tree.links]
 return mats

records={};material_records={}
for role,path in sources.items():
 for part,package in data.items():
  s,lamps=setup(path,part);material_records[role+'/'+part]=routes()
  for row in package['views']:
   view=row['id'];camera_and_lights(s,lamps,row['baseline_camera'],part);folder=OUT/role/part;folder.mkdir(parents=True,exist_ok=True);p=folder/(view+'.png');s.render.filepath=str(p);bpy.ops.render.render(write_still=True);records[role+'/'+part+'/'+view]={'render':artifact(p),'camera':record(s,lamps),'visible_mesh_owners':[o.name for o in render_visible()]}
  print('FINISHED_PART',role,part,flush=True)
 (OUT/'render-records.json').write_text(json.dumps(records,indent=2))

# Small integrated diagnostics: neutral face, color-only face, checker face/hair/body, half close.
diagnostics={};front=next(v for v in data['face']['views'] if v['id']=='front')['baseline_camera']
def diag_save(name,s,lamps):
 folder=OUT/'diagnostics';folder.mkdir(exist_ok=True);p=folder/(name+'.png');s.render.filepath=str(p);bpy.ops.render.render(write_still=True);diagnostics[name]={'render':artifact(p),'camera':record(s,lamps)}
s,lamps=setup(sources['candidate'],'face');hair_hide();camera_and_lights(s,lamps,front,'face');diag_save('face_neutral_bare',s,lamps)
for name in ['MIA_V14_SculptedSkin','MIA_V06_BODY_SKIN']:
 for slot in bpy.data.objects[name].material_slots:
  if not slot.material or not slot.material.use_nodes:continue
  m=slot.material.copy();slot.material=m;n=m.node_tree.nodes;mul=n.get('PigmentTimesControlledLight')
  if mul and mul.inputs[1].is_linked:
   em=next((x for x in n if x.type=='EMISSION'),None)
   if em:m.node_tree.links.new(mul.inputs[1].links[0].from_socket,em.inputs[0])
diag_save('face_color_only',s,lamps)
s,lamps=setup(sources['candidate'],'face');hair_hide();camera_and_lights(s,lamps,front,'face');bpy.data.objects['MIA_V14_SculptedSkin'].material_slots[7].material=material('checker');diag_save('face_uv',s,lamps)
s,lamps=setup(sources['candidate'],'face');hair_hide();camera_and_lights(s,lamps,front,'face');skin=bpy.data.objects['MIA_V14_SculptedSkin'];key=next(k for k in skin.data.shape_keys.key_blocks if k.name.endswith('Fcl_EYE_Close'));key.value=.5;bpy.context.view_layer.update();diag_save('face_close_half',s,lamps)
for part,name,owner in [('hair','hair_uv','MIA_V17_PIXAL_DetailedHair'),('body','body_uv','MIA_V06_BODY_SKIN')]:
 s,lamps=setup(sources['candidate'],part);camera_and_lights(s,lamps,next(v for v in data[part]['views'] if v['id']=='front')['baseline_camera'],part);check=material('checker')
 for slot in bpy.data.objects[owner].material_slots:slot.material=check
 diag_save(name,s,lamps)
for part,package in data.items():
 for row in package['views']:assert records['baseline/'+part+'/'+row['id']]['camera']==records['candidate/'+part+'/'+row['id']]['camera'],(part,row['id'])
for role,p in sources.items():assert sha(p)==source_art[role]['sha256']
(OUT/'render-records.json').write_text(json.dumps(records,indent=2));(OUT/'material-routes.json').write_text(json.dumps(material_records,indent=2));(OUT/'diagnostics.json').write_text(json.dumps(diagnostics,indent=2))
(OUT/'render-manifest.json').write_text(json.dumps({'baseline_native':source_art['baseline'],'candidate_native':source_art['candidate'],'input_packages':{k:artifact(v) for k,v in packages.items()},'renderer':artifact(__file__),'same_conditions_all_views':True,'native_saved':False,'native_hashes_unchanged':True,'keys_policy':'Actual render-visible mesh non-Basis nonzero keys only; visible expression keys neutralized in-memory for matched neutral comparison; hidden archived key values excluded.','freestyle_policy':'OFF for matched review, including neutral body; production materials retained for face/hair. Separate root ink tests excluded.','art_status':'DIAGNOSTIC WIP ONLY; no ART/animation pass inferred.'},indent=2));print('INTEGRATED_REVIEW_DONE',flush=True)
