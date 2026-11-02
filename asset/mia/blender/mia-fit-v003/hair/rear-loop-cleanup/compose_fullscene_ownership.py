"""Flat technical ownership visualization of actual full-scene CPU ray results."""
from pathlib import Path
import numpy as np,json
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;d=np.load(P/'fullscene-family-ownership-DATA.npz');f=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16);board=Image.new('RGB',(640*5,760),(237,241,244));dr=ImageDraw.Draw(board);record={}
for j,name in enumerate(['000','003','021','018','back_full']):
 o=d[name+'_owner'];n=d[name+'_normal'];shade=np.clip(.38+.55*np.abs(n[:,:,1]),0,1);rgb=np.repeat(shade[:,:,None],3,2)*255;rgb[o==0]=[42,48,53];rgb[o==2]*=[1.0,.9,.83];rgb[o==4]=[238,56,49];im=Image.fromarray(rgb.astype(np.uint8)).resize((640,640),Image.Resampling.NEAREST);board.paste(im,(640*j,45));dr.text((640*j+12,14),name+' / complete family in red',font=f,fill=(20,30,40));ys,xs=np.where(o==4);record[name]=dict(selected_firsthit_pixels=len(xs),image_pixels=o.size,pixel_bounds=[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())] if len(xs) else None)
 if len(xs):
  x,y=float(xs.mean())*640/384+640*j,float(ys.mean())*640/384+45;dr.ellipse((x-16,y-16,x+16,y+16),outline=(255,210,30),width=2)
 dr.text((640*j+12,701),str(len(xs))+' selected pixels of147456 (not area proof)',font=small,fill=(20,30,40))
dr.text((12,735),'Full-scene CPU ownership DATA, not shader/art render. Red only pure Rear_Waves U family; source forelocks/bangs/braid/bun untouched.',font=small,fill=(20,30,40));board.save(P/'fullscene-front-profile-ownership-DATA.png');(P/'fullscene-ownership-pixel-counts-DATA.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record)
