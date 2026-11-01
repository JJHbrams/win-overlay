import ast,sys,json
from pathlib import Path
src=Path(__file__).resolve().parent.parent/'finish-7/render_source_motion.py';tree=ast.parse(src.read_text());nodes=[]
for n in tree.body:
 if isinstance(n,ast.For):break
 nodes.append(n)
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(src),'exec'))
for mode,hair,matte,views in [('native_hair',True,False,[r.VIEWS[0],next(v for v in r.VIEWS if v['id']=='left_oblique')]),('matte',False,True,[{'id':'lowfront','yaw':0,'elevation':-10,'roll':0},{'id':'low30','yaw':30,'elevation':-10,'roll':0},{'id':'steep','yaw':60,'elevation':0,'roll':0},{'id':'profile','yaw':90,'elevation':0,'roll':0}])]:
 s=load(hair,matte)
 for k in bpy.data.objects['MIA_V14_SculptedSkin'].data.shape_keys.key_blocks:k.value=0
 for v in views:render(s,mode+'_'+v['id'],v,mode)
(OUT/'render-records.json').write_text(json.dumps({'source':r.artifact(SOURCE),'recipe':r.artifact(__file__),'records':records},indent=2));assert r.sha(SOURCE)==source_sha
print('TARGETED_DONE')
