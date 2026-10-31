"""Persistent review copy; original meshes, UVs, keys, production materials/maps unchanged."""
import bpy,json,hashlib,struct,math
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent;SRC=Path(r'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v17/integrated-v18/Mia_HeadHair_v18.blend');DST=OUT/'Mia_LookdevReview_v19.blend';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();source_sha=sha(SRC);bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene

def scope():
 r={}
 for o in bpy.data.objects:
  if o.type!='MESH':continue
  data=b''.join(struct.pack('<3f',*v.co) for v in o.data.vertices)+b''.join(struct.pack('<2f',*v.uv) for l in o.data.uv_layers for v in l.data)
  if o.data.shape_keys:data+=b''.join(struct.pack('<3f',*v.co) for k in o.data.shape_keys.key_blocks for v in k.data)
  r[o.name]={'mesh_uv_keys':hashlib.sha256(data).hexdigest(),'material_slots':[x.material.name if x.material else None for x in o.material_slots],'matrix':[list(row) for row in o.matrix_world]}
 return r
before=scope();images={i.name:hashlib.sha256(bytes(i.packed_file.data)).hexdigest() for i in bpy.data.images if i.packed_file}
for image in bpy.data.images:
 if image.packed_file:image.use_fake_user=True
# Keep source world as a fake-user datablock for comparison; active review world is explicit neutral.
s.world.use_fake_user=True;world=bpy.data.worlds.new('V19_NeutralReviewWorld');world.use_nodes=True;bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.18,.18,.18,1);bg.inputs['Strength'].default_value=.10;s.world=world
for o in s.objects:
 if o.type=='LIGHT':o.hide_render=True
rig=bpy.data.collections.new('V19_REVIEW_RIG');s.collection.children.link(rig)
skin=bpy.data.collections.new('V19_DIAGNOSTIC_SKIN_LINKS');s.collection.children.link(skin)
for name in ['MIA_V06_BODY_SKIN','MIA_V14_SculptedSkin']:skin.objects.link(bpy.data.objects[name])
target=Vector((0,0,1.555));lights=[]
for name,loc,energy,size in [('Key',(-.6,-1.,2.2),60,1.),('Fill',(.8,-.8,1.8),15,1.5),('Edge',(0,.9,2.05),8,.8)]:
 d=bpy.data.lights.new('V19_'+name,'AREA');d.energy=energy;d.color=(1,1,1);d.shape='DISK';d.size=size;o=bpy.data.objects.new('V19_'+name,d);rig.objects.link(o);o.location=loc;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler();lights.append({'name':o.name,'location':loc,'energy':energy,'size':size})
cameras=[]
for framing,scale in [('Head',.29),('Hair',.48)]:
 for name,az,el in [('Front',0,0),('Profile',90,0),('Back',180,0),('ThreeQuarterL',45,0),('ThreeQuarterR',-45,0),('Elev20',0,20)]:
  a,e=math.radians(az),math.radians(el);d=bpy.data.cameras.new('V19_'+framing+'_'+name);d.type='ORTHO';d.ortho_scale=scale;d.clip_start=.01;d.clip_end=100;o=bpy.data.objects.new(d.name,d);rig.objects.link(o);o.location=target+Vector((2*math.cos(e)*math.sin(a),-2*math.cos(e)*math.cos(a),2*math.sin(e)));o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler();o['review_target']=list(target);cameras.append({'name':o.name,'scale':scale,'azimuth':az,'elevation':el,'location':list(o.location)})
s.camera=bpy.data.objects['V19_Head_Front'];s.render.engine='BLENDER_EEVEE';s.render.resolution_x=s.render.resolution_y=1000;s.render.resolution_percentage=100;s.render.pixel_aspect_x=s.render.pixel_aspect_y=1;s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1;s.view_settings.use_curve_mapping=False
# Preserve the source beauty layer; diagnostics exclude all source collection roots and use linked originals only.
beauty=s.view_layers[0];beauty['V19_role']='Original production toon materials under controlled review camera/world. Emission is not a physical light response.'
clay=bpy.data.materials.new('V19_DIAGNOSTIC_DiffuseClay');clay.use_nodes=True;n=clay.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfDiffuse');bs.inputs['Color'].default_value=(.18,.18,.18,1);bs.inputs['Roughness'].default_value=0;clay.node_tree.links.new(bs.outputs[0],out.inputs['Surface'])
spec=bpy.data.materials.new('V19_DIAGNOSTIC_SpecularProbe');spec.use_nodes=True;bs=next(n for n in spec.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=(0,0,0,1);bs.inputs['Metallic'].default_value=0;bs.inputs['Roughness'].default_value=.30;bs.inputs['IOR'].default_value=1.45
for name,mat in [('V19_DiffuseClay_SkinOnly',clay),('V19_SpecularProbe_SkinOnly',spec)]:
 layer=s.view_layers.new(name);layer.material_override=mat
 for child in layer.layer_collection.children:child.exclude=child.name not in {rig.name,skin.name}
 layer['V19_role']='Diagnostic shader override on complete linked body and skin only; eye/alpha cards/hair excluded. No model materials replaced.'
s['V19_findings']='Production skin/hair are emission toon; lamps do not meaningfully calibrate their tone. Skin synthetic vector(-.300,-.649,.699),hair(+.300,-.650,.700) retained unchanged.';s['V19_source_sha256']=source_sha;s['V19_review_instructions']='Use named cameras and view layers. Standard/None is controlled REVIEW look; original production look was Standard/Medium High Contrast. Material override layers are temporary diagnostics, not target materials.'
assert scope()==before
bpy.context.window.view_layer=beauty
for layer in s.view_layers:layer.use=layer==beauty
beauty_name=beauty.name
bpy.ops.wm.save_as_mainfile(filepath=str(DST));bpy.ops.wm.open_mainfile(filepath=str(DST));s=bpy.context.scene;assert scope()==before;assert images=={i.name:hashlib.sha256(bytes(i.packed_file.data)).hexdigest() for i in bpy.data.images if i.packed_file}
# Execute supported layer-switch rendering on a fresh-open copy; no post-render save.
checks=[]
for layer_name,camera_name,filename in [(beauty_name,'V19_Head_Front','review_toon_front'),('V19_DiffuseClay_SkinOnly','V19_Head_Front','review_clay_front'),('V19_DiffuseClay_SkinOnly','V19_Head_ThreeQuarterL','review_clay_three_quarter'),('V19_SpecularProbe_SkinOnly','V19_Head_ThreeQuarterL','review_specular_three_quarter')]:
 for layer in s.view_layers:layer.use=layer.name==layer_name
 bpy.context.window.view_layer=s.view_layers[layer_name];s.camera=bpy.data.objects[camera_name];s.render.filepath=str(OUT/(filename+'.png'));bpy.ops.render.render(write_still=True,layer=layer_name);checks.append({'layer':layer_name,'camera':camera_name,'file':filename+'.png'})
assert sha(SRC)==source_sha
r={'source':str(SRC),'source_sha256':source_sha,'review_native_sha256':sha(DST),'recipe_sha256':sha(Path(__file__)),'mesh_coordinates_uv_keys_material_slots_matrix_exact':len(before),'packed_images_byte_exact':len(images),'active_saved_camera':'V19_Head_Front','source_beauty_layer_preserved':s.view_layers[0].name,'review_color_management':'Standard/None exposure0 gamma1','cameras':cameras,'lights':lights,'runtime_checks':checks,'saved_after_checks':False};(OUT/'review-rig-manifest.json').write_text(json.dumps(r,indent=2));print('REVIEW_SHA',r['review_native_sha256'])
