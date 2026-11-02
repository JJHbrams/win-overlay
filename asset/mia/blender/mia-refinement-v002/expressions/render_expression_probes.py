"""Actual source-camera facial prototypes, isolated from hair and final animation."""
from pathlib import Path
import argparse, copy, hashlib, json, runpy, sys
import bpy
P=Path(__file__).resolve().parent; phase=P.parent; old=phase.parent/'mia-visible-art-v30/render_native_review.py'
ap=argparse.ArgumentParser();ap.add_argument('--native',required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--tag',required=True);ap.add_argument('--quick',action='store_true')
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);native=Path(a.native).resolve()
sys.argv=[str(old),'--','--native',str(native),'--sha256',a.sha256,'--tag','v002-expression-setup-'+a.tag,'--preset','source','--only','__configure_no_frames__']
env=runpy.run_path(str(old),run_name='v002_expression_setup');render=env['render'];g=render.__globals__
out=phase/'expressions/review'/a.tag;out.mkdir(parents=True,exist_ok=True);g['out']=out;env['a'].only=''
ctrl=bpy.data.objects['Mia_FacialControls_v002'];rows=json.loads((P/'expression-intents.json').read_text(encoding='utf-8'))['panels']
front=copy.deepcopy(env['spec']);front['resolution']=[512,512]
chosen=[1,2,8,10,12,14] if a.quick else range(1,17)
controls=[]
for row in rows:
 if row['panel'] not in chosen:continue
 for name in ctrl.keys():
  if name.startswith('P') and name[:3][1:].isdigit():ctrl[name]=0.
 prop=f"P{row['panel']:02}_{row['id']}";ctrl[prop]=1.;ctrl.update_tag();bpy.context.scene.frame_set(row['panel']+1);bpy.context.view_layer.update()
 label=f"P{row['panel']:02}-{row['id']}";render(label,front,True,False)
 controls.append(dict(id=label,source_panel=row['source_panel'],source_crop=row['source_crop'],property=prop,
   active={k.name:k.value for k in env['master'].data.shape_keys.key_blocks if k.value},
   head_gaze='Fixed actual source front for deformation diagnosis. Panel head/gaze estimates deliberately not applied yet.',
   intended_recipe=row['initial_key_recipe']))
for name in ctrl.keys():
 if name.startswith('P') and name[:3][1:].isdigit():ctrl[name]=0.
ctrl.update_tag();bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
(out/'pose-records.json').write_text(json.dumps(dict(native=str(native),sha256=a.sha256,wrapper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),poses=controls,
   source_art_approved=False,scope='Diagnostic fixed-front actual prototypes; not a16panel matching claim or final animated action.'),indent=2)+'\n',encoding='utf-8')
print('EXPRESSION_ACTUAL_PROBES_DONE',len(controls),flush=True)
