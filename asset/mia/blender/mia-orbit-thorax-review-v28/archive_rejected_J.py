"""Preserve J's real profile improvement and unresolved boxlike lower pole."""
from pathlib import Path
import hashlib
import json
import shutil

HERE=Path(__file__).resolve().parent
SOURCE=Path('C:/Users/antio/.codex/worktrees/mia-reference-recovery/win-overlay/asset/mia/blender/mia-thorax-review-v28')
DEST=HERE/'evidence/rejected-thorax-J'
files=['source-soft-J/'+s for s in [
    'handoff-J-delta.npz','construction.json','actual-I-J-pocket-sections.png',
    'evaluated-placement-comparison.json','evaluated-pocket-rays.json',
    'local-intersection-audit.json','raw-pocket-orientation.json',
    'two-mass-actual-audit.json','protected-array-audit-J.json']]
files += ['renders/J-core-plus-soft/geometry-clay/'+s for s in
          ['front.png','profile.png','oblique.png','render-records.json']]
files += ['renders/J-core-plus-soft/owner-clay/'+s for s in
          ['highfront35.png','highoblique35.png','lowfront35.png','lowoblique35.png','render-records.json']]
records=[]
for relative in files:
    source=SOURCE/relative
    dest=DEST/relative
    assert source.is_file(),source
    assert not dest.exists(), 'Snapshots are immutable'
    dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,dest)
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    assert digest(source)==digest(dest)
    records.append({'path':relative,'origin':str(source),'sha256':digest(dest)})
(DEST/'snapshot-manifest.json').write_text(json.dumps({
    'status':'REJECTED / intended soft-mass anatomy unmet',
    'actual_review':'Root and independent reviewer read first3 and±35 views; reviewer read all36 actual rotating clay frames. J has a real rounded profile/underfold but a near-level cross-width floor and abrupt root corners with long side walls, visible across yaw0..40/300..350. No new topological tearing or reversal claimed.',
    'preserve':'Corrected G3 core and improved sagittal return/source-informed apex.',
    'do_not':'Adopt G2J780b4b combined native; infer shape PASS from positive-control intersections or decomposition.',
    'files':records},indent=2),encoding='utf-8')
print('Rejected J snapshot:',len(records),'files')
