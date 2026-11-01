"""Preserve the actual failed E contribution audit, without duplicate natives."""
from pathlib import Path
import hashlib
import json
import shutil

HERE = Path(__file__).resolve().parent
PRODUCER = Path('C:/Users/antio/.codex/worktrees/mia-reference-recovery/win-overlay/asset/mia/blender/mia-thorax-review-v28')
DEST = HERE / 'evidence' / 'rejected-thorax-E'
FILES = [
    'decompose_actual_E_masses.py', 'handoff-E-delta.npz',
    'mass-audit-E/actual-two-mass-audit.json',
    'mass-audit-E/actual-E-two-mass-decomposition.npz',
    'mass-audit-E/actual-core-skin-sections.png',
    'mass-audit-E/explicit-Dsoft-normal-footprint.png',
    'mass-audit-E/source-core-skin-front.png',
    'mass-audit-E/source-core-skin-profile.png',
    'mass-audit-E/source-core-skin-oblique.png',
    'sculpt-D-report.json', 'sculpt-E-report.json',
]
FILES += ['renders/E-without-explicit-Dsoft/geometry-clay/' + name
          for name in ('front.png', 'profile.png', 'oblique.png', 'render-records.json')]
manifest = []
for relative in FILES:
    source = PRODUCER / relative
    assert source.is_file(), source
    dest = DEST / relative
    assert not dest.exists(), 'Evidence snapshots are immutable: ' + str(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    shutil.copy2(source, dest)
    assert hashlib.sha256(dest.read_bytes()).hexdigest() == digest
    manifest.append({'path': relative, 'origin': str(source), 'sha256': digest})
(DEST / 'snapshot-manifest.json').write_text(json.dumps({
    'status': 'REJECTED / core anatomy gate unmet; no selection implied',
    'native_E_sha256': 'dfb9e2c3d9774f9dc3c00bd396e20a5b6f8b3aaa926570aff1a8d5f9d549c87c',
    'meaning': 'Actual E contribution decomposition. Core label means E without explicit Dsoft, not a separately approved ribcage scaffold.',
    'limits': 'The1.25mm comparison isolates f-blend residual, not every common baseline contribution retained by the upper extension. Horizontal core sections are single ovals, not literal paired duplicate breasts. The failed sagittal prominence/rim and inherited construction remain the issue.',
    'original_natives': 'Preserved in producer worktree; not duplicated here. The handoff records exact E target coordinates for all42 named keys.',
    'files': manifest,
}, indent=2), encoding='utf-8')
print('Rejected E evidence archived:', len(manifest), 'files')
