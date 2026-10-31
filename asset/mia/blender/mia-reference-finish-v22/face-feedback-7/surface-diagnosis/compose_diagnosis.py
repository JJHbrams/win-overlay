"""Technical composition of unchanged Blender renders and measured mesh sections."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,math
H=Path(__file__).resolve().parent
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16)
for sign,name in [(1,'positive'),(-1,'negative')]:
    board=Image.new('RGB',(1960,972),(235,235,235));d=ImageDraw.Draw(board)
    for row,el in enumerate([-10,0,10]):
        for col,ya in enumerate([0,15,30,45,60,75,90]):
            yaw=sign*ya;im=Image.open(H/('matte_yaw%+03d_elev%+03d.png'%(yaw,el))).convert('RGBA')
            tile=Image.new('RGBA',im.size,(205,205,205,255));tile.alpha_composite(im);tile=tile.convert('RGB').resize((280,280))
            board.paste(tile,(col*280,row*324+32));d.text((col*280+7,row*324+5),'Yaw %+d / elevation %+d'%(yaw,el),font=small,fill='black')
    board.save(H/('continuous-'+name+'-yaw.png'))
data=json.loads((H/'actual-sections-and-cage.json').read_text())
board=Image.new('RGB',(1500,830),'white');d=ImageDraw.Draw(board)
d.text((30,15),'Actual evaluated vertical sections: front depth vs height (skin only)',font=font,fill='black')
d.text((30,45),'Neutral Face6. Local +Y is forward. Geometric samples; not a fitted target or proof of a disconnected surface.',font=small,fill='black')
colors=['#b54b3c','#e49a29','#3d79bd','#469d76']
for side in [-1,1]:
    x0=80 if side==-1 else 820;y0=730;width=580;height=600
    def xy(y,z):return (x0+(y-.010)/.075*width,y0-(z-1.475)/.080*height)
    for z in [1.48,1.49,1.50,1.51,1.52,1.53,1.54,1.55]:
        a=xy(.010,z);b=xy(.085,z);d.line([a,b],fill='#dddddd');d.text((x0-60,a[1]-7),'%.3f'%z,font=small,fill='black')
    for y in [.02,.04,.06,.08]:
        a=xy(y,1.475);b=xy(y,1.555);d.line([a,b],fill='#eeeeee');d.text((a[0]-13,y0+10),'%d mm'%round(y*1000),font=small,fill='black')
    d.text((x0,90),'Local X %s (screen %s)'%('negative' if side<0 else 'positive','right' if side<0 else 'left'),font=font,fill='black')
    for idx,absx in enumerate([.035,.045,.055,.065]):
        sec=min(data['sections']['vertical'],key=lambda q:abs(q['x']-side*absx));points=[]
        for s in sec['samples']:
            hit=s['hit'];valid=hit and hit['owner']=='MIA_V14_SculptedSkin' and hit['p'][1]>.015
            if valid:points.append(xy(hit['p'][1],s['z']))
            else:
                if len(points)>1:d.line(points,fill=colors[idx],width=3)
                points=[]
        if len(points)>1:d.line(points,fill=colors[idx],width=3)
        d.text((x0+idx*145,780),'X=%+.0f mm'%(side*absx*1000),font=small,fill=colors[idx])
    a=xy(.010,1.532);b=xy(.085,1.532);d.line([a,b],fill='#b02070',width=2)
    d.text((x0+190,a[1]-24),'lower-lid / cheek turn, Z 1.532',font=small,fill='#b02070')
board.save(H/'evaluated-vertical-sections.png')
print('Composed two rotation sheets and measured section plot.')
