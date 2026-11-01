"""Read-only actual neutral, half and full Close with visible lash followers."""
import ast,sys,json
from pathlib import Path
src=Path(__file__).with_name('render_source_motion.py')
tree=ast.parse(src.read_text())
# Share the frozen camera/material setup and helpers, without its render loops.
nodes=[]
for n in tree.body:
 if isinstance(n,ast.For):break
 nodes.append(n)
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(src),'exec'))
for mode,matte in [('native',False),('matte',True)]:
 s=load(False,matte);skin=bpy.data.objects['MIA_V14_SculptedSkin'];keys=skin.data.shape_keys.key_blocks
 for k in keys:k.value=0.
 for stage,value in [('neutral',0.),('half',.5),('full',1.)]:
  keys['Face.M_F00_000_00_Fcl_EYE_Close'].value=value;bpy.context.view_layer.update()
  for yaw in [0,30,-30]:
   view={'id':stage,'yaw':yaw,'elevation':0,'roll':0}
   render(s,mode+'_'+stage+'_yaw%+03d'%yaw,view,mode+' actual Close '+str(value))
assert r.sha(SOURCE)==source_sha
(OUT/'render-records.json').write_text(json.dumps({'source':r.artifact(SOURCE),'recipe':r.artifact(__file__),'shared_setup':r.artifact(src),'records':records,'limits':'Actual evaluated geometry; no saved scene mutations. Render review still required.'},indent=2))
(OUT/'executed-render.py').write_bytes(Path(__file__).read_bytes())
print('BLINK_STAGES_DONE',len(records))
