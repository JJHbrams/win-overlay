"""Actual heldD/E audit and Normal comparisons; uniform image scale."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;A=P/'actual-audit';old=Path('C:/Users/antio/.codex/visualizations/2026/10/29/01a1885c-8934-7af0-a487-a7f8d5981f65/upperbody-audit-20261103');rows=json.loads((A/'render-records.json').read_text());assert len(rows)==9;font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15)
def paired(left,right,label,out):
    board=Image.new('RGB',(1280,700),'#202632');d=ImageDraw.Draw(board);board.paste(Image.open(left).convert('RGB'),(0,32));board.paste(Image.open(right).convert('RGB'),(640,32));d.text((8,7),'HELD D / '+label,font=font,fill='white');d.text((648,7),'E one support/fair candidate / '+label,font=font,fill='white');d.text((8,678),'Same actual camera/material/light/pose; private context seams, no head scale; not whole-body ART approval.',font=small,fill='white');board.save(out)
for view in ['back180','rear140','rear220','rearhigh140','rearlow140']:
    r=next(r for r in rows if r['state']=='E' and r['mode']=='gray' and r['view']==view);paired(old/('D-'+view+'.png'),Path(r['path']),view,P/('D-E-'+view+'.png'))
paired(A/'D-normal-rear140.png',A/'E-normal-rear140.png','ACTUAL GeometryNormal',P/'D-E-normal-rear140.png')
gray=[r for r in rows if r['mode']=='gray'];sheet=Image.new('RGB',(1600,880),'#202632');d=ImageDraw.Draw(sheet)
for i,r in enumerate(gray):
    x=(i%4)*400;y=(i//4)*440;sheet.paste(Image.open(r['path']).convert('RGB').resize((400,400),Image.Resampling.LANCZOS),(x,y+30));d.text((x+7,y+7),'E '+r['view'],font=small,fill='white')
sheet.save(P/'E-audit-seven.png');print('E_AUDIT_PAIRS_COMPOSED')
