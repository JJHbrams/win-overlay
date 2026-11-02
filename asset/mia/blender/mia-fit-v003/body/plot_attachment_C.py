"""Actual triangle sections and control neighborhoods, not a render substitute."""
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;d=np.load(P/'current-body-limit.npz');g=np.load(P.parents[1]/'mia-body-underwear-v002/support-G/actual-core-limit.npz');b=np.load(P/'form-C-evaluated.npz');v=d['world'];t=d['triangles'];mi=d['triangle_materials'];raw=d['raw_world'];ids=np.where((raw[:,0]>.005)&(raw[:,0]<.13)&(raw[:,1]<-.025)&(raw[:,2]>1.17)&(raw[:,2]<1.35))[0]
def slice_segments(points,x):
    pts=points[t];z=pts[:,:,0]-x;active=(mi==1)&(z.min(1)<0)&(z.max(1)>0);result=[]
    for tri in pts[active]:
        cross=[]
        for i,j in [(0,1),(1,2),(2,0)]:
            a,c=tri[i],tri[j]
            if (a[0]-x)*(c[0]-x)<0:
                q=a+(c-a)*(x-a[0])/(c[0]-a[0]);cross.append([-q[1]*1000,q[2]*1000])
        if len(cross)==2:result.append(cross)
    return result
im=Image.new('RGB',(1620,1200),'white');draw=ImageDraw.Draw(im);font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',16);small=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',10)
draw.text((12,8),'ACTUAL EVALUATED triangle sections; gray=fixed core, blue=current G, red=C. mm in world, no per-view fit.',font=font,fill='black')
for n,x in enumerate([.025,.04,.055,.07,.085,.10]):
    ox=(n%3)*540+40;oy=(n//3)*570+65
    def screen(q):return (ox+(q[0]-40)*3.2,oy+(1350-q[1])*2.7)
    for y in range(1170,1351,10):
        draw.line([screen((40,y)),screen((180,y))],fill='#e5e5e5');draw.text((ox-34,screen((40,y))[1]-5),str(y),fill='black',font=small)
    draw.text((ox,oy-25),f'x={x*1000:.0f}mm; controls within2.5mm',font=font,fill='black')
    for points,color,label in [(g['world'],'#7b8b91','fixed core'),(v,'#334d9b','current G'),(b['world'],'#c34632','C')]:
        for segment in slice_segments(points,x):
            if all(1165<q[1]<1351 and 38<q[0]<182 for q in segment):draw.line([screen(q) for q in segment],fill=color,width=2)
    near=ids[abs(raw[ids,0]-x)<.0025]
    for i in near:
        a,c=screen((-raw[i,1]*1000,raw[i,2]*1000));draw.ellipse((a-2,c-2,a+2,c+2),fill='#334d9b');draw.text((a+3,c),str(i),font=small,fill='#334d9b')
im.save(P/'attachment-sections-current-C.png')
im=Image.new('RGB',(1700,1100),'white');draw=ImageDraw.Draw(im)
edges=d['raw_edges'];roi=np.isin(edges,ids).all(1)
for n,axes in enumerate([(0,2),(1,2)]):
    r=raw[ids][:,axes]*1000;lo=r.min(0);hi=r.max(0);scale=min(750/(hi[0]-lo[0]),1000/(hi[1]-lo[1]));ox=n*850+40
    def screen(q):return (ox+(q[0]-lo[0])*scale,60+(hi[1]-q[1])*scale)
    draw.text((ox,10),'ACTUAL raw cage '+str(axes),font=font,fill='black')
    for seg in raw[edges[roi]][:,:,axes]*1000:draw.line([screen(q) for q in seg],fill='#999999')
    for i in ids:
        a,c=screen(raw[i,list(axes)]*1000);draw.ellipse((a-2,c-2,a+2,c+2),fill='#334d9b');draw.text((a+3,c),str(i),font=small,fill='black')
im.save(P/'attachment-control-neighborhood-C-repeated.png');print('ATTACHMENT_SECTIONS_DONE',flush=True)
