import sys,subprocess
from pathlib import Path
O=Path(__file__).parent;V=sys.argv[1] if len(sys.argv)>1 else 'E';exe='C:/Program Files/Blender Foundation/Blender 5.2/blender.exe'
for args in [[V],[V,'closure']]:
 r=subprocess.run([exe,'-b','--python',str(O/'render_lash_first.py'),'--',*args]);assert r.returncode==0
