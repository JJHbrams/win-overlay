"""Numerical 4096 RGBA recovery bake: exact old pigment to unique current strips.

Evaluates retained static ash/ink/overlay data only. RGB is existing artwork;
alpha is a physical 4mm boundary gate. No new strokes or imagegen.
"""
from pathlib import Path
import numpy as np,json,collections,hashlib
from PIL import Image
P=Path(__file__).resolve().parent;O=P/'v29-pigment';A=P/'crown-strip-A';d=np.load(O/'fallback-payload.npz');uv=np.load(A/'proxy-strip-result.npz');cfg=json.loads((O/'static-pigment.json').read_text());audit=json.loads((A/'report.json').read_text());assert not audit['exact_triangle_overlap_pairs_above_1e_13'];assert np.array_equal(d['polygon_indices'],uv['selected_polygon_indices']);N={r['name']:r for r in cfg['nodes']};images={}
for name,row in cfg['images'].items():
 file=O/row['file'];assert hashlib.sha256(file.read_bytes()).hexdigest()==row['sha256'];images[name]=np.array(Image.open(file).convert('RGBA'))
def sample(name,q):
 im=images[name];h,w=im.shape[:2];x=q[:,0]*w-.5;y=(1-q[:,1])*h-.5;x0=np.floor(x).astype(int);y0=np.floor(y).astype(int);fx=x-x0;fy=y-y0;result=np.zeros((len(q),4));srgb=cfg['images'][name]['colorspace']=='sRGB'
 for dx,dy,wt in [(0,0,(1-fx)*(1-fy)),(1,0,fx*(1-fy)),(0,1,(1-fx)*fy),(1,1,fx*fy)]:
  ix=np.clip(x0+dx,0,w-1);iy=np.clip(y0+dy,0,h-1);a=im[iy,ix].astype(float)/255
  if srgb:a[:,:3]=np.where(a[:,:3]<=.04045,a[:,:3]/12.92,((a[:,:3]+.055)/1.055)**2.4)
  result+=a*wt[:,None]
 return result
def pigment(q):
 base=sample('MIA_V17_Pixal_Repacked4096.003',q);signals=sample('MIA_V22_AuthoredStrandSignals',q);generated=sample('MIA_V22_GeneratedSelectiveLockPigment',q);lum=base[:,:3]@np.array([.2126,.7152,.0722]);r=N['V22_OwnedAshPalette']['ramp'];positions=np.array([e['position'] for e in r['elements']]);colors=np.array([e['color'][:3] for e in r['elements']]);i=np.clip(np.searchsorted(positions,lum,side='right')-1,0,len(positions)-2);t=np.clip((lum-positions[i])/(positions[i+1]-positions[i]),0,1);assert r['interpolation']=='EASE';t=t*t*(3-2*t);palette=colors[i]*(1-t[:,None])+colors[i+1]*t[:,None]
  # Match the actual retained three legacy MixRGB operations, not a new grade.
 clean=N['V22_CLEAN_PALETTE_72_PERCENT'];factor=clean['inputs']['0'];a=np.array(clean['inputs']['1'][:3])*(1-factor)+palette*factor;ink=N['믹스 (레거시).001'];assert ink['blend_type']=='MIX';a=a*(1-signals[:,0,None])+np.array(ink['inputs']['2'][:3])*signals[:,0,None];high=N['믹스 (레거시).002'];assert high['blend_type']=='ADD';a=a+np.array(high['inputs']['2'][:3])*signals[:,1,None]
 if high.get('use_clamp'):a=np.clip(a,0,1)
 return a*(1-generated[:,3,None])+generated[:,:3]*generated[:,3,None]
size=4096;U=uv['loop_uv'].astype(float);oldUV=d['old_loop_uv'].astype(float);rgb=np.zeros((size,size,3),np.uint8);alpha=np.zeros((size,size),np.float32);owner=np.full((size,size),-1,np.int32);weights=d['interior_weight'][d['raw_vertices']];hits=np.zeros(len(U),int);stamped=[]
for i,t in enumerate(U):
 cross=(t[1,0]-t[0,0])*(t[2,1]-t[0,1])-(t[1,1]-t[0,1])*(t[2,0]-t[0,0]);assert cross>0;x0=max(0,int(np.floor(t[:,0].min()*size-.5)));x1=min(size-1,int(np.ceil(t[:,0].max()*size-.5)));y0=max(0,int(np.floor((1-t[:,1].max())*size-.5)));y1=min(size-1,int(np.ceil((1-t[:,1].min())*size-.5)));xx,yy=np.meshgrid(np.arange(x0,x1+1),np.arange(y0,y1+1));p=np.stack([(xx+.5)/size,1-(yy+.5)/size],-1);a=t[1]-t[0];b=t[2]-t[0];v=p-t[0];s=(v[:,:,0]*b[1]-v[:,:,1]*b[0])/cross;z=(a[0]*v[:,:,1]-a[1]*v[:,:,0])/cross;inside=(s>=-1e-10)&(z>=-1e-10)&(s+z<=1+1e-10);y,x=np.where(inside);bc=np.stack([1-s[y,x]-z[y,x],s[y,x],z[y,x]],-1);y+=y0;x+=x0
 if not len(y):
  c=t.mean(0);x=np.array([min(size-1,max(0,int(c[0]*size)))]);y=np.array([min(size-1,max(0,int((1-c[1])*size)))]);bc=np.array([[1/3]*3]);assert owner[y[0],x[0]]<0;stamped.append(i)
 hits[i]=len(y);src=bc@oldUV[i];color=pigment(src);color=np.where(color<=.0031308,color*12.92,1.055*np.maximum(color,0)**(1/2.4)-.055);rgb[y,x]=np.uint8(np.clip(color*255+.5,0,255));alpha[y,x]=bc@weights[i];owner[y,x]=i
 if i%1000==0:print('V29_STATIC_BAKE',i,len(U),flush=True)
# Twelve-pixel numeric nearest-neighbor padding, never new artistic fill.
valid=owner>=0;padded=valid.copy()
for step in range(12):
 prev=padded.copy();chosen=np.zeros_like(prev)
 for dy,dx in [(-1,0),(1,0),(0,-1),(0,1)]:
  good=np.roll(prev,(dy,dx),(0,1))
  if dy>0:good[:dy]=False
  elif dy<0:good[dy:]=False
  if dx>0:good[:,:dx]=False
  elif dx<0:good[:,dx:]=False
  use=good&~prev&~chosen;rr=np.roll(rgb,(dy,dx),(0,1));aa=np.roll(alpha,(dy,dx),(0,1));rgb[use]=rr[use];alpha[use]=aa[use];chosen|=use
 padded|=chosen
# Exact physical layer boundary -> UV support. Four bilinear texels around
# densely sampled boundary edges are0, so neighboring legacy material joins.
old=np.load(O/'geometry-input.npz');co=old['co'];q,iv=np.unique(np.round(co,6),axis=0,return_inverse=True);F=iv[d['raw_vertices']];ed=collections.defaultdict(list)
for i,t in enumerate(F):
 for j in range(3):ed[tuple(sorted((int(t[j]),int(t[(j+1)%3]))))].append((i,j,(j+1)%3))
boundary_samples=[]
for edge,entries in ed.items():
 if len(entries)==2:continue
 for i,j,k in entries:
  a,b=U[i,j],U[i,k];count=max(2,int(np.linalg.norm((a-b)*size)*2)+1);boundary_samples.extend(a[None,:]+np.linspace(0,1,count)[:,None]*(b-a)[None,:])
points=np.asarray(boundary_samples);xx=points[:,0]*size-.5;yy=(1-points[:,1])*size-.5;x0=np.floor(xx).astype(int);y0=np.floor(yy).astype(int);zero=np.zeros((size,size),bool)
for dy,dx in [(0,0),(0,1),(1,0),(1,1)]:
 x=np.clip(x0+dx,0,size-1);y=np.clip(y0+dy,0,size-1);alpha[y,x]=0;zero[y,x]=True
rgba=np.dstack([rgb,np.uint8(np.clip(alpha*255+.5,0,255))]);out=O/'RecoveredStaticCrown_4096_RGBA.png';Image.fromarray(rgba).save(out);Image.fromarray(np.uint8(zero)*255).save(O/'BoundaryZeroSupport_DATA.png');Image.fromarray(np.uint8(valid)*255).save(O/'UniqueAtlasOwnership_DATA.png');np.savez_compressed(O/'fallback-baked-payload.npz',polygon_indices=d['polygon_indices'],raw_source_ids=d['raw_source_ids'],raw_vertices=d['raw_vertices'],loop_uv=uv['loop_uv'])
report=dict(texture=str(out),dimensions=[size,size],texture_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),payload_sha256=hashlib.sha256((O/'fallback-baked-payload.npz').read_bytes()).hexdigest(),source_static_description_sha256=hashlib.sha256((O/'static-pigment.json').read_bytes()).hexdigest(),target_UV_sha256=hashlib.sha256((A/'proxy-strip-result.npz').read_bytes()).hexdigest(),old_existing_UV_overlap_pairs=4,new_unique_UV_overlap_pairs=0,covered_texels=int(valid.sum()),all4999_faces_sampled=bool((hits>0).all()),subtexel_centroid_numeric_stamps=stamped,padding_pixels=12,boundary_segments=sum(len(v) for v in ed.values() if len(v)!=2),boundary_support_texels_forced_zero=int(zero.sum()),boundary_bilinear_alpha_exact_zero=True,new_art_generated=False,old_normals_lights_geometry_reused=False,current_live_guide_not_baked=True,limits='Numerical static pigment recovery with8bit output quantization; current live guide is preserved in shader and actual current normals/light remain live. Tiny surface slivers with no covered pixel centre receive one numeric centroid sample. Actual one-frame shader and multi-angle source review required before selection.')
(O/'baked-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2),flush=True)
