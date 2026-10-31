"""Arrange unchanged, hash-checked Blender sweep renders; no image warping or art verdict."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ap = argparse.ArgumentParser()
ap.add_argument('--baseline', required=True)
ap.add_argument('--candidate', required=True)
ap.add_argument('--output-dir', required=True)
a = ap.parse_args()
out = Path(a.output_dir).resolve()
if out.exists() and any(out.iterdir()):
    raise RuntimeError('Choose a new empty comparison directory')
out.mkdir(parents=True, exist_ok=True)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
artifact = lambda p: {'path': str(Path(p).resolve()), 'sha256': sha(p)}
records, sources = {}, {}
for role in ('baseline', 'candidate'):
    p = Path(getattr(a, role)).resolve()
    data = json.loads(p.read_text(encoding='utf-8'))
    assert sha(data['source']['path']) == data['source']['sha256']
    sources[role] = data['source']
    records[role] = {(r['mode'], r['yaw'], r['elevation']): r for r in data['records']}
    for row in data['records']:
        assert sha(row['render']['path']) == row['render']['sha256']
assert records['baseline'].keys() == records['candidate'].keys(), 'Sweep coverage differs'
for key, before in records['baseline'].items():
    after = records['candidate'][key]
    for prop in ('matrix', 'ortho_scale', 'resolution'):
        assert before[prop] == after[prop], (key, prop)
font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 20)
small = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 16)

def tile(role, key, size):
    im = Image.open(records[role][key]['render']['path']).convert('RGBA')
    bg = Image.new('RGBA', im.size, (205, 205, 205, 255))
    bg.alpha_composite(im)
    return bg.convert('RGB').resize(size, Image.Resampling.LANCZOS)

outputs = []
for el in (-10, 0, 10):
    board = Image.new('RGB', (1920, 740), '#edf1f4')
    draw = ImageDraw.Draw(board)
    for row, role in enumerate(('baseline', 'candidate')):
        for col, yaw in enumerate((-60, -30, 0, 30, 60, 90)):
            board.paste(tile(role, ('matte', yaw, el), (320, 320)), (col*320, row*370+42))
            draw.text((col*320+8, row*370+8), f'{role} {sources[role]["sha256"][:8]} / yaw {yaw:+d}', font=small, fill='#172633')
    p = out/f'matte-elevation{el:+d}-before-after.png'
    board.save(p)
    outputs.append(artifact(p))
for yaw, el in ((0, -10), (30, -10), (-30, -10), (45, 0), (60, 0), (90, 0)):
    key = ('matte', yaw, el)
    board = Image.new('RGB', (1400, 750), '#edf1f4')
    draw = ImageDraw.Draw(board)
    for col, role in enumerate(('baseline', 'candidate')):
        board.paste(tile(role, key, (700, 700)), (col*700, 50))
        draw.text((col*700+12, 14), f'{role} {sources[role]["sha256"][:8]} | yaw {yaw:+d}, elevation {el:+d}', font=font, fill='#172633')
    p = out/f'matte-yaw{yaw:+d}-elevation{el:+d}-before-after.png'
    board.save(p)
    outputs.append(artifact(p))
(out/'comparison-manifest.json').write_text(json.dumps({'sources': sources, 'record_inputs': {r: artifact(getattr(a, r)) for r in ('baseline', 'candidate')}, 'camera_records_equal': True, 'input_images_unchanged': True, 'transform': 'Identical uniform thumbnail scaling only; no refit, no feature warp.', 'art_status': 'NOT_EVALUATED', 'outputs': outputs, 'composer': artifact(__file__)}, indent=2), encoding='utf-8')
print(json.dumps({'comparisons': len(outputs), 'output': str(out)}))
