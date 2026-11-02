"""Validate frozen history and source reproduction evidence; never an ART gate."""
from pathlib import Path
import ast
import hashlib
import json

import numpy as np
from PIL import Image

P = Path(__file__).resolve().parent
W = Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    cfg = json.loads((P / 'CHECKPOINT.json').read_text())
    listed = (P / 'CHECKPOINT_FILES.txt').read_text().splitlines()
    files = {r['path']: r for r in cfg['files']}
    assert set(listed) == set(files) | {'CHECKPOINT.json'}
    assert cfg['new_fill_selected'] is False and cfg['ART'] is False
    for rel, row in files.items():
        path = P / rel
        assert path.is_file() and path.stat().st_size == row['bytes'], rel
        assert sha(path) == row['sha256'], rel
        assert path.suffix not in ['.blend', '.blend1', '.log', '.pyc'], rel
        assert '__pycache__' not in path.parts and rel != 'current-geometry.npz'
        if path.suffix == '.py':
            ast.parse(path.read_text(encoding='utf-8'), filename=rel)
        elif path.suffix == '.json':
            json.loads(path.read_text(encoding='utf-8'))
    for ref in cfg['protected_external_sources']:
        assert sha(W / ref['path']) == ref['sha256'], ref['path']
    for report, payload in [('manifest.json', 'locks.npz'),
                            ('detail-prototypes.json', 'detail-prototypes.npz'),
                            ('detailed-fill.json', 'detailed-fill.npz'),
                            ('buried-core.json', 'buried-core.npz'),
                            ('identity-assembly.json', 'identity-assembly.npz')]:
        assert json.loads((P / report).read_text())['payload_sha256'] == sha(P / payload)
    own = np.load(P / 'identity-assembly.npz')
    ids = own['source_faces']
    assert len(ids) == 15922 and len(np.unique(ids)) == len(ids)
    assert own['source_triangles'].shape == (15922, 3)
    assert np.array_equal(np.unique(own['source_triangles']), own['source_vertices'])
    assert len(own['source_raw_faces']) == 15922
    guard = json.loads((P / 'checkpoint-source-ownership-guard.json').read_text())
    assert guard['existing_owners_protected'] == 618
    assert guard['outside_owner_changes'] == []
    assert guard['scene_before_after_restore_exact']
    assert guard['explicit_Main_data_before_after_restore_exact']
    assert guard['original_raw_source_ids_and_triangles_exact']
    assert guard['prior_U_mask_disjoint'] and guard['temporary_changed_faces'] == len(ids)
    assert not any(guard[k] for k in ['rendered', 'native_saved', 'live_mutated', 'ART', 'new_fill_selected'])
    for batch in cfg['render_batch_precheckpoint_scans']:
        assert batch['completion_observed'] and not batch['shader_or_runtime_error_observed']
    count = 0
    for folder in ['actual-first4', 'actual-detailed-B', 'actual-identity']:
        records = json.loads((P / folder / 'records.json').read_text())
        for rec in records:
            path = P / folder / Path(rec['path']).name
            assert sha(path) == rec['image_sha256']
            assert rec['native_saved'] is False
            assert rec['base_native_sha256'] == cfg['base_native_sha256']
            with Image.open(path) as im:
                if 'resolution' in rec:
                    assert list(im.size) == rec['resolution']
                elif 'resolution' in rec['camera']:
                    assert list(im.size) == rec['camera']['resolution']
            assert rec['camera']['clip'] == [0.10000000149011612, 10.0]
            count += 1
    assert count == 8
    masks = np.load(P / 'identity-owned-firsthit.npz')
    proof = json.loads((P / 'identity-pixel-proof.json').read_text())
    for rec, summary in zip(json.loads((P / 'actual-identity/records.json').read_text()), proof['views']):
        # Baseline front is a prior committed U-cleanup actual; back is in this package.
        baseline = Path(rec['baseline_render'])
        candidate = P / 'actual-identity' / Path(rec['path']).name
        assert sha(baseline) == rec['baseline_sha256']
        a = np.array(Image.open(baseline).convert('RGBA'), dtype=np.int16)
        b = np.array(Image.open(candidate).convert('RGBA'), dtype=np.int16)
        assert a.shape == b.shape
        delta = np.abs(a - b)
        mask = masks[rec['view']]
        assert int(mask.sum()) == summary['owned_firsthit_pixels']
        assert int(delta[mask].max()) == summary['owned_max_channel_difference']
        assert int(delta.max()) == summary['whole_frame_max_channel_difference']
        assert int((delta.max(2)[mask] > 2).sum()) == summary['owned_pixels_over2']
        assert int((delta.max(2) > 8).sum()) == summary['whole_frame_pixels_over8'] == 0
    return dict(status='CHECKPOINT_HISTORY_VALIDATED_NOT_ART_ACCEPTANCE',
                files=len(listed), bytes=sum(r['bytes'] for r in files.values()),
                Python_AST_validated=sum(r.endswith('.py') for r in files),
                actual_images_verified=count, identity_pixel_statistics_recomputed=True,
                CPU_original_ownership_and_rollback_guard_verified=True,
                external_source_hashes_verified=len(cfg['protected_external_sources']),
                rendered=False, native_saved=False, new_fill_selected=False, ART=False)


if __name__ == '__main__':
    print(json.dumps(main(), indent=2))
