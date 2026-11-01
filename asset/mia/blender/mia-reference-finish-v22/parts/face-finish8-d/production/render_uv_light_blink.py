"""Actual current shader color-only, UV checker, light and limited blink checks."""
import ast,sys,json
from pathlib import Path
src=Path(__file__).resolve().parent.parent/'finish-7/render_source_motion.py';tree=ast.parse(src.read_text());nodes=[]
for n in tree.body:
 if isinstance(n,ast.For):break
 nodes.append(n)
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(src),'exec'))
front={'id':'front','yaw':0,'elevation':0,'roll':0};oblique={'id':'oblique','yaw':30,'elevation':0,'roll':0}
for mode in ['native_closeup','color_only','uv_checker','light_left','light_right']:
 s=load(False,False);skin=bpy.data.objects['MIA_V14_SculptedSkin'];mat=skin.data.materials[7];nt=mat.node_tree
 for k in skin.data.shape_keys.key_blocks:k.value=0
 if mode=='color_only':
  em=next(n for n in nt.nodes if n.type=='EMISSION');nt.links.new(nt.nodes['FINISH8_FineLinePigment'].outputs['Color'],em.inputs['Color'])
 if mode=='uv_checker':
  check=bpy.data.materials.new('READONLY_ACTUAL_UV_CHECKER');check.use_nodes=True;n=check.node_tree.nodes;n.clear();uv=n.new('ShaderNodeUVMap');uv.uv_map='UVMap';tex=n.new('ShaderNodeTexChecker');tex.inputs['Scale'].default_value=40;tex.inputs['Color1'].default_value=(.07,.18,.35,1);tex.inputs['Color2'].default_value=(.7,.78,.85,1);em=n.new('ShaderNodeEmission');out=n.new('ShaderNodeOutputMaterial');check.node_tree.links.new(uv.outputs['UV'],tex.inputs['Vector']);check.node_tree.links.new(tex.outputs['Color'],em.inputs['Color']);check.node_tree.links.new(em.outputs[0],out.inputs['Surface']);skin.data.materials[7]=check
 if mode.startswith('light_'):
  for o in s.objects:
   if o.type=='LIGHT':o.hide_render=True
  lamp=bpy.data.lights.new('ACTUAL_DIRECTION_PROBE','AREA');lamp.energy=100;lamp.shape='DISK';lamp.size=.5;o=bpy.data.objects.new('ACTUAL_DIRECTION_PROBE',lamp);s.collection.objects.link(o);r.aim(o,(-.5 if mode=='light_left' else .5,-.6,1.8),(0,0,1.54))
 for v in [front,oblique]:
  r.camera(s,v);s.camera.location.z-=.01;s.camera.data.ortho_scale=.22;s.render.filepath=str(OUT/(mode+'_'+v['id']+'.png'));bpy.context.view_layer.update();bpy.ops.render.render(write_still=True);rec=r.record(s,v,mode);rec['ortho_scale']=.22;records.append({'label':mode+'_'+v['id'],'render':r.artifact(s.render.filepath),'camera':rec})
s=load(False,False);keys=bpy.data.objects['MIA_V14_SculptedSkin'].data.shape_keys.key_blocks
for value in [0,.5,1]:
 for k in keys:k.value=0
 keys['Face.M_F00_000_00_Fcl_EYE_Close'].value=value
 for yaw in [0,30,-30,60]:render(s,'blink_%03d_yaw%+03d'%(round(value*100),yaw),{'id':'blink','yaw':yaw,'elevation':0,'roll':0},'native actual blink')
assert r.sha(SOURCE)==source_sha
(OUT/'render-records.json').write_text(json.dumps({'source':r.artifact(SOURCE),'recipe':r.artifact(__file__),'records':records,'limits':'Checker/color-only/light tests are temporary readonly material/light changes; native geometry untouched. Limited symmetric blink only, not all-expression certification.'},indent=2));print('UV_LIGHT_BLINK_DONE',len(records))
