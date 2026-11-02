"""Lay out source and actual renders without feature fitting; make orbit preview."""
from pathlib import Path
import argparse, hashlib, json
from PIL import Image, ImageDraw, ImageFont

P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--tag',required=True);a=ap.parse_args()
root=P/'review'/a.tag
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
panels=json.loads((P/'expressions/expression-intents.json').read_text())['panels']
records=json.loads((root/'expressions/render-records.json').read_text())
by=lambda name:next(r for r in records if r['id']==name)
out=root/'expression-panels';out.mkdir(parents=True,exist_ok=True)
manifest=[];overview=Image.new('RGB',(2048,780),(237,242,246))
for row in panels:
    stem=f"P{row['panel']:02}-{row['id']}"
    src=P/'expressions'/row['source_panel']
    assert sha(src)==row['panel_sha256']
    on,off=by(stem+'-hairON'),by(stem+'-hairOFF')
    assert all(sha(r['path'])==r['sha256'] for r in [on,off])
    board=Image.new('RGB',(1024,390),(237,242,246));d=ImageDraw.Draw(board)
    board.paste(Image.open(src).convert('RGB'),(0,55))
    for x,r in [(384,on),(704,off)]:
        im=Image.open(r['path']).convert('RGB');assert im.width==im.height
        board.paste(im.resize((320,320),Image.Resampling.LANCZOS),(x,35))
    for x,label in [(8,'SOURCE '+str(row['panel'])+' / original384x256'),(392,'Actual / hair ON'),(712,'Actual / hair OFF')]:d.text((x,8),label,font=font,fill=(24,38,49))
    limit='07 hand gesture remains a separate body-pose task.' if row['panel']==7 else 'Head/gaze are estimates; no per-feature image warp or proportion acceptance.'
    d.text((8,365),limit,font=small,fill=(24,38,49))
    file=out/(stem+'.png');assert not file.exists();board.save(file)
    overview.paste(board.resize((512,195),Image.Resampling.LANCZOS),(((row['panel']-1)%4)*512,((row['panel']-1)//4)*195))
    manifest.append(dict(panel=row['panel'],source={'path':str(src),'sha256':sha(src)},hairON=on,hairOFF=off,
                         board={'path':str(file),'sha256':sha(file)},source_display='Original aspect and source pixels; layout only. Corresponding head/gaze estimates, not calibrated identity acceptance.'))
overview.save(root/'expressions-source16-overview.png')
(out/'panels.json').write_text(json.dumps(dict(panels=manifest,art_approved=False),indent=2)+'\n',encoding='utf-8')
orbit=root/'orbit'
if (orbit/'render-records.json').exists():
    rs=json.loads((orbit/'render-records.json').read_text());frames=[]
    for r in rs:
        assert sha(r['path'])==r['sha256'];frames.append(Image.open(r['path']).convert('RGB'))
    frames[0].save(root/'Mia-v002-head-orbit.gif',save_all=True,append_images=frames[1:],duration=120,loop=0,optimize=False)
print('V002_EXPRESSION_BOARDS_DONE',len(manifest),root)
