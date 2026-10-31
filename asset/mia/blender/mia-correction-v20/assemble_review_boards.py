"""Technical contact sheets of actual saved-native renders, using uniform resizing only."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

p = argparse.ArgumentParser()
p.add_argument('--before', required=True)
p.add_argument('--after', required=True)
p.add_argument('--output-dir', required=True)
a = p.parse_args()
before, after, out = (Path(x).resolve() for x in (a.before, a.after, a.output_dir))
out.mkdir(parents=True, exist_ok=True)
font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 20)
small = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 15)
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
sources = []
sets = {
    'head-before-after': ['head_front', 'head_left', 'head_profile', 'head_back'],
    'face-shape-before-after': ['clay_face_front', 'clay_face_left', 'clay_face_right', 'clay_face_profile'],
    'body-before-after': ['clay_body_front', 'clay_body_three_quarter', 'clay_body_profile', 'clay_body_back'],
}
for title, names in sets.items():
    sheet = Image.new('RGB', (1600, 948), '#20262b')
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 10), 'MIA / ACTUAL BLENDER RENDERS / WIP - art approval remains separate', font=font, fill='white')
    for row, (directory, label) in enumerate([(before, 'First integrated pass'), (after, 'Additional correction')]):
        y = 46 + row * 438
        draw.text((16, y), label, font=font, fill='#c6d7e2')
        for col, name in enumerate(names):
            path = directory / (name + '.png')
            with Image.open(path) as im:
                tile = ImageOps.contain(im.convert('RGB'), (396, 396), Image.Resampling.LANCZOS)
            sheet.paste(tile, (col * 400 + (400 - tile.width) // 2, y + 30))
            draw.text((col * 400 + 8, y + 412), name, font=small, fill='white')
            sources.append({'sheet': title, 'row': row, 'source': str(path), 'sha256': sha(path)})
    draw.text((16, 928), 'Same view setup; image sizing is uniform. No feature warping or generated replacement imagery.', font=small, fill='#b0bec7')
    sheet.save(out / (title + '.png'))
(out / 'board-sources.json').write_text(json.dumps(sources, indent=2), encoding='utf-8')
print(json.dumps({'boards': list(sets), 'source_images': len(sources)}))
