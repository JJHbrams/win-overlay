"""Copy explicit small replay dependencies; never copy experiment scene caches."""
from pathlib import Path
import argparse, hashlib, json, shutil

P = Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
ap.add_argument('--face', required=True)
ap.add_argument('--body', required=True)
ap.add_argument('--hair')
ap.add_argument('--crown')
ap.add_argument('--nape')
ap.add_argument('--receipt', default='portable-copy-face-body.json')
a = ap.parse_args()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
records = []

def copy(src, dest, expected=None):
    src, dest = Path(src).resolve(), Path(dest)
    digest = sha(src)
    if expected:
        assert digest == expected
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        assert sha(dest) == digest, 'Refuse to replace a copied dependency: ' + str(dest)
    else:
        shutil.copyfile(src, dest)
    assert sha(dest) == digest
    records.append(dict(source=str(src), path=str(dest.resolve()), sha256=digest, bytes=src.stat().st_size))

face = Path(a.face).resolve()
manifest = json.loads((face/'audit/D2-portable-manifest.json').read_text())
for row in manifest['portable_files']:
    copy(face/row['relative_path'], P/'parts/face-D2'/row['relative_path'], row['sha256'])
for name in ['HANDOFF_D2.md', 'REVIEW_D2.md', 'audit/D2-portable-manifest.json', 'audit/D2-portable-replay-guard.json', 'art/provenance-D.json']:
    copy(face/name, P/'parts/face-D2'/name)
body = Path(a.body).resolve()
for name in ['replay_current_scene.py', 'body-final-delta.npz', 'body-weight-delta.json', 'underwear-uv.npy',
             'Mia_BodyUnderwear_Color_2048.png', 'Mia_Body_SeamHeight_2048.png', 'Mia_Body_Roughness_2048.png',
             'Mia_BodyPigment_R_2048.png', 'Mia_BodyPigment_G_2048.png', 'Mia_BodyPigment_B_2048.png',
             'current-scene-replay-guard.json']:
    copy(body/name, P/'parts/body-G'/name)
if a.hair:
    hair = Path(a.hair).resolve()
    copy(hair/'apply_bundle_M.py', P/'parts/hair-MN/apply_bundle_M.py')
    bundle = hair/'portable-MN-static'
    hm = json.loads((bundle/'manifest.json').read_text())
    copy(bundle/'manifest.json', P/'parts/hair-MN/bundle/manifest.json')
    copy(bundle/hm['library']['file'], P/'parts/hair-MN/bundle'/hm['library']['file'], hm['library']['sha256'])
    for actor in hm['actors']:
        copy(bundle/actor['data'], P/'parts/hair-MN/bundle'/actor['data'], actor['data_sha256'])
    for name in ['HANDOFF.md', 'portable-MN-static/fresh-replay-verification.json']:
        copy(hair/name, P/'parts/hair-MN'/name)
if a.crown:
    for name in ['apply_crown_O.py','report.json','main-coordinate-delta.npz','fresh-verification.json','portable-manifest.json','stub-identification-board.png']:
        copy(Path(a.crown)/name, P/'parts/crown-O'/name)
if a.nape:
    for name in ['apply_nape_P.py','repair.json','fresh-verification.json','portable-manifest.json','initial-clearance.json','junction-analysis.json']:
        copy(Path(a.nape)/name, P/'parts/nape-P'/name)
for name in ['HANDOFF.md','portable-manifest.json','final-image-inventory.json','final-render-completion.json','native-retirement-allowlist.json']:
    if (body/name).exists():copy(body/name,P/'parts/body-G'/name)
receipt=P/'parts'/a.receipt
assert not receipt.exists(), 'Use a new copy receipt filename'
receipt.write_text(json.dumps(dict(files=records, copied_bytes=sum(r['bytes'] for r in records),
    scope='Small explicit replay/data/map dependencies only; no full native snapshot.'), indent=2)+'\n', encoding='utf-8')
print('SMALL_COMPONENT_INPUTS_COPIED', len(records), sum(r['bytes'] for r in records))
