"""Freeze the accepted lash stage and measured failures, excluding failed large natives."""
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
source = native.parent
dest = P / 'parts' / ('lashes-' + a.tag)
assert not dest.exists(), 'A frozen stage must not be overwritten'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(native) == a.sha256
guard = json.loads((source / ('lash-' + a.tag + '-fresh-preservation-contact.json')).read_text())
assert guard['candidate_sha256'] == a.sha256
assert guard['all_computed_preservation_and_mesh_checks_pass']
native_dest = dest / 'native' / (a.sha256[:12] + '-' + native.name)
native_dest.parent.mkdir(parents=True)
shutil.copyfile(native, native_dest)
assert sha(native_dest) == a.sha256
files = []
for pattern in ['*lash*.py', '*tufts*.py', 'audit_mesh_helpers.py', 'ray_lash_strokes.py',
                'lash-*.json', 'lash-*.npz']:
    files.extend(source.glob(pattern))
for folder in ['E-first', 'E-closure', 'E-hideprobe', 'E-legacyprobe', 'F-gate', a.tag + '-gate']:
    files.extend(p for p in (source / 'lash-review' / folder).rglob('*') if p.is_file() and p.suffix in ['.png', '.json'])
files.extend((source / 'lash-review').glob('*source-first.png'))
records = []
for file in sorted(set(files)):
    target = dest / 'proof' / file.relative_to(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(file, target)
    assert sha(target) == sha(file)
    records.append({'path': target.relative_to(dest).as_posix(), 'sha256': sha(target), 'origin': str(file)})
(dest / 'snapshot-manifest.json').write_text(json.dumps({'native': {'path': native_dest.relative_to(dest).as_posix(), 'sha256': a.sha256},
    'scope': 'Independent upper/lower lashes, explicit master legacy-card evaluation mask, protected C2 geometry. Source style and actual deformation reviewed separately from technical guards.',
    'rejected': 'D upright pins; E half-blink root float; F local lower-tuft inversion despite improved root contact. Failed native binaries are not copied.',
    'files': records}, indent=2), encoding='utf-8')
print(json.dumps({'native': str(native_dest), 'sha256': a.sha256, 'proof_files': len(records)}))
