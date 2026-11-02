"""CPU projected-triangle ray diagnostic on frozen Main only; no shaded render."""
from pathlib import Path
import json,numpy as np
P=Path(__file__).resolve().parent;a=np.load(P/'main-logical-inputs.npz');b=np.load(P/'current-inputs.npz');field=np.load(P/'fringe-B.npz');cfg=json.loads((P/'candidate-B.json').read_text());cam=np.array(json.loads((P/'current-inputs.json').read_text())['camera']['matrix'])
f=a['faces'];d=-cam[:3,2];right=cam[:3,0];up=cam[:3,1]
def projected(q):return np.column_stack((q@right,q@up,q@d))
def prepare(q):
    tri=projected(q)[f];return tri,tri[:,:,:2].min(1),tri[:,:,:2].max(1)
def hit(cache,pt):
    tri,mn,mx=cache;p=projected(pt[None])[0];ii=np.flatnonzero((mn[:,0]<=p[0])&(mx[:,0]>=p[0])&(mn[:,1]<=p[1])&(mx[:,1]>=p[1]));t=tri[ii]
    v0=t[:,1,:2]-t[:,0,:2];v1=t[:,2,:2]-t[:,0,:2];v=p[:2]-t[:,0,:2];det=v0[:,0]*v1[:,1]-v0[:,1]*v1[:,0];good=abs(det)>1e-15
    u=np.divide(v[:,0]*v1[:,1]-v[:,1]*v1[:,0],det,out=np.zeros(len(ii)),where=good);w=np.divide(v0[:,0]*v[:,1]-v0[:,1]*v[:,0],det,out=np.zeros(len(ii)),where=good)
    z=t[:,0,2]*(1-u-w)+t[:,1,2]*u+t[:,2,2]*w;valid=good&(u>=0)&(w>=0)&(u+w<=1)&(z<p[2]-.0005)
    ii=ii[valid];z=z[valid]
    if len(ii):i=int(ii[np.argmin(z)]);return {'face':i,'root':int(a['face_component_root'][i])}
    return None
q=a['world'];target=q.copy();target[field['indices']]+=field['delta_local'];before=prepare(q);after=prepare(target);report=[]
for side in [-1,1]:
    pts=b['brow_world_'+str(side)].reshape(-1,3,3)[:,1];lo,hi=cfg['brow_width_case'][str(side)]['observed_u'];rows=[]
    for col,p in enumerate(pts):
        if lo<=col/64<=hi:rows.append({'column':col,'before':hit(before,p),'after':hit(after,p)})
    report.append({'side':side,'samples':len(rows),'visible_before':sum(r['before'] is None for r in rows),'visible_after':sum(r['after'] is None for r in rows),'rows':rows})
(P/'Main-only-prediction-B.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps([{k:r[k] for k in ['side','samples','visible_before','visible_after']} for r in report]))
