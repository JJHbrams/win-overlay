"""Create the explicit archival whitelist/hash inventory; never add to Git or edit a model."""
from pathlib import Path
import hashlib
import json
import re

P = Path(__file__).resolve().parent


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


recipes = sorted(p.name for p in P.glob('*.py') if p.name != 'source_trace_grid.py')
reports = [
    'README.md', 'STATE.md', 'PLAN.md', 'base-audit.json', 'source_paths_v06.json',
    'manifest.json', 'locks.npz', 'CPU-guard.json',
    'detailed-branch-inventory-DATA.json', 'detailed-branch-inventory-DATA.npz',
    'intact-detail-donors-DATA.json', 'intact-detail-donors-DATA.npz',
    'detailed-fragment-boundaries-DATA.json', 'detail-prototypes.json', 'detail-prototypes.npz',
    'detailed_layer_layout.json', 'detailed-fill.json', 'detailed-fill.npz',
    'buried-core.json', 'buried-core.npz', 'detailed-CPU-guard.json',
    'donor-exposure-DATA.json', 'source-material-active-route.json',
    'identity-assembly.json', 'identity-assembly.npz', 'identity-copy-CPU-report.json',
    'identity-owned-firsthit.json', 'identity-owned-firsthit.npz', 'identity-pixel-proof.json',
    'checkpoint-source-ownership-guard.json',
    'SOURCE_3D_CURVES_VOLUME_DATA.png', 'DETAILED_LAYER_SOURCE_OWNERSHIP_DATA.png',
    'DONOR_EXPOSURE_DATA.png', 'IDENTITY_EXTERIOR_OWNERSHIP_DATA.png',
    'IDENTITY_ACTUAL_PIXEL_PROOF.png',
]
actuals = [p.relative_to(P).as_posix() for name in ['actual-first4', 'actual-detailed-B', 'actual-identity']
           for p in sorted((P / name).iterdir()) if p.suffix in ['.png', '.json']]
listed = sorted(set(recipes + reports + actuals + ['CHECKPOINT_FILES.txt', 'CHECKPOINT.json']))
(P / 'CHECKPOINT_FILES.txt').write_text('\n'.join(listed) + '\n', encoding='utf-8', newline='\n')
scans = []
for folder, logname, marker, expected in [
    ('actual-first4', 'actual-first4.log', 'CENTRAL_FILL_FIRST4_DONE', 4),
    ('actual-detailed-B', 'actual-detailed-B.log', 'DETAILED_B_PROBE_DONE2', 2),
    ('actual-identity', 'actual-identity.log', 'IDENTITY_ACTUAL_DONE2', 2),
]:
    log = P / logname
    content = log.read_text(encoding='utf-8', errors='replace')
    scan = dict(folder=folder, original_log_sha256=sha(log), expected_actual_image_count=expected,
                completion_marker=marker, completion_observed=marker in content,
                shader_or_runtime_error_observed=bool(re.search(r'(?i)error|failed|traceback|too many', content)),
                note='Observed during checkpoint curation; raw log deliberately excluded from commit.')
    assert scan['completion_observed'] and not scan['shader_or_runtime_error_observed'], scan
    scans.append(scan)
manifest = dict(schema=1, status='REJECTED_A_B_AND_IDENTITY_HISTORY_ONLY',
    new_fill_selected=False, ART=False, native_saved=False, live_mutated=False,
    branch='codex/mia-v003-hair', prior_selected_partial_commits=['c35d332', '5c0b5b4'],
    base_native_sha256='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1',
    source_Main_authored_coordinate_sha256='16d192576cd8ecc1905f4eba96b4686c038e8c94a56e6eec7dee552e6eee0b2c',
    protected_external_sources=[
        dict(path='asset/mia/blender/mia-refinement-v002/integrated/Mia_v0.0.2_Review_R3b.blend',
             sha256='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'),
        dict(path='asset/mia/references/mia-clean-master-v22.png',
             sha256='3c760f1c276f343258ac38c6abbe370a511b9a148f4ffa37a08f8a277fa05d19'),
        dict(path='asset/mia/references/received/mia-body-v06-confirmed-20261102.png',
             sha256='6d88d1bc6b579d1ac53436d9f1fa50f903117ac244e307b8e08a9d1e270080e1')],
    render_batch_precheckpoint_scans=scans,
    exclusions=['*.blend*', '*.log', '__pycache__/', 'current-geometry.npz', 'held-first-six/',
                'superseded source_paths.json', 'redundant source grids'],
    files=[dict(path=rel, bytes=(P / rel).stat().st_size, sha256=sha(P / rel))
           for rel in listed if rel != 'CHECKPOINT.json'])
(P / 'CHECKPOINT.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(dict(files=len(listed), bytes=sum(r['bytes'] for r in manifest['files']),
                      excluded_local_files_untouched=True, model_mutated=False), indent=2))
