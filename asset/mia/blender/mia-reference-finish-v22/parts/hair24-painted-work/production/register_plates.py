import numpy as np,json
from PIL import Image
from pathlib import Path
P=Path(__file__).parent/'sculpt2';rows=[]
for view in ['back','profile']:
 src=Image.open(P/('generated_'+view+'_pigment.png')).convert('RGBA');target=Image.open(P/('paintplate_'+view+'.png')).convert('RGBA')
 a=np.asarray(src.resize((256,256)),float)[...,3]/255;b=np.asarray(target.resize((256,256)),float)[...,3]/255
 alpha=Image.fromarray(a.astype(np.float32),'F')
 def loss(p):
  s,x,y=p
  if not .6<s<1.3:return 10
  out=np.asarray(alpha.transform((256,256),Image.Transform.AFFINE,(1/s,0,-x/s,0,1/s,-y/s),resample=Image.Resampling.BILINEAR));inter=np.minimum(out,b).sum();union=np.maximum(out,b).sum();return 1-inter/union
 by,bx=np.where(b>.5);ay,ax=np.where(a>.5);scale=((b>.5).sum()/(a>.5).sum())**.5;start=[scale,bx.mean()-scale*ax.mean(),by.mean()-scale*ay.mean()]
 best=np.array(start);score=loss(best)
 for step in [.06,.03,.015,.0075,.00375,.001875,.0009375]:
  for _ in range(4):
   improved=False
   for axis,delta in [(0,step),(1,step*70),(2,step*70)]:
    for direction in [-1,1]:
     probe=best.copy();probe[axis]+=direction*delta;value=loss(probe)
     if value<score:best=probe;score=value;improved=True
   if not improved:break
 s,tx,ty=best
 # Registration is uniform scale + translation only. No anisotropic scaling.
 source_ratio=src.width/1024;sfull=s/source_ratio;tx*=4;ty*=4
 registered=src.transform((1024,1024),Image.Transform.AFFINE,(1/sfull,0,-tx/sfull,0,1/sfull,-ty/sfull),resample=Image.Resampling.BICUBIC)
 registered.save(P/('registered_'+view+'_pigment.png'))
 rows.append({'view':view,'source_size':list(src.size),'uniform_scale':sfull,'translation_xy':[tx,ty],'rotation_degrees':0,'mask_soft_iou':1-score,'note':'Generated plate input globally registered to frozen actual alpha silhouette. No mesh or per-feature warp. Actual target mask used during bake.'})
(P/'pigment-registration.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
