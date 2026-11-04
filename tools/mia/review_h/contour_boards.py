"""Reuse the frozen uniform source registration for the live contour02 trial."""
from pathlib import Path
import importlib.util
import json

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'.mia-cache/body-h/live/neck-contour02'
spec = importlib.util.spec_from_file_location('contour_common_boards', ROOT/'tools/mia/review_h/gray_boards.py')
common = importlib.util.module_from_spec(spec); spec.loader.exec_module(common)
before = json.loads((OUT/'before-v2/capture.json').read_text())
after = json.loads((OUT/'after-v2/capture.json').read_text())
rows = [{r['name']: r for r in record['frames']} for record in [before, after]]
assert before['original_pose'] == after['original_pose']
views = []
for name in ['front', 'profile', 'back', 'oblique']:
    first, second = rows[0][name], rows[1][name]
    assert common.camera(first['fixture']) == common.camera(second['fixture'])
    matrix, registration = common.registration(second, name)
    tiles = [common.label(common.source_panel(common.SOURCES[0], name), 'MAIN / original pixels'),
             common.label(common.source_panel(common.SOURCES[1], name), 'VISIBILITY / uncertain pose'),
             common.label(common.actual(first, matrix), 'D69d4 / gray body only'),
             common.label(common.actual(second, matrix), 'Contour02 / unselected trial')]
    full = Image.new('RGB', (2000, 1064))
    detail = Image.new('RGB', (2000, 540))
    for i, tile in enumerate(tiles):
        full.paste(tile, (500*i, 0))
        # 300x300 original-source coordinates ->500x500, uniform in BOTH axes.
        crop = tile.crop((100, 205, 400, 505)).resize((500, 500), Image.Resampling.LANCZOS)
        detail.paste(common.label(crop, ['MAIN', 'VISIBILITY', 'BEFORE', 'AFTER / trial'][i]), (500*i, 0))
    board = OUT/('source-'+name+'.png'); full.save(board)
    detail.save(OUT/('upper-'+name+'.png'))
    views.append(dict(id=name, reference=dict(**common.art(common.SOURCES[0]), crop_xyxy=common.PANELS[name][1]),
                      secondary_reference=dict(**common.art(common.SOURCES[1]), crop_xyxy=common.PANELS[name][1]),
                      baseline_render=common.art(first['path']), candidate_render=common.art(second['path']),
                      comparison_board=common.art(board), baseline_camera=common.camera(first['fixture']),
                      candidate_camera=common.camera(second['fixture']),
                      reference_registration=dict(uniform_scale=1., translation_xy=[250-common.PANELS[name][0], 40.], rotation_degrees=0., normalization_basis='Original pixels; crop/reposition only'),
                      baseline_registration=registration, candidate_registration=registration,
                      pose_uncertainty=dict(yaw_degrees=second['yaw'], pitch_degrees=second['pitch'], interpretation='Nominal view hypothesis; source drawing pose/camera not calibrated'),
                      observed_differences='PENDING direct root/independent visual review',
                      unresolved='M3 source likeness; posterior cap and head cut may remain. No allM1..6/FB or ART approval.',
                      material_mode='Same isolated all-gray body-only object overrides; hair/eye accessory actors omitted, not final character appearance'))
for name in ['high', 'low', 'opposite']:
    first, second = rows[0][name], rows[1][name]
    assert common.camera(first['fixture']) == common.camera(second['fixture'])
    a, b = [Image.open(r['path']).convert('RGB') for r in [first, second]]
    assert a.size == b.size
    board = Image.new('RGB', (a.width*2, a.height+40))
    board.paste(common.label(a, 'BEFORE / '+name), (0, 0))
    board.paste(common.label(b, 'AFTER / '+name), (a.width, 0))
    board.save(OUT/('before-after-'+name+'.png'))
native = common.art(before['native'])
package = dict(schema_version=1, part='body', required_views=[v['id'] for v in views],
               baseline_native=dict(**native, role='Saved C baseline STATIC WIP'),
               candidate_native=dict(**native, role='Same saved input; candidate exists only in actual live coordinates, NOT saved native'),
               candidate_saved=False, baseline_world_sha256=before['world_sha256'], candidate_world_sha256=after['world_sha256'],
               scope='Actual live trial preflight. Final maps/native/64frame review remains required.', views=views)
(OUT/'reference-review.json').write_text(json.dumps(package, indent=2)+'\n', encoding='utf8')
print('CONTOUR02_SOURCE_BOARDS_READY_UNJUDGED')
