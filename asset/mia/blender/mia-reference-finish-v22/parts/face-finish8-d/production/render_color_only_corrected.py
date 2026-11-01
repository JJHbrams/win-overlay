"""Pigment-only face AND cap/body; native eye materials retained as context."""
import ast,sys,json
from pathlib import Path
src=Path(__file__).resolve().parent.parent/'finish-7/render_source_motion.py';tree=ast.parse(src.read_text());nodes=[]
for n in tree.body:
 if isinstance(n,ast.For):break
 nodes.append(n)
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(src),'exec'))
s=load(False,False);routes=[]
for name in ['MIA_V14_SculptedSkin','MIA_V06_BODY_SKIN']:
 for mat in bpy.data.objects[name].data.materials:
  if not mat or not mat.use_nodes:continue
  nt=mat.node_tree;light=nt.nodes.get('PigmentTimesControlledLight');em=next((n for n in nt.nodes if n.type=='EMISSION'),None)
  if light and em and light.inputs[1].is_linked:
   source=light.inputs[1].links[0].from_socket;nt.links.new(source,em.inputs['Color']);routes.append({'owner':name,'material':mat.name,'pigment_socket':source.node.name+'.'+source.name})
  elif name=='MIA_V06_BODY_SKIN' and em and nt.nodes.get('MIA_BODY_SKIN_ATLAS'):
   source=nt.nodes['MIA_BODY_SKIN_ATLAS'].outputs['Color'];nt.links.new(source,em.inputs['Color']);routes.append({'owner':name,'material':mat.name,'pigment_socket':source.node.name+'.Color'})
for v in [{'id':'front','yaw':0,'elevation':0,'roll':0},{'id':'oblique','yaw':30,'elevation':0,'roll':0}]:
 r.camera(s,v);s.camera.location.z-=.01;s.camera.data.ortho_scale=.22;s.render.filepath=str(OUT/('color_only_face_cap_'+v['id']+'.png'));bpy.context.view_layer.update();bpy.ops.render.render(write_still=True);camera=r.record(s,v,'Actual unlit face and cap/body pigment; native eye/lash context');camera['ortho_scale']=.22;records.append({'label':'color_only_face_cap_'+v['id'],'render':r.artifact(s.render.filepath),'camera':camera})
(OUT/'render-records.json').write_text(json.dumps({'source':r.artifact(SOURCE),'recipe':r.artifact(__file__),'routes':routes,'records':records,'supersedes':'Earlier color_only_* bypassed face only, left cap lit. Those images are mixed-context diagnostics, not pure face+cap pigment.'},indent=2));assert r.sha(SOURCE)==source_sha;print('CORRECTED_COLOR_DONE')
