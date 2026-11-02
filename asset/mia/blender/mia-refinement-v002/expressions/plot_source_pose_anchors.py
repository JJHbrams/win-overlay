"""Analytic crop/coordinate plot for source-pose estimates, never new concept art."""
from pathlib import Path
import json,hashlib,math
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;out=P/'pose-calibration-r3';out.mkdir(parents=True,exist_ok=True)
rows=json.loads((P/'expression-intents.json').read_text())['panels']
points=[[[155,104],[212,92]],[[142,111],[197,91]],[[151,105],[211,88]],[[132,104],[178,83]],[[149,105],[210,92]],[[134,99],[182,79]],[[151,108],[211,93]],[[156,106],[212,92]],[[151,106],[210,92]],[[147,108],[201,91]],[[151,108],[213,96]],[[159,106],[212,86]],[[151,107],[210,93]],[[149,106],[210,94]],[[151,106],[211,94]],[[154,107],[212,93]]]
canvas=Image.new('RGB',(2720,1760),(237,242,246));draw=ImageDraw.Draw(canvas);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',12);records=[]
draw.text((12,10),'Original source / equal-aspect crops + provisional coordinate markers (analysis only)',font=font,fill=(24,38,49))
for j,(row,pp) in enumerate(zip(rows,points)):
    ox=(j%4)*680+25;oy=(j//4)*425+75
    file=P/row['source_panel'];im=Image.open(file).convert('RGB');canvas.paste(im.crop((105,60,235,130)).resize((650,350),Image.Resampling.NEAREST),(ox,oy))
    for x in range(110,236,10):
        xx=ox+(x-105)*5;draw.line((xx,oy,xx,oy+350),fill=(160,160,160),width=1);draw.text((xx-8,oy+353),str(x),font=small,fill=(24,38,49))
    for y in range(60,131,10):
        yy=oy+(y-60)*5;draw.line((ox,yy,ox+650,yy),fill=(160,160,160),width=1);draw.text((ox-24,yy-5),str(y),font=small,fill=(24,38,49))
    rendered=[(ox+(p[0]-105)*5,oy+(p[1]-60)*5) for p in pp];draw.line(rendered,fill=(220,20,20),width=2)
    for x,y in rendered:draw.ellipse((x-8,y-8,x+8,y+8),outline=(255,20,20),width=2)
    angle=math.degrees(math.atan2(pp[1][1]-pp[0][1],pp[1][0]-pp[0][0]));draw.text((ox,oy-28),f'{row["panel"]:02} provisional axis {angle:.1f}deg',font=font,fill=(24,38,49))
    records.append(dict(panel=row['panel'],source=str(file),source_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),points_xy=pp,provisional_axis_deg_y_down=angle,
        uncertainty='Initial visual iris/lid-center markers, about1–3originalpixels; closed02 uses lid centers. Must inspect the plot; not calibrated geometry/proportion truth.'))
canvas.save(out/'source-eye-axis-markers-provisional.png')
(out/'source-eye-axis-markers-provisional.json').write_text(json.dumps(dict(records=records,scope='Pose-estimate analysis only. No source pixels or aspect were changed; no per-feature image warping.'),indent=2)+'\n',encoding='utf-8')
print(out/'source-eye-axis-markers-provisional.png')
