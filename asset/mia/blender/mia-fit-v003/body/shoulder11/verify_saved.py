"""Read-only final11 integrity; optional --root remaps recorded asset/mia paths."""
from pathlib import Path
import argparse,ast,hashlib,json,re
import numpy as np
from PIL import Image
ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path);args=ap.parse_args();rel=Path('asset/mia/blender/mia-fit-v003/body/shoulder11')
P=args.root.resolve()/rel if args.root else Path(__file__).resolve().parent
def resolve(p):
    s=str(p).replace('\\','/');mark='/asset/mia/'
    return args.root.resolve()/('asset/mia/'+s.split(mark,1)[1]) if args.root and mark in s else Path(p)
sha=lambda p:hashlib.sha256(resolve(p).read_bytes()).hexdigest();read=lambda p:json.loads(resolve(p).read_text(encoding='utf-8-sig'))
raw=np.load(P/'shoulder11.npz');final=np.load(P/'shoulder11-canonical.npz');base=np.load(P.parent/'posterior-union09/posterior09.npz')
assert sha(P/'shoulder11.npz')=='61c655d1916776940b1a29d32fe1dd9fbd5633007fa465a58d36394e3efde94b'
assert sha(P/'shoulder11-canonical.npz')=='9382e21638e35ce36e3818cc0eb8e060994cc05227a5c56b262dcea7f4b843e9'
assert np.array_equal(raw['triangles'],final['triangles']);changed=np.flatnonzero(np.any(raw['world']!=final['world'],axis=1));proof=read(P/'roundoff-canonicalization.json')
assert len(changed)==proof['changed_points']==4 and set(changed)=={m['raw11_vertex'] for m in proof['bijective_mapping']}
assert proof['maximum_distance_m']<=1e-7 and proof['all_other_coordinates_bitexact']
for m in proof['bijective_mapping']:
    assert np.array_equal(final['world'][m['raw11_vertex']],base['world'][m['old09_vertex']])
    assert np.array_equal(raw['world'][m['raw11_vertex'],1:],final['world'][m['raw11_vertex'],1:])
# Independently redo exact physical matching without assuming remeshed IDs.
lookup={q.tobytes():i for i,q in enumerate(final['world'])};faces={tuple(sorted(map(int,q))) for q in final['triangles']};v0=base['world'];f0=base['triangles']
for mask in [v0[:,2]<=1.36,v0[:,2]>=1.465,(abs(v0[:,0])<=.125)&(v0[:,1]<=-.03)&(v0[:,2]>=1.18)&(v0[:,2]<=1.35)]:
    ids=np.flatnonzero(mask);assert all(v0[i].tobytes() in lookup for i in ids)
    for face in f0[mask[f0].all(1)]:assert tuple(sorted(lookup[v0[i].tobytes()] for i in face)) in faces
assert all(s['exact'] for s in read(P/'protected-physical-triangles.json').values())
cpu=read(P/'CPU-audit.json');assert not cpu['new_nonadjacent_intersections'] and cpu['main_lower_passage_open'] and cpu['connected_components']==1
rows=read(P/'actual/render-records.json');assert len(rows)==len(list((P/'actual').glob('*.png')))==16
for r in rows:
    assert sha(r['path'])==r['sha256'] and Image.open(resolve(r['path'])).size==(640,640)
    assert sha(r['native']['path'])==r['native']['sha256'] and sha(r['payload']['path'])==r['payload']['sha256']
    assert sha(P/'render_saved_pair.py')==r['renderer_sha256'] and not r['geometry_mutated_after_open'] and not r['native_saved_by_renderer']
    data=np.load(resolve(r['payload']['path']));assert hashlib.sha256(data['world'].tobytes()).hexdigest()==r['actual_raw_evaluated_f32_sha256']
    peer=next(x for x in rows if x['state']!=r['state'] and x['mode']==r['mode'] and x['view']==r['view'])
    assert peer['camera']==r['camera'] and peer['actual_semantic_state']==r['actual_semantic_state']
    assert abs(r['camera']['clip_start']-.1)<1e-7 and r['camera']['clip_end']==10
pkg=read(P/'reference-review.json');assert set(pkg['required_views'])=={'front','profile','back','oblique'}
for role in ['baseline_native','candidate_native']:assert sha(pkg[role]['path'])==pkg[role]['sha256']
for v in pkg['views']:
    for role in ['reference','baseline_render','candidate_render','comparison_board']:assert sha(v[role]['path'])==v[role]['sha256']
    box=v['reference']['crop_xyxy'];assert abs((box[2]-box[0])-(box[3]-box[1]))<1e-8
    assert Image.open(resolve(v['reference']['path'])).size==(1536,1024) and v['baseline_camera']==v['candidate_camera']
assert read(P/'reference-review-validation.json')['evidence_valid']
for b in read(P/'board-records.json')['boards']:assert sha(b['path'])==b['sha256']
held=read(P/'protected-input-hashes.json')
for path,h in held.items():assert sha(path)==h,path
native=read(P/'native/export-report.json');reopen=read(P/'native/fresh-reopen.json');assert sha(native['path'])==native['sha256']==reopen['sha256']=='462cb972ab37aff1cffe9763e8d46923a4be7453c0e6efe8546ea7b38b84e0ad'
assert resolve(native['path']).stat().st_size==2827750 and reopen['raw_world_triangles_bitexact_to_NPZ']
assert len(list(P.rglob('*.blend')))==1 and not list(P.rglob('*.blend1'))
log=(P/'actual.log').read_text(encoding='utf-8-sig');assert 'SHOULDER11_ACTUAL16_DONE_GPU_RELEASE' in log and not re.search(r'traceback|compile error|shader.*failed|error:',log,re.I)
for f in P.glob('*.py'):ast.parse(f.read_text(encoding='utf-8'))
manifest=P/'manifest.json'
if manifest.exists():
    for row in read(manifest)['files']:
        f=P/row['path'];assert f.stat().st_size==row['bytes'] and sha(f)==row['sha256'],str(f)
print(json.dumps(dict(status='PASS read-only evidence integrity ONLY',ART='Root/fresh reviewer S11-AC1..5 boundedstatic PASS; fullsource/fullMia OPEN',
    actuals=16,source_views=4,raw_and_FINAL_retained=True,exact_restored_points=4,protected_input_files=len(held),manifest_checked=manifest.exists(),proofs_or_manifest_written=False,GPU_used=False),indent=2))
