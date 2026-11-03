"""Compose only verified actual renders; never synthesize or warp a body view.

The input selection explicitly identifies runtime records. The frozen reference
registration is transported through the actual orthographic camera, using one
uniform image SRT. This script does not fit any character landmarks.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import math
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

P = Path(__file__).resolve().parent
BLENDER_ROOT = P.parents[2]
SHA = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def artifact(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': SHA(path)}


def checked(row):
    path = Path(row['path'])
    assert path.is_file() and SHA(path) == row['sha256'], path
    return Image.open(path).convert('RGB')


def font(size):
    return ImageFont.truetype('C:/Windows/Fonts/arial.ttf', size)


def label(image, title):
    out = Image.new('RGB', (image.width, image.height + 40), (230, 236, 240))
    out.paste(image, (0, 40))
    ImageDraw.Draw(out).text((12, 10), title, fill=(30, 40, 50), font=font(19))
    return out


def camera_record(row):
    c = row['camera']
    keys = ['projection', 'matrix', 'frame', 'active_shape_keys', 'lighting',
            'color_management', 'resolution', 'pixel_aspect', 'lens_shift',
            'ortho_scale', 'clip_start', 'clip_end']
    if 'world' in c:
        keys.append('world')
    return {k: c[k] for k in keys}


def registration(current, old):
    """New actual pixels -> old actual camera pixels -> frozen source pixels."""
    c, oc = current, old['camera']
    assert c['projection'] == oc['projection'] == 'ORTHO'
    assert c['pixel_aspect'] == oc['pixel_aspect'] == [1, 1]
    n, o = np.asarray(c['matrix'], float), np.asarray(oc['matrix'], float)
    # No new yaw/pitch fitting: this must be the same physical orientation.
    assert np.max(abs(n[:3, :3] - o[:3, :3])) < 2e-6
    w, h = c['resolution']
    ow, oh = oc['resolution']
    mpp, ompp = c['ortho_scale'] / max(w, h), oc['ortho_scale'] / max(ow, oh)
    s = mpp / ompp
    # Depth displacement cancels under matching ORTHO orientations.
    q = n[:3, 3]
    center = np.array([ow / 2 + np.dot(q - o[:3, 3], o[:3, 0]) / ompp,
                       oh / 2 - np.dot(q - o[:3, 3], o[:3, 1]) / ompp])
    new_to_old = np.array([[s, 0., center[0] - s * w / 2],
                           [0., s, center[1] - s * h / 2], [0., 0., 1.]])
    old_source = old['registration']
    source_to_old = np.asarray(old_source['source_to_render'], float)
    panel_shift = np.eye(3)
    panel_shift[0, 2] = 250 - old_source['source_center_x']
    matrix = panel_shift @ np.linalg.inv(source_to_old) @ new_to_old
    assert abs(matrix[0, 0] - matrix[1, 1]) < 1e-12
    assert abs(matrix[0, 1]) + abs(matrix[1, 0]) < 1e-12
    rec = dict(uniform_scale=float(matrix[0, 0]),
               translation_xy=[float(matrix[0, 2]), float(matrix[1, 2] + 40)],
               rotation_degrees=0.,
               normalization_basis='Frozen common whole-height source SRT transported by actual ORTHO mpp/camera center. Total height is normalization, not a tested proportion.',
               notes='No per-view anatomical refit, feature stretching, perspective reconstruction or anisotropic resize.')
    return matrix, rec


def panel(image, matrix):
    inverse = np.linalg.inv(matrix)
    return image.transform((500, 1024), Image.Transform.AFFINE,
                           tuple(inverse[:2].ravel()), Image.Resampling.BICUBIC,
                           fillcolor=(35, 35, 35))


def make_orbits(selection):
    states = ('SkinOnly', 'Underwear')
    rows = selection['orbit']
    assert all(len(rows[s]) == 32 for s in states)
    frames = {s: [] for s in states}
    paired = []
    for i in range(32):
        a, b = (rows[s][i] for s in states)
        assert abs(a['yaw'] - i * 11.25) < 1e-6 and a['yaw'] == b['yaw']
        assert camera_record(a) == camera_record(b), i
        for s, row in zip(states, (a, b)):
            assert row['native_sha256'] == selection['candidate_native']['sha256']
            for key in ('world_sha256', 'review_uv_sha256'):
                assert row[key] == selection[key], (s, i, key)
            frames[s].append(label(checked(row), f'{s} / {row["yaw"]:06.2f} deg'))
        f = Image.new('RGB', (1280, 940))
        f.paste(frames[states[0]][-1], (0, 0))
        f.paste(frames[states[1]][-1], (640, 0))
        paired.append(f)
    thumb = Image.new('RGB', (2560, 3760))
    for i, f in enumerate(paired):
        thumb.paste(f.resize((640, 470), Image.Resampling.LANCZOS), ((i % 4) * 640, (i // 4) * 470))
    palette = thumb.quantize(colors=256)
    durations = [120, 130] * 16
    outputs = {}
    for name, sequence in [('Mia-SkinOnly', frames['SkinOnly']), ('Mia-Underwear', frames['Underwear']), ('Mia-Body-Turntable', paired)]:
        path = P / (name + '.gif')
        q = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in sequence]
        q[0].save(path, save_all=True, append_images=q[1:], duration=durations,
                  loop=0, disposal=2, optimize=False)
        with Image.open(path) as gif:
            assert gif.n_frames == 32
            total = 0
            for i in range(gif.n_frames):
                gif.seek(i)
                total += gif.info['duration']
            assert total == 4000
        outputs[name] = dict(**artifact(path), frames=32, duration_ms=4000,
                             provenance='32 actual angles per material; no intermediate-image generation.')
    contact = Image.new('RGB', (2560, 940))
    for j, i in enumerate((0, 8, 16, 24)):
        contact.paste(paired[i].resize((640, 470), Image.Resampling.LANCZOS), (j * 640, 0))
    contact = contact.crop((0, 0, 2560, 470))
    contact.save(P / 'material-orbit-contact.png')
    outputs['contact'] = artifact(P / 'material-orbit-contact.png')
    return outputs


def make_source_package(selection):
    context_path = Path(selection['surface_context'])
    context = json.loads(context_path.read_text(encoding='utf-8'))['source_context']
    source = Path(selection['reference'])
    source_image = Image.open(source).convert('RGB')
    views = []
    for name in ('front', 'profile', 'back', 'oblique'):
        rows = selection['source_views'][name]
        before, after = rows['baseline'], rows['candidate']
        bc, ac = camera_record(before), camera_record(after)
        assert bc == ac, name
        matrix, reg = registration(ac, context['views'][name])
        old = context['views'][name]['registration']
        crop = old['source_crop_xyxy']
        ref_panel = Image.new('RGB', (500, 1024), (225, 234, 240))
        ref_panel.paste(source_image.crop(crop), (round(250 - old['source_center_x'] + crop[0]), crop[1]))
        tiles = [label(ref_panel, 'SOURCE / original aspect'),
                 label(panel(checked(before), matrix), 'R3b baseline / hair OFF'),
                 label(panel(checked(after), matrix), 'Review12 Underwear / hair OFF')]
        board = Image.new('RGB', (1500, 1064))
        for j, tile in enumerate(tiles):
            board.paste(tile, (500 * j, 0))
        path = P / ('source-' + name + '.png')
        board.save(path)
        refreg = dict(uniform_scale=1., translation_xy=[250 - old['source_center_x'], 40.], rotation_degrees=0.,
                      normalization_basis='Original source pixels at unchanged aspect; panel translation only. Source whole-height anchor remains the frozen normalization.')
        baseline_reg = dict(reg, translation_xy=[reg['translation_xy'][0] + 500, reg['translation_xy'][1]])
        candidate_reg = dict(reg, translation_xy=[reg['translation_xy'][0] + 1000, reg['translation_xy'][1]])
        views.append(dict(id=name, reference=dict(**artifact(source), crop_xyxy=crop),
                          baseline_render=artifact(before['path']), candidate_render=artifact(after['path']),
                          comparison_board=artifact(path), baseline_camera=bc, candidate_camera=ac,
                          reference_registration=refreg, baseline_registration=baseline_reg, candidate_registration=candidate_reg,
                          pose_uncertainty=selection['pose_uncertainty'],
                          observed_differences=rows['observations'], unresolved=rows['unresolved'],
                          material_mode='Actual EEVEE target toon; source has underwear/hair, both model body-review renders hide hair. Original R3b surface versus newly fitted Underwear UV maps.'))
    package = dict(schema_version=1, part='body', required_views=['front', 'profile', 'back', 'oblique'],
                   baseline_native=selection['baseline_native'], candidate_native=selection['candidate_native'], views=views,
                   geometry_approval='Not granted by this presentation or evidence validator.')
    path = P / 'reference-review.json'
    dump(path, package)
    validator = BLENDER_ROOT / 'mia-reference-finish-v22/validate_reference_review.py'
    spec = importlib.util.spec_from_file_location('review_validator', validator)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.validate(path)
    dump(P / 'reference-review-validation.json', report)
    assert report['evidence_valid'], report['errors']
    return artifact(path)


def main():
    selection = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    for key in ('baseline_native', 'candidate_native'):
        assert SHA(selection[key]['path']) == selection[key]['sha256']
    outputs = make_orbits(selection)
    outputs['source_review'] = make_source_package(selection)
    dump(P / 'presentation-manifest.json', dict(selection=artifact(sys.argv[1]), outputs=outputs))
    print(json.dumps(outputs, ensure_ascii=False))


if __name__ == '__main__':
    main()
