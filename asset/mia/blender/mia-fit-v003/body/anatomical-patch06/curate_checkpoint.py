"""Curate ONLY this rejected prototype folder; no geometry/native/GPU change."""
from pathlib import Path
import ast,hashlib,json
P=Path(__file__).resolve().parent;repo=P.parents[5]
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
files=[]
for f in sorted(P.rglob('*')):
    if not f.is_file() or '__pycache__' in f.parts or f.name in ['handoff.json','checkpoint-06.json','evaluated06.npz'] or f.suffix=='.log':continue
    if f.suffix not in ['.py','.json','.md','.png','.npz']:continue
    assert f.suffix!='.blend'
    if f.suffix=='.py':ast.parse(f.read_text(encoding='utf-8'))
    files.append(dict(path=f.relative_to(P).as_posix(),bytes=f.stat().st_size,sha256=sha(f)))
r=json.loads((P/'actual-four/render-records.json').read_text());assert len(r)==4
for x in r:assert sha(P/'actual-four'/Path(x['path']).name)==x['sha256']
g=json.loads((P/'cpu-guard.json').read_text());assert g['prototype_sha256']==sha(P/'prototype06.npz') and g['strict_nonadjacent_contacts']==0
payload=dict(status='REJECTED static prototype06; root and producer viewedactual4. No adoption/anatomy/wholeMia approval.',prototype_sha256=sha(P/'prototype06.npz'),actual_frames=4,gpu_released=True,native_saved=False,migration='UNVERIFIED',source_binding='FAIL',continuity='FAIL: actual pinch/doublelip/flattenedmass',
    dependencies=dict(baseline_native='canonical asset/mia/blender/mia-refinement-v002/integrated/Mia_v0.0.2_Review_R3b.blend',baseline_sha256=g['native_sha256'],parent_runtime='body inputs/current caches/target01 retained by historicala9f385e and53d1ff2 checkpoints',source_constraints='../source-binding/constraints.json',root_merge='d63346e3082b09c849257828557e69b9803b876b'),
    files=files,total_bytes=sum(x['bytes'] for x in files),excluded='Regenerable evaluated06 cache, pycache, logs, full captions/natives; all old unknown files remain untouched.')
(P/'checkpoint-06.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')
paths=[str((P/x['path']).relative_to(repo)).replace('\\','/') for x in files]+[str((P/'checkpoint-06.json').relative_to(repo)).replace('\\','/')]
(P/'checkpoint-pathspec.nul').write_bytes(('\0'.join(paths)+'\0').encode())
print('PATCH06_CHECKPOINT_CURATED',len(paths),payload['total_bytes'],flush=True)
