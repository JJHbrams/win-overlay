"""Actual symmetric half/full contact check, front and60degrees."""
import ast,sys,json
from pathlib import Path
src=Path(__file__).resolve().parents[2]/'render_source_motion.py';tree=ast.parse(src.read_text());nodes=[]
for n in tree.body:
 if isinstance(n,ast.For):break
 nodes.append(n)
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(src),'exec'))
for mode,matte in [('native',False),('matte',True)]:
 s=load(False,matte);keys=bpy.data.objects['MIA_V14_SculptedSkin'].data.shape_keys.key_blocks
 for k in keys:k.value=0.
 for stage,value in [('half',.5),('full',1.)]:
  keys['Face.M_F00_000_00_Fcl_EYE_Close'].value=value;bpy.context.view_layer.update()
  for yaw in [0,60]:
   view={'id':stage,'yaw':yaw,'elevation':0,'roll':0};render(s,mode+'_'+stage+'_yaw%+03d'%yaw,view,mode+' actual symmetric Close '+str(value))
assert r.sha(SOURCE)==source_sha
(OUT/'render-records.json').write_text(json.dumps({'source':r.artifact(SOURCE),'recipe':r.artifact(__file__),'records':records,'limits':'Only symmetric Close.5 and1 atfront/+60; not all47expressions.'},indent=2));print('LIMITED_BLINK_DONE',len(records))
