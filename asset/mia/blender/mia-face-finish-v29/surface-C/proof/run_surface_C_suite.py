"""Serial GPU probes for frozen C; fail on Python errors or missing records."""
from pathlib import Path
import subprocess,json,hashlib,time
P=Path(__file__).parent.resolve();N=P/'surface-C/Mia_FaceSurface_v29_C.blend';BL=Path('C:/Program Files/Blender Foundation/Blender 5.2/blender.exe');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();digest=sha(N);started=time.monotonic();counts={}
for preset,count in [('features',6),('response',8),('map-controls',4),('blink',6),('headfollow',4)]:
 print('SURFACE_C_START',preset,flush=True);subprocess.run([str(BL),'-b','--python-exit-code','1','--python',str(P/'render_surface_probes.py'),'--','--native',str(N),'--preset',preset,'--hair','off'],check=True);folder=N.parent/('probes-'+preset+'-hair-off');r=json.loads((folder/'probe-records.json').read_text());assert r['native_sha256']==digest and len(r['records'])==count
 for value in r['records'].values():
  assert sha(Path(value['path']))==value['sha256'];assert Path(value['actual_linear_render_result']['path']).exists()
 counts[preset]=count;print('SURFACE_C_FINISHED',preset,count,flush=True)
assert sha(N)==digest;(N.parent/'surface-probe-suite-run.json').write_text(json.dumps({'native':str(N),'native_sha256':digest,'elapsed_seconds':time.monotonic()-started,'completed':counts,'native_saved':False,'status':'Actual probes complete; source/material/response acceptance separate'},indent=2),encoding='utf8');print('SURFACE_C_SUITE_DONE',time.monotonic()-started,flush=True)
