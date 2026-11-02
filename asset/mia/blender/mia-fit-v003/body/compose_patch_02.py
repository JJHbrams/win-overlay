"""Actual matched-fixture01/02 gray comparisons, no registration warp."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;O=P/'posed-target'
a=json.loads((O/'actual-01/render-records.json').read_text());b=json.loads((O/'actual-02/render-records.json').read_text())
font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',17)
rows=[]
for r in b:
    old=next(x for x in a if x['view']==r['view'] and x['mode']==r['mode'])
    assert old['camera']==r['camera'] and old['color_management']==r['color_management']
    assert old['native_sha256']==r['native_sha256']
    def lights(x):
        return sorted([{k:v for k,v in y.items() if k not in ['name','hidden']} for y in x['actual_all_light_flags_before_render'] if not y['hidden']],key=lambda y:y['energy'])
    assert lights(old)==lights(r)
    im=Image.new('RGB',(1280,690),'#273039');d=ImageDraw.Draw(im)
    for x,img,label in [(0,old,'REJECTED01'),(640,r,'PATCH02 / HYPOTHESIS')]:
        q=Image.open(img['path']).convert('RGB');assert q.size==(640,640);im.paste(q,(x,35));d.text((x+10,9),label+' / '+r['view'],font=font,fill='white')
    d.text((10,674),'Exact camera + actual active light matrices/energies/sizes/shadows + color records match. No image warp.',font=font,fill='white')
    path=O/f'actual01-02-{r["view"]}.png';im.save(path)
    rows.append(dict(view=r['view'],baseline=old['path'],baseline_sha256=old['sha256'],candidate=r['path'],candidate_sha256=r['sha256'],board=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),camera_actual_lights_color_exact=True))
(O/'actual01-02-comparisons.json').write_text(json.dumps(dict(boards=rows,status='Limited actual surface comparison; no source ART acceptance.',material_world_note='Both actual scripts construct physical gray RGB.23/roughness.85 and worldRGB.18/strength.2, then assert slot identity before/after every render. Original-data/pose guards are separate.'),indent=2)+'\n',encoding='utf-8')
print('PATCH02_ACTUAL_COMPARISONS_DONE',len(rows),flush=True)
