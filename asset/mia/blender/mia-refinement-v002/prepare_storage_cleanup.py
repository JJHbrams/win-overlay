"""Prepare an exact, fresh-index-checked obsolete snapshot manifest. Does not delete."""
from pathlib import Path
import datetime, hashlib, json, os, subprocess
P=Path(__file__).resolve().parent;out=P/'storage';out.mkdir(exist_ok=True)
root=P.parents[3]
repos={
 'canonical':root,
 'reference':Path('C:/Users/antio/.codex/worktrees/mia-reference-recovery/win-overlay'),
 'face':Path('C:/Users/antio/.codex/worktrees/mia-final-face-v12/win-overlay'),
 'hair':Path('C:/Users/antio/.codex/worktrees/mia-head-hair-fit-v16/win-overlay')}
assert root.name=='win-overlay'
facefile=Path('C:/Users/antio/.codex/worktrees/mia-v002-face/win-overlay/asset/mia/blender/mia-facial-maps-v002/cleanup-candidates.json')
hairfile=Path('C:/Users/antio/.codex/worktrees/mia-v002-hair/win-overlay/asset/mia/blender/mia-hair-refine-v002/deletion-candidates.json')
face=json.loads(facefile.read_text(encoding='utf-8'));hair=json.loads(hairfile.read_text(encoding='utf-8'))
rows=[]
def add(repo,path,size,reason):rows.append(dict(repository=str(repo),path=str(Path(path)),bytes=size,reason=reason,tracked=False))
for r in face['candidates']:add(repos['face'],r['path'],r['bytes'],'Superseded untracked face full-scene snapshot/backup; small replay data, maps, frames and actual selected native retained.')
for r in hair['delete_candidates']:add(repos['hair'],r['path'],r['bytes'],r['reason'])
protect_reference={
 'asset/mia/blender/mia-thorax-review-v28/core-first-G3/Mia_G3_TrueCore.blend',
 'asset/mia/blender/mia-thorax-review-v28/source-soft-L/Mia_L_CorePlusBreast.blend'}
reference_folders={'mia-thorax-review-v28','mia-body-finish-v22','mia-body-finish-v23','mia-body-form-v21','mia-body-surface-v20-r2','mia-face-surface-v29','mia-toon-surfaces-v30'}
canonical_folders={'mia-reference-finish-v22','mia-visible-art-v30','mia-face-finish-v29','mia-orbit-thorax-review-v28'}
for tag,allowed in [('canonical',canonical_folders),('reference',reference_folders)]:
 inv=json.loads((out/(tag+'-before.json')).read_text(encoding='utf-8'))
 for r in inv['all_files']:
  parts=Path(r['relative']).parts
  if r['tracked'] or len(parts)<4 or parts[3] not in allowed:continue
  if tag=='reference' and r['relative'] in protect_reference:continue
  if r['extension']=='.blend' and r['bytes']>1_000_000:
   add(repos[tag],r['path'],r['bytes'],'Obsolete untracked full-scene research iteration; selected v001/current candidates and G3/L provenance originals retained.')
  elif r['extension'] in {'.blend1','.blend@'}:
   main=Path(r['path'][:-1])
   if r['extension']=='.blend@' or main.is_file():add(repos[tag],r['path'],r['bytes'],'Older backup or failed Blender write temporary from a superseded research stage.')
# Older hair autosave backups have corresponding newer .blend files. Keep the four
# limited research checkpoints themselves; only the autosave copies are discarded.
hair_root=repos['hair']/'asset/mia'
for folder,dirs,files in os.walk(hair_root,followlinks=False):
 dirs[:]=[d for d in dirs if not os.path.isjunction(Path(folder)/d)]
 for name in files:
  f=Path(folder)/name
  if f.suffix!='.blend1':continue
  main=f.with_name(name[:-1])
  if main.is_file() and main.stat().st_mtime>=f.stat().st_mtime:
   add(repos['hair'],f,f.stat().st_size,'Superseded untracked Blender autosave; corresponding newer main native exists.')
whitelist=[Path(x['path']).resolve() for x in face['protected_canonical']]+[Path(x['path']).resolve() for x in hair['whitelist']]
whitelist += [(repos['reference']/x).resolve() for x in protect_reference]
whitelist += [Path(face['genuine_0240_donor_to_preserve']['path']).resolve()]
index={str(repo):{x.lower().replace('\\','/') for x in subprocess.check_output(['git','ls-files','-z'],cwd=repo).decode('utf-8').split('\0') if x} for repo in repos.values()}
unique={}
for r in rows:
 p=Path(r['path']);repo=Path(r['repository']);scope=(repo/'asset/mia/blender').resolve()
 assert p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(scope),r
 assert p.resolve().drive.upper()=='C:' and p.resolve() not in whitelist,r
 assert p.suffix in {'.blend','.blend1','.blend@'},r
 assert p.stat().st_size==r['bytes'],r
 rel=p.relative_to(repo).as_posix();assert rel.lower() not in index[str(repo)],r
 r['relative']=rel;r['mtime_ns']=p.stat().st_mtime_ns
 unique[str(p.resolve()).lower()]=r
rows=sorted(unique.values(),key=lambda r:r['path'].lower())
protected=[]
for p in whitelist:
 assert p.is_file(),p
 protected.append(dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
by_repo={str(repo):sum(r['bytes'] for r in rows if r['repository']==str(repo)) for repo in repos.values()}
report=dict(schema_version=1,created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
 authorization='User explicitly requested intermediate-artifact cleanup after C drive exhaustion, 2026-11-02.',
 status='PREPARED_NOT_EXECUTED',candidates=rows,count=len(rows),bytes=sum(r['bytes'] for r in rows),by_repository=by_repo,
 protected=protected,all_tracked_files_preserved=True,source_art_and_small_evidence_preserved=True,
 original_candidate_manifests=[dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in [facefile,hairfile]],
 history_limit='Removed rejected exact-native paths will be explicitly marked historical. Their small deltas, art, screenshots and recorded hashes remain. No selected checkpoint or Git history is deleted.')
f=out/'cleanup-manifest.json';f.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(manifest=str(f),count=report['count'],bytes=report['bytes'],by_repository=by_repo,protected=len(protected)),indent=2))
