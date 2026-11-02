"""Read-only actual evaluated sections across named local control edges."""
from pathlib import Path
from collections import defaultdict
import json,hashlib
import numpy as np
P=Path(__file__).resolve().parent;raw=np.load(P/'prototype06.npz')['world'];d=np.load(P/'evaluated06.npz');v=d['world'];t=d['triangles'];mi=d['triangle_materials']
def section(edge):
    a,b=raw[list(edge)];origin=(a+b)/2;normal=(b-a)/np.linalg.norm(b-a);signed=(v-origin)@normal
    sel=(mi==1)&(signed[t].min(1)<-1e-9)&(signed[t].max(1)>1e-9);graph=defaultdict(list);points={};segments=[]
    for fi in np.flatnonzero(sel):
        hits=[]
        for ia,ib in [(0,1),(1,2),(2,0)]:
            u,w=map(int,t[fi,[ia,ib]]);du,dw=signed[u],signed[w]
            if du*dw<0:
                key=tuple(sorted((u,w)));points[key]=v[u]+du/(du-dw)*(v[w]-v[u]);hits.append(key)
        if len(hits)==2:
            u,w=hits;graph[u].append(w);graph[w].append(u);segments.append((u,w,int(fi)))
    def distseg(u,w):
        pa,pb=points[u],points[w];dd=pb-pa;f=np.clip((origin-pa)@dd/max(dd@dd,1e-20),0,1);return np.linalg.norm(pa+f*dd-origin)
    u,w,fi=min(segments,key=lambda s:distseg(s[0],s[1]));mind=distseg(u,w)
    def follow(start,previous):
        path=[start]
        for _ in range(3000):
            nexts=[n for n in graph[path[-1]] if n!=previous]
            if len(nexts)!=1:break
            previous=path[-1];nn=nexts[0]
            if nn in path:break
            path.append(nn)
        return path
    left=follow(u,w);right=follow(w,u);keys=left[::-1]+right;p=np.array([points[k] for k in keys]);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))];mid=arc[len(left)-1]
    def at(s):return np.array([np.interp(s,arc,p[:,i]) for i in range(3)])
    turns=[]
    for s in np.arange(max(.005,mid-.015),min(arc[-1]-.005,mid+.015),.001):
        p0,p1,p2=at(s-.005),at(s),at(s+.005);d1=p1-p0;d2=p2-p1;ang=np.degrees(np.arccos(np.clip(d1@d2/(np.linalg.norm(d1)*np.linalg.norm(d2)),-1,1)));turns.append((ang,s,at(s)))
    worst=max(turns,key=lambda r:r[0])
    return dict(raw_edge=list(edge),plane_origin=origin.tolist(),plane_normal=normal.tolist(),closest_actual_section_mm=float(mind*1000),component_points=len(p),max5mm_chord_turn_degrees=float(worst[0]),worst_location_world=worst[2].tolist(),
        samples=[dict(arc_offset_mm=float(ds*1000),world=at(mid+ds).tolist()) for ds in [-.010,-.005,0,.005,.010] if 0<mid+ds<arc[-1]])
rows=[section(e) for e in [(585,586),(490,585),(156,157),(325,626),(76,157),(3587,3604)]]
report=dict(status='Diagnostic geometry sections; not an anatomical curvature threshold or acceptance',prototype_sha256=hashlib.sha256((P/'prototype06.npz').read_bytes()).hexdigest(),evaluated_cache_sha256=hashlib.sha256((P/'evaluated06.npz').read_bytes()).hexdigest(),
    method='Actual material1 triangle-plane intersections; plane normal to named raw edge. Closest connected section selected geometrically, no evaluated-prefix raw-ID assumption. Maximum angle between5mm chords in15mm arclength window.',rows=rows,geometry_changed=False,gpu_used=False)
(P/'section-diagnostic.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('PATCH06_SECTIONS_READONLY_DONE',[(r['raw_edge'],round(r['max5mm_chord_turn_degrees'],2)) for r in rows],flush=True)
