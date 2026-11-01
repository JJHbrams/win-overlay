import subprocess
from pathlib import Path
O=Path(__file__).parent;exe='C:/Program Files/Blender Foundation/Blender 5.2/blender.exe';baseline='C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v22/face-rebuild-10/selected-v27/native/e9c865412130-Mia_Foundation_v27.blend'
for native,tag in [(baseline,'baseline-e9-corrected'),(str(O/'Mia_Orbit_v28_G2.blend'),'candidateG2')]:
 print('CORRECTED_SOURCE4_BEGIN',tag,flush=True);r=subprocess.run([exe,'-b','--python',str(O/'render_review.py'),'--',native,tag,'source4']);assert r.returncode==0;print('CORRECTED_SOURCE4_END',tag,flush=True)
