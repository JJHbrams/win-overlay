"""Matched D/E bare front, bilateral oblique, profile, lowfront and two lights."""
import ast,sys,json
from pathlib import Path
src=Path(__file__).resolve().parent.parent/'finish-7/render_source_motion.py';tree=ast.parse(src.read_text());nodes=[]
for n in tree.body:
 if isinstance(n,ast.For):break
 nodes.append(n)
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(src),'exec'))
s=load(False,True)
for k in bpy.data.objects['MIA_V14_SculptedSkin'].data.shape_keys.key_blocks:k.value=0
for yaw,el in [(0,0),(30,0),(-30,0),(90,0),(0,-10),(30,-10),(-30,-10)]:
 render(s,'matte_yaw%+03d_elev%+03d'%(yaw,el),{'id':'connected_cheek','yaw':yaw,'elevation':el,'roll':0},'Actual18percent diffuse fixed white rig')
for side in [-1,1]:
 s=load(False,False)
 for obj in s.objects:
  if obj.type=='LIGHT':obj.hide_render=True
 lamp=bpy.data.lights.new('ACTUAL_DIRECTION_PROBE','AREA');lamp.energy=100;lamp.shape='DISK';lamp.size=.5;o=bpy.data.objects.new('ACTUAL_DIRECTION_PROBE',lamp);s.collection.objects.link(o);r.aim(o,(side*.5,-.6,1.8),(0,0,1.54))
 for yaw in [30,-30]:render(s,'native_light%+d_yaw%+03d'%(side,yaw),{'id':'direction_probe','yaw':yaw,'elevation':0,'roll':0},'Actual native pigment with opposite scene light')
assert r.sha(SOURCE)==source_sha
(OUT/'render-records.json').write_text(json.dumps({'source':r.artifact(SOURCE),'recipe':r.artifact(__file__),'records':records,'limits':'Actual same saved geometry in all views; no source/per-view mesh fit. D materials unchanged.'},indent=2));print('CONNECTED_CHEEK_REVIEW_DONE',len(records))
