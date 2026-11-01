"""Freeze accepted bounded body proof and exact replay payload, not duplicate natives."""
from pathlib import Path
import hashlib
import json
import shutil

HERE=Path(__file__).resolve().parent
SOURCE=Path('C:/Users/antio/.codex/worktrees/mia-reference-recovery/win-overlay/asset/mia/blender/mia-thorax-review-v28')
DEST=HERE/'parts/thorax-L'
files=[p for p in (SOURCE/'source-soft-L').iterdir() if p.is_file() and p.suffix in ('.json','.npz','.png','.gif')]
for relative in ['source4-uniform-L','renders/L-core-plus-soft','renders/I-true-core/owner-clay-orbit']:
    files += [p for p in (SOURCE/relative).rglob('*') if p.is_file() and p.suffix in ('.json','.png')]
files += [SOURCE/'core-first-G3'/s for s in ['construction.json','station-orientation-audit.json','true-core-plus-soft.npz']]
files += [SOURCE/s for s in ['build_elliptic_soft_L.py','audit_lower_envelope_L.py','audit_local_intersections_L.py','assemble_orbit_L.py','package_frozen_L.py','render_review.py','render_frozen_L_suite.py']]
records=[]
for source in files:
    relative=source.relative_to(SOURCE)
    dest=DEST/relative
    assert not dest.exists(), 'Frozen evidence cannot be overwritten'
    dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,dest)
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    assert digest(source)==digest(dest)
    records.append({'path':relative.as_posix(),'origin':str(source),'sha256':digest(dest)})
(DEST/'snapshot-manifest.json').write_text(json.dumps({
    'scope':'Independently supported bounded AC4 component, not whole-body/ART/dynamics acceptance.',
    'original_L_native_sha256':'e703cbacbbb9f0a564b3671b14e8066ad0240636e8592eba0643bbfd25836f0e',
    'native_storage':'Original component native stays in producer worktree. Canonical integrated-G2L native contains bit-exact L847-index/42-key targets; exact handoff archived here reproduces them. Original component package paths are provenance, not a newly portable package.',
    'primary_canonical_review':'../../integrated-G2L/source4-uniform-G2L/reference-review.json',
    'source_limits':'Bra conceals nude attachment and source poses/yaw differ. Public adult photos only qualitative, not archived.',
    'files':records},indent=2),encoding='utf-8')
print('L proof snapshot:',len(records),'files')
