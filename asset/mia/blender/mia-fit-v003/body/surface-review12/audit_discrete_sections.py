"""Read-only physical triangle sections/facet turns; no ART verdict from math."""
from pathlib import Path
import json,hashlib
import numpy as np
P=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report={}
for label,name in [('B','joined-static.npz'),('C','joined-geometric-C.npz'),('D','joined-discrete-D.npz'),('D2','joined-discrete-D2.npz'),('D3','joined-discrete-D3.npz'),('E','joined-expanded-E.npz')]:
    d=np.load(P/name);v=d['world'].astype(float);f=d['triangles'];part=d['source_part'];tri=v[f];e1=tri[:,1]-tri[:,0];e2=tri[:,2]-tri[:,0]
    normal=np.cross(e1,e2);normal/=np.linalg.norm(normal,axis=1)[:,None]
    edge=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),1);fi=np.tile(np.arange(len(f)),3);order=np.lexsort((edge[:,1],edge[:,0]));edge=edge[order];fi=fi[order]
    ix=np.flatnonzero((edge[1:]==edge[:-1]).all(1));a,b=fi[ix],fi[ix+1];edges=edge[ix]
    angle=np.degrees(np.arccos(np.clip((normal[a]*normal[b]).sum(1),-1,1)));mid=v[edges].mean(1)
    boundary=(part[a]==3)^(part[b]==3)
    low,high=(1.005,1.145) if label=='E' else (1.035,1.115)
    masks={'waist_lower':abs(mid[:,2]-low)<1e-7,'waist_upper':abs(mid[:,2]-high)<1e-7,'neck_lower':abs(mid[:,2]-1.445)<1e-7,'neck_upper':abs(mid[:,2]-1.465)<1e-7,'arms':abs(mid[:,0])>.18}
    stats=lambda q:dict(count=len(q),median_deg=float(np.median(q)),p95_deg=float(np.percentile(q,95)),max_deg=float(q.max()))
    boundaries={key:stats(angle[boundary&mask]) for key,mask in masks.items()}
    # The vertex/triangle IDs are held across all four collar revisions.
    rows=np.load(P/('collar-rows-E.npz' if label=='E' else 'collar-rows-D2.npz'));rings={}
    for key in rows.files:
        countRows=rows[key].shape[0];lut=np.full(len(v),-1);lut[rows[key].ravel()]=np.repeat(np.arange(countRows),rows[key].shape[1]);theta=np.full(len(v),-1);theta[rows[key].ravel()]=np.tile(np.arange(rows[key].shape[1]),countRows);sel=(lut[edges[:,0]]>=0)&(lut[edges[:,0]]==lut[edges[:,1]])
        angular=(lut[edges[:,0]]>=0)&(lut[edges[:,1]]>=0)&(theta[edges[:,0]]==theta[edges[:,1]])&(abs(lut[edges[:,0]]-lut[edges[:,1]])==1)
        rings[key]=dict(**stats(angle[sel]),per_ring_max_deg=[float(angle[sel&(lut[edges[:,0]]==k)].max()) for k in range(countRows)],angular_same_index_edge_normal_turns=stats(angle[angular]))
    det=e1[:,0]*e2[:,2]-e1[:,2]*e2[:,0];ok=abs(det)>1e-14
    def front(z):
        aa=np.zeros(len(f));bb=aa.copy();x=-tri[:,0,0];dz=z-tri[:,0,2]
        aa[ok]=(x[ok]*e2[ok,2]-dz[ok]*e2[ok,0])/det[ok];bb[ok]=(e1[ok,0]*dz[ok]-e1[ok,2]*x[ok])/det[ok]
        hit=ok&(aa>=-1e-7)&(bb>=-1e-7)&(aa+bb<=1+1e-7);ids=np.flatnonzero(hit);q=tri[ids,0]+aa[ids,None]*e1[ids]+bb[ids,None]*e2[ids];k=np.argmin(q[:,1]);return float(q[k,1]),int(ids[k])
    zz=np.linspace(low,high,36 if label=='E' else 13);yy=np.array([front(z)[0] for z in zz]);slopes=np.degrees(np.arctan2(np.diff(yy),np.diff(zz)))
    examples=[]
    for z in ([1.004,1.006,1.015,1.035,1.055,1.075,1.095,1.115,1.144,1.146] if label=='E' else [1.034,1.036,1.038,1.045,1.055,1.075,1.095,1.105,1.114,1.116]):
        y0,_=front(z-.0005);y1,_=front(z+.0005)
        examples.append(dict(z_m=z,angle_deg=float(np.degrees(np.arctan2(y1-y0,.001)))))
    report[label]=dict(geometry_path=name,geometry_sha256=sha(P/name),actual_boundary_facet_turns=boundaries,actual_interior_ring_facet_turns=rings,front_X0_physical_section=dict(z_m=zz.tolist(),y_m=yy.tolist(),triangle_ids=[front(z)[1] for z in zz],successive_row_secant_angles_deg=slopes.tolist(),one_mm_central_secants=examples))
out=dict(scope='Actual geometric triangle normals/plane-ray intersections, not CUSTOM shading normals. Boundary values include irregular zipper facets. Same-ring edges measure axial normal turn; same-theta-index between-row edges measure angular normal turn. No rendering/model mutation.',variants=report,decision='B/C actual FAIL; D/D2 CPU held/unselected, D2 produced ZERO actuals. D3 actual gray review required. Finite endpoint improvement is not ART PASS.')
(P/'discrete-section-proof.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(report['E'],indent=2))
