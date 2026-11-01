"""Sequential offline GPU evidence for frozen L; no native mutations."""
from pathlib import Path
import subprocess
P=Path(__file__).parent.resolve();BL=Path('C:/Program Files/Blender Foundation/Blender 5.2/blender.exe');N=P/'source-soft-L/Mia_L_CorePlusBreast.blend'
jobs=[('owner-clay','highfront35,highoblique35,lowfront35,lowoblique35',0,False),('geometry-clay','front,profile,back,oblique,yaw30',0,False),('geometry-clay','front,oblique',20,False),('geometry-clay','front,oblique',-20,False),('owner-clay','front',0,True)]
for mode,views,pose,orbit in jobs:
 args=[str(BL),'-b','--python',str(P/'render_review.py'),'--','--native',str(N),'--role','L-core-plus-soft','--mode',mode,'--views',views]
 if pose:args+=['--pose',str(pose)]
 if orbit:args+=['--orbit']
 print('L_EVIDENCE_START',mode,views,pose,orbit,flush=True);subprocess.run(args,check=True);print('L_EVIDENCE_DONE',mode,pose,orbit,flush=True)
