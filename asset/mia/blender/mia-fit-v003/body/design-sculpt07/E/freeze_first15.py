"""Curate the immutable first E actual15; no frozen ancestor writes."""
from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent;D=P.parent/'D'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
native=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-refinement-v002/integrated/Mia_v0.0.2_Review_R3b.blend')
assert sha(native)=='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'
protected=json.loads((P/'D-protected-hashes.json').read_text())
assert all(sha(D/k)==v for k,v in protected.items())
rows=[]
for folder,n in [('actual-E',6),('actual-audit',9)]:
    rr=json.loads((P/folder/'render-records.json').read_text());assert len(rr)==n
    for r in rr:
        path=P/folder/Path(r['path']).name;assert sha(path)==r['sha256'];rows.append(dict(path=str(path.relative_to(P)),sha256=r['sha256'],view=r['view'],mode=r.get('mode','gray'),state=r.get('state','E')))
assert len(rows)==15
files={str(f.relative_to(P)).replace('\\','/'):sha(f) for f in sorted(P.rglob('*')) if f.is_file() and '__pycache__' not in f.parts and f.name!='manifest.json' and 'bra-diagnostic' not in f.parts and 'posterior-form02' not in f.parts}
out=dict(status='FIRST15 FROZEN; bounded breast support improvement; posterior visible continuity AC1 FAIL; no all-E acceptance',native_sha256=sha(native),D_protected_files=len(protected),D_all_protected_hashes_exact=True,mesh_sha256=sha(P/'sculpt07-E.npz'),parameters_sha256=sha(P/'parameters.json'),actual_frames=rows,files=files,native_saved=False,head_scale_changed=False,full_axilla_acceptance='UNVERIFIED',temporary_context_seams='UNVERIFIED')
(P/'manifest.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print('E_FIRST15_MANIFEST_READY',len(files),len(rows),len(protected))
