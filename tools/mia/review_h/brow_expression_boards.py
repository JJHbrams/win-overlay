"""Diagnostic source/original/display boards; no source-pose ART claim."""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
out = ROOT/'.mia-cache/face-live/brow-expression4'
source = ROOT/'asset/mia/references/mia-expression-style-confirmed-20261031.png'
art = Image.open(source).convert('RGB')
assert art.size == (1536, 1024)
font = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', 18)
states = [('neutral', 1), ('irritated', 5), ('surprised', 12), ('blink', 2)]
board = Image.new('RGB', (1536, 4*580), '#e4edf2')
draw = ImageDraw.Draw(board)
for i, (label, panel) in enumerate(states):
    y = i*580
    x, sy = ((panel-1)%4)*384, ((panel-1)//4)*256
    crop = art.crop((x, sy, x+384, sy+256))
    board.paste(crop, (64, y+124))  # Original pixels, no aspect or scale change.
    for j, suffix in enumerate(['original', 'display06'], start=1):
        board.paste(Image.open(out/(label+'-'+suffix+'.png')).convert('RGB'), (512*j, y+40))
    labels = [f'SOURCE P{panel:02} / 원본 픽셀·시점 다름', label+' / R3b', label+' / 부분 눈썹 표시 .60']
    for j, text in enumerate(labels): draw.text((512*j+12, y+10), text, font=font, fill='#20313c')
    note = '완전 blink 진단; 원화 P02는 near-close 참고' if label == 'blink' else 'head/gaze 중립 고정: 표정 가독성 진단, 원화 포즈 정합·ART 판정 아님'
    draw.text((12, y+556), note, font=font, fill='#20313c')
path = out/'source-expression-diagnostic.png'; assert not path.exists(); board.save(path)
record = dict(scope='Readability diagnostic only, original source crop pixels and aspect held; no pose registration or ART approval',
    board=dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest()),
    source=dict(path=str(source), sha256=hashlib.sha256(source.read_bytes()).hexdigest()),
    evidence=dict(path=str(out/'expression-evidence.json'), sha256=hashlib.sha256((out/'expression-evidence.json').read_bytes()).hexdigest()))
(out/'board.json').write_text(json.dumps(record, indent=2)+'\n', encoding='utf8')
print(json.dumps(record))
