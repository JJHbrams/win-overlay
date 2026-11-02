from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;R=P/'renders-form-A';records=json.loads((R/'render-records.json').read_text());font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',19);small=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',15);out=[]
for view in ['front','profile','highoblique','lowoblique']:
    b=next(r for r in records if r['view']==view and r['variant']=='baseline');c=next(r for r in records if r['view']==view and r['variant']=='candidate');assert b['camera']==c['camera'];im=Image.new('RGB',(1280,720),'#edf2f4');d=ImageDraw.Draw(im)
    d.text((12,10),'CURRENT 4dc1 / '+view,font=font,fill='#142f40');d.text((652,10),'FORM A / same actual geometry fixture',font=font,fill='#142f40');im.paste(Image.open(b['path']).convert('RGB'),(0,42));im.paste(Image.open(c['path']).convert('RGB'),(640,42));d.text((12,690),'ORTHO640 .1/10m; actual gray110/38/22 lights; unchanged camera/pose/world. No shape/ART pass from metrics.',font=small,fill='#142f40')
    file=P/('form-A-'+view+'-before-after.png');im.save(file);out.append(dict(view=view,path=str(file),sha256=hashlib.sha256(file.read_bytes()).hexdigest(),baseline=b['path'],candidate=c['path']))
(P/'form-A-boards.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print('BODY_FORM_A_BOARDS_DONE',len(out))
