"""Bake geometry-aligned generated pigment plates into valid longitudinal UVs.

Plate pixels are authored inputs, never screenshots or model evidence. Visibility
is precomputed against the frozen actual mesh; unseen texels keep alpha zero.
"""
import json,sys,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
P=Path(__file__).parent/'sculpt2';OUT=P.parent/'paint1';OUT.mkdir(exist_ok=True)
back,profile=map(Path,sys.argv[1:3]);N=1024
def image(path):return np.asarray(Image.open(path).convert('RGBA'),dtype=float)/255
def linear(x):return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)
def srgb(x):return np.where(x<=.0031308,x*12.92,1.055*np.maximum(x,0)**(1/2.4)-.055)
plates={};masks={}
for view,path in [('back',back),('profile',profile)]:
 im=image(path);plates[view]=linear(im[...,:3]);masks[view]=image(P/('paintplate_'+view+'.png'))[...,3]*im[...,3]
def sample(arr,uv):
 h,w=arr.shape[:2];x=np.clip(uv[:,0]*(w-1),0,w-1);y=np.clip((1-uv[:,1])*(h-1),0,h-1);xi=x.astype(int);yi=y.astype(int);xx=np.minimum(xi+1,w-1);yy=np.minimum(yi+1,h-1);a=x-xi;b=y-yi
 if arr.ndim==3:a=a[:,None];b=b[:,None]
 return arr[yi,xi]*(1-a)*(1-b)+arr[yi,xx]*a*(1-b)+arr[yy,xi]*(1-a)*b+arr[yy,xx]*a*b
reports=[]
for row in json.loads((P/'paint-meshes.json').read_text()):
 d=np.load(row['npz']);out=np.zeros((N,N,4),dtype=float);filled=np.zeros((N,N),bool)
 for tri,uv in zip(d['triangles'],d['uv']):
  xy=np.stack([uv[:,0]*(N-1),(1-uv[:,1])*(N-1)],axis=1)
  lo=np.maximum(0,np.floor(xy.min(axis=0)).astype(int));hi=np.minimum(N-1,np.ceil(xy.max(axis=0)).astype(int))
  if np.any(hi<lo):continue
  xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1));pts=np.stack([xx.ravel(),yy.ravel()],1)
  ab=xy[1]-xy[0];ac=xy[2]-xy[0];den=ab[0]*ac[1]-ab[1]*ac[0]
  if abs(den)<1e-10:continue
  q=pts-xy[0];b=(q[:,0]*ac[1]-q[:,1]*ac[0])/den;c=(ab[0]*q[:,1]-ab[1]*q[:,0])/den;a=1-b-c;inside=(a>=-1e-6)&(b>=-1e-6)&(c>=-1e-6)
  if not inside.any():continue
  pts=pts[inside];bc=np.stack([a[inside],b[inside],c[inside]],1);col=np.zeros((len(pts),3));weights=np.zeros(len(pts))
  for view in ['back','profile']:
   puv=bc@d[view+'_uv'][tri];wt=bc@d[view+'_weight'][tri];wt*=sample(masks[view],puv);wt*=((puv>=0)&(puv<=1)).all(1)
   col+=sample(plates[view],puv)*wt[:,None];weights+=wt
  valid=weights>.015;col[valid]/=weights[valid,None];col[~valid]=0
  px,py=pts[:,0],pts[:,1];out[py,px,:3]=srgb(col);out[py,px,3]=np.clip(weights/.12,0,1);filled[py,px]=True
 # A four-texel gutter copies the actual atlas edge; it does not invent detail.
 known=filled.copy()
 for _ in range(4):
  nextknown=known.copy()
  for axis,shift in [(0,1),(0,-1),(1,1),(1,-1)]:
   neighbors=np.roll(known,shift,axis);take=(~nextknown)&neighbors;out[take]=np.roll(out,shift,axis)[take];nextknown[take]=True
  known=nextknown
 path=OUT/(row['owner']+'_Pigment1024.png');Image.fromarray(np.uint8(np.clip(out,0,1)*255+.5),'RGBA').save(path)
 reports.append({'owner':row['owner'],'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'resolution':[N,N],'painted_fraction_of_uv_surface':float((out[...,3][filled]>.05).mean()),'color_space':'sRGB','route':'V24_GatherPaintUV -> generated geometry-aligned pigment RGBA -> alpha fallback to inherited ash -> scene-light toon -> Emission'})
report={'source_native_sha256':json.loads((P/'paint-projection.json').read_text())['source_native_sha256'],'maps':reports,'plates':[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [back,profile]],'limits':['Generated plates are input, not model evidence','Paint applies only to the three new gathered owners','Unseen projected texels retain unpainted ash fallback','No ear/nape repair or main-hair detail claim']}
(OUT/'pigment-manifest.json').write_text(json.dumps(report,indent=2));print(json.dumps(reports,indent=2))
