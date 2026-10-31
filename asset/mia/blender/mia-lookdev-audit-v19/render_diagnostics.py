"""Read-only in-memory overrides. Intentionally no save operation."""
import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent;SRC=Path(r'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v17/integrated-v18/Mia_HeadHair_v18.blend');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before=sha(SRC);records=[]
def emitmat(name,color):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;n.clear();em=n.new('ShaderNodeEmission');em.inputs[0].default_value=color;out=n.new('ShaderNodeOutputMaterial');m.node_tree.links.new(em.outputs[0],out.inputs[0]);return m
for mode,angle in [('target',0),('target',45),('lamps_off',0),('unlit_color_signal',0),('uv_checker',0),('diffuse_clay',45),('specular_probe',45)]:
 bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;c=s.camera;t=math.radians(angle);c.location=(2*math.sin(t),-2*math.cos(t),1.555);c.rotation_euler=(Vector((0,0,1.555))-c.location).to_track_quat('-Z','Y').to_euler();c.data.type='ORTHO';c.data.ortho_scale=.48;c.data.shift_x=c.data.shift_y=0;s.render.resolution_x=s.render.resolution_y=1000;s.render.resolution_percentage=100
 body=bpy.data.objects['MIA_V06_BODY_SKIN'];face=bpy.data.objects['MIA_V14_SculptedSkin'];hair=bpy.data.objects['MIA_V17_PIXAL_DetailedHair'];haircol=bpy.data.collections['MIA_V17_PIXAL_HAIR'];owners=[body,face]+list(haircol.objects)
 if mode=='lamps_off':
  for o in s.objects:
   if o.type=='LIGHT':o.data.energy=0
 if mode in ['unlit_color_signal','uv_checker','diffuse_clay','specular_probe']:s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
 if mode=='unlit_color_signal':
  for ob in [body,face,hair]:
   index=7 if ob==face else 0;mat=ob.material_slots[index].material.copy();ob.material_slots[index].material=mat;n=mat.node_tree.nodes;l=mat.node_tree.links;em=next(n for n in n if n.type=='EMISSION');mix=em.inputs[0].links[0].from_node
   # Bypass normal-driven lighting only; preserve pigment and fixed skin base tint / hair tone conversion.
   if ob==hair:l.new(mix.inputs[1].links[0].from_socket,em.inputs[0])
   else:
    for link in list(mix.inputs[2].links):l.remove(link)
    mix.inputs[2].default_value=(.78,.65,.58,1)
 if mode=='uv_checker':
  for ob in owners:
   if not ob.data.uv_layers:continue
   m=emitmat('Diagnostic_checker',(1,1,1,1));n=m.node_tree.nodes;l=m.node_tree.links;uv=n.new('ShaderNodeUVMap');uv.uv_map='MIA_V17_PAINT_UV' if ob==hair else ob.data.uv_layers.active.name;ch=n.new('ShaderNodeTexChecker');ch.inputs['Scale'].default_value=20;ch.inputs['Color1'].default_value=(.08,.18,.20,1);ch.inputs['Color2'].default_value=(.60,.55,.42,1);l.new(uv.outputs[0],ch.inputs['Vector']);em=next(v for v in n if v.type=='EMISSION');l.new(ch.outputs[0],em.inputs[0])
   if ob==face:ob.material_slots[7].material=m
   else:
    for slot in ob.material_slots:slot.material=m
 if mode in ['diffuse_clay','specular_probe']:
  for o in haircol.objects:o.hide_render=True
  # Hide only separate liner meshes; skin/cap remain complete. Eye cards keep their existing alpha.
  for o in s.objects:
   if o.name.startswith(('MIA_V14_UpperLash','MIA_V14_OuterWing')):o.hide_render=True
   if o.type=='LIGHT':o.hide_render=True
  bg=next(n for n in s.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.18,.18,.18,1);bg.inputs['Strength'].default_value=.10
  for name,loc,power,size in [('DiagnosticKey',(-.6,-1.,2.2),60,1.0),('DiagnosticFill',(.8,-.8,1.8),15,1.5)]:
   d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,1.555))-o.location).to_track_quat('-Z','Y').to_euler()
  m=bpy.data.materials.new(mode);m.use_nodes=True;n=m.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial')
  if mode=='diffuse_clay':bs=n.new('ShaderNodeBsdfDiffuse');bs.inputs['Color'].default_value=(.18,.18,.18,1);bs.inputs['Roughness'].default_value=0
  else:bs=n.new('ShaderNodeBsdfPrincipled');bs.inputs['Base Color'].default_value=(0,0,0,1);bs.inputs['Metallic'].default_value=0;bs.inputs['Roughness'].default_value=.30;bs.inputs['IOR'].default_value=1.45
  m.node_tree.links.new(bs.outputs[0],out.inputs['Surface']);face.material_slots[7].material=m
  for slot in body.material_slots:slot.material=m
 name=mode+('_front' if angle==0 else '_three_quarter');s.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True);records.append({'name':name,'camera_location':list(c.location),'ortho_scale':c.data.ortho_scale,'view':s.view_settings.view_transform,'look':s.view_settings.look})
assert sha(SRC)==before;(OUT/'diagnostic-render-evidence.json').write_text(json.dumps({'source_sha256_before':before,'source_sha256_after':sha(SRC),'saved_native':False,'renders':records,'note':'Unlit signal is not certified physical albedo. Specular probe is a temporary test shader, not a delivered material/map.'},indent=2));print('READ_ONLY_SOURCE',before)
