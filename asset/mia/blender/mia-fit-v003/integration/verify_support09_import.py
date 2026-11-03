"""Read frozen 09 artifacts in the canonical checkout; never rewrite their proof."""
import ast
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[5]
PACK = ROOT / 'asset/mia/blender/mia-fit-v003/body/posterior-union09'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(path):
    normalized = str(path).replace('\\', '/')
    marker = '/asset/mia/'
    assert marker in normalized, normalized
    return ROOT / ('asset/mia/' + normalized.split(marker, 1)[1])


def artifact(item):
    path = canonical(item['path'])
    assert path.is_file() and sha(path) == item['sha256'], path
    return path


manifest = read(PACK / 'manifest.json')
for item in manifest['files']:
    path = PACK / item['path']
    assert path.stat().st_size == item['bytes'] and sha(path) == item['sha256'], path
assert len(manifest['files']) == 83
payload_sha = sha(PACK / 'posterior09.npz')
assert payload_sha == 'd5bf574ea958923fc70fe6ade4de7e0b64ec970c3cf15156be5f135af3c9cdd2'
data = np.load(PACK / 'posterior09.npz')
assert data['world'].shape == (67992, 3) and data['triangles'].shape == (135980, 3)
assert np.isfinite(data['world']).all()
world_sha = hashlib.sha256(data['world'].tobytes()).hexdigest()
actuals = []
for folder, renderer, expected in [('actual8', 'render_actual8.py', 8),
                                    ('actual-extra3', 'render_extra3.py', 3)]:
    rows = read(PACK / folder / 'render-records.json')
    assert len(rows) == len(list((PACK / folder).glob('*.png'))) == expected
    for row in rows:
        path = artifact(row)
        artifact(row['baseline_E_render'])
        assert Image.open(path).size == tuple(row['camera']['resolution'])
        assert row['payload_sha256'] == payload_sha
        assert row['actual_private_vertex_sha256'] == row['actual_evaluated_private_vertex_sha256'] == world_sha
        assert row['renderer_sha256'] == sha(PACK / renderer)
        assert row['original47_and_Face690_exact'] and row['entire_evaluated_original_context_exact']
        assert not row['native_saved'] and not row['head_scale_changed']
        assert 0.09999 < row['camera']['clip_start'] < 0.10001 and row['camera']['clip_end'] == 10
    actuals.extend(rows)
boards = []
for name in ['review-records.json', 'extra-review-records.json']:
    for row in read(PACK / name)['boards']:
        artifact({'path': row.get('board', row.get('path')),
                  'sha256': row.get('board_sha256', row.get('sha256'))})
        for key in ['baseline', 'baseline_E', 'baseline_D', 'candidate', 'source']:
            if row.get(key):
                artifact(row[key])
        boards.append(row)
protected = read(PACK / 'protected-input-hashes.json')
for path, digest in protected.items():
    assert sha(canonical(path)) == digest, path
native = read(PACK / 'native/export-report.json')
reopen = read(PACK / 'native/fresh-reopen.json')
native_path = artifact(native)
assert native['sha256'] == reopen['sha256'] == '7bc207b804775b9637858fed8e9faf5d831f6ae034d62da6792522fe1e9c4158'
assert native_path.stat().st_size == native['bytes'] == reopen['bytes'] == 2841748
assert reopen['raw_world_triangle_arrays_bitexact_to_NPZ'] and reopen['no_UV_weights_rig_keys_actions']
assert hashlib.sha256(data['world'].astype(np.float32).tobytes()).hexdigest() == reopen['world_f32_sha256']
assert hashlib.sha256(data['triangles'].astype(np.int32).tobytes()).hexdigest() == reopen['triangles_i32_sha256']
original = ROOT / 'asset/mia/blender/mia-refinement-v002/integrated/Mia_v0.0.2_Review_R3b.blend'
assert sha(original) == '4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'
scripts = list(PACK.glob('*.py'))
for path in scripts:
    ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
report = dict(evidence_integrity='PASS', manifest_files=len(manifest['files']),
              actual_images=len(actuals), boards=len(boards), protected_inputs=len(protected),
              python_ASTs=len(scripts), canonical_native_bytes=native['bytes'],
              subset_native_sha256=native['sha256'], original_R3b_unchanged=True,
              frozen_proof_files_rewritten=False, GPU_used=False,
              visual_review='../UPPERBODY_SUPPORT_09_REVIEW.md',
              art_scope='Bounded static upper-body shape guide; not production or whole-Mia ART.',
              full_native_source_review_gate='OPEN; actual images predate subset export and retain R3b-plus-NPZ provenance.')
out = Path(__file__).with_name('posterior09-import.json')
out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(report, indent=2))
