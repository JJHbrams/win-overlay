"""Verify saved evidence bytes; this does not perform or imply a new ART review."""
from pathlib import Path
import ast
import hashlib
import json
import re
import numpy as np
from PIL import Image

P = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_text(encoding='utf-8-sig'))
build = read(P / 'build-report.json')
cpu = read(P / 'CPU-audit.json')
diff = read(P / 'parameter-diff.json')
assert diff['only_change'] == [{'path': '.posterior_wall.blend', 'before': .010, 'after': .014}]
assert sha(P / 'parameters.json') == build['parameters_sha256'] == diff['candidate_parameters_sha256']
payload = sha(P / 'posterior09.npz')
assert payload == build['mesh_sha256'] == cpu['mesh_sha256']
assert payload == 'd5bf574ea958923fc70fe6ade4de7e0b64ec970c3cf15156be5f135af3c9cdd2'
data = np.load(P / 'posterior09.npz')
assert data['world'].shape == (67992, 3) and data['triangles'].shape == (135980, 3)
assert np.isfinite(data['world']).all()
vh = hashlib.sha256(data['world'].tobytes()).hexdigest()
assert cpu['finite'] and cpu['connected_components'] == 1
assert not cpu['boundary_edges'] and not cpu['nonmanifold_edges']
assert not cpu['inconsistent_edge_winding'] and cpu['euler_characteristic'] == 2
assert not cpu['new_nonadjacent_intersections'] and cpu['positive_intersection_control']
assert cpu['breast_surface']['exact'] and cpu['main_lower_passage_open']
rows8 = read(P / 'actual8/render-records.json')
rows3 = read(P / 'actual-extra3/render-records.json')
assert len(rows8) == len(list((P / 'actual8').glob('*.png'))) == 8
assert len(rows3) == len(list((P / 'actual-extra3').glob('*.png'))) == 3
assert read(P / 'render-preparation.json')['render_called'] is False
extra_prep = read(P / 'actual-extra3/render-preparation.json')
assert extra_prep['render_called'] is False
for path, h in extra_prep['initial8_hashes'].items():
    assert sha(path) == h, path
for group, renderer in [(rows8, 'render_actual8.py'), (rows3, 'render_extra3.py')]:
    for r in group:
        assert sha(r['path']) == r['sha256']
        assert Image.open(r['path']).size == tuple(r['camera']['resolution'])
        assert sha(r['baseline_E_render']['path']) == r['baseline_E_render']['sha256']
        assert r['payload_sha256'] == payload
        assert r['actual_private_vertex_sha256'] == r['actual_evaluated_private_vertex_sha256'] == vh
        assert r['renderer_sha256'] == sha(P / renderer)
        assert r['native_sha256'] == '4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'
        assert r['original47_and_Face690_exact'] and r['entire_evaluated_original_context_exact']
        assert not r['native_saved'] and not r['head_scale_changed']
        assert .09999 < r['camera']['clip_start'] < .10001 and r['camera']['clip_end'] == 10
        if r['mode'] == 'gray':
            assert r['actual_material_signature']['sha256'] == '92a5c6b160f69f268b12ba4d385fed0239fce287c17d88c856ea6b090966658f'
        if group is rows3:
            assert r['initial_eight_unchanged']
boards = []
for name in ['review-records.json', 'extra-review-records.json']:
    for b in read(P / name)['boards']:
        assert sha(b.get('board', b.get('path'))) == b.get('board_sha256', b.get('sha256'))
        for key in ['baseline', 'baseline_E', 'baseline_D', 'candidate', 'source']:
            s = b.get(key)
            if s:
                assert sha(s['path']) == s['sha256']
                if 'original_size' in s:
                    assert Image.open(s['path']).size == tuple(s['original_size'])
                    x0, y0, x1, y1 = s['crop_xyxy']
                    assert abs((x1 - x0) - (y1 - y0)) < .001
        boards.append(b)
protected = read(P / 'protected-input-hashes.json')
for path, h in protected.items():
    assert sha(path) == h, path
native = read(P / 'native/export-report.json')
reopen = read(P / 'native/fresh-reopen.json')
assert sha(native['path']) == native['sha256'] == reopen['sha256']
assert native['sha256'] == '7bc207b804775b9637858fed8e9faf5d831f6ae034d62da6792522fe1e9c4158'
assert Path(native['path']).stat().st_size == native['bytes'] == reopen['bytes'] == 2841748
assert reopen['raw_world_triangle_arrays_bitexact_to_NPZ'] and reopen['origin0_matrix_identity']
assert reopen['no_UV_weights_rig_keys_actions'] and reopen['actual_gray_output_constants_verified']
assert reopen['objects'] == 14 and reopen['cameras'] == 10 and reopen['lights'] == 3
assert len(list(P.rglob('*.blend'))) == 1 and not list(P.rglob('*.blend1'))
for name, marker in [('actual8.log', 'POSTERIOR09_ACTUAL8_DONE_GPU_RELEASE'),
                     ('actual-extra3/render.log', 'POSTERIOR09_EXTRA3_DONE_GPU_RELEASE'),
                     ('native/fresh-reopen.log', 'POSTERIOR09_STATIC_FRESH_REOPEN_PASS')]:
    log = (P / name).read_text(encoding='utf-8-sig')
    assert marker in log and not re.search(r'traceback|compile error|shader.*failed|error:', log, re.I)
for script in P.glob('*.py'):
    ast.parse(script.read_text(encoding='utf-8'), filename=str(script))
report = dict(status='PASS saved evidence integrity; root/fresh reviewer bounded static-guide acceptance',
              actual_frames=11, initial_actual_frames=8, additional_actual_frames=3,
              geometry_variants=1, boards=len(boards), protected_input_files=len(protected),
              candidate_sha256=payload, native_sha256=native['sha256'], native_bytes=native['bytes'],
              original47_Face690_entire_context_exact=True, actual_vertex_hashes_match=True,
              initial_eight_bytes_held=True, native_fresh_reopen_exact=True, GPU_used_by_check=False,
              scope='Working static upper-body shape guide only; coupled anterior arch also changes.',
              tradeoffs='24.460mL increase; broadback1.441/lat1.591/cap1.018/designneck0.217mm bounds; main9.32353mm passage open; local roof slices close.',
              unverified='Complete internal walls/anatomy ART, temporary context seams, production UV/rig/weights/animation/fullbody integration.')
(P / 'saved-evidence-check.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
files = [dict(path=f.relative_to(P).as_posix(), bytes=f.stat().st_size, sha256=sha(f))
         for f in sorted(P.rglob('*')) if f.is_file() and '__pycache__' not in f.parts and f.name != 'manifest.json']
(P / 'manifest.json').write_text(json.dumps(dict(scope='posterior-union09 files only', files=files), indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(report, indent=2))
