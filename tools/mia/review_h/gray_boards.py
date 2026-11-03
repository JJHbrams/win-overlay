"""Uniformly register actual E/H gray renders to original-aspect source panels.

Estimated front/back camera poses are explicitly separate from nominal views.
This does not infer a calibrated camera from a drawing or grant art acceptance.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'.mia-cache/body-h/gray'
MIA = ROOT/'asset/mia'
MPP_SOURCE = .001845870535714286
ZERO_SOURCE = 971.9137795513633
OLD_TARGET = np.array([0., -.018, .86])
SOURCES = [MIA/'references/received/mia-body-v06-confirmed-20261102.png',
           MIA/'references/body-foundation/v06/mia-body-visibility-guide-v06.png']
PANELS = dict(front=(239, [0, 0, 440, 1024]),
              profile=(568, [440, 0, 750, 1024]),
              back=(935, [750, 0, 1120, 1024]),
              oblique=(1317, [1120, 0, 1536, 1024]))


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def art(path): return dict(path=str(Path(path).resolve()), sha256=sha(path))


def camera(f):
    return dict(projection=f['projection'], matrix=f['camera_matrix'],
                frame=f['frame'], active_shape_keys=f['active_shape_keys'],
                lighting=f['lights'], world=f['world'],
                color_management=f['color_management'], resolution=f['resolution'],
                pixel_aspect=f['pixel_aspect'], lens_shift=f['shift'],
                ortho_scale=f['ortho_scale'], lens=f['lens'],
                clip_start=f['clip'][0], clip_end=f['clip'][1],
                pose_sha256=f['pose_sha256'])


def registration(row, panel):
    f = row['fixture']; w, h = f['resolution']
    matrix = np.array(f['camera_matrix']); right, up = matrix[:3, 0], matrix[:3, 1]
    displacement = np.array(f['target_world'])-OLD_TARGET
    s = f['ortho_scale']/max(w, h)/MPP_SOURCE
    axis = PANELS[panel][0]
    m = np.array([[s, 0., axis+displacement@right/MPP_SOURCE-s*w/2],
                  [0., s, ZERO_SOURCE-(OLD_TARGET[2]+displacement@up)/MPP_SOURCE-s*h/2],
                  [0., 0., 1.]])
    m[0, 2] += 250-axis
    return m, dict(uniform_scale=s, translation_xy=[float(m[0, 2]), float(m[1, 2]+40)],
                   rotation_degrees=0.,
                   normalization_basis='Frozen common whole-height SRT; total height is normalized, not verified. Actual matching ORTHO basis transports camera target only.',
                   notes='Scalar SRT only. Profile horizontal568 remains provisional; front/back fitted shared pose is explicitly recorded as an estimate, not an exact drawing camera.')


def label(im, title):
    out = Image.new('RGB', (im.width, im.height+40), (230, 236, 240)); out.paste(im, (0, 40))
    ImageDraw.Draw(out).text((10, 11), title, fill=(30, 40, 50), font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 17))
    return out


def source_panel(path, panel):
    axis, crop = PANELS[panel]
    out = Image.new('RGB', (500, 1024), (225, 234, 240))
    out.paste(Image.open(path).convert('RGB').crop(crop), (round(250-axis+crop[0]), 0))
    return out


def actual(row, matrix):
    assert sha(row['path']) == row['sha256']
    return Image.open(row['path']).convert('RGB').transform(
        (500, 1024), Image.Transform.AFFINE, tuple(np.linalg.inv(matrix)[:2].ravel()),
        Image.Resampling.BICUBIC, fillcolor=(35, 35, 35))


def main():
    global OUT
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', type=Path, default=OUT)
    args = parser.parse_args()
    OUT = args.directory.resolve()
    assert (ROOT/'.mia-cache/body-h').resolve() in OUT.parents
    capture = json.loads((OUT/'capture.json').read_text())
    rows = {(r['state'], r['name']): r for r in capture['frames']}
    views = []
    for name in ['front', 'profile', 'back', 'oblique']:
        actual_name = name+'_fit' if name in ('front', 'back') else name
        before, after = rows['E', actual_name], rows['H', actual_name]
        assert camera(before['fixture']) == camera(after['fixture'])
        matrix, reg = registration(after, name)
        tiles = [label(source_panel(SOURCES[0], name), 'MAIN / original aspect'),
                 label(source_panel(SOURCES[1], name), 'VISIBILITY guide / uncertain pose'),
                 label(actual(before, matrix), 'E / hair OFF / gray body'),
                 label(actual(after, matrix), 'H / hair OFF / gray body')]
        board = Image.new('RGB', (2000, 1064))
        for j, tile in enumerate(tiles): board.paste(tile, (j*500, 0))
        path = OUT/('source-'+name+'.png'); board.save(path)
        # Same original-pixel crop in all columns, never a feature-normalized face/body crop.
        crops = [tile.crop((100, 205, 400, 455)).resize((600, 500), Image.Resampling.LANCZOS) for tile in tiles]
        detail = Image.new('RGB', (2400, 540))
        for j, (crop, title) in enumerate(zip(crops, ['MAIN', 'VISIBILITY', 'E gray', 'H gray'])):
            detail.paste(label(crop, title), (j*600, 0))
        detail.save(OUT/('upper-'+name+'.png'))
        views.append(dict(id=name, reference=dict(**art(SOURCES[0]), crop_xyxy=PANELS[name][1]),
                          secondary_reference=dict(**art(SOURCES[1]), crop_xyxy=PANELS[name][1]),
                          baseline_render=art(before['path']), candidate_render=art(after['path']),
                          comparison_board=art(path), baseline_camera=camera(before['fixture']),
                          candidate_camera=camera(after['fixture']),
                          reference_registration=dict(uniform_scale=1., translation_xy=[250-PANELS[name][0], 40.], rotation_degrees=0., normalization_basis='Original source pixels and aspect; panel crop/reposition only.'),
                          baseline_registration=reg, candidate_registration=reg,
                          pose_uncertainty=dict(yaw_degrees=after['yaw'], pitch_degrees=after['pitch'], interpretation='Front/back shared fitted estimate; profile/oblique nominal90/30. Main and visibility guide have drawing/pose differences.'),
                          observed_differences='PENDING actual image review; no automated artistic judgment.',
                          unresolved='Cervical shape, shoulder roof/cap/axilla and existing overall body likeness require independent actual review. Hair occludes main reference neck. Head scale unapplied.',
                          material_mode='BODY neutral gray; preserved original R3b head/actors. Unsaved component preflight, not final saved review.'))
    native = rows['E', 'front']['native']
    package = dict(schema_version=1, part='body', required_views=list(PANELS),
                   baseline_native=dict(**native, role='Immutable R3b scene used for unsaved E component'),
                   candidate_native=dict(**native, role='Same immutable scene used for unsaved H component; NOT a saved H native'),
                   baseline_payload=rows['E', 'front']['payload'], candidate_payload=rows['H', 'front']['payload'],
                   candidate_saved=False, scope='Unsaved gray preflight only; FB native/orbit outcomes remain unverified.', views=views)
    (OUT/'reference-review.json').write_text(json.dumps(package, indent=2)+'\n', encoding='utf8')
    print('H_GRAY_SOURCE_BOARDS_READY_NOT_ART', flush=True)


if __name__ == '__main__': main()
