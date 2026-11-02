"""Source-picked visible paths and actual 3D mesh/control projections. DATA only."""
from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;spec=json.loads((P/'source_paths_v06.json').read_text());data=np.load(P/'locks.npz');src=Image.open('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/references/received/mia-body-v06-confirmed-20261102.png');colors=[(57,145,200),(182,113,210),(67,179,130),(226,158,44),(224,90,79),(83,181,191)];f=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18);sm=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14);board=Image.new('RGB',(1800,860),(237,241,244));dr=ImageDraw.Draw(board);crop=src.crop((750,50,1120,420)).resize((740,740),Image.Resampling.LANCZOS);board.paste(crop,(0,50));dr.text((12,15),'FULL v06 rear paths / original aspect / manual source control picks',font=f,fill=(20,30,40))
for row,color in zip(spec['locks'],colors):
 p=[((u-750)*2,(v-50)*2+50) for u,v in row['source_uv']];dr.line(p,fill=color,width=3)
 for xy in p:dr.ellipse((xy[0]-3,xy[1]-3,xy[0]+3,xy[1]+3),fill=color)
 dr.text((p[-1][0]+5,p[-1][1]),row['name'].replace('_',' '),font=sm,fill=color,stroke_width=1,stroke_fill=(20,30,40))
for x0,side,title in [(780,False,'Actual 3D back controls + closed mesh wire'),(1300,True,'Actual 3D profile / inferred depth')]:
 dr.text((x0,15),title,font=f,fill=(20,30,40));
 def project(p):return [(x0+240+(float(q[1])-.14)*1100 if side else x0+240-float(q[0])*1100,60+(1.72-float(q[2]))*1100) for q in p]
 for row,color in zip(spec['locks'],colors):
  name=row['name'];co=data[name+'_co'];center=data[name+'_center'];control=data[name+'_control'];nr=(len(co)-2)//16
  for j in [0,4,8,12]:dr.line(project(co[:nr*16].reshape(nr,16,3)[:,j]),fill=tuple(int(v*.65+85) for v in color),width=1)
  dr.line(project(center),fill=color,width=3);pts=project(control)
  for k,xy in enumerate(pts):dr.ellipse((xy[0]-3,xy[1]-3,xy[0]+3,xy[1]+3),fill=(100,100,100) if k<2 else color)
  dr.text((pts[-1][0]+4,pts[-1][1]),name.replace('_',' '),font=sm,fill=color)
dr.text((12,815),'Visible X/Z from the same whole-height uniform registration; gray root controls are buried attachment extensions to current higher bun.',font=f,fill=(20,30,40));dr.text((12,842),'These are real generated mesh/control projections, not final shaded artwork. Six asymmetric source paths, separate underlayers and foreground owners.',font=f,fill=(20,30,40));board.save(P/'SOURCE_3D_CURVES_VOLUME_DATA.png');print('SOURCE_VOLUME_DATA_READY')
