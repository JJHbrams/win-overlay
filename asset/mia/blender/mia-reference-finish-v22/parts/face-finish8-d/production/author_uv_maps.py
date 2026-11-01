"""Authored geometry-aligned pigment/masks, limited generated difference input.
No broad generated illumination, scalp, eye pixels or background is projected.
"""
import json,hashlib
from pathlib import Path
from collections import Counter
import numpy as np
from PIL import Image,ImageFilter,ImageDraw
ROOT=Path(__file__).resolve().parent;DATA=ROOT/'shape-b/paint-input';OUT=ROOT/'look-a/maps';OUT.mkdir(parents=True,exist_ok=True)
GEN=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v22/static-finish-8/face-paint-input/generated-pigment-plate.png')
d=json.loads((DATA/'projection-metadata.json').read_text());P=np.array(d['evaluated_vertices']);PX=np.array(d['pixel_vertices']);N=2048
pos=np.full((N,N,3),np.nan,np.float32);px=np.zeros((N,N,2),np.float32);valid=np.zeros((N,N),bool);skintri=[]
for tri in d['triangles']:
 if tri['material']!=7:continue
 ids=tri['vertices'];p=P[ids];n=np.cross(p[1]-p[0],p[2]-p[0]);norm=np.linalg.norm(n)
 if norm<1e-14:continue
 uv=np.array(tri['uv']['UVMap'])*N-.5
 lo=np.maximum(np.floor(uv.min(0)).astype(int),0);hi=np.minimum(np.ceil(uv.max(0)).astype(int),N-1)
 if np.any(hi<lo):continue
 x,y=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1));v0=uv[1]-uv[0];v1=uv[2]-uv[0];den=v0[0]*v1[1]-v0[1]*v1[0]
 if abs(den)<1e-9:continue
 dx=x-uv[0,0];dy=y-uv[0,1];b=(dx*v1[1]-dy*v1[0])/den;c=(v0[0]*dy-v0[1]*dx)/den;a=1-b-c;mask=(a>=-1e-5)&(b>=-1e-5)&(c>=-1e-5)
 yy=y[mask];xx=x[mask];w=np.stack([a[mask],b[mask],c[mask]],1);pp=w@p
 front=(~valid[yy,xx])|(pp[:,1]>=pos[yy,xx,1]);yy=yy[front];xx=xx[front];w=w[front];pp=pp[front]
 pos[yy,xx]=pp;px[yy,xx]=w@PX[ids];valid[yy,xx]=True;skintri.append(tri)
assert valid.sum()>10000,int(valid.sum())
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def linear(c):return np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
def srgb(c):return np.where(c<=.0031308,12.92*c,1.055*np.maximum(c,0)**(1/2.4)-.055)
def sample(im):
 xy=np.clip(px,0,1535);xx=np.rint(xy[:,:,0]).astype(int);yy=np.rint(xy[:,:,1]).astype(int);return im[yy,xx]
original=Image.open(ROOT/'shape-a/paint-input/actual-native-face-aligned.png').convert('RGBA');generated=Image.open(GEN).convert('RGBA');gen_size=generated.size;generated=generated.resize((1536,1536),Image.Resampling.LANCZOS)
origlin=linear(np.asarray(original)[:,:,:3]/255.);genlin=linear(np.asarray(generated)[:,:,:3]/255.);ratio=np.clip(sample(genlin)/np.maximum(sample(origlin),.02),.75,1.12)
old=np.load(DATA/'old-pigment-linear.npy');base=old.copy();x,y,z=np.nan_to_num(pos).transpose(2,0,1);ax=abs(x)
region=valid*smooth(.010,.042,y)*(1-smooth(.060,.074,ax))*smooth(1.467,1.482,z)*(1-smooth(1.573,1.590,z))
flat=np.zeros_like(base[:,:,:3]);flat[:]=[.92,.69,.60]
# Original generated/local shadows are removed from broad cheek/nose pigment.
# Crisp local strokes come from relative high-frequency paint, restricted to
# actual brow/lip skin; no eye carrier pixels or silhouette edges are sampled.
blur=linear(np.asarray(generated.filter(ImageFilter.GaussianBlur(24)))[:,:,:3]/255.)
detail=np.clip(sample(genlin)/np.maximum(sample(blur),.02),.22,1.08)
brow=smooth(.012,.019,ax)*(1-smooth(.055,.064,ax))*smooth(1.551,1.555,z)*(1-smooth(1.563,1.570,z))
lip=(1-smooth(.012,.018,ax))*smooth(1.489,1.492,z)*(1-smooth(1.498,1.502,z))
flat*=1+(detail-1)*np.maximum(brow,lip)[:,:,None]
# Small warm lip pigment, independent from broad facial lighting.
lipcolor=np.array([.80,.39,.36]);flat=flat*(1-.12*lip[:,:,None])+lipcolor*(.12*lip[:,:,None])
base[:,:,:3]=old[:,:,:3]*(1-region[:,:,None])+flat*region[:,:,None];base[:,:,3]=1
# Actual evaluated aperture boundary: derive lower arc from each hemisphere.
ec=Counter(tuple(sorted((t['vertices'][i],t['vertices'][(i+1)%3]))) for t in d['triangles'] for i in range(3))
boundary=sorted({i for e,n in ec.items() if n==1 for i in e});bp=P[boundary];curves=[];fat=np.zeros((N,N),np.float32);ink=fat.copy()
for sign in [-1,1]:
 q=bp[(bp[:,0]*sign>.013)&(bp[:,0]*sign<.059)&(bp[:,1]>.035)&(bp[:,2]>1.527)&(bp[:,2]<1.557)]
 bins=np.linspace(.014,.058,65);xs=[];zs=[]
 for a,b in zip(bins[:-1],bins[1:]):
  qq=q[(q[:,0]*sign>=a)&(q[:,0]*sign<b)]
  if len(qq):xs.append(float(np.mean(qq[:,0]*sign)));zs.append(float(qq[:,2].min()))
 assert len(xs)>20
 # Remove upper-only canthus tail; the center lower arc is measured, not guessed.
 curves.append({'side':sign,'x':xs,'lower_z':zs});lz=np.interp(ax,xs,zs);dist=lz-z
 taper=smooth(.016,.023,ax)*(1-smooth(.049,.058,ax));side=(x*sign>0)
 cres=smooth(-.0002,.0012,dist)*(1-smooth(.0032,.0080,dist))*taper*side*region
 fat=np.maximum(fat,.62*cres)
 line=np.exp(-((dist-.00065)/.00040)**2)*taper*side*region
 ink=np.maximum(ink,.48*line)
# Generated input contributes only bounded local pigment difference in the bags.
base[:,:,:3]*=1+(ratio-1)*fat[:,:,None]*.65
# Small nostril accents, rather than the inherited broad painted nose triangle.
nostril=np.exp(-((ax-.0034)/.00085)**2-((z-1.5158)/.00065)**2)*region
ink=np.maximum(ink,.30*nostril)
base[:,:,:3]=np.clip(base[:,:,:3],0,1.2)
np.save(OUT/'BasePigment_LINEAR.npy',base.astype(np.float32));np.save(OUT/'FatigueMask_LINEAR.npy',fat);np.save(OUT/'FineLineMask_LINEAR.npy',ink)
Image.fromarray(np.uint8(np.clip(srgb(base[:,:,:3]),0,1)[::-1]*255)).save(OUT/'BasePigment_sRGB_2048.png')
for name,a in [('FatigueMask',fat),('FineLineMask',ink),('PaintVisibility',region)]:Image.fromarray(np.uint8(np.clip(a,0,1)[::-1]*255)).save(OUT/(name+'_LINEAR_2048.png'))
layout=Image.new('RGB',(N,N),'#f1f0e8');draw=ImageDraw.Draw(layout)
for tri in d['triangles']:
 if tri['material']!=7:continue
 uv=np.array(tri['uv']['UVMap']);points=[(float(u*N),float((1-v)*N)) for u,v in uv];draw.line(points+[points[0]],fill='#75899e',width=1)
layout.save(OUT/'actual-skin-UV-layout-2048.png')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
(OUT/'map-authoring.json').write_text(json.dumps({'status':'NEW AUTHORED MAPS / ART UNAPPROVED','geometry':d['source'],'generated_input':{'path':str(GEN),'sha256':sha(GEN),'size':gen_size},'alignment':{'projection_plate_size':[1536,1536],'generated_uniform_scale':1536/gen_size[0],'feature_warp':False,'scope':'Actual skin triangles only; generated difference restricted to lower-lid pigment; brow/lip relative detail only. No scalp, eye, background or broad cast-light projection.'},'uv':'Existing actual UVMap retained; checker and shader consumption pending.','resolution':[N,N],'rasterized_texels':int(valid.sum()),'painted_texels':int((region>.01).sum()),'lower_arcs':curves,'channels':{'BasePigment':'linear RGB pigment with source-style local brow/lip detail','FatigueMask':'linear scalar actual lower-aperture crescent; consumed brown-mauve multiplication','FineLineMask':'linear scalar lower-lid and small nostril accents; consumed dark-pigment multiplication'},'recipe':{'path':str(Path(__file__)),'sha256':sha(__file__)},'limits':['Generated input is a paint suggestion, never actual render evidence.','No new fine-detail claim from resampling1254px input to2K UV. New curves/masks are authored at geometry scale.','Limited material/UV review required.']},indent=2));print('MAPS_AUTHORED',int(valid.sum()))
