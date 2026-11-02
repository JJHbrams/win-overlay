from pathlib import Path
import numpy as np,json,collections
from PIL import Image
from v29_static_numeric import StaticPigment
P=Path(__file__).resolve().parent;O=P/'v29-pigment';d=np.load(O/'fallback-payload.npz');U=np.load(O/'fallback-baked-payload.npz')['loop_uv'].astype(float);im=np.array(Image.open(O/'RecoveredStaticCrown_4096_RGBA.png').convert('RGBA'));size=im.shape[0];old=np.load(O/'geometry-input.npz');co=old['co'];q,iv=np.unique(np.round(co,6),axis=0,return_inverse=True);F=iv[d['raw_vertices']];ed=collections.defaultdict(list)
for i,t in enumerate(F):
 for j in range(3):ed[tuple(sorted((int(t[j]),int(t[(j+1)%3]))))].append((i,j,(j+1)%3))
def sample(q):
 x=q[:,0]*size-.5;y=(1-q[:,1])*size-.5;x0=np.floor(x).astype(int);y0=np.floor(y).astype(int);fx=x-x0;fy=y-y0;out=np.zeros((len(q),4))
 for dx,dy,wt in [(0,0,(1-fx)*(1-fy)),(1,0,fx*(1-fy)),(0,1,(1-fx)*fy),(1,1,fx*fy)]:
  a=im[np.clip(y0+dy,0,size-1),np.clip(x0+dx,0,size-1)].astype(float)/255;a[:,:3]=np.where(a[:,:3]<=.04045,a[:,:3]/12.92,((a[:,:3]+.055)/1.055)**2.4);out+=a*wt[:,None]
 return out
boundary=[];queries=[];pairs=[];expectedUV=[];expectedWeight=[];weights=d['interior_weight'][d['raw_vertices']]
for edge,entries in ed.items():
 if len(entries)!=2:
  for i,j,k in entries:
   a,b=U[i,j],U[i,k];steps=max(2,int(np.linalg.norm((a-b)*size)*2)+1);boundary.extend(a[None,:]+np.linspace(0,1,steps)[:,None]*(b-a)[None,:])
  continue
 pair=[]
 for i,j,k in entries:
  bc=np.full(3,.02);bc[j]=bc[k]=.49;pair.append(len(queries));queries.append(bc@U[i]);expectedUV.append(bc@d['old_loop_uv'][i]);expectedWeight.append(bc@weights[i])
 pairs.append(pair)
gate=sample(np.array(boundary))[:,3];assert gate.max()==0.;queries=np.array(queries);pairs=np.array(pairs);pixels=sample(queries);evaluator=StaticPigment(O);expected=evaluator.evaluate(np.array(expectedUV));weight=np.array(expectedWeight);fallback=np.array([.12,.115,.12]);actual=pixels[:,:3]*pixels[:,3,None]+fallback*(1-pixels[:,3,None]);expected=expected*weight[:,None]+fallback*(1-weight[:,None]);error=abs(actual-expected);seam=abs((actual[pairs[:,0]]-actual[pairs[:,1]])-(expected[pairs[:,0]]-expected[pairs[:,1]]));report=dict(boundary_uv_samples=len(boundary),boundary_bilinear_alpha_max=float(gate.max()),interior_shared_edges=len(pairs),inside_edge_RGB_linear_absolute_error_p50_90_99_max=np.percentile(error,[50,90,99,100]).tolist(),added_seam_discontinuity_linear_p50_90_99_max=np.percentile(seam,[50,90,99,100]).tolist(),interior_field='Numeric8bit static-color+physical-gate remap compared against direct old-data evaluation at inset physical-edge samples; current guide is not baked.',limits='High tails at UV tips/quantization/forced-zero physical border must be checked in actual render. No shader/ART pass from numerical seams.');(O/'baked-seam-audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
