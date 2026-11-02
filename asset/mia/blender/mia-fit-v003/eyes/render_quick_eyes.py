"""Five actual frames: lower-rim comparison and separate old-fold ablation."""
from pathlib import Path
import runpy,sys,copy,importlib.util,json,bpy,hashlib
P=Path(__file__).resolve().parent;C=P.parents[1];V=C/'mia-refinement-v002';N=V/'integrated/Mia_v0.0.2_Review_R3b.blend';SHA='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'
old=C/'mia-visible-art-v30/render_native_review.py';sys.argv=[str(old),'--','--native',str(N),'--sha256',SHA,'--tag','v003-eye-quick','--preset','source','--only','__setup__'];env=runpy.run_path(str(old),run_name='v003eyequick');render=env['render'];render.__globals__['out']=P/'quick-A';(P/'quick-A').mkdir(exist_ok=True);env['a'].only=''
front=copy.deepcopy(env['pkg']['views'][0]['candidate_camera']);oblique=copy.deepcopy(env['pkg']['views'][3]['candidate_camera']);front['resolution']=oblique['resolution']=[768,768]
for label,spec in [('before-front',front),('before-oblique',oblique)]:render(label,spec,True,False)
spec=importlib.util.spec_from_file_location('lowerlid',P/'apply_lower_lid.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);result=m.apply();bpy.context.scene.frame_set(2);bpy.context.view_layer.update()
for label,spec in [('after-front',front),('after-oblique',oblique)]:render(label,spec,True,False)
for name in ['MIA_V27_SharedHeadBody','V28G_InnerLid_-1','V28G_InnerLid_1']:
 mat=bpy.data.objects[name].material_slots[0].material
 for node in ['V29_FoldGain','V30_FoldGain']:mat.node_tree.nodes[node].outputs[0].default_value=0.
render('after-front-oldFoldOFF',front,True,False)
(P/'quick-A/component.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
assert hashlib.sha256(N.read_bytes()).hexdigest()==SHA
print('EYE_QUICK_ACTUAL_DONE',5,flush=True)
