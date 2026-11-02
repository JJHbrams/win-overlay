"""Labeled actual intact/cutaway gray/normal comparison."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;r=json.loads((P/'render-records.json').read_text(encoding='utf-8'));assert len(r)==4;font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15);out=Image.new('RGB',(1280,1372),'#202632');draw=ImageDraw.Draw(out)
for i,row in enumerate(r):
    f=Path(row['path']);assert hashlib.sha256(f.read_bytes()).hexdigest()==row['sha256'];x=(i%2)*640;y=(i//2)*670;out.paste(Image.open(f).convert('RGB'),(x,y+30));label='ACTUAL D '+row['phase']+' / '+row['mode'];draw.text((x+8,y+7),label,font=font,fill='white')
draw.text((8,1348),'DIAGNOSTIC material cutaway only; opposite arm skin is visible. Both-wall anatomy/clearance remains UNVERIFIED.',font=small,fill='white');out.save(P/'actual-axilla-four.png');print('D_AXILLA_ACTUAL4_COMPOSED')
