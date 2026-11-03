"""Equal-scale actual numerical curves. PIL avoids installing plotting packages."""
from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;a=json.loads((P/'CPU-audit.json').read_text(encoding='utf-8'))
im=Image.new('RGB',(1440,820),'white');draw=ImageDraw.Draw(im)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',12)
draw.text((15,8),'ACTUAL TRIANGLE / MATCHED PHYSICAL PLANES | E gray, 08 orange | Equal axis scale; mixed turns, no ART PASS',font=font,fill='black')
for k,row in enumerate(a['roof_curve_comparisons']):
    col=k%4;rr=k//4;ox=col*360+42;oy=rr*390+62;scale=5.;x0=133.;ztop=1290.
    for x in range(135,176,5):
        px=ox+(x-x0)*scale;draw.line((px,oy,px,oy+285),fill='#dddddd');draw.text((px-8,oy+289),str(x),font=small,fill='black')
    for z in range(1235,1291,5):
        py=oy+(ztop-z)*scale;draw.line((ox,py,ox+215,py),fill='#dddddd');draw.text((ox-32,py-6),str(z),font=small,fill='black')
    for role,color in [('before','#777777'),('after','#d95f02')]:
        points=[(ox+(abs(r[role]['world'][0])*1000-x0)*scale,oy+(ztop-r[role]['world'][2]*1000)*scale) for r in row['samples']]
        if len(points)>1:draw.line(points,fill=color,width=2)
    draw.text((ox-15,oy-28),f"side{row['side']:+d} Y={row['plane_Y']*1000:.0f}mm",font=font,fill='black')
    draw.text((ox-15,oy+314),f"max3.75mm turn {row['before_turn']['maximum_degrees']:.1f} -> {row['after_turn']['maximum_degrees']:.1f}deg",font=small,fill='black')
    draw.text((ox-15,oy+331),'|world X| mm; vertical world Z mm',font=small,fill='black')
im.save(P/'CPU-roof-curves.png')
