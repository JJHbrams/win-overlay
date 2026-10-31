import bpy,math,json,hashlib
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent;files={'before':OUT.parent/'mia-body-correction-v20/Mia_BodyCorrection_v20.blend','after':OUT/'Mia_HairCorrection_v20.blend'};sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();hashes={k:sha(p) for k,p in files.items()}
for state,src in files.items():
 bpy.ops.wm.open_mainfile(filepath=str(src));s=bpy.context.scene
 for o in s.objects:
  if o.type=='LIGHT':o.hide_render=True
 world=bpy.data.worlds.new('V20_DiagnosticWorld');world.use_nodes=True;bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(.18,.18,.18,1);bg.inputs[1].default_value=.10;s.world=world
 col=bpy.data.collections.new('V20_ClayVisible');s.collection.children.link(col)
 for name in ['MIA_V06_BODY_SKIN','MIA_V14_SculptedSkin']:col.objects.link(bpy.data.objects[name])
 for o in bpy.data.collections['MIA_V17_PIXAL_HAIR'].all_objects:
  if o.type=='MESH' and not o.hide_render:col.objects.link(o)
 mat=bpy.data.materials.new('V20_Clay');mat.use_nodes=True;mat.node_tree.nodes.clear();out=mat.node_tree.nodes.new('ShaderNodeOutputMaterial');bs=mat.node_tree.nodes.new('ShaderNodeBsdfDiffuse');bs.inputs[0].default_value=(.18,.18,.18,1);mat.node_tree.links.new(bs.outputs[0],out.inputs[0])
 layer=s.view_layers.new('V20_ActualHairClay');layer.material_override=mat
 for c in layer.layer_collection.children:c.exclude=c.name!=col.name
 for l in s.view_layers:l.use=l==layer
 bpy.context.window.view_layer=layer
 lights=[]
 for name,pos,power,size in [('Key',(-.6,-1,2.2),60,1),('Fill',(.8,-.8,1.8),15,1.5),('Edge',(0,.9,2.05),8,.8)]:
  d=bpy.data.lights.new('V20_'+name,'AREA');d.energy=power;d.size=size;o=bpy.data.objects.new(d.name,d);col.objects.link(o);lights.append((o,pos))
 cam=s.camera;cam.data.ortho_scale=.52;s.render.resolution_x=s.render.resolution_y=1000;s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
 for name,deg in [('profile',90),('back',180)]:
  t=math.radians(deg);cam.location=(2*math.sin(t),-2*math.cos(t),1.475);cam.rotation_euler=(Vector((0,0,1.475))-cam.location).to_track_quat('-Z','Y').to_euler()
  for o,(x,y,z) in lights:o.location=(x*math.cos(t)-y*math.sin(t),x*math.sin(t)+y*math.cos(t),z);o.rotation_euler=(Vector((0,0,1.55))-o.location).to_track_quat('-Z','Y').to_euler()
  s.render.filepath=str(OUT/(state+'_clay_'+name+'.png'));bpy.ops.render.render(write_still=True,layer=layer.name)
assert hashes=={k:sha(p) for k,p in files.items()};(OUT/'clay-evidence.json').write_text(json.dumps({'sources_unchanged':hashes,'mode':'actual skin and visible hair, diffuse .18, standard none exposure0 gamma1; camera-relative white rig; no save','ortho_scale':.52,'target_z':1.475},indent=2))
