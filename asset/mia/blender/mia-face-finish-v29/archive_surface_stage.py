"""Freeze the actual guarded material native and compact authoring/probe evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

P = Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
ap.add_argument('--native', required=True)
ap.add_argument('--sha256', required=True)
ap.add_argument('--tag', required=True)
a = ap.parse_args()
native = Path(a.native).resolve()
source = native.parent.parent
dest = P / ('surface-' + a.tag)
assert not dest.exists()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(native) == a.sha256
guard_path = native.parent / 'surface-candidate-guard.json'
guard = json.loads(guard_path.read_text())
assert guard['candidate_sha256'] == a.sha256
assert guard['geometry_all_owners_exact'] and guard['packed_map_reopen_verification']
target_native = dest / 'native' / ('Mia_FaceFinish_v29_' + a.tag + '.blend')
target_native.parent.mkdir(parents=True)
shutil.copyfile(native, target_native)
assert sha(target_native) == a.sha256
files = list(source.glob('*.py'))
files += [source / n for n in ['active-surface-inventory.json', 'actual-visible-surface-scope.json',
    'actual-pigment-UV-thumbnail.png', 'actual-active-route-thumbnail.png',
    'actual-head-neck-mask-thumbnail.png', 'actual-packed-pigment-display.png',
    'STAGING_STATE.json', 'SURFACE_AUDIT_AND_PROPOSAL.md',
    'surface-staging-api-validation.json', 'wall-fade-native-endpoint-validation.json']]
for folder in ['art-pigment-A', 'art-pigment-B', 'native-control-maps-final']:
    files += [p for p in (source / folder).rglob('*') if p.is_file() and p.suffix in ['.png', '.txt', '.json', '.exr']]
files += [p for p in native.parent.rglob('*') if p.is_file() and p.suffix in ['.json', '.png', '.npz', '.exr']]
records = []
for file in sorted(set(files)):
    if not file.is_file():
        continue
    target = dest / 'proof' / file.relative_to(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(file, target)
    assert sha(file) == sha(target)
    records.append({'path': target.relative_to(dest).as_posix(), 'sha256': sha(target), 'origin': str(file)})
(dest / 'snapshot-manifest.json').write_text(json.dumps({'native': {'path': target_native.relative_to(dest).as_posix(), 'sha256': a.sha256},
    'scope': 'G-based material-only face/wall application. Actual UV, packed image/color-space/active-output checks plus source and actual-light probes required separately.',
    'detail_provenance': 'Generated cosmetic art B is1254square sRGB. Numerical native controls2048 float Non-Color; lossless ZIP repack preserves pixel bytes, not an increase of art detail.',
    'files': records}, indent=2), encoding='utf-8')
print(json.dumps({'native': str(target_native), 'sha256': a.sha256, 'proof_files': len(records)}))
