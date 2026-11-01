"""Actual final-candidate neutral source cameras; no model save."""
import ast,sys,json
from pathlib import Path
src=Path(__file__).with_name('render_source_motion.py');tree=ast.parse(src.read_text());nodes=[]
for n in tree.body:
 if isinstance(n,ast.For):break
 nodes.append(n)
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(src),'exec'))
for mode,hair,matte in [('native_hair',True,False),('native_bare',False,False),('matte',False,True)]:
 s=load(hair,matte)
 for key in bpy.data.objects['MIA_V14_SculptedSkin'].data.shape_keys.key_blocks:key.value=0.
 bpy.context.view_layer.update()
 for view in r.VIEWS:render(s,mode+'_'+view['id'],view,mode+' actual neutral source camera')
assert r.sha(SOURCE)==source_sha
(OUT/'render-records.json').write_text(json.dumps({'source':r.artifact(SOURCE),'recipe':r.artifact(__file__),'shared_setup':r.artifact(src),'records':records,'limits':'Original source-camera uncertainty retained; neutral references are not a calibrated camera fit.'},indent=2));(OUT/'executed-render.py').write_bytes(Path(__file__).read_bytes());print('NEUTRAL_SOURCE_FOUR_DONE',len(records))
