"""Snapshot the cleared geometry stage, excluding failed large natives."""
from pathlib import Path
import hashlib
import json
import shutil

HERE=Path(__file__).resolve().parent
SRC=Path('C:/Users/antio/.codex/worktrees/mia-final-face-v12/win-overlay/asset/mia/blender/mia-eye-lash-v29')
DEST=HERE/'parts/medial-C2'
NATIVE=SRC/'Mia_EyeLash_v29_C2.blend'
SHA='e04bc76faaa3f9a855e81660d19bc89adf62b89119c61e087a9a6cf7c394dd26'
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert digest(NATIVE)==SHA
guard=json.loads((SRC/'medial-C2-fresh-remap-preservation.json').read_text())
assert guard['all_computed_checks_pass']
files=[SRC/s for s in ['medial-baseline-inspection.json','build_medial_A.py',
    'medial-A-audit.json','medial-A-deltas.npz','medial-A-fresh-preservation.json',
    'medial-A-fringe-rays.json','audit_medial_saved.py','ray_medial_fringe.py',
    'render_medial_stage.py','render_medial_macro.py','board_medial_stage.py',
    'trim_iris_C.py','audit_C_reopened.py','board_medial_C2_gate.py','run_medial_C2_gate.py',
    'medial-C2-iris-topology-remap.npz','medial-C2-iris-remap-audit.json',
    'medial-C2-fresh-remap-preservation.json']]
for name in ['baseline','baseline-close','baseline-identity','A','C2','C2-post','C2-identity','fringe','macros']:
    files += [p for p in (SRC/'medial-review'/name).rglob('*') if p.is_file() and p.suffix in ('.png','.json')]
files += list((SRC/'medial-review').glob('*.png'))
records=[]
for source in files:
    rel=source.relative_to(SRC)
    dest=DEST/'proof'/rel
    assert not dest.exists(), 'Frozen geometry proof is immutable'
    dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,dest)
    assert digest(source)==digest(dest)
    records.append({'path':str(dest.relative_to(DEST)).replace('\\','/'),'origin':str(source),'sha256':digest(dest)})
native_dest=DEST/'native'/(SHA[:12]+'-'+NATIVE.name)
native_dest.parent.mkdir(parents=True,exist_ok=True)
assert not native_dest.exists()
shutil.copyfile(NATIVE,native_dest)
assert digest(native_dest)==SHA
(DEST/'snapshot-manifest.json').write_text(json.dumps({
    'native':{'path':str(native_dest.relative_to(DEST)).replace('\\','/'),'sha256':SHA},
    'baseline_sha256':'f0dead17dba4f492c47652dab62c48a93bcd0100bc2586ca3ac315d41a977ee2',
    'geometry_gate':'Root and fresh independent reviewer support bounded AC1/AC2; all42 protection checks are measured, not inferred from counts.',
    'scope':'Actual64-control medial skin/recess correction plus coordinated wall/fringe, then alpha-zero iris-exterior trim. Two declared iris topology remaps only; exact BodyL/other fields preserved.',
    'numeric_limit':'Opaque UV-sampled surface interpolation max about0.0000581mm across6155+samples/key; not claimed bit-exact surface. Full expression combinations unvalidated.',
    'pending':'Upper/lower lashes, applied facial maps/specular, final source4/rotation/integrated audit; no whole-character ART approval.',
    'files':records},indent=2),encoding='utf-8')
print(json.dumps({'native':str(native_dest),'sha256':SHA,'proof_files':len(records)}))
