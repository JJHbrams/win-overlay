"""Source-aspect color context for an actual bounded static pigment trial.

This is not a calibrated drawing-camera fit or a geometry/proportion approval.
Raw frames stay ignored; the established evidence validator judges integrity.
"""
from pathlib import Path
import importlib.util
import json

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'.mia-cache/face-live/v29-pigment-source01'
SOURCE = ROOT/'asset/mia/references/mia-clean-master-v22.png'
spec = importlib.util.spec_from_file_location('mia_existing_source_boards', ROOT/'tools/mia/review_h/gray_boards.py')
existing = importlib.util.module_from_spec(spec); spec.loader.exec_module(existing)
font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 16)
# Opposite oblique has no matching master pose. Show the original, unmirrored
# oblique and label that limit rather than implying invented source coverage.
CROPS = dict(front=(195, 0, 455, 345), profile=(490, 0, 710, 345),
             back=(720, 0, 990, 345), left_oblique=(985, 0, 1220, 345),
             right_oblique=(985, 0, 1220, 345))


def tile(path, crop, title):
    im = Image.open(path).convert('RGB').crop(crop)
    scale = min(400/im.width, 610/im.height)
    size = tuple(round(x*scale) for x in im.size)
    offset = ((400-size[0])//2, 40+(610-size[1])//2)
    canvas = Image.new('RGB', (400, 700), (230, 236, 240))
    canvas.paste(im.resize(size, Image.Resampling.LANCZOS), offset)
    ImageDraw.Draw(canvas).text((8, 10), title, fill=(30, 40, 50), font=font)
    return canvas, dict(uniform_scale=scale,
        translation_xy=[offset[0]-crop[0]*scale, offset[1]-crop[1]*scale],
        rotation_degrees=0., normalization_basis='Whole crop uniformly fit for color/flow context; no measured shape/proportion fit.',
        notes='No anisotropic scaling, feature warp, source reflection or inferred drawing camera.')


def main():
    before = json.loads((OUT/'before/capture.json').read_text())
    after = json.loads((OUT/'after/capture.json').read_text())
    assert before['native'] == after['native'] and before['body_sha256'] == after['body_sha256']
    assert set(before['actors']) == set(after['actors'])
    for name, actor in before['actors'].items():
        assert actor['mesh'] == after['actors'][name]['mesh']
        assert actor['matrix'] == after['actors'][name]['matrix']
    rows_b = {r['name']:r for r in before['frames']}
    rows_a = {r['name']:r for r in after['frames']}
    assert set(rows_b) == set(rows_a) and len(rows_a) == 7
    for name in rows_a:
        assert rows_b[name]['fixture'] == rows_a[name]['fixture'], name
    # The initial -90 profile was the opposite side of the drawing. Keep that
    # immutable diagnostic, use the actual +90 supplement for source context.
    for phase, rows in [('before', rows_b), ('after', rows_a)]:
        supplement = ROOT/'.mia-cache/face-live/v29-pigment-source-profile01'/phase/'capture.json'
        packet = json.loads(supplement.read_text())
        assert packet['native'] == before['native'] and packet['body_sha256'] == before['body_sha256']
        assert len(packet['frames']) == 1
        rows['profile'] = packet['frames'][0]
    assert rows_b['profile']['fixture'] == rows_a['profile']['fixture']
    views = []
    for name, crop in CROPS.items():
        b, a = rows_b[name], rows_a[name]
        for r in (b,a): assert existing.sha(r['path']) == r['sha256']
        source, sr = tile(SOURCE, crop, 'v22 / original aspect')
        bt, br = tile(b['path'], (0, 0, 800, 800), 'BEFORE / actual ORTHO')
        at, ar = tile(a['path'], (0, 0, 800, 800), 'AFTER / static pigment only')
        board = Image.new('RGB', (1200, 730), (230, 236, 240))
        for i, im in enumerate((source,bt,at)): board.paste(im, (400*i,0))
        note = 'Color/flow context only; drawing pose/light uncertain. Opposite source pose unavailable; no mirrored source.'
        ImageDraw.Draw(board).text((8, 705), note, font=font, fill=(30,40,50))
        path = OUT/('source-'+name+'.png'); assert not path.exists(); board.save(path)
        views.append(dict(id=name, reference=dict(**existing.art(SOURCE),crop_xyxy=list(crop)),
            baseline_render=existing.art(b['path']), candidate_render=existing.art(a['path']),
            comparison_board=existing.art(path), baseline_camera=existing.camera(b['fixture']),
            candidate_camera=existing.camera(a['fixture']), reference_registration=sr,
            baseline_registration=br, candidate_registration=ar,
            pose_uncertainty='Nominal 0/+90/180/-35/+35 model yaw. Master is a stylized drawing, not recovered camera. Opposite oblique source is context only, unmirrored. Profile before is the original shader on the same current mesh; extra UV7 is unused.',
            material_mode='Current EEVEE toon light; copied pigment branch on 4999 retained faces only; geometry/normals held.',
            observed_differences='PENDING actual visual readback; technical invariance is not likeness.',
            unresolved='Old front/nape extraction damage, broad rear sheets, regular S locks and final UV/normal/paint finish remain open.'))
    package = dict(schema_version=1,part='surface',required_views=list(CROPS),
        baseline_native=dict(**before['native'],role='Immutable base; actual baseline is unsaved replayed body/hair'),
        candidate_native=dict(**after['native'],role='Same immutable base, unsaved pigment delta; not saved candidate native'),
        candidate_saved=False,body_sha256=after['body_sha256'],
        scope='Bounded static pigment review only. Source-camera, moved-light, all-hair M2 and ART remain open.',views=views)
    (OUT/'reference-review.json').write_text(json.dumps(package,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(actual_pairs=7,source_boards=5,fixture_exact=True,ART=False)))


if __name__ == '__main__': main()
