"""CPU ordered rays on actual C evaluated triangles; no render/save."""
from pathlib import Path
import json,numpy as np
P=Path(__file__).resolve().parent;d=np.load(P/'form-C-evaluated.npz');raw=np.load(P/'form-C-delta.npz')['selected_world'];base=np.load(P/'current-body-limit.npz');core=base['core'];rec=next(r for r in json.loads((P/'renders-form-C-gray/render-records.json').read_text()) if r['view']=='lowoblique');m=np.asarray(rec['camera']['matrix']);v=d['world'];t=d['triangles'];a=v[t[:,0]];e1=v[t[:,1]]-a;e2=v[t[:,2]]-a;direction=-m[:3,2];h=np.cross(np.broadcast_to(direction,e2.shape),e2);det=(e1*h).sum(1);valid=abs(det)>1e-12;inv=np.zeros(len(det));inv[valid]=1/det[valid];out=[]
for px,py in [(x,y) for x in [435,445,455,465,475] for y in [380,390,400,410,420]]:
    origin=m[:3,3]+m[:3,0]*((px+.5)/640-.5)*.4+m[:3,1]*(.5-(py+.5)/640)*.4;s=origin-a;u=inv*(s*h).sum(1);q=np.cross(s,e1);vv=inv*(q*direction).sum(1);dist=inv*(e2*q).sum(1);ids=np.flatnonzero(valid&(u>=0)&(vv>=0)&(u+vv<=1)&(dist>.1)&(dist<10));ids=ids[np.argsort(dist[ids])];hits=[]
    for i in ids[:5]:
        pos=origin+direction*dist[i];near=np.argsort(np.linalg.norm(raw-pos,axis=1))[:8];hits.append(dict(eval_triangle=int(i),material=int(d['triangle_materials'][i]),distance=float(dist[i]),position=pos.tolist(),nearest_raw=[dict(index=int(j),distance_mm=float(np.linalg.norm(raw[j]-pos)*1000),C=raw[j].tolist(),current=base['raw_world'][j].tolist(),core=core[j].tolist()) for j in near]))
    out.append(dict(pixel=[px,py],hits=hits))
(P/'C-actual-root-owner.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
for row in out:
    if row['hits']:print(row['pixel'],np.round(row['hits'][0]['position'],5),[q['index'] for q in row['hits'][0]['nearest_raw'][:4]],flush=True)
print('C_RETURN_OWNER_DONE',flush=True)
