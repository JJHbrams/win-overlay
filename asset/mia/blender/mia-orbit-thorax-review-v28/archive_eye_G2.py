"""Freeze the independently reviewed eye component without failed native copies."""
from pathlib import Path
import hashlib
import json
import shutil
import sys

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
SOURCE=Path('C:/Users/antio/.codex/worktrees/mia-final-face-v12/win-overlay/asset/mia/blender/mia-orbit-review-v28')
sys.path.insert(0,str(HERE.parent/'mia-reference-finish-v22'))
from archive_reference_package import archive

DEST=HERE/'parts/eye-G2'
supplements=[SOURCE/s for s in [
    'final-patch-manifest-G2.json','G2_HANDOFF.md',
    'v28F-geometry-patch.npz','v28F-features.npz','v28F-features.json',
    'v28F-pigment-pixels.npz','replay_patch.py',
    'v28G2-components.npz','v28G2-components.json','replay_orbit_G2.py',
    'source-contour-trace.json','evaluated-contour-source-e9-F.png',
    'DIAGNOSIS.md','temporary-shader-default-audit.json',
    'render_review.py','render_full_orbit_audit.py','render_G2_reference_final.py',
    'full-orbit-audit/G2-actual-structure-audit.json',
    'full-orbit-audit/G2-seam-corner-visibility.json',
    'full-orbit-audit/G2-replay-audit.json',
    'full-orbit-audit/G2-continuous-yaw-pitch.gif',
    'full-orbit-audit/G2-orbit-contactsheet.png']]
result=archive(SOURCE/'reference-review-G2.json',DEST,REPO,supplements)
files=[]
for folder in ['full-orbit-audit/sweep_prod-G2','full-orbit-audit/trial-G2',
               'full-orbit-audit/wallproof-G2','full-orbit-audit/deform-G2',
               'renders/candidateG2']:
    files += [p for p in (SOURCE/folder).rglob('*') if p.is_file() and p.suffix in ('.png','.json')]
files += [p for p in (SOURCE/'full-orbit-audit').glob('*G2-records.json')]
records=[]
for source in files:
    relative=source.relative_to(SOURCE)
    dest=DEST/'proof'/relative
    assert not dest.exists(), 'Frozen proof cannot be overwritten'
    dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,dest)
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    assert digest(source)==digest(dest)
    records.append({'path':relative.as_posix(),'origin':str(source),'sha256':digest(dest)})
(DEST/'proof-manifest.json').write_text(json.dumps({
    'files':records,'scope':'Actual G2 rotating/macroscopic/limited deformation images; original metadata retained.',
    'F_paint_dependency':'v28F-pigment-pixels.npz is the tested lossless packed-pixel replay route. Optional EXR fallback from producer manifest is intentionally not duplicated.',
    'art_acceptance':'Bounded component review only; no full character/42-key-combination approval.'},indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
