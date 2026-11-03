"""ONE existing native VolumeCube meshing, own11 output only; CPU/no native save."""
from pathlib import Path
import sys,json,hashlib
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
SOURCE=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-fit-v003/body/design-sculpt07/E/build_breast.py')
assert not (P/'shoulder11.npz').exists(),'ONE approved construction; no overwrite/variant.'
code=SOURCE.read_text(encoding='utf-8').replace("P/'breast-step.npz'","P/'shoulder11.npz'").replace("P/'breast-build-report.json'","P/'build-report.json'").replace('SCULPT07_E_NATIVE_MESH_DONE','SHOULDER11_ONE_NATIVE_MESH_DONE')
exec(compile(code,str(SOURCE),'exec'),globals())
for path,h in json.loads((P/'protected-input-hashes.json').read_text()).items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==h,path
