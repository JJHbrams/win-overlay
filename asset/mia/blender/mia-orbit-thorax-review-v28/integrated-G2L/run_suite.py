"""Sequential GPU-only frozen-native source and limited integration probes."""
from pathlib import Path
import subprocess
import sys

P=Path(__file__).resolve().parent
EXE='C:/Program Files/Blender Foundation/Blender 5.2/blender.exe'
NATIVE=P/'Mia_Foundation_v28_G2L.blend'
jobs=[('face-source4','render_face.py',[str(NATIVE),'integrated','source4']),
      ('face-follow','render_face.py',[str(NATIVE),'integrated','follow']),
      ('face-blink','render_face.py',[str(NATIVE),'integrated','blink']),
      ('body-source5','render_body.py',['--native',str(NATIVE),'--role','integrated','--mode','geometry-clay','--views','front,profile,back,oblique,yaw30']),
      ('body-arm+20','render_body.py',['--native',str(NATIVE),'--role','integrated','--mode','geometry-clay','--views','front,oblique','--pose','20']),
      ('body-arm-20','render_body.py',['--native',str(NATIVE),'--role','integrated','--mode','geometry-clay','--views','front,oblique','--pose','-20']),
      ('body-production','render_body.py',['--native',str(NATIVE),'--role','integrated','--mode','production','--views','front,oblique'])]
for name,script,args in jobs:
    print('BEGIN',name,flush=True)
    with (P/(name+'.log')).open('w',encoding='utf-8') as log:
        result=subprocess.run([EXE,'-b','--python',str(P/script),'--']+args,stdout=log,stderr=subprocess.STDOUT)
    assert result.returncode==0,(name,result.returncode)
    print('DONE',name,flush=True)
print('INTEGRATED_RENDER_SUITE_DONE',flush=True)
