from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
O=Path(__file__).resolve().parent;G=np.load(O/'projection-geometry.npz');cams=json.loads((O/'projection-cameras.json').read_text());names=['Front','Profile','Back','LeftOblique','RightOblique']
paint=Image.open(O/'hair-paintover.png').convert('RGB');tw=paint.width//3;th=paint.height//2
views=[]
for i,name in enumerate(names):
 tile=paint.crop(((i%3)*tw,(i//3)*th,(i%3+1)*tw,(i//3+1)*th)).resize((1000,1000),Image.Resampling.LANCZOS)
 rgb=np.asarray(tile,np.float32)[::-1]/255;linear=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
 views.append({'name':name,'paint':linear,'encoded':rgb,'depth':np.load(O/('depth_'+name+'.npy')),'light':np.load(O/('light_'+name+'.npy')),'inv':np.array(cams[name]['inverse']),'scale':cams[name]['scale'],'normal':np.array(cams[name]['matrix'])[:3,2]})
N=4096;out=np.zeros((N,N,4),np.float32);occupied=np.zeros((N,N),bool);winner=np.zeros((N,N),np.uint8);coords=G['coords'];normals=G['normals']
def sample(a,x,y):
 ix=np.clip(np.floor(x).astype(int),0,998);iy=np.clip(np.floor(y).astype(int),0,998);fx=(x-ix).clip(0,1);fy=(y-iy).clip(0,1)
 return a[iy,ix]*(1-fx)[...,None]*(1-fy)[...,None]+a[iy,ix+1]*fx[...,None]*(1-fy)[...,None]+a[iy+1,ix]*(1-fx)[...,None]*fy[...,None]+a[iy+1,ix+1]*fx[...,None]*fy[...,None]
points=[];normal_points=[];pixels=[]
for ti,(ids,uv) in enumerate(zip(G['triangles'],G['tri_uv'])):
 v=uv*N-.5;x0=max(0,int(np.floor(v[:,0].min())));x1=min(N-1,int(np.ceil(v[:,0].max())));y0=max(0,int(np.floor(v[:,1].min())));y1=min(N-1,int(np.ceil(v[:,1].max())))
 if x1<x0 or y1<y0:continue
 X,Y=np.meshgrid(np.arange(x0,x1+1),np.arange(y0,y1+1));a,b,c=v;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
 if abs(den)<1e-9:continue
 w0=((b[1]-c[1])*(X-c[0])+(c[0]-b[0])*(Y-c[1]))/den;w1=((c[1]-a[1])*(X-c[0])+(a[0]-c[0])*(Y-c[1]))/den;w2=1-w0-w1;inside=(w0>=-.03)&(w1>=-.03)&(w2>=-.03)
 pw=w0[...,None]*coords[ids[0]]+w1[...,None]*coords[ids[1]]+w2[...,None]*coords[ids[2]];nw=w0[...,None]*normals[ids[0]]+w1[...,None]*normals[ids[1]]+w2[...,None]*normals[ids[2]];nw/=np.linalg.norm(nw,axis=2).clip(1e-8)[...,None]
 valid=inside
 points.append(pw[valid].astype(np.float32));normal_points.append(nw[valid].astype(np.float32));pixels.append((Y[valid]*N+X[valid]).astype(np.int32))
 if ti%25000==0:print("RASTER",ti,flush=True)
pw_all=np.concatenate(points);nw_all=np.concatenate(normal_points);pix_all=np.concatenate(pixels);del points,normal_points,pixels
flat=out.reshape(-1,4);occupied.ravel()[pix_all]=True
for offset in range(0,len(pix_all),65536):
 pw=pw_all[offset:offset+65536,None,:];nw=nw_all[offset:offset+65536,None,:];idx=pix_all[offset:offset+65536]
 total=np.zeros_like(pw);sumw=np.zeros(pw.shape[:2]);maxw=np.zeros_like(sumw);which=np.zeros_like(sumw,dtype=np.uint8)
 for vi,view in enumerate(views):
  inv=view['inv'];pc=pw@inv[:3,:3].T+inv[:3,3];xx=(pc[:,:,0]/view['scale']+.5)*1000-.5;yy=(pc[:,:,1]/view['scale']+.5)*1000-.5;dep=-pc[:,:,2]
  depth=sample(view['depth'],xx,yy);visible=(xx>1)&(xx<998)&(yy>1)&(yy<998)&(depth[:,:,1]>.95)&(np.abs(depth[:,:,0]-dep)<.0025)
  col=sample(view['paint'],xx,yy);enc=sample(view['encoded'],xx,yy)
  # Reject likely generated skin contamination; do not project face/body pixels.
  validcolor=(enc.max(axis=2)<.73)&((enc[:,:,0]-enc[:,:,1])<.13)&((enc[:,:,0]-enc[:,:,2])<.16)
  technical=sample(view['light'],xx,yy)[:,:,:3].mean(axis=2).clip(.4,1.2)
  base=col/technical[:,:,None];weight=(np.abs(nw@view['normal'])**6)*visible*validcolor
  total+=base*weight[:,:,None];sumw+=weight;win=weight>maxw;which[win]=vi+1;maxw=np.maximum(maxw,weight)
 valid=sumw[:,0]>.025
 flat[idx[valid],:3]=(total[valid,0]/sumw[valid,0,None]).clip(0,.8)
 flat[idx[valid],3]=np.clip(sumw[valid,0]/.15,0,1)
 if offset%1048576==0:print('PROJECT',offset,len(pix_all),flush=True)
coverage_before=float((out[:,:,3]>.5).sum()/max(occupied.sum(),1))
# Extend only the projected UV paint at its boundary, not geometry or source pixels.
for _ in range(3):
 empty=out[:,:,3]==0;total=np.zeros_like(out);count=np.zeros((N,N),np.float32)
 for axis,step in [(0,1),(0,-1),(1,1),(1,-1)]:
  moved=np.roll(out,step,axis);ok=moved[:,:,3]>0;total+=moved*ok[:,:,None];count+=ok
 fill=empty&(count>0);out[fill]=total[fill]/count[fill,None]
linear=out[:,:,:3];encoded=np.where(linear<=.0031308,linear*12.92,1.055*np.power(linear,1/2.4)-.055).clip(0,1);rgba=np.dstack([encoded,out[:,:,3].clip(0,1)]);Image.fromarray(np.rint(rgba[::-1]*255).astype(np.uint8),'RGBA').save(O/'Mia_GeneratedInkPaint_4096.png');Image.fromarray((out[::-1,:,3]*255).astype(np.uint8)).save(O/'projection-coverage.png')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();(O/'projection-provenance.json').write_text(json.dumps({'generated_input':{'path':str((O/'hair-paintover.png').resolve()),'sha256':sha(O/'hair-paintover.png'),'size':list(paint.size),'per_view_pixels':[tw,th],'provider':'built-in image_gen; authored paintover, NOT actual render'},'source_view_geometry':'fixed 396840f3 head cameras; no mesh/UV changes','texture':{'path':str((O/'Mia_GeneratedInkPaint_4096.png').resolve()),'sha256':sha(O/'Mia_GeneratedInkPaint_4096.png'),'encoding':'sRGB RGB + straight coverage alpha','dimensions':[4096,4096]},'projection':'actual rendered depth/target visibility, abs(normal dot view)^6 blend, 2.5mm depth tolerance; generated color divided by captured technical diffuse ramp, not full physical delighting','coverage_fraction_of_rasterized_UV':coverage_before,'limits':['Five 512-square generated panels do not equal 4K unique painted information','Generated paint can have cross-view drift; final actual native views must be inspected','Unknown/unseen areas fall back to checkpoint material','Artist shadows/highlights remain painted information; not pure albedo','No face/body pixels intentionally projected; conservative chroma/visibility masks applied']},indent=2));print('PROJECT_DONE',coverage_before)
