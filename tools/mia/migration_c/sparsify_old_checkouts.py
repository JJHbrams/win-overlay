"""Retire exact recoverable exports from old C checkouts, preserving local work.

No history rewrite, force-clean, recursive removal, or untracked-file deletion.
The input is the separately prepared manifest, verified again before each use.
"""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'.mia-cache/git-storage-20261104'
ALLOW = {'mia-body-head-v06','mia-final-face-v12','mia-head-hair-fit-v16','mia-reference-recovery',
         'mia-v002-body','mia-v002-face','mia-v002-hair','mia-v003-design-sculpt'}
BASE = Path('C:/Users/antio/.codex/worktrees').resolve()
CACHE = Path('C:/Users/antio/Desktop/Workspace/projects/win-overlay/.git/lfs/objects')

def git(wt, *args, data=None):
    env = os.environ.copy(); env['GIT_LFS_SKIP_SMUDGE'] = '1'
    p = subprocess.run(['git',*args],cwd=wt,input=data,capture_output=True,env=env)
    if p.returncode: raise RuntimeError(p.stderr.decode('utf8',errors='replace'))
    return p.stdout

def hashes(path):
    size=path.stat().st_size; a=hashlib.sha1(); a.update(f'blob {size}\0'.encode()); b=hashlib.sha256()
    with path.open('rb') as stream:
        while part := stream.read(4*1024*1024): a.update(part); b.update(part)
    return a.hexdigest(),b.hexdigest()

def files(wt):
    result={}
    for directory, dirs, names in os.walk(wt,followlinks=False):
        dirs[:]=[n for n in dirs if n!='.git' and not(Path(directory)/n).is_symlink()]
        for name in names:
            p=Path(directory)/name
            if name=='.git':continue
            st=p.stat();result[p.relative_to(wt).as_posix()]=(st.st_size,st.st_mtime_ns)
    return result

def literal(rel):
    return '!/'+''.join('\\'+c if c in '*?[' else c for c in rel)

def main():
    target=sys.argv[1];assert target in ALLOW
    wt=(BASE/target/'win-overlay').resolve();assert wt.is_relative_to(BASE) and wt!=ROOT
    result_path=OUT/f'sparse-{target}.json';assert not result_path.exists()
    rows=[r for r in json.loads((OUT/'sparse-candidates.json').read_text())if r['worktree']==target]
    status=git(wt,'status','--porcelain=v1','--untracked-files=all','-z')
    changed=set(git(wt,'diff','HEAD','--name-only','-z').decode('utf8').split('\0'))
    index={}
    for entry in git(wt,'ls-files','--stage','-z').decode('utf8').split('\0'):
        if not entry:continue
        info,rel=entry.split('\t',1);mode,oid,stage=info.split()
        if stage=='0':index[rel]=oid
    before=files(wt);verified=[];skipped=[]
    for row in rows:
        rel=row['relativePath'];p=(wt/rel).resolve()
        assert p.is_relative_to(wt) and rel.startswith('asset/mia/blender/')
        assert not re.search(r'references?|source|checkpoint|review|r3b|shoulder11|v31|brows_lashes|cleanhair',rel,re.I)
        if rel in changed or rel not in index or not p.is_file():skipped.append(rel);continue
        assert index[rel]==row['indexBlobOid'] and p.stat().st_size==row['materializedBytes']
        oid,digest=hashes(p);lfs=None
        if oid!=index[rel]:
            size=int(git(wt,'cat-file','-s',index[rel]))
            if size>1024:skipped.append(rel);continue
            pointer=git(wt,'cat-file','blob',index[rel]).decode('ascii',errors='replace')
            match=re.fullmatch(r'version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize ([0-9]+)\n',pointer)
            if not match or digest!=match[1] or p.stat().st_size!=int(match[2]):skipped.append(rel);continue
            lfs=CACHE/match[1][:2]/match[1][2:4]/match[1]
            assert lfs.is_file() and lfs.stat().st_size==p.stat().st_size and hashes(lfs)[1]==digest
        verified.append(dict(path=rel,bytes=p.stat().st_size,sha256=digest,index_oid=index[rel],lfs_cache=str(lfs)if lfs else None))
    sparse_path=Path(git(wt,'rev-parse','--git-path','info/sparse-checkout').decode().strip())
    if not sparse_path.is_absolute():sparse_path=wt/sparse_path
    enabled=subprocess.run(['git','config','--bool','core.sparseCheckout'],cwd=wt,capture_output=True).stdout.strip()==b'true'
    old_patterns=sparse_path.read_text(encoding='utf8')if enabled and sparse_path.is_file()else '/*\n'
    excluded={r['path']for r in verified}
    # Do not accidentally materialize pre-existing sparse absences.
    absences={p for p in index if p not in before and p not in changed}
    patterns=old_patterns.rstrip()+'\n'+'\n'.join(literal(p)for p in sorted(excluded|absences))+'\n'
    record=dict(worktree=str(wt),HEAD=git(wt,'rev-parse','HEAD').decode().strip(),
                before_bytes=sum(v[0]for v in before.values()),verified=verified,skipped=skipped,
                old_sparse_patterns=old_patterns,status_before_sha256=hashlib.sha256(status).hexdigest(),phase='VERIFIED_BEFORE')
    result_path.write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
    output=git(wt,'sparse-checkout','set','--no-cone','--no-sparse-index','--stdin',data=patterns.encode())
    after=files(wt)
    assert not(set(after)-set(before)),'Unexpected checkout expansion'
    assert set(before)-set(after)==excluded,'Unexpected removed or retained files'
    assert all(after[p]==v for p,v in before.items()if p not in excluded),'Noncandidate changed'
    assert git(wt,'status','--porcelain=v1','--untracked-files=all','-z')==status,'Local work status changed'
    assert git(wt,'rev-parse','HEAD').decode().strip()==record['HEAD']
    record.update(phase='COMPLETE',removed_files=len(excluded),removed_bytes=sum(r['bytes']for r in verified),
                  after_bytes=sum(v[0]for v in after.values()),all_non_candidate_files_metadata_exact=True,
                  local_work_status_exact=True,history_refs_kept=True)
    result_path.write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in record.items()if k not in ['verified','skipped','old_sparse_patterns']},indent=2),flush=True)

if __name__=='__main__':main()
