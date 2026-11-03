"""Six actual E views and heldD high/low comparisons, uniform resizing only."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;D=P.parent/'D';A=P/'actual-E';rows=json.loads((A/'render-records.json').read_text());assert len(rows)==6;font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15);sheet=Image.new('RGB',(1440,1020),'#202632');draw=ImageDraw.Draw(sheet)
for i,r in enumerate(rows):
    f=Path(r['path']);assert hashlib.sha256(f.read_bytes()).hexdigest()==r['sha256'];im=Image.open(f).convert('RGB').resize((480,480),Image.Resampling.LANCZOS);x=(i%3)*480;y=(i//3)*510;sheet.paste(im,(x,y+30));draw.text((x+8,y+7),'ACTUAL E '+r['view'],font=font,fill='white')
sheet.save(P/'actual-six-E.png');board=Image.new('RGB',(1280,1370),'#202632');draw=ImageDraw.Draw(board)
for i,view in enumerate(['upperoblique','loweropposite']):
    r=next(q for q in rows if q['view']==view);old=next(q for q in json.loads((D/'actual-six-D/render-records.json').read_text()) if q['view']==view);assert r['camera']==old['camera'];y=i*670;board.paste(Image.open(D/'actual-six-D'/('gray-'+view+'.png')).convert('RGB'),(0,y+30));board.paste(Image.open(A/('gray-'+view+'.png')).convert('RGB'),(640,y+30));draw.text((8,y+7),'HELD D '+view,font=font,fill='white');draw.text((648,y+7),'E support + local fair '+view,font=font,fill='white')
draw.text((8,1345),'Same actual fixtures; no calibrated art for extra angles. Context seams/axilla remain UNVERIFIED.',font=small,fill='white');board.save(P/'held-D-E-high-low.png');print('E_CORE6_COMPOSED')
