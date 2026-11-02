"""Fixed whole-height registration: source | current baseline | rejected01."""
from pathlib import Path
import json, hashlib
from PIL import Image, ImageDraw, ImageFont

P = Path(__file__).resolve().parent
O = P / 'posed-target'
reg = json.loads((P / 'current-v06-boards.json').read_text())
source = Image.open(reg['source']).convert('RGBA')
scale = reg['registration']['scale']
dy = reg['registration']['vertical_translation']
font = ImageFont.truetype('C:/Windows/Fonts/consola.ttf', 17)
small = ImageFont.truetype('C:/Windows/Fonts/consola.ttf', 13)
rows = []
for view, bounds, center in [('front', (0, 440), 239), ('profile', (440, 750), 568)]:
    im = Image.new('RGB', (1500, 1100), '#273039')
    d = ImageDraw.Draw(im)
    crop = source.crop((bounds[0], 0, bounds[1], 1024))
    im.paste(crop, (round(250 - (center - bounds[0])), 45), crop)
    d.text((12, 10), 'USER v06 / ' + view, font=font, fill='white')
    paths = [P/'current-source4'/f'{view}.png', O/'actual-01'/f'source-{view}.png']
    for col, path in enumerate(paths, 1):
        img = Image.open(path).convert('RGBA')
        img = img.resize((round(img.width*scale), round(img.height*scale)), Image.Resampling.LANCZOS)
        im.paste(img, (round(250+col*500-400*scale), round(45+dy)), img)
        d.text((12+col*500, 10), ['CURRENT4dc1', 'STATIC01 / REJECTED FORM'][col-1], font=font, fill='white')
    for y in [54, 950]:
        d.line((0, 45+y, 1500, 45+y), fill='#99b8bd')
    d.text((10, 1060), f'One BASELINE front sole-to-crown scale {scale:.9f}, vertical shift {dy:.6f}px; all three original aspect.', font=small, fill='white')
    d.text((10, 1080), 'No feature/width normalization. Inherited underwear/maps remain pending. Target01 is a static construction hypothesis, not approved.', font=small, fill='white')
    path = O / f'v06-current-target01-{view}.png'
    im.save(path)
    rows.append(dict(view=view, board=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest(), baseline=str(paths[0]), candidate=str(paths[1])))
(O/'source-boards-01.json').write_text(json.dumps(dict(registration=reg['registration'], source=reg['source'], source_sha256=reg['source_sha256'], boards=rows, status='REJECTED SURFACE; no body ART or garment approval'), indent=2)+'\n', encoding='utf-8')
print('POSED_TARGET_01_SOURCE_BOARDS_DONE', flush=True)
