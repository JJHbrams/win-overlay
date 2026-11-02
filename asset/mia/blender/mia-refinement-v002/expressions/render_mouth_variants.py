"""Compare existing anatomical mouth channels before inventing missing teeth."""
from pathlib import Path
import argparse, copy, hashlib, json, runpy, sys
import bpy
P=Path(__file__).resolve().parent;phase=P.parent;old=phase.parent/'mia-visible-art-v30/render_native_review.py'
ap=argparse.ArgumentParser();ap.add_argument('--native',required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--tag',required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);native=Path(a.native).resolve()
sys.argv=[str(old),'--','--native',str(native),'--sha256',a.sha256,'--tag','v002-mouth-setup-'+a.tag,'--preset','source','--only','__configure_no_frames__']
env=runpy.run_path(str(old),run_name='v002_mouth_setup');render=env['render'];out=P/'review'/a.tag;out.mkdir(parents=True,exist_ok=True)
render.__globals__['out']=out;env['a'].only='';ctrl=bpy.data.objects['Mia_FacialControls_v002'];front=copy.deepcopy(env['spec']);front['resolution']=[512,512]
recipes=[('I',{'MTH_I':1.}),('E',{'MTH_E':1.}),('I_Fun',{'MTH_I':.9,'MTH_Fun':.4,'MTH_Up':.15}),('E_Fun_Joy',{'MTH_E':.8,'MTH_Fun':.35,'MTH_Joy':.15})]
rows=[]
for label,recipe in recipes:
 for key in ctrl.keys():
  if key.startswith('Manual_') or (key.startswith('P') and key[:3][1:].isdigit()):ctrl[key]=0.
 for key,value in recipe.items():ctrl['Manual_'+key]=value
 ctrl.update_tag();bpy.context.scene.frame_set(len(rows)+2);bpy.context.view_layer.update();render(label,front,True,False)
 rows.append(dict(id=label,recipe=recipe,actual_master_keys={k.name:k.value for k in env['master'].data.shape_keys.key_blocks if k.value}))
(out/'mouth-variant-records.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
print('MOUTH_VARIANTS_ACTUAL_DONE',len(rows),flush=True)
