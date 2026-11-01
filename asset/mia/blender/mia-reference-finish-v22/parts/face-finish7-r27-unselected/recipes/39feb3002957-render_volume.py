"""Identical actual matte camera/light views, with real eye/lash visible."""
import ast,sys,json
from pathlib import Path
src=Path(__file__).resolve().parent.parent/'render_source_motion.py';tree=ast.parse(src.read_text());nodes=[]
for n in tree.body:
 if isinstance(n,ast.For):break
 nodes.append(n)
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(src),'exec'))
s=load(False,True)
for key in bpy.data.objects['MIA_V14_SculptedSkin'].data.shape_keys.key_blocks:key.value=0.
for yaw,el in [(0,0),(0,-10),(30,0),(-30,0),(30,-10),(-30,-10),(60,0),(-60,0),(90,0)]:
 view={'id':'volume','yaw':yaw,'elevation':el,'roll':0};render(s,'matte_yaw%+03d_elev%+03d'%(yaw,el),view,'18percent diffuse fixed rig actual neutral')
assert r.sha(SOURCE)==source_sha
(OUT/'render-records.json').write_text(json.dumps({'source':r.artifact(SOURCE),'recipe':r.artifact(__file__),'records':records},indent=2));print('VOLUME_RENDER_DONE',len(records))
