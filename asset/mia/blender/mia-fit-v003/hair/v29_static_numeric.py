"""Evaluate the frozen old static pigment data for numerical rebake/audit only."""
from pathlib import Path
import json,numpy as np,hashlib
from PIL import Image
class StaticPigment:
 def __init__(self,folder):
  folder=Path(folder);self.cfg=json.loads((folder/'static-pigment.json').read_text());self.N={r['name']:r for r in self.cfg['nodes']};self.images={}
  for name,row in self.cfg['images'].items():
   file=folder/row['file'];assert hashlib.sha256(file.read_bytes()).hexdigest()==row['sha256'];self.images[name]=np.array(Image.open(file).convert('RGBA'))
 def sample(self,name,q):
  im=self.images[name];h,w=im.shape[:2];x=q[:,0]*w-.5;y=(1-q[:,1])*h-.5;x0=np.floor(x).astype(int);y0=np.floor(y).astype(int);fx=x-x0;fy=y-y0;result=np.zeros((len(q),4));srgb=self.cfg['images'][name]['colorspace']=='sRGB'
  for dx,dy,wt in [(0,0,(1-fx)*(1-fy)),(1,0,fx*(1-fy)),(0,1,(1-fx)*fy),(1,1,fx*fy)]:
   ix=np.clip(x0+dx,0,w-1);iy=np.clip(y0+dy,0,h-1);a=im[iy,ix].astype(float)/255
   if srgb:a[:,:3]=np.where(a[:,:3]<=.04045,a[:,:3]/12.92,((a[:,:3]+.055)/1.055)**2.4)
   result+=a*wt[:,None]
  return result
 def evaluate(self,q):
  N=self.N;base=self.sample('MIA_V17_Pixal_Repacked4096.003',q);signals=self.sample('MIA_V22_AuthoredStrandSignals',q);generated=self.sample('MIA_V22_GeneratedSelectiveLockPigment',q);lum=base[:,:3]@np.array([.2126,.7152,.0722]);r=N['V22_OwnedAshPalette']['ramp'];positions=np.array([e['position'] for e in r['elements']]);colors=np.array([e['color'][:3] for e in r['elements']]);i=np.clip(np.searchsorted(positions,lum,side='right')-1,0,len(positions)-2);t=np.clip((lum-positions[i])/(positions[i+1]-positions[i]),0,1);assert r['interpolation']=='EASE';t=t*t*(3-2*t);palette=colors[i]*(1-t[:,None])+colors[i+1]*t[:,None];clean=N['V22_CLEAN_PALETTE_72_PERCENT'];factor=clean['inputs']['0'];a=np.array(clean['inputs']['1'][:3])*(1-factor)+palette*factor;ink=N['믹스 (레거시).001'];assert ink['blend_type']=='MIX';a=a*(1-signals[:,0,None])+np.array(ink['inputs']['2'][:3])*signals[:,0,None];high=N['믹스 (레거시).002'];assert high['blend_type']=='ADD';a+=np.array(high['inputs']['2'][:3])*signals[:,1,None]
  if high.get('use_clamp'):a=np.clip(a,0,1)
  return a*(1-generated[:,3,None])+generated[:,:3]*generated[:,3,None]
