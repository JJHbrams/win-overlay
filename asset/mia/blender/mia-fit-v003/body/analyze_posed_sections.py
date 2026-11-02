"""Actual triangle-plane sections and tangent data, not an art render."""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;O=P/'posed-target'

def section_segments(world,triangles,materials,x):
    tri=world[triangles];d=tri[:,:,0]-x
    active=(materials==1)&(d.min(1)<0)&(d.max(1)>0)&(tri[:,:,2].max(1)>1.15)&(tri[:,:,2].min(1)<1.37)
    out=[]
    for face in tri[active]:
        points=[]
        for a,b in [(0,1),(1,2),(2,0)]:
            p,q=face[a],face[b]
            if (p[0]-x)*(q[0]-x)<0:
                points.append((p+(q-p)*(x-p[0])/(q[0]-p[0]))[[1,2]])
        if len(points)==2:out.append(points)
    return np.asarray(out)

def front_envelope(segments,z):
    y=np.full(len(z),np.nan)
    for i,zz in enumerate(z):
        lo=segments[:,:,1].min(1);hi=segments[:,:,1].max(1)
        a=segments[(lo<=zz)&(hi>=zz)]
        if len(a):
            den=a[:,1,1]-a[:,0,1];valid=abs(den)>1e-12;a=a[valid];den=den[valid]
            if len(a):y[i]=np.min(a[:,0,0]+(a[:,1,0]-a[:,0,0])*(zz-a[:,0,1])/den)
    return y

def analyze(number='01'):
    baseline=np.load(P/'current-body-limit.npz');candidate=np.load(O/f'evaluated-{number}.npz');datasets=[('Current4dc1',baseline['world'],'#6578af')]
    if number!='01':datasets.append(('Rejected01',np.load(O/'evaluated-01.npz')['world'],'#bb9a5b'))
    datasets.append(('Target'+number,candidate['world'],'#c44731'))
    t=candidate['triangles'];mi=candidate['triangle_materials'];font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',16);small=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',12)
    im=Image.new('RGB',(1500,1040),'white');dr=ImageDraw.Draw(im);dr.text((12,8),'ACTUAL EVALUATED FRONT SECTIONS; blue=current4dc1, red=target'+number+'. No painted/rendered substitute.',font=font,fill='black');rows=[]
    for n,x in enumerate([.025,.035,.045,.060,.080,.100]):
        ox=(n%3)*500+55;oy=(n//3)*500+50
        def screen(y,z):return (ox+(-y*1000-65)*3.6,oy+(1360-z*1000)*2.1)
        for zz in np.arange(1.16,1.361,.01):
            dr.line([screen(-.065,zz),screen(-.170,zz)],fill='#e5e5e5')
            dr.text((ox-45,screen(-.065,zz)[1]-6),str(round(zz*1000)),font=small,fill='black')
        dr.text((ox,oy-20),f'X={x*1000:.0f}mm; Z mm / projection mm',font=font,fill='black')
        for label,world,color in datasets:
            seg=section_segments(world,t,mi,x)
            for a,b in seg:
                if a[0]<-.055 and b[0]<-.055:dr.line([screen(*a),screen(*b)],fill=color,width=2)
            z=np.arange(1.17,1.311,.001);y=front_envelope(seg,z);tan=np.degrees(np.arctan2(-np.gradient(y,z),np.ones(len(z))));turn=np.abs(np.diff(tan,2))
            clean=lambda a:[float(v) if np.isfinite(v) else None for v in a]
            rows.append(dict(x=x,label=label,z_mm=(z*1000).tolist(),front_y_mm=clean(y*1000),tangent_degrees=clean(tan),max_discrete_second_tangent_difference_degrees=float(np.nanmax(turn)) if np.isfinite(turn).any() else None,note='Frontmost actual triangle-plane intersection. Derivatives are sampled geometry diagnostics, not anatomical target angles; missing surface samples are null.'))
    im.save(O/f'evaluated-sections-{number}.png')
    (O/f'section-analysis-{number}.json').write_text(json.dumps(dict(sections=rows,status='Surface diagnosis only; no source/ART acceptance.'),indent=2)+'\n',encoding='utf-8')
    print('ACTUAL_EVALUATED_SECTIONS_DONE',number,flush=True)

if __name__=='__main__':
    import sys
    analyze(sys.argv[1] if len(sys.argv)>1 else '01')
