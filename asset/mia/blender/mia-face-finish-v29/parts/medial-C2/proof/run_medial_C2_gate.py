import subprocess
from pathlib import Path
O=Path(__file__).parent;exe='C:/Program Files/Blender Foundation/Blender 5.2/blender.exe'
for script,args in [('render_medial_macro.py',['C2']),('render_medial_stage.py',['C2']),('render_medial_stage.py',['C2','post']),('render_medial_stage.py',['baseline','identity']),('render_medial_stage.py',['C2','identity'])]:
 print('MEDIAL_GATE_JOB',script,args,flush=True);r=subprocess.run([exe,'-b','--python',str(O/script),'--',*args]);assert r.returncode==0
