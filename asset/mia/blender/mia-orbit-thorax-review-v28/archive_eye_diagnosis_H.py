"""Freeze the source-decoration versus real-opening correction, with no H mesh."""
from pathlib import Path
import hashlib
import json
import shutil

HERE=Path(__file__).resolve().parent
SOURCE=Path('C:/Users/antio/.codex/worktrees/mia-final-face-v12/win-overlay/asset/mia/blender/mia-orbit-review-v28')
DEST=HERE/'evidence/eye-H-layer-diagnosis'
manifest=json.loads((SOURCE/'upper-H-proof-manifest.json').read_text(encoding='utf-8-sig'))
files={Path(r['path']).resolve() for r in manifest['proof_artifacts']}
files.update(SOURCE/name for name in ['upper-H-proof-manifest.json','UPPER_H_REVIEW.md',
    'render_upper_H_clean.py','upper_H_layer_separation.py'])
records=[]
for source in sorted(files):
    relative=source.relative_to(SOURCE)
    target=DEST/relative
    assert not target.exists(), 'Frozen diagnostic cannot be overwritten'
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,target)
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    assert digest(source)==digest(target)
    records.append({'path':relative.as_posix(),'origin':str(source),'sha256':digest(target)})
for source in manifest['source_images_read_only']:
    assert hashlib.sha256(Path(source['path']).read_bytes()).hexdigest()==source['sha256']
(DEST/'snapshot-manifest.json').write_text(json.dumps({
    'status':'AC1 appearance unresolved; no H native or geometry edit',
    'correction':'Source lash/eyeliner/makeup outer lines are not anatomical lid/free-margin targets. Even a visible ocular occlusion boundary can be the edge of an opaque cosmetic layer.',
    'decision':'Withdraw black-tail-based down-canthus inference. Actual clean G2 upper margin rounds down; no specific anatomical H displacement justified. Preserve supported orbital/cheek and L body.',
    'files':records},indent=2),encoding='utf-8')
print('Layer-separated diagnosis snapshot:',len(records),'files')
