"""Explicit checkpoint allowlist; never stage native caches or unrelated worktrees."""
from pathlib import Path
import argparse,hashlib,json,subprocess
P=Path(__file__).resolve().parent;ROOT=P.parents[3]
ap=argparse.ArgumentParser();ap.add_argument('--stage',action='store_true');a=ap.parse_args()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='codex/mia-v002-refinement'
selected=set()
def add(file):
    file=file.resolve();assert file.is_relative_to(ROOT)
    if file.is_file() and '__pycache__' not in file.parts and file.suffix not in ['.pyc','.blend1']:
        selected.add(file)
def tree(folder):
    for file in folder.rglob('*'):
        if file.is_file():add(file)
for name in ['CURRENT_STATE.json','WORKING_PROTOCOL.md']:add(P.parents[1]/name)
for file in P.iterdir():
    if file.is_file() and file.suffix in ['.py','.json','.md','.ps1','.log']:add(file)
for name in ['parts','art','storage']:tree(P/name)
for file in (P/'expressions').iterdir():
    if file.is_file() and file.suffix in ['.py','.json']:add(file)
for name in ['source-panels','smile-calibration-r3','pose-calibration-r3']:tree(P/'expressions'/name)
tree(P/'review/integrated-R3b')
tree(P/'review/integrated-R3-855d/intermediates')  # Actual failed-run evidence; not a completed4-case suite.
for file in (P/'integrated').glob('*.json'):add(file)
for name in ['Mia_v0.0.2_Review_R2.blend','Mia_v0.0.2_Review_R3b.blend']:add(P/'integrated'/name)
for required in [P/'R3B_WORKING_REVIEW.json',P/'INDEPENDENT_R3B_REVIEW.md',P/'review/integrated-R3b/verification-completion.json']:
    assert required in selected,'Missing final checkpoint evidence: '+str(required)
for file in selected:
    if file.suffix=='.blend':
        assert file.parent==P/'integrated' or file.is_relative_to(P/'parts/hair-MN/bundle'),'Unexpected whole-scene cache in stage selection'
manifest=P/'storage/checkpoint-file-manifest.json';spec=P/'storage/checkpoint-pathspec.nul'
selected.discard(manifest);selected.discard(spec)
rows=[dict(path=f.relative_to(ROOT).as_posix(),bytes=f.stat().st_size,sha256=sha(f)) for f in sorted(selected)]
manifest.write_text(json.dumps(dict(files=rows,total_bytes=sum(r['bytes'] for r in rows),
    scope='Explicit refinement/runtime/maps/current101proof plus R2dependency and currentR3b. No OP/failedR3 full scenes, expression/native junction caches, unselected producer full scenes or unrelated project files.'),indent=2)+'\n',encoding='utf-8')
paths=[r['path'] for r in rows]+[manifest.relative_to(ROOT).as_posix()]
spec.write_bytes(b'\0'.join(p.encode('utf-8') for p in paths)+b'\0')
if a.stage:
    assert not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).strip(),'Review preexisting staged work first'
    subprocess.run(['git','add','--pathspec-from-file='+str(spec),'--pathspec-file-nul'],cwd=ROOT,check=True)
    staged=set(subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines())
    assert staged.issubset(paths),'Unexpected staged path'
print('CHECKPOINT_'+('STAGED' if a.stage else 'ALLOWLIST_READY'),len(rows),sum(r['bytes'] for r in rows))
