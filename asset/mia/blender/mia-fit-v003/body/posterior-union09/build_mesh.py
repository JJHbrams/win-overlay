"""Run existing E native VolumeCube/VolumeToMesh once in this namespace."""
from pathlib import Path
import sys,json,hashlib
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
SOURCE=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-fit-v003/body/design-sculpt07/E/build_breast.py')
assert not (P/'posterior09.npz').exists(),'No reconstruction sweep/overwrite'
code=SOURCE.read_text(encoding='utf-8').replace("P/'breast-step.npz'","P/'posterior09.npz'").replace("P/'breast-build-report.json'","P/'build-report.json'").replace('SCULPT07_E_NATIVE_MESH_DONE','POSTERIOR09_NATIVE_MESH_DONE')
exec(compile(code,str(SOURCE),'exec'),globals())
protected=json.loads((P/'protected-input-hashes.json').read_text(encoding='utf-8'))
for path,h in protected.items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==h,('Frozen input changed',path)
