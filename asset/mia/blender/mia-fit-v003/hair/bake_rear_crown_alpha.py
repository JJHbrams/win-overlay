"""Keep recovered RGB bytes exact; bake only the physical rear owner alpha."""
from pathlib import Path
import numpy as np,json,hashlib
from PIL import Image
P=Path(__file__).resolve().parent;O=P/'v29-pigment';d=np.load(O/'fallback-baked-payload.npz');own=np.load(O/'rear-crown-owner.npz');base=json.loads((O/'baked-report.json').read_text());src=O/'RecoveredStaticCrown_4096_RGBA.png';assert hashlib.sha256(src.read_bytes()).hexdigest()==base['texture_sha256'];rgba=np.array(Image.open(src).convert('RGBA'));U=d['loop_uv'].astype(float);size=rgba.shape[0];field=np.zeros((size,size),np.float32);valid=np.zeros((size,size),bool)
for i,t in enumerate(U):
 a,b=t[1]-t[0],t[2]-t[0];cross=a[0]*b[1]-a[1]*b[0];x0=max(0,int(np.floor(t[:,0].min()*size-.5)));x1=min(size-1,int(np.ceil(t[:,0].max()*size-.5)));y0=max(0,int(np.floor((1-t[:,1].max())*size-.5)));y1=min(size-1,int(np.ceil((1-t[:,1].min())*size-.5)));xx,yy=np.meshgrid(np.arange(x0,x1+1),np.arange(y0,y1+1));v=np.stack([(xx+.5)/size,1-(yy+.5)/size],-1)-t[0];s=(v[:,:,0]*b[1]-v[:,:,1]*b[0])/cross;z=(a[0]*v[:,:,1]-a[1]*v[:,:,0])/cross;inside=(s>=-1e-10)&(z>=-1e-10)&(s+z<=1+1e-10);y,x=np.where(inside);bc=np.stack([1-s[y,x]-z[y,x],s[y,x],z[y,x]],-1);y+=y0;x+=x0
 if not len(y):
  c=t.mean(0);x=np.array([int(c[0]*size)]);y=np.array([int((1-c[1])*size)]);bc=np.array([[1/3]*3])
 field[y,x]=bc@own['corner_weight'][i];valid[y,x]=True
for step in range(12):
 prev=valid.copy();taken=np.zeros_like(prev)
 for dy,dx in [(-1,0),(1,0),(0,-1),(0,1)]:
  good=np.roll(prev,(dy,dx),(0,1))
  if dy>0:good[:dy]=False
  elif dy<0:good[dy:]=False
  if dx>0:good[:,:dx]=False
  elif dx<0:good[:,dx:]=False
  use=good&~prev&~taken;values=np.roll(field,(dy,dx),(0,1));field[use]=values[use];taken|=use
 valid|=taken
rgba[:,:,3]=np.uint8(np.clip(rgba[:,:,3].astype(float)*field+.5,0,255));guard=[]
for i in own['protected_face_rows']:
 for j,k in [(0,1),(1,2),(2,0)]:
  a,b=U[i,j],U[i,k];count=max(2,int(np.linalg.norm((a-b)*size)*2)+1);guard.extend(a[None,:]+np.linspace(0,1,count)[:,None]*(b-a)[None,:])
q=np.asarray(guard);xx=q[:,0]*size-.5;yy=(1-q[:,1])*size-.5;x0=np.floor(xx).astype(int);y0=np.floor(yy).astype(int)
for dy,dx in [(0,0),(0,1),(1,0),(1,1)]:rgba[np.clip(y0+dy,0,size-1),np.clip(x0+dx,0,size-1),3]=0
out=O/'RecoveredRearCrown_4096_RGBA.png';Image.fromarray(rgba).save(out);original=np.array(Image.open(src).convert('RGBA'));assert np.array_equal(rgba[:,:,:3],original[:,:,:3]);assert np.all(rgba[:,:,3]<=original[:,:,3]);report=dict(texture_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),payload_sha256=base['payload_sha256'],dimensions=[size,size],RGB_byte_exact_to_verified_static_recovery=True,alpha='Verified global4mm boundary fade times rest-space rear Crown owner, with exact-zero bilinear support on held front-visible surface edges',front_protected_face_rows=len(own['protected_face_rows']),front_guard_samples=len(guard),alpha_nonzero_texels=int((rgba[:,:,3]>0).sum()),alpha_changed_texels=int((rgba[:,:,3]!=original[:,:,3]).sum()),never_global_guide_removal=True,new_art_generated=False,native_saved=False,limits='Only a bounded rear-guide-art challenger. Actual one018 shader/art proof before any broader review/adoption.');(O/'rear-guide-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
