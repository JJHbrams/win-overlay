"""Actual matched grazing/fullClose before/after with immutable provenance."""
import json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;out=P/'reviews/v31-brows-lashes-source4/paired'
b=P/'reviews/v31-close-before/source/grazingClosed.png';a=P/'reviews/v31-close-after/source/grazingClosed.png'
board=Image.new('RGB',(1024,606),(237,242,246));d=ImageDraw.Draw(board);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',21)
for i,(path,label) in enumerate([(b,'BEFORE / full closure'),(a,'AFTER / full closure')]):
 im=Image.open(path).convert('RGB');assert im.size==(512,512);board.paste(im,(512*i,48));d.text((512*i+10,12),label,font=font,fill=(24,38,49))
d.text((12,575),'Same ORTHO camera / lights / pose; clip .1..10m. Half-close style still open.',font=font,fill=(24,38,49))
dest=out/'closed-before-after.png';board.save(dest);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
(out/'closed-comparison.json').write_text(json.dumps({'before':{'path':str(b),'sha256':sha(b)},'after':{'path':str(a),'sha256':sha(a)},'board':{'path':str(dest),'sha256':sha(dest)},'before_record':str(b.parent/'render-records.json'),'after_record':str(a.parent/'render-records.json'),'scope':'Full-closure upperfan shape only, not arbitrary poses or wholecharacterART.'},indent=2),encoding='utf-8');print(dest)
