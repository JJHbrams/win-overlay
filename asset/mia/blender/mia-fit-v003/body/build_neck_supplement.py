"""Explicit current below-chin neck guide; no head/model mutation."""
from pathlib import Path
import json,hashlib
import numpy as np
from field_math import periodic_theta
P=Path(__file__).resolve().parent;O=P/'scaffold-fullbody';g=json.loads((O/'guide-data.json').read_text());mappath=(Path(__file__).resolve().parent/'inputs/mapping-frame1.npz');m=np.load(mappath);q=m['q0_world'];edges=np.load(P/'current-body-limit.npz')['raw_edges'];a,b=edges.T;rings=[];evidence=[]
for zz in [1.455,1.430,1.405,1.386]:
    limit=.075 if zz>1.39 else .20
    mask=(a<3957)&(b<3957)&((q[a,2]-zz)*(q[b,2]-zz)<0)&(abs(q[a,0])<limit)&(abs(q[b,0])<limit);aa=q[a[mask]];bb=q[b[mask]];t=(zz-aa[:,2])/(bb[:,2]-aa[:,2]);pts=aa+(bb-aa)*t[:,None];pts=np.unique(np.round(pts,7),axis=0);cx=float(np.median(pts[:,0]));cy=float((pts[:,1].min()+pts[:,1].max())/2);ang=np.arctan2(pts[:,0]-cx,-(pts[:,1]-cy));order=np.argsort(ang);pts=pts[order];ang=ang[order];unique=np.r_[True,np.diff(ang)>1e-5];pts=pts[unique];ang=ang[unique];sample=periodic_theta(ang,pts[:,:2],-np.arange(12)*2*np.pi/12);r=np.column_stack([sample,np.full(12,zz)]);rings.append(r.tolist());evidence.append(dict(z=zz,source='Actual frame1 posed control-cage edge/plane intersections, excluding Face690; current under-chin/mid-neck then clavicular-base surface. Not the small internal core ring.',intersections=len(pts),bounds_min=pts.min(0).tolist(),bounds_max=pts.max(0).tolist()))
curves=[]
for i,r in enumerate(rings):curves.append(dict(name=f'neck.section.{i:02d}',points=r,closed=True))
for j in range(12):curves.append(dict(name=f'neck.meridian.{j:02d}',points=[r[j] for r in rings],closed=False))
data=dict(revision=1,base_fullbody_guide_sha256=hashlib.sha256((O/'guide-data.json').read_bytes()).hexdigest(),mapping_sha256=hashlib.sha256(mappath.read_bytes()).hexdigest(),curves=curves,rings=rings,evidence=evidence,limits='Explicit clavicle-base to current under-chin neck coverage. Current upper neck/head attachment preserved. Source/current chin-height and1.08head-ratio hypothesis remain separate root work; no face/chin scaling or sculpt.',status='GUIDE_SUPPLEMENT_ONLY; no model/rig/key changes')
(O/'neck-supplement.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8');print('NECK_SUPPLEMENT_DATA_DONE',len(curves),evidence,flush=True)
