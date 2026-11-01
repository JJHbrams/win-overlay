"""Arrange actual matched matte captures; no retouch, fit, or new art generation."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / 'volume-recovery-review'
assert not OUT.exists(), 'Preserve prior evidence'
PAIRS = [ROOT/'parts/face-finish7-r27-unselected/evidence/r23_before',
         ROOT/'parts/face-finish7-r28-review/evidence/after']
labels = ['matte_yaw+00_elev-10', 'matte_yaw+30_elev-10']
data = [json.loads((p/'render-records.json').read_text()) for p in PAIRS]
records = [{r['label']: r for r in d['records']} for d in data]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
OUT.mkdir()
board = Image.new('RGB', (1600, 1700), '#edf1f4')
draw = ImageDraw.Draw(board)
font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 25)
for col, title in enumerate(['BEFORE / R23 REJECTED FLAT SURFACE', 'AFTER / R28 REVIEW CANDIDATE']):
    draw.text((col*800+15, 15), title, fill='#172633', font=font)
inputs = []
for row, label in enumerate(labels):
    cameras = [r[label]['camera'] for r in records]
    assert cameras[0]['projection'] == cameras[1]['projection'] == 'ORTHO'
    assert abs(cameras[0]['ortho_scale']-cameras[1]['ortho_scale']) < 1e-7
    assert np.max(np.abs(np.asarray(cameras[0]['matrix'])-cameras[1]['matrix'])) < 1e-6
    for col, folder in enumerate(PAIRS):
        rec = records[col][label]
        path = folder/Path(rec['render']['path']).name
        assert sha(path) == rec['render']['sha256']
        im = Image.open(path).convert('RGB')
        assert im.size == (1000, 1000)
        board.paste(im.resize((800, 800), Image.Resampling.LANCZOS), (col*800, 55+row*800))
        inputs.append({'path': str(path), 'sha256': sha(path), 'record': rec})
draw.text((15, 1665), 'Same raw matte captures; uniform display resize only. Surface/whole likeness NOT approved.', fill='#172633', font=font)
dest = OUT/'r23-r28-matte.png'
board.save(dest)
(OUT/'comparison-manifest.json').write_text(json.dumps({'status': 'REVIEW ONLY / ART UNAPPROVED', 'inputs': inputs, 'output': {'path': dest.name, 'sha256': sha(dest)}, 'recipe_sha256': sha(Path(__file__))}, indent=2), encoding='utf-8')
print(dest)
