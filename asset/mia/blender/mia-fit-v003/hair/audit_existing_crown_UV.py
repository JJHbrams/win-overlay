from pathlib import Path
import numpy as np,json,collections
P=Path(__file__).resolve().parent;O=P/'v29-pigment';U=np.load(O/'fallback-payload.npz')['old_loop_uv'].astype(float)
def cross(a,b):return float(a[0]*b[1]-a[1]*b[0])
def area(a,b):
 out=list(a)
 for j in range(3):
  p,q=b[j],b[(j+1)%3];inside=[]
  for k,v in enumerate(out):
   prev=out[k-1];sv=cross(q-p,v-p);sp=cross(q-p,prev-p)
   if sv>=0:
    if sp<0:inside.append(prev+(v-prev)*(sp/(sp-sv)))
    inside.append(v)
   elif sp>=0:inside.append(prev+(v-prev)*(sp/(sp-sv)))
  out=inside
  if not out:return 0.
 return abs(sum(cross(out[i],out[(i+1)%len(out)]) for i in range(len(out))))*.5
grid=collections.defaultdict(list);pairs=set();lo=U.min(1);hi=U.max(1)
for i,(a,b) in enumerate(zip(lo,hi)):
 p=np.floor(a*128).astype(int);q=np.floor(b*128).astype(int)
 for x in range(p[0],q[0]+1):
  for y in range(p[1],q[1]+1):
   for j in grid[x,y]:pairs.add((j,i))
   grid[x,y].append(i)
bad=[]
for i,j in pairs:
 if np.any(hi[i]<lo[j]) or np.any(hi[j]<lo[i]):continue
 value=area(U[i],U[j])
 if value>1e-13:bad.append([i,j,value])
tri_area=np.abs((U[:,1,0]-U[:,0,0])*(U[:,2,1]-U[:,0,1])-(U[:,1,1]-U[:,0,1])*(U[:,2,0]-U[:,0,0]))/2
report=dict(existing_UV='MIA_V17_PAINT_UV',real_faces=len(U),triangle_overlap_pairs_gt_1e_13=bad,covered_absolute_UV_area=float(tri_area.sum()),triangle_texel_area_at4096_p0_10_50_90_100=np.percentile(tri_area*4096**2,[0,10,50,90,100]).tolist(),limits='No model modifications. Nonoverlap is not enough: tiny existing islands and boundary-alpha bilinear support must also be checked before a one-image originalUV recovery.');(O/'existing-UV-overlap-audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
