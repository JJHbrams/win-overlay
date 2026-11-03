"""Read-only saved-evidence check; --root remaps recorded asset/mia paths."""
from pathlib import Path
import argparse,ast,hashlib,json,re
import numpy as np
from PIL import Image

ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path);args=ap.parse_args()
REL=Path('asset/mia/blender/mia-fit-v003/body/shoulder10')
P=(args.root.resolve()/REL) if args.root else Path(__file__).resolve().parent
def resolve(path):
    s=str(path).replace('\\','/');marker='/asset/mia/'
    if args.root and marker in s:return args.root.resolve()/('asset/mia/'+s.split(marker,1)[1])
    return Path(path)
sha=lambda p:hashlib.sha256(resolve(p).read_bytes()).hexdigest()
read=lambda p:json.loads(resolve(p).read_text(encoding='utf-8-sig'))
build=read(P/'build-report.json');cpu=read(P/'CPU-audit.json');rows=read(P/'actual/render-records.json');pkg=read(P/'reference-review.json')
assert build['candidate_NPZ_sha256']==cpu['candidate_sha256']==sha(P/'shoulder10.npz')=='cedb2844033eff973f82f3c45853c2a12fcd2c1dc44d6fc753f1d077eeb0a79d'
assert len(rows)==len(list((P/'actual').glob('*.png')))==16
assert len({(r['state'],r['mode'],r['view']) for r in rows})==16
assert cpu['triangles_exact'] and cpu['X_Y_coordinates_exact'] and cpu['Jacobian']['analytical_global_lower_bound']>0
assert all(s['coords_exact'] and s['triangles_exact'] for s in cpu['protected_sets']) and not cpu['new_nonadjacent_intersections']
data=np.load(P/'shoulder10.npz');base=np.load(resolve(pkg['baseline_native']['path']).parent.parent/'posterior09.npz')
assert np.array_equal(data['triangles'],base['triangles']) and np.array_equal(data['world'][:,:2],base['world'][:,:2])
for mask in [base['world'][:,2]<=1.36,base['world'][:,2]>=1.465]:assert np.array_equal(data['world'][mask],base['world'][mask])
for r in rows:
    assert sha(r['path'])==r['sha256'] and Image.open(resolve(r['path'])).size==(640,640)
    assert sha(r['native']['path'])==r['native']['sha256'] and sha(r['payload']['path'])==r['payload']['sha256']
    assert r['renderer_sha256']==sha(P/'render_saved_pair.py') and not r['geometry_mutated_after_open'] and not r['native_saved_by_renderer']
    q=np.load(resolve(r['payload']['path']));assert hashlib.sha256(q['world'].tobytes()).hexdigest()==r['actual_raw_evaluated_f32_sha256']
    match=next(x for x in rows if x['state']!=r['state'] and x['mode']==r['mode'] and x['view']==r['view'])
    assert r['camera']==match['camera'] and r['actual_semantic_state']==match['actual_semantic_state']
    assert abs(r['camera']['clip_start']-.1)<1e-7 and r['camera']['clip_end']==10
assert set(pkg['required_views'])=={'front','profile','back','oblique'} and len(pkg['views'])==4
for item in [pkg['baseline_native'],pkg['candidate_native']]:assert sha(item['path'])==item['sha256']
for v in pkg['views']:
    for role in ['reference','baseline_render','candidate_render','comparison_board']:assert sha(v[role]['path'])==v[role]['sha256']
    assert v['baseline_camera']==v['candidate_camera']
    box=v['reference']['crop_xyxy'];assert abs((box[2]-box[0])-(box[3]-box[1]))<1e-8
    assert Image.open(resolve(v['reference']['path'])).size==(1536,1024)
assert read(P/'reference-review-validation.json')['evidence_valid']
for b in read(P/'board-records.json')['boards']:assert sha(b['path'])==b['sha256']
protected=read(P/'protected-input-hashes.json')
for path,h in protected.items():assert sha(path)==h,path
native=read(P/'native/export-report.json');reopen=read(P/'native/fresh-reopen.json')
assert sha(native['path'])==native['sha256']==reopen['sha256']=='920f68dc3477db3c0a51fc7c22f2e086602f341f85daf183eadf9e1866167cf4'
assert resolve(native['path']).stat().st_size==2845768 and reopen['raw_world_triangles_bitexact_to_NPZ']
assert len(list(P.rglob('*.blend')))==1 and not list(P.rglob('*.blend1'))
log=(P/'actual.log').read_text(encoding='utf-8-sig');assert 'SHOULDER10_ACTUAL16_DONE_GPU_RELEASE' in log and not re.search(r'traceback|compile error|shader.*failed|error:',log,re.I)
for py in P.glob('*.py'):ast.parse(py.read_text(encoding='utf-8'))
manifest=P/'manifest.json'
if manifest.exists():
    for row in read(manifest)['files']:
        f=P/row['path'];assert f.stat().st_size==row['bytes'] and sha(f)==row['sha256'],str(f)
print(json.dumps(dict(status='PASS read-only evidence integrity ONLY',ART='FAIL S10-AC1/AC2; rejected, no promotion',actuals=16,source_views=4,protected_input_files=len(protected),
    saved_native_pair=True,manifest_checked=manifest.exists(),proofs_or_manifest_written=False,GPU_used=False,root_remapped=str(args.root) if args.root else None),indent=2))
