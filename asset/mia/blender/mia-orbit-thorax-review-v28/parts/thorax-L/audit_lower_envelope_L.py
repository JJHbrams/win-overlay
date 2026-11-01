"""Actual evaluated lower-envelope samples and core/skin plane sections."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np,json
P=Path(__file__).parent;O=P/'source-soft-L';font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
report={};curves={}
for tag in ['J','K','L']:
 d=np.load(P/f'source-soft-{tag}/evaluated-skin.npz');c=np.load(P/f'source-soft-{tag}/evaluated-core.npz')['vertices'];v=d['vertices'];active=np.linalg.norm(v-c,axis=1)>.005
 select=active&(v[:,0]>.005)&(v[:,0]<.115)&(c[:,1]<-.025)&(c[:,2]>1.22)&(c[:,2]<1.34);rows=[]
 for x in np.arange(.01,.105,.0025):
  m=select&(abs(v[:,0]-x)<.00125)
  if m.any():rows.append({'x_m':float(x),'actual_min_skin_z_m':float(v[m,2].min()),'sample_count':int(m.sum())})
 curves[tag]=rows;report[tag]={'selection':'Actual corresponding evaluated skin-core offset >5mm, right anterior breast, coreZ1.22..1.34; threshold excludes vanishing attachment. This is independent of light but is not a full skin silhouette tracing.','bins':rows}
 path=P/f'renders/{tag}-core-plus-soft/owner-clay/profile.png'
 if not path.exists():path=P/f'renders/{tag}-core-plus-soft/geometry-clay/profile.png'
 alpha=np.array(Image.open(path).convert('RGBA'))[:,:,3];points=[]
 for y in range(280,421):
  xx=np.flatnonzero(alpha[y]>128)
  if len(xx):points.append((int(xx.min()),y))
 apex=min(points);waisty=round(400+(1.24-1.145)*1250);waistx=int(np.flatnonzero(alpha[waisty]>128).min())
 report[tag]['actual_profile_alpha']={'apex_x_px':apex[0],'apex_y_px':apex[1],'apex_z_m':1.24+(400-apex[1])*.0008,'own_waist_front_px':waistx,'apex_projection_relative_own_waist_px':waistx-apex[0],'camera':'Actual ORTHO.64 700x800 profile, targetZ1.24; alpha128 boundary; 1px uncertainty.'}
im=Image.new('RGB',(1000,580),'white');dr=ImageDraw.Draw(im);dr.text((25,12),'Actual evaluated lower envelope: J / K rejected, L frozen review',font=font,fill='black')
for z in np.arange(1.225,1.281,.005):
 y=500-(z-1.225)/.055*400;dr.line((100,y,950,y),fill=(220,220,220));dr.text((20,y-9),f'{z:.3f}',font=font,fill='black')
for x in np.arange(.01,.101,.01):
 xx=100+(x-.01)/.09*850;dr.line((xx,100,xx,500),fill=(235,235,235));dr.text((xx-15,510),str(round(x*1000)),font=font,fill='black')
for k,(tag,col) in enumerate([('J',(130,130,130)),('K',(120,70,160)),('L',(210,90,20))]):
 points=[(100+(r['x_m']-.01)/.09*850,500-(r['actual_min_skin_z_m']-1.225)/.055*400) for r in curves[tag]]
 if len(points)>1:dr.line(points,fill=col,width=4)
 dr.text((100+200*k,60),tag,font=font,fill=col)
dr.text((180,550),'WorldX mm; 2.5mm bins, active tissue >5mm. Geometry sample is not art acceptance.',font=font,fill='black');im.save(O/'actual-lower-envelope-J-K-L.png')
(O/'lower-envelope-audit.json').write_text(json.dumps(report,indent=2),encoding='utf8')

def segments(v,f,axis,value):
 t=v[f];good=(t[:,:,axis].min(1)<value)&(t[:,:,axis].max(1)>value);t=t[good];result=[]
 for tri in t:
  pts=[]
  for a,b in zip(tri,np.roll(tri,-1,axis=0)):
   da=a[axis]-value;db=b[axis]-value
   if da*db<0:pts.append(a+(b-a)*(-da)/(db-da))
  if len(pts)==2:result.append(pts)
 return result
canvas=Image.new('RGB',(1500,960),'white');draw=ImageDraw.Draw(canvas);draw.text((20,10),'ACTUAL evaluated G3 core (black) + L skin (orange), same polygon loops',font=font,fill='black')
sectionrecords=[]
for j,(axis,value) in enumerate([(0,.025),(0,.055),(0,.085),(2,1.245),(2,1.275),(2,1.310)]):
 col=j%3;row=j//3;ox=col*500;oy=45+row*445
 draw.text((ox+15,oy+5),('Sagittal X=' if axis==0 else 'Horizontal Z=')+str(value)+' m',font=font,fill='black')
 if axis==0:axes=[1,2];bounds=[-.16,.08,1.20,1.35]
 else:axes=[0,1];bounds=[-.135,.135,-.16,.08]
 x0,x1,y0,y1=bounds
 def pixel(q):return (ox+25+(q[axes[0]]-x0)/(x1-x0)*450,oy+420-(q[axes[1]]-y0)/(y1-y0)*370)
 counts={}
 for role,color,width in [('core',(30,30,30),2),('skin',(215,90,20),2)]:
  d=np.load(O/f'evaluated-{role}.npz');ss=segments(d['vertices'],d['triangles'],axis,value);counts[role]=len(ss)
  for a,b in ss:
   if all(x0<=q[axes[0]]<=x1 and y0<=q[axes[1]]<=y1 for q in [a,b]):draw.line([pixel(a),pixel(b)],fill=color,width=width)
 sectionrecords.append({'plane_axis':axis,'plane_value_m':value,'segment_counts':counts,'display_bounds':bounds})
canvas.save(O/'actual-core-L-sections.png');(O/'section-metadata.json').write_text(json.dumps({'method':'Exact triangle-plane intersections of reopened evaluated core/skin; no invented clean core, no section fitting. Black core and orange skin are actual contributions to final L.','sections':sectionrecords},indent=2))
print('L_GEOMETRY_EVIDENCE',json.dumps({t:r['actual_profile_alpha'] for t,r in report.items()}),flush=True)
