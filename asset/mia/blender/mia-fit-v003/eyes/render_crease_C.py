"""Bounded lash-cleared skin crease, four actual frames; no native save."""
from pathlib import Path
import bpy,runpy,sys,copy,importlib.util,json,hashlib
P=Path(__file__).resolve().parent;C=P.parents[1];N=C/'mia-refinement-v002/integrated/Mia_v0.0.2_Review_R3b.blend';SHA='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'
old=C/'mia-visible-art-v30/render_native_review.py';sys.argv=[str(old),'--','--native',str(N),'--sha256',SHA,'--tag','v003-crease-C','--preset','source','--only','__setup__'];env=runpy.run_path(str(old),run_name='creaseC');render=env['render'];out=P/'crease-C';out.mkdir(exist_ok=True);render.__globals__['out']=out;env['a'].only=''
def module(file):
 sp=importlib.util.spec_from_file_location(file.stem,file);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
results=[module(P/'apply_lower_lid.py').apply(),module(P/'apply_aligned_crease.py').apply(P/'upper-crease-visible-C.json')]
slots={n:list(bpy.data.objects[n].data.materials) for n in render.__globals__['original']};render.__globals__['original']=slots;expected={n:[m.name for m in ms] for n,ms in slots.items()}
ctrl=bpy.data.objects['Mia_FacialControls_v002'];bpy.context.scene.frame_set(2);bpy.context.view_layer.update()
front=copy.deepcopy(env['pkg']['views'][0]['candidate_camera']);oblique=copy.deepcopy(env['pkg']['views'][3]['candidate_camera']);front['resolution']=oblique['resolution']=[768,768]
def shoot(label,spec):
 assert {n:[m.name for m in bpy.data.objects[n].data.materials] for n in slots}==expected
 render(label,spec,True,False)
 assert {n:[m.name for m in bpy.data.objects[n].data.materials] for n in slots}==expected
shoot('visible-front',front);shoot('visible-oblique',oblique)
for v,label in [(.5,'half'),(1.,'closed')]:
 ctrl['Manual_EYE_Close']=v;ctrl.update_tag();bpy.context.scene.frame_set(3 if v==.5 else 4);bpy.context.view_layer.update();shoot('visible-'+label,front)
(out/'component.json').write_text(json.dumps(dict(results=results,material_slots_asserted=expected,config_sha256=hashlib.sha256((P/'upper-crease-visible-C.json').read_bytes()).hexdigest(),limitations='Source comparison pending. Right covered ends omitted rather than moved to brow height. Actual closure and visibility need visual review.'),indent=2)+'\n',encoding='utf-8')
assert hashlib.sha256(N.read_bytes()).hexdigest()==SHA
print('VISIBLE_CREASE_C_ACTUAL_DONE',4,flush=True)
