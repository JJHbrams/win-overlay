"""Test existing closed-smile range before inventing another facial mesh key."""
from pathlib import Path
import bpy,copy,hashlib,json,runpy,sys
P=Path(__file__).resolve().parent;phase=P.parent;native=phase/'integrated/Mia_v0.0.2_Review_R2.blend';digest='eed408b82e9a6160377e92e97fe94ce9619a51393e1ec1d4c928f4a4fd498d82'
old=phase.parent/'mia-visible-art-v30/render_native_review.py';sys.argv=[str(old),'--','--native',str(native),'--sha256',digest,'--tag','smile-r3-setup','--preset','source','--only','__setup_no_frames__'];env=runpy.run_path(str(old),run_name='smile_calibration_setup');render=env['render'];out=P/'smile-calibration-r3';out.mkdir(parents=True,exist_ok=True);render.__globals__['out']=out;env['a'].only='';c=bpy.data.objects['Mia_FacialControls_v002'];rows=json.loads((P/'expression-intents.json').read_text())['panels'];v=copy.deepcopy(env['spec']);v['resolution']=[512,512];probes=[]
for panel,fun in [(8,.65),(16,.45)]:
 row=rows[panel-1]
 for n in c.keys():
  if n.startswith('P') and n[:3][1:].isdigit() or n.startswith('Manual_'):c[n]=0.
 c[f'P{panel:02}_{row["id"]}']=1.;c['Manual_MTH_Fun']=fun-row['initial_key_recipe'].get('MTH_Fun',0.);c.update_tag();bpy.context.scene.frame_set(panel+1);bpy.context.view_layer.update()
 for suffix,hide in [('hairON',False),('hairOFF',True)]:render(f'P{panel:02}-Fun{fun:.2f}-'+suffix,v,hide,False)
 probes.append(dict(panel=panel,old_recipe=row['initial_key_recipe'],tested_MTH_Fun=fun,manual_addition=c['Manual_MTH_Fun'],source_panel=row['source_panel'],scope='Same source-preset head/gaze and camera; existing smile amplitude only, not geometry/key/texture edits.'))
(out/'parameter-delta.json').write_text(json.dumps(dict(native=str(native),sha256=digest,probes=probes,wrapper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),native_saved=False,art_approved=False),indent=2)+'\n',encoding='utf-8');assert hashlib.sha256(native.read_bytes()).hexdigest()==digest;print('SMILE_EXISTING_RANGE_PROBE_DONE',4,flush=True)
