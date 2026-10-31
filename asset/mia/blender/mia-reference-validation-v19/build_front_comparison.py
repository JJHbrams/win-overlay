"""Measurement figure from unchanged art and actual renders; no image generation or mesh edits."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

p = argparse.ArgumentParser()
for name in ['model-landmarks', 'ref-landmarks', 'model-bare', 'model-hair', 'reference', 'output-dir']:
    p.add_argument('--' + name, required=True)
a = p.parse_args()
out = Path(a.output_dir).resolve()
out.mkdir(parents=True, exist_ok=True)
data = json.loads(Path(a.model_landmarks).read_text(encoding='utf-8'))
ref_data = json.loads(Path(a.ref_landmarks).read_text(encoding='utf-8'))
lm = data['landmarks']
pupils = sorted([x['points'][0]['pixel_top_left'] for x in lm['iris_pupil_uv_centers']
                 if x['kind'] == 'pupil_shader_center'], key=lambda q: q[0])
model = np.array(pupils + [lm['mouth_geometric_boundary']['center_mean']['pixel_top_left'],
                           lm['chin_actual_mesh_min_z']['pixel_top_left']])
ref = np.array([ref_data['points'][k]['xy'] for k in [
    'left_image_visible_pupil_center', 'right_image_visible_pupil_center',
    'mouth_seam_center', 'chin_outline_tip']], dtype=float)

def registration(source, target):
    sv, tv = source[1] - source[0], target[1] - target[0]
    angle = np.arctan2(tv[1], tv[0]) - np.arctan2(sv[1], sv[0])
    scale = np.linalg.norm(tv) / np.linalg.norm(sv)
    rotation = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
    matrix = np.eye(3)
    matrix[:2, :2] = scale * rotation
    matrix[:2, 2] = target[0] - scale * rotation @ source[0]
    return matrix, scale, float(np.degrees(angle))

matrix, scale, angle = registration(model[:2], ref[:2])
registered = (matrix[:2, :2] @ model.T).T + matrix[:2, 2]
mid_model, mid_ref = model[:2].mean(axis=0), ref[:2].mean(axis=0)
sensitivity, sens_scale, sens_angle = registration(np.array([mid_model, model[3]]), np.array([mid_ref, ref[3]]))
images = {'reference': np.array(Image.open(a.reference).convert('RGBA')),
          'bare': np.array(Image.open(a.model_bare).convert('RGBA')),
          'hair': np.array(Image.open(a.model_hair).convert('RGBA'))}

font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 20)
small = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 16)
title_font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 25)
viewport = np.array([[2., 0., -700.], [0., 2., -480.], [0., 0., 1.]])
panel_size = (680, 500)

def layer_image(name, mat):
    inverse = np.linalg.inv(viewport @ mat)
    return Image.fromarray(images[name]).transform(panel_size, Image.Transform.AFFINE,
        tuple(inverse[:2, :].ravel()), resample=Image.Resampling.BICUBIC)

def panel(mode, mat=matrix, contours=False):
    canvas = Image.new('RGBA', panel_size, '#d8dfe2')
    if mode == 'reference' or mode.startswith('overlay'):
        canvas.alpha_composite(layer_image('reference', np.eye(3)))
    if mode != 'reference':
        layer = layer_image('hair' if 'hair' in mode else 'bare', mat)
        if mode.startswith('overlay'):
            layer.putalpha(layer.getchannel('A').point(lambda x: round(x*.5)))
        canvas.alpha_composite(layer)
    draw = ImageDraw.Draw(canvas)
    def xy(q):
        return tuple((viewport[:2, :2] @ q + viewport[:2, 2]).tolist())
    for x in range(350, 691, 50):
        u = int((x-350)*2)
        draw.line((u, 0, u, 500), fill=(150, 160, 170, 85), width=1)
        draw.text((u+3, 477), str(x), font=small, fill='#e5e9ed')
    if mode == 'reference' or mode.startswith('overlay'):
        for q in ref:
            x, y = xy(q)
            draw.ellipse((x-5, y-5, x+5, y+5), outline='#ffca35', width=2)
    if mode != 'reference':
        q_model = (mat[:2, :2] @ model.T).T + mat[:2, 2]
        for q in q_model:
            x, y = xy(q)
            draw.line((x-6, y, x+6, y), fill='#00cce2', width=2)
            draw.line((x, y-6, x, y+6), fill='#00cce2', width=2)
        if mode.startswith('overlay'):
            for q, target in zip(q_model[2:], ref[2:]):
                draw.line((xy(q), xy(target)), fill='#ff704b', width=2)
        if contours:
            for contour in lm['geometric_eyelid_contours']:
                points = np.array([x['pixel_top_left'] for x in contour['full_ordered_boundary']])
                points = (mat[:2, :2] @ points.T).T + mat[:2, 2]
                draw.line([xy(q) for q in points], fill='#00cce2', width=1)
    return canvas.convert('RGB')

figure = Image.new('RGB', (2100, 1230), '#f4f6f8')
draw = ImageDraw.Draw(figure)
draw.text((20, 15), f'FRONT REGISTRATION | visible pupils | uniform scale {scale:.4f}, roll {angle:.2f} degrees', font=title_font, fill='#182d39')
draw.text((20, 51), 'Gold: reference estimates +/-2px. Cyan: actual projected model. Rotation, uniform scale and translation only.', font=font, fill='#344957')
titles = ['Original portrait', 'Actual model / hair hidden', '50% overlay / geometric landmarks',
          'Original portrait', 'Actual model / hair visible', '50% overlay / same transform']
modes = ['reference', 'bare', 'overlay_bare', 'reference', 'hair', 'overlay_hair']
for i, (title, mode) in enumerate(zip(titles, modes)):
    x, y = 20+(i%3)*695, 96+(i//3)*550
    draw.text((x, y), title, font=font, fill='#182d39')
    figure.paste(panel(mode, contours=i in [1, 2]), (x, y+31))
draw.text((20, 1200), 'Reference pixel coordinates. This front diagnostic does not validate camera pose, other views, albedo or lighting.', font=small, fill='#344957')
figure.save(out / 'front-registered-comparison.png')

figure = Image.new('RGB', (1410, 620), '#f4f6f8')
draw = ImageDraw.Draw(figure)
draw.text((20, 15), 'Anchor sensitivity: changing anchors changes the residual, not the model.', font=title_font, fill='#182d39')
for i, (mat, title) in enumerate([(matrix, 'Two visible pupils'), (sensitivity, 'Eye midpoint + chin (normalized, not validated)')]):
    draw.text((20+695*i, 57), title, font=font, fill='#182d39')
    figure.paste(panel('overlay_bare', mat), (20+695*i, 91))
figure.save(out / 'front-anchor-sensitivity.png')

def ratios(points):
    eye_mid = points[:2].mean(axis=0)
    pupil_distance = float(np.linalg.norm(points[1] - points[0]))
    return {'mouth_chin_over_pupil_distance': float(np.linalg.norm(points[3]-points[2])/pupil_distance),
            'eye_mid_chin_over_pupil_distance': float(np.linalg.norm(points[3]-eye_mid)/pupil_distance)}

report = {'model_native_sha256': data['source_sha_before'],
          'source_files_sha256': {str(Path(x).resolve()): hashlib.sha256(Path(x).read_bytes()).hexdigest()
                                 for x in [a.reference, a.model_bare, a.model_hair, a.model_landmarks, a.ref_landmarks]},
          'primary_registration': {'anchors': 'visible pupil shader centers to manual visible pupils',
                                   'matrix_model_pixels_to_reference_pixels': matrix.tolist(), 'uniform_scale': scale, 'rotation_degrees': angle},
          'sensitivity_registration': {'anchors': 'eye midpoint and chin; these distances are normalized, not validated',
                                        'matrix': sensitivity.tolist(), 'uniform_scale': sens_scale, 'rotation_degrees': sens_angle},
          'reference_points_approximate': ref.tolist(), 'model_projected_points': model.tolist(),
          'registered_model_points': registered.tolist(), 'residual_model_minus_reference_pixels': (registered-ref).tolist(),
          'reference_ratios_approximate': ratios(ref), 'model_ratios': ratios(model),
          'limits': ['Reference ±2px manual uncertainty; head pose/asymmetry cannot be resolved by two points.',
                     'Uniform S/R/T only. No anisotropic resizing or local feature warping.',
                     'Two-pupil alignment fixes pupil distance; it does not test that distance itself.',
                     'Hair hides reference skin contour. No full-face width inferred from hair outline.',
                     'This is one front diagnostic; profile/back/oblique comparisons are required independently.',
                     'Current beauty uses synthetic emission shading. This plot is not albedo or lighting validation.']}
(out / 'front-registration.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps({k: report[k] for k in ['primary_registration', 'reference_ratios_approximate', 'model_ratios']}, indent=2))
