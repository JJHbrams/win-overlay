from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',18);small=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',13);out=[];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
base=json.loads((P/'renders-form-B/render-records.json').read_text());cand=json.loads((P/'renders-form-C-gray/render-records.json').read_text())
for c in cand:
    view=c['view'];b=next(r for r in base if r['view']==view and r['variant']=='baseline');assert b['camera']==c['camera'];im=Image.new('RGB',(1280,720),'#edf2f4');d=ImageDraw.Draw(im);d.text((12,10),'CURRENT4dc1 / '+view,font=font,fill='#142f40');d.text((652,10),'FORM C / torso+bust; shoulders pending',font=font,fill='#142f40');im.paste(Image.open(b['path']).convert('RGB'),(0,42));im.paste(Image.open(c['path']).convert('RGB'),(640,42));d.text((12,690),'Matched distant BODY gray110/38/22 .18/.2; head exact. Actual shape comparison, no anatomy PASS from metrics.',font=small,fill='#142f40');file=P/('form-C-'+view+'-before-after.png');im.save(file);out.append(dict(mode='gray',view=view,path=str(file),sha256=sha(file)))
reg=json.loads((P/'current-v06-boards.json').read_text())['registration'];scale=reg['scale'];shift=reg['vertical_translation'];REF=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/references/received/mia-body-v06-confirmed-20261102.png');ref=Image.open(REF).convert('RGBA');base=json.loads((P/'current-source4/render-records.json').read_text());cand=json.loads((P/'renders-form-C-source/render-records.json').read_text());centers=dict(front=239,profile=568,back=935,oblique=1317);crops=dict(front=(0,440),profile=(440,750),back=(750,1120),oblique=(1120,1536))
for c in cand:
    view=c['view'];b=next(r for r in base if r['view']==view);assert b['camera']==c['camera'];assert b['lighting']==c['lighting'];im=Image.new('RGB',(1500,1100),'#273039');d=ImageDraw.Draw(im)
    for x,label in [(12,'USER v06 / '+view),(512,'CURRENT4dc1'),(1012,'FORM C / torso+bust')]:d.text((x,10),label,font=font,fill='white')
    left,right=crops[view];crop=ref.crop((left,0,right,1024));im.paste(crop,(int(250-(centers[view]-left)),45),crop)
    for mid,r in [(750,b),(1250,c)]:
        a=Image.open(r['path']).convert('RGBA');a=a.resize((round(a.width*scale),round(a.height*scale)),Image.Resampling.LANCZOS);im.paste(a,(round(mid-400*scale),round(45+shift)),a)
    for y in [54,950]:d.line((0,45+y,1500,45+y),fill='#99b8bd')
    d.text((10,1060),'ONE fixed whole-height scale/translation from baseline; original aspect; shoulders/head/hips/legs unchanged.',font=small,fill='white');d.text((10,1080),'C keeps inherited underwear only to expose fit failure. Garment/UV/maps are NOT selected or fixed by this shape probe.',font=small,fill='white');file=P/('form-C-v06-'+view+'.png');im.save(file);out.append(dict(mode='source',view=view,path=str(file),sha256=sha(file)))
(P/'form-C-boards.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print('FORM_C_BOARDS_DONE',len(out),flush=True)
