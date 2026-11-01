"""Source|baseline|candidate boards with frozen scalar registration, plus orbit preview."""
import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

P = Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
ap.add_argument('--native', required=True)
a = ap.parse_args()
native = Path(a.native).resolve()
oldpath = P.parent / 'mia-orbit-thorax-review-v28/reviews/G2L-face/reference-review.json'
old = json.loads(oldpath.read_text())
out = P / 'final-review'
dest = out / 'source-boards'
dest.mkdir(parents=True, exist_ok=True)
font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 21)
records = {r['id']: r for r in json.loads((out / 'source/render-records.json').read_text())}
baseline_records = {r['id']: r for r in json.loads((out / 'source-baseline/render-records.json').read_text())}
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()

def artifact(path):
    path = Path(path).resolve()
    return {'path': Path(os.path.relpath(path, dest)).as_posix(), 'sha256': sha(path)}

def transform(im, reg):
    scale = reg['uniform_scale']
    angle = math.radians(reg['rotation_degrees'])
    c, s = math.cos(angle), math.sin(angle)
    x, y = reg['translation_xy']
    return im.convert('RGBA').transform((640, 640), Image.Transform.AFFINE,
        (c/scale, s/scale, -(c*x+s*y)/scale, -s/scale, c/scale, (s*x-c*y)/scale),
        Image.Resampling.BICUBIC, fillcolor=(237, 242, 246, 255))

rows = []
for row in old['views']:
    name = row['id']
    ref = (oldpath.parent / row['reference']['path']).resolve()
    baseline = Path(baseline_records[name + '-hairOFF']['path'])
    cand = Path(records[name + '-hairOFF']['path'])
    assert records[name + '-hairOFF']['native_sha256'] == sha(native)
    baseline_camera = baseline_records[name + '-hairOFF']['camera']
    actual_camera = records[name + '-hairOFF']['camera']
    assert baseline_camera == actual_camera, 'Actual camera/light/pose mismatch: ' + name
    src = Image.open(ref).convert('RGBA')
    crop = row['reference']['crop_xyxy']
    cropped = src.crop(crop)
    cropped.save(dest / (name + '-source-crop.png'))
    canvas = Image.new('RGBA', src.size, (237, 242, 246, 255))
    canvas.paste(cropped, crop[:2])
    reg = copy.deepcopy(row['candidate_registration'])
    tiles = [transform(canvas, row['reference_registration']),
             transform(Image.open(baseline), reg), transform(Image.open(cand), reg),
             transform(Image.open(records[name + '-hairON']['path']), reg)]
    board = Image.new('RGB', (2560, 740), (237, 242, 246))
    draw = ImageDraw.Draw(board)
    for i, (tile, label) in enumerate(zip(tiles, ['SOURCE / original aspect', 'BASELINE G2L / hair OFF',
                                                'v29 / hair OFF', 'v29 / hair ON'])):
        board.paste(tile.convert('RGB'), (640*i, 50))
        draw.text((640*i+12, 12), label, font=font, fill=(24, 38, 49))
    draw.text((12, 702), name + ' | unchanged source aspect; frozen uniform SRT; matching actual camera/light/pose', font=font, fill=(24, 38, 49))
    bp = dest / (name + '-source-baseline-final.png')
    board.save(bp)
    rows.append({'id': name, 'reference': dict(artifact(ref), crop_xyxy=crop,
                    crop_artifact=artifact(dest / (name + '-source-crop.png'))),
        'baseline_render': artifact(baseline), 'candidate_render': artifact(cand),
        'comparison_board': artifact(bp), 'baseline_camera': baseline_camera, 'candidate_camera': actual_camera,
        'reference_registration': row['reference_registration'], 'baseline_registration': reg,
        'candidate_registration': copy.deepcopy(reg), 'pose_uncertainty': row['pose_uncertainty'],
        'observed_differences': 'Actual modeled medial union/recess, independent upper/lower lash volume and active face-surface maps. Final visual reviewer observations are recorded separately.',
        'unresolved': ['Full-character ART remains unapproved; hair/body/garments retain documented limits.',
                       'Source gaze, expression and occluded anatomical positions remain uncertain.',
                       'Eye-to-chin normalization excludes that span from independent proportion claims.'],
        'material_mode': 'Actual final production material; hair visibility labeled. Native matte/color-only/light probes are separate evidence.'})
pkg = {'schema_version': 1, 'part': 'surface', 'baseline_native': artifact((oldpath.parent / old['candidate_native']['path']).resolve()),
       'candidate_native': artifact(native), 'required_views': ['front', 'profile', 'left_oblique', 'right_oblique'],
       'views': rows, 'status': 'Evidence integrity package; visual acceptance requires the independent audit.'}
(dest / 'reference-review.json').write_text(json.dumps(pkg, indent=2), encoding='utf-8')
orbit_dir = out / 'orbit'
if (orbit_dir / 'render-records.json').exists():
    orbit = json.loads((orbit_dir / 'render-records.json').read_text())
    frames = [Image.open(r['path']).convert('RGB') for r in orbit]
    assert len(frames) == 24 and all(r['native_sha256'] == sha(native) for r in orbit)
    frames[0].save(out / 'Mia_v29_review_orbit.gif', save_all=True, append_images=frames[1:], duration=120, loop=0, disposal=2)
    sheet = Image.new('RGB', (4*256, 6*282), (237, 242, 246))
    draw = ImageDraw.Draw(sheet)
    for i, frame in enumerate(frames):
        frame.thumbnail((256, 256))
        x, y = i % 4 * 256, i // 4 * 282
        sheet.paste(frame, (x, y+26))
        draw.text((x+8, y+2), str(i*15) + 'deg / actual render', font=font, fill=(24,38,49))
    sheet.save(out / 'orbit-contactsheet.png')
    (out / 'orbit-preview.json').write_text(json.dumps({'native': artifact(native), 'actual_frames': 24,
        'camera_yaw_degrees': list(range(0,360,15)), 'gif_frame_duration_ms': 120,
        'meaning': 'Static model camera orbit for review. Not a 30fps character animation or physics validation.'}, indent=2), encoding='utf-8')
print('V29_SOURCE_BOARDS_WRITTEN', len(rows))
