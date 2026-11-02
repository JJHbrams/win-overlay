"""Transient CPU installation and actual iris/head control response; no native save."""
from pathlib import Path
import argparse, hashlib, importlib.util, json, sys
import bpy,numpy as np
P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--native',required=True);ap.add_argument('--sha256',required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);native=Path(a.native).resolve();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(native)==a.sha256;bpy.ops.wm.open_mainfile(filepath=str(native),use_scripts=False)
def arrays():
 return {o.name:{k.name:np.array([v.co[:] for v in k.data],dtype=np.float32).tobytes() for k in o.data.shape_keys.key_blocks} for o in bpy.context.scene.objects if o.type=='MESH' and o.data.shape_keys}
original=arrays();spec=importlib.util.spec_from_file_location('head_gaze_delta',P/'expression_control_delta.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
report=mod.apply_to_current_scene();after=arrays();assert all(all(after[n][key]==arr for key,arr in ks.items()) for n,ks in original.items())
c=bpy.data.objects[report['controller']];rig=bpy.data.objects[report['rig']];head=rig.pose.bones['J_Bip_C_Head'];states=[]
for prop,value in [('HeadPitch',8.),('HeadYaw',-12.),('HeadRoll',12.),('GazeX',1.),('GazeX',-1.),('GazeY',1.),('GazeY',-1.)]:
 for p in ['HeadPitch','HeadYaw','HeadRoll','GazeX','GazeY']:c[p]=0.
 c[prop]=value;c.update_tag();bpy.context.scene.frame_set(len(states)+2);bpy.context.view_layer.update()
 states.append(dict(property=prop,value=value,head_local_euler=list(head.rotation_euler),effective_gaze=[c['_EffectiveGazeX'],c['_EffectiveGazeY']],
  iris_gaze_values={o.name:{k.name:k.value for k in o.data.shape_keys.key_blocks if k.name.startswith('Mia.Gaze.')} for o in bpy.context.scene.objects if o.name.startswith('V28G_Iris_')}))
for p in ['HeadPitch','HeadYaw','HeadRoll','GazeX','GazeY']:c[p]=0.
c.update_tag();bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
assert sha(native)==a.sha256
(P/'head-gaze-transient-audit.json').write_text(json.dumps(dict(input_native=str(native),input_sha256=a.sha256,installation=report,states=states,original_key_arrays_exact=True,native_saved=False,art='NOT_EVALUATED'),indent=2)+'\n',encoding='utf-8')
print('HEAD_GAZE_TRANSIENT_AUDIT_OK',json.dumps(report),flush=True)
