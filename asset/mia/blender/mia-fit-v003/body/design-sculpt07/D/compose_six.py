"""Actual held high/low C-to-D comparisons; no image aspect warp."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;C=P.parent/'C';A=P/'actual-six-D';rows=json.loads((A/'render-records.json').read_text());assert len(rows)==6
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15);sheet=Image.new('RGB',(1440,1020),'#202632');draw=ImageDraw.Draw(sheet)
for i,r in enumerate(rows):
    f=A/Path(r['path']).name;assert hashlib.sha256(f.read_bytes()).hexdigest()==r['sha256'];im=Image.open(f).convert('RGB');im=im.resize((480,480),Image.Resampling.LANCZOS);x=(i%3)*480;y=(i//3)*510;sheet.paste(im,(x,y+30));draw.text((x+8,y+7),'ACTUAL D '+r['view'],font=font,fill='white')
sheet.save(P/'actual-six-contact-sheet.png');board=Image.new('RGB',(1280,1370),'#202632');draw=ImageDraw.Draw(board)
for i,view in enumerate(['upperoblique','loweropposite']):
    row=next(r for r in rows if r['view']==view);old=next(r for r in json.loads((C/'expanded-review/render-records.json').read_text()) if r['view']==view);assert row['camera']==old['camera'];y=i*670;left=Image.open(C/'expanded-review'/(view+'.png')).convert('RGB');right=Image.open(A/('gray-'+view+'.png')).convert('RGB');board.paste(left,(0,y+30));board.paste(right,(640,y+30));draw.text((8,y+7),'HELD C '+view,font=font,fill='white');draw.text((648,y+7),'D upper-only warp '+view,font=font,fill='white')
draw.text((8,1345),'Same actual fixtures; no calibrated art for these extra angles. Context seams/axilla remain UNVERIFIED.',font=small,fill='white');board.save(P/'held-C-D-high-low.png');print('D_CORE6_CONTACT_COMPOSED')
