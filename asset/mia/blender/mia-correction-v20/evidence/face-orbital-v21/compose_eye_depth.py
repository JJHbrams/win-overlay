"""Technical crop sheets from real Blender renders; no model or artwork editing."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np,json
ROOT=Path(__file__).resolve().parent
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',24)
crops={'front':(350,630,1050,960),'left45':(290,630,990,960),'profile90':(200,630,900,960)}
def sheet(folder,variants,views,name):
 out=Image.new('RGB',(700*len(variants),390*len(views)),(235,235,235));draw=ImageDraw.Draw(out)
 for row,view in enumerate(views):
  for col,label in enumerate(variants):
   src=Image.open(folder/(label+'_'+view+'.png')).convert('RGB').crop(crops[view])
   out.paste(src,(col*700,row*390+50));draw.text((col*700+12,row*390+12),label+' / '+view,font=font,fill=(10,10,10))
 out.save(folder/name)
folder=ROOT/'eye-depth-diagnostic';variants=['retreat_1p5','retreat_0p5','baseline','advance_0p5','advance_1p5']
sheet(folder,variants,['front','left45','profile90'],'position-comparison.png')
metrics=[]
for view in crops:
 base=np.asarray(Image.open(folder/('baseline_'+view+'.png')).convert('RGB')).astype(int)
 for label in variants:
  a=np.asarray(Image.open(folder/(label+'_'+view+'.png')).convert('RGB')).astype(int);delta=np.max(abs(a-base),axis=2);ys,xs=np.where(delta>1)
  metrics.append({'view':view,'variant':label,'pixels_changed_more_than_1_code':int(len(xs)),'changed_bbox':[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)] if len(xs) else None})
(folder/'pixel-difference.json').write_text(json.dumps(metrics,indent=2))
folder=ROOT/'eye-curvature-diagnostic'
sheet(folder,['depth_0p9','depth_1p0','depth_1p1'],['left45','profile90'],'curvature-comparison.png')
