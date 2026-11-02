"""Actual mesh intersections and declared line air intervals, not field distance."""
from pathlib import Path
import json,hashlib,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;D=P.parent;sys.path.insert(0,str(D));import field
p=json.loads((D/'parameters.json').read_text(encoding='utf-8'));d=np.load(D/'sculpt07-D.npz');v=d['world'].astype(float);tri=d['triangles'];parts=v[tri];f,reg=field.make(p);norm=np.cross(parts[:,1]-parts[:,0],parts[:,2]-parts[:,0]);norm/=np.linalg.norm(norm,axis=1)[:,None];out=[];payload={};font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14);im=Image.new('RGB',(1200,900),'#202632');draw=ImageDraw.Draw(im)
for j,z in enumerate([1.26,1.28,1.30,1.32]):
    delta=parts[:,:,2]-z;ids=np.flatnonzero((delta.min(1)<0)&(delta.max(1)>0));segments=[];fis=[]
    for fi in ids:
        face=parts[fi];pts=[]
        for a,b in [(0,1),(1,2),(2,0)]:
            if (face[a,2]-z)*(face[b,2]-z)<0:pts.append(face[a]+(face[b]-face[a])*((z-face[a,2])/(face[b,2]-face[a,2])))
        if len(pts)==2:segments.append(pts);fis.append(fi)
    segments=np.asarray(segments);fis=np.asarray(fis);payload['z_'+str(z)]=segments;lines=[];x0=(j%2)*600;y0=(j//2)*450
    draw.text((x0+10,y0+8),'ACTUAL D right axilla Z%.3f'%z,font=font,fill='white')
    def xy(q):return (x0+50+(q[0]-.10)*1600,y0+54+(q[1]+.11)*1600)
    for xt in [.10,.15,.20,.25]:
        xx=xy([xt,-.11])[0];draw.line((xx,y0+48,xx,y0+390),fill='#414957');draw.text((xx-12,y0+394),'%.2f'%xt,font=small,fill='#b6c6d6')
    for yt in [-.10,-.05,0.,.05,.10]:
        yyplot=xy([.10,yt])[1];draw.line((x0+45,yyplot,x0+295,yyplot),fill='#414957');draw.text((x0+3,yyplot-7),'%+.2f'%yt,font=small,fill='#b6c6d6')
    plot=im.crop((x0+45,y0+48,x0+295,y0+390));plotdraw=ImageDraw.Draw(plot)
    for seg in segments:
        if seg[:,0].max()<.10 or seg[:,0].min()>.25:continue
        plotdraw.line([(xy(q)[0]-x0-45,xy(q)[1]-y0-48) for q in seg],fill='#75e6cb',width=2)
    im.paste(plot,(x0+45,y0+48))
    for yy in [-.035,0.,.035]:
        active=(segments[:,:,1].min(1)<yy)&(segments[:,:,1].max(1)>yy);ss=segments[active];ii=fis[active];xx=ss[:,0,0]+(ss[:,1,0]-ss[:,0,0])*((yy-ss[:,0,1])/(ss[:,1,1]-ss[:,0,1]));hits=sorted([(float(x),int(fi)) for x,fi in zip(xx,ii) if x>0],key=lambda q:q[0]);dedup=[]
        for q in hits:
            if not dedup or abs(q[0]-dedup[-1][0])>1e-7:dedup.append(q)
        air=[]
        for a,b in zip(dedup[::2],dedup[1::2]):
            if a[0]<.26 and b[0]>.10:air.append(dict(x_interval_m=[a[0],b[0]],width_m=b[0]-a[0],boundary_triangle_ids=[a[1],b[1]]))
        detailed=[]
        for x,fi in dedup:
            point=np.array([[x,yy,z]]);vals={name:float(field.evaluate(expr,point)[0]) for name,expr in reg.items()};detailed.append(dict(point=[x,yy,z],triangle=fi,actual_geometric_normal=norm[fi].tolist(),nearest_field_term=min(vals,key=vals.get),field_term_values_approximate=vals))
        lines.append(dict(y=yy,starting_x0_inside_torso_assumption=True,positive_x_surface_hits=detailed,actual_air_intervals=air,limit='Widths are actual mesh intersections ALONG this declared horizontal line, not shortest 3D clearance or mandated anatomical gaps. Primitive field nearest-label is only a construction diagnostic, not anatomical ownership proof.'))
        line_y=xy([.10,yy])[1];draw.line((x0+45,line_y,x0+400,line_y),fill='#5c6573');label='Y%+.3f: '%yy+(','.join('%.2fmm'%(a['width_m']*1000) for a in air) if air else 'no line gap');draw.text((x0+405,line_y-8),label,font=small,fill='white')
        for a in air:draw.line((xy([a['x_interval_m'][0],yy]),xy([a['x_interval_m'][1],yy])),fill='#ffbc68',width=4)
    out.append(dict(z=z,actual_segments=len(segments),line_samples=lines));draw.text((x0+12,y0+420),'Equal1600px/m axes; X/Y metres. Anterior −Y up; one merged actor.',font=small,fill='white')
im.save(P/'actual-axilla-sections.png');np.savez_compressed(P/'actual-axilla-sections.npz',**payload)
(P/'actual-axilla-sections.json').write_text(json.dumps(dict(mesh_sha256=hashlib.sha256((D/'sculpt07-D.npz').read_bytes()).hexdigest(),sections=out,diagram_x_pixels_per_metre=1600,diagram_y_pixels_per_metre=1600,diagram_axes_equal_scale=True,arbitrary_airpoints_not_targets=True,field_values_not_exact_distances=True,component_field_invariance_not_final_surface_invariance=True,status='Actual section/line geometry only; intact/cutaway visual anatomy review required.'),indent=2)+'\n',encoding='utf-8');print('D_ACTUAL_AXILLA_SECTIONS_DONE',json.dumps([dict(z=r['z'],lines=[dict(y=q['y'],air_width_mm=[a['width_m']*1000 for a in q['actual_air_intervals']]) for q in r['line_samples']]) for r in out]),flush=True)
