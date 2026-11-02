"""Four actual upper-crease registration/deformation frames; no scene save."""
from pathlib import Path
import bpy,runpy,sys,copy,importlib.util,json,hashlib
P=Path(__file__).resolve().parent;C=P.parents[1];V=C/'mia-refinement-v002';N=V/'integrated/Mia_v0.0.2_Review_R3b.blend';SHA='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'
old=C/'mia-visible-art-v30/render_native_review.py';sys.argv=[str(old),'--','--native',str(N),'--sha256',SHA,'--tag','v003-crease-quick-B','--preset','source','--only','__setup__'];env=runpy.run_path(str(old),run_name='v003creasequick');render=env['render'];out=P/'crease-B';out.mkdir(exist_ok=True);render.__globals__['out']=out;env['a'].only=''
results=[]
for name,file in [('lowerlid','apply_lower_lid.py'),('fold','apply_aligned_crease.py')]:
 sp=importlib.util.spec_from_file_location(name,P/file);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);results.append(m.apply())
# The factory deliberately restores captured production slots for each frame.
# Capture the NEW scoped copies, otherwise its restore silently reviews old folds.
slots={name:list(bpy.data.objects[name].data.materials) for name in render.__globals__['original']}
render.__globals__['original']=slots
expected={name:[m.name for m in mats] for name,mats in slots.items()}
def checked_render(label,spec):
 assert {name:[m.name for m in bpy.data.objects[name].data.materials] for name in slots}==expected
 render(label,spec,True,False)
 assert {name:[m.name for m in bpy.data.objects[name].data.materials] for name in slots}==expected
ctrl=bpy.data.objects['Mia_FacialControls_v002'];bpy.context.scene.frame_set(2);bpy.context.view_layer.update()
front=copy.deepcopy(env['pkg']['views'][0]['candidate_camera']);oblique=copy.deepcopy(env['pkg']['views'][3]['candidate_camera']);front['resolution']=oblique['resolution']=[768,768]
checked_render('aligned-front',front);checked_render('aligned-oblique',oblique)
for value,label in [(.5,'half'),(1.,'closed')]:
 ctrl['Manual_EYE_Close']=value;ctrl.update_tag();bpy.context.scene.frame_set(3 if value==.5 else 4);bpy.context.view_layer.update();checked_render('aligned-'+label,front)
(out/'component.json').write_text(json.dumps(dict(results=results,material_slots_asserted=expected,failed_previous='crease-A restored original captured materials: its neutral image was pixel-exact old-fold. Retained as failed evidence.',scope='Aligned UVvector crease actual neutral/oblique/half/full. No physical fold-groove or wholeART claim.'),indent=2)+'\n',encoding='utf-8');assert hashlib.sha256(N.read_bytes()).hexdigest()==SHA
print('ALIGNED_CREASE_ACTUAL_DONE',4,flush=True)
