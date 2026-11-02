"""Original-source context and CPU ownership comparisons. Not art renders."""
from pathlib import Path
import numpy as np,json
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;size=384;labels=np.load(P/'global-components.npz')['face_component'];f=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16)
configs=[('firsthit-data.npz','Baseline'),('masked-firsthit-data.npz','Six complete front skins only / rejected'),('backing-plus-six-firsthit-data.npz','Six skins + complete backing branch / DATA')]
if (P/'logical-family-firsthit-data.npz').exists():configs.append(('logical-family-firsthit-data.npz','Whole logical family / DATA'))
out=Image.new('RGB',(768*len(configs),850),(237,241,244));draw=ImageDraw.Draw(out)
for k,(name,title) in enumerate(configs):
 d=np.load(P/name);face=d['loop_close_face'];normal=d['loop_close_normal'];shade=np.clip(.23+.64*np.abs(normal[:,:,1]),0,1);rgb=np.uint8(np.repeat(shade[:,:,None],3,axis=2)*255);rgb[face<0]=(42,48,53);im=Image.fromarray(rgb).resize((768,768),Image.Resampling.NEAREST);out.paste(im,(768*k,40));draw.text((768*k+10,12),title,font=f,fill=(20,30,40))
draw.text((10,819),'CPU Main-only first-hit geometry DATA; no color/shader/art/saved-native result. Exact same camera; original coordinates held.',font=f,fill=(20,30,40));out.save(P/'topology-family-before-after-DATA.png')

# Show all newly exposed small owners on the six-plus-backing view.
d=np.load(P/'logical-family-firsthit-data.npz');face=d['loop_close_face'];normal=d['loop_close_normal'];shade=np.clip(.23+.64*np.abs(normal[:,:,1]),0,1);rgb=np.uint8(np.repeat(shade[:,:,None],3,axis=2)*255);rgb[face<0]=(42,48,53);comp=np.full_like(face,-1);comp[face>=0]=labels[face[face>=0]];rng=np.random.default_rng(184)
for k in np.unique(comp):
 if k<0 or k==488:continue
 rgb[comp==k]=rng.integers(70,230,size=3)
im=Image.fromarray(rgb).resize((1152,1152),Image.Resampling.NEAREST);dr=ImageDraw.Draw(im)
for k in np.unique(comp):
 yy,xx=np.where(comp==k)
 if k<0 or len(xx)<35:continue
 dr.text((float(np.median(xx))*3,float(np.median(yy))*3),str(k),font=small,fill='white',stroke_width=2,stroke_fill=(20,30,40))
im.save(P/'exposed-after-family-owners-DATA.png')
src=Image.open('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/references/mia-clean-master-v22.png').convert('RGB');context=Image.new('RGB',(1200,700),(237,241,244));dr=ImageDraw.Draw(context)
for k,(title,box) in enumerate([('Approved v22 back / original aspect',(748,0,942,230)),('Approved v22 profile / original aspect',(510,0,710,230))]):
 crop=src.crop(box);scale=min(580/crop.width,600/crop.height);crop=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS);context.paste(crop,(600*k+(600-crop.width)//2,50));dr.text((600*k+15,15),title,font=f,fill=(20,30,40))
dr.text((15,663),'Natural layered pointed waves; no matching suspended central U bridge. Uncalibrated source context only.',font=f,fill=(20,30,40));context.save(P/'source-back-profile-context.png')
print('TOPOLOGY_SOURCE_CONTEXT_READY')
