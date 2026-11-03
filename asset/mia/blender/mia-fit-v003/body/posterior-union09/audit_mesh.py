"""Actual09 mesh, correspondence-free sections and whole-region guards. CPU."""
from pathlib import Path
import sys,json,hashlib,importlib.util
sys.dont_write_bytecode=True
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent;CAN=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia');E=CAN/'blender/mia-fit-v003/body/design-sculpt07/E'
spec=importlib.util.spec_from_file_location('frozen08_geometry',P.parent/'posterior-continuity08/geometry.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
a=np.load(E/'breast-step.npz');b=np.load(P/'posterior09.npz');v0=a['world'];f0=a['triangles'];v=b['world'];f=b['triangles'];assert np.isfinite(v).all()
n0,vn0=g.normals(v0.astype(float),f0);n,vn=g.normals(v.astype(float),f)
def tree(q,ff):return BVHTree.FromPolygons([Vector(x) for x in q],ff.tolist(),all_triangles=True)
t0=tree(v0,f0);t1=tree(v,f)
old_vertices={q.tobytes():i for i,q in enumerate(v0)};mapped=np.array([old_vertices.get(q.tobytes(),-1) for q in v],np.int32)
old_faces={tuple(sorted(q)) for q in f0};unchanged=np.array([bool(np.min(q)>=0 and tuple(sorted(q)) in old_faces) for q in mapped[f]])
changed_faces=np.flatnonzero(~unchanged);changed_tree=tree(v,f[changed_faces]);intersections=[];tested=0;seen=set()
for local,j in changed_tree.overlap(t1):
    i=int(changed_faces[local]);j=int(j);pair=(min(i,j),max(i,j))
    if i==j or pair in seen or np.intersect1d(f[i],f[j]).size:continue
    seen.add(pair);tested+=1
    if g.triangle_intersects(v[f[i]].astype(float),v[f[j]].astype(float)):intersections.append(pair)
assert not intersections,intersections[:20]
aa=np.array([[0,0,0],[.01,0,0],[0,.01,0]],float);bb=np.array([[.002,.002,-.002],[.002,.002,.002],[.008,.002,0.]])
assert g.triangle_intersects(aa,bb) and not g.triangle_intersects(aa,bb+[0,0,.1])
directed=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);edges,inv,count=np.unique(np.sort(directed,axis=1),axis=0,return_inverse=True,return_counts=True)
winding=np.bincount(inv,weights=np.where(directed[:,0]<directed[:,1],1,-1));assert np.all(count==2) and not np.any(winding)
parent=np.arange(len(v))
def root(i):
    while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
    return i
for x,y in edges:
    x=root(x);y=root(y)
    if x!=y:parent[x]=y
components=len({root(i) for i in range(len(v))});assert components==1
area=np.linalg.norm(np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]),axis=1);assert area.min()>1e-12
def equal_surface(label,select):
    ids=np.flatnonzero(select(v0));newcoords={q.tobytes() for q in v};miss=[int(i) for i in ids if v0[i].tobytes() not in newcoords]
    faces=np.flatnonzero(select(v0)[f0].all(1));physical09={tuple(sorted(int(j) for j in mapped[row])) for row in f if min(mapped[row])>=0}
    missingfaces=[int(i) for i in faces if tuple(sorted(map(int,f0[i]))) not in physical09]
    return dict(region=label,source_vertices=len(ids),unmatched_vertices=len(miss),source_triangles=len(faces),unmatched_triangles=len(missingfaces),exact=not miss and not missingfaces)
breast=equal_surface('E supported front breast: |X|<=.125,Y<=-.030,Z1.18..1.35',lambda q:(abs(q[:,0])<=.125)&(q[:,1]<=-.030)&(q[:,2]>=1.18)&(q[:,2]<=1.35))
neck=equal_surface('Entire design neck aboveZ1.420',lambda q:q[:,2]>=1.420)
assert breast['exact'],breast
def region_guard(name,predicate):
    results=[]
    for label,q,ff,nn,target in [('E_to09',v0,f0,n0,t1),('09_toE',v,f,n,t0)]:
        ids=np.flatnonzero(predicate(q));dist=[]
        for p in q[ids]:co,no,fi,dd=target.find_nearest(Vector(p));assert co is not None;dist.append(dd)
        cent=q[ff].mean(1);faceids=np.flatnonzero(predicate(cent));angles=[]
        for i in faceids:
            co,no,fi,dd=target.find_nearest(Vector(cent[i]));angles.append(float(np.degrees(np.arccos(np.clip(np.dot(nn[i],no),-1,1)))))
        results.append(dict(direction=label,all_region_vertices=len(ids),actual_bounds=[q[ids].min(0).tolist(),q[ids].max(0).tolist()],surface_distance_mm=np.percentile(dist,[50,95,99,100]).tolist(),surface_distance_units='metres; display conversion below',normal_difference_degrees=np.percentile(angles,[50,95,99,100]).tolist()))
        results[-1]['surface_distance_mm']=(np.array(results[-1]['surface_distance_mm'])*1000).tolist();results[-1].pop('surface_distance_units')
    return dict(name=name,measure='Full declared region, symmetric actual nearest-triangle distances; no global-index or primitive-field bound assumption',directions=results)
guards=[region_guard('broad back/scapula |X|<.130,Y>.025,Z1.28..1.44',lambda q:(abs(q[:,0])<.130)&(q[:,1]>.025)&(q[:,2]>1.28)&(q[:,2]<1.44)),
        region_guard('broad lateral lat |X|.07..145,Y>.025,Z1.27..1.36',lambda q:(abs(q[:,0])>.070)&(abs(q[:,0])<.145)&(q[:,1]>.025)&(q[:,2]>1.27)&(q[:,2]<1.36)),
        region_guard('shoulder cap allY,|X|.125..205,Z1.34..1.42',lambda q:(abs(q[:,0])>.125)&(abs(q[:,0])<.205)&(q[:,2]>1.34)&(q[:,2]<1.42)),
        region_guard('entire design neck aboveZ1.420 EXACT-coordinate guard failed; measure magnitude',lambda q:q[:,2]>=1.420)]
gaps=[]
for z,y in [(1.26,0.),(1.25,0.),(1.24,0.),(1.28,.035),(1.26,.020),(1.265,.025)]:
    rows=[]
    for label,q,ff in [('E',v0,f0),('09',v,f)]:
        hits=[h for h in g.line_hits(q,ff,0,{1:y,2:z}) if 0<h['world'][0]<.30];intervals=[[hits[i]['world'][0],hits[i+1]['world'][0]] for i in range(0,len(hits)-1,2)]
        rows.append(dict(state=label,hits=hits,air_intervals=intervals,widths_mm=[1000*(bb-aa) for aa,bb in intervals]))
    gaps.append(dict(z=z,y=y,states=rows))
main_open=bool(gaps[0]['states'][1]['air_intervals']);assert main_open,'MAIN lower passage closed; no GPU'
roofs=[]
for side in [1,-1]:
    for y in [.018,.020,.025,.030]:
        rows=[]
        for x in np.arange(.135,.170001,.00125):
            h0=g.roof(v0,f0,side*x,y);h1=g.roof(v,f,side*x,y)
            if h0 and h1:rows.append(dict(x=float(side*x),E=h0,candidate=h1,delta_z_mm=(h1['world'][2]-h0['world'][2])*1000))
        roofs.append(dict(side=side,y=y,samples=rows))
auditfixtures=json.loads((E/'actual-audit/render-records.json').read_text(encoding='utf-8'));corefixtures=json.loads((E/'actual-E/render-records.json').read_text(encoding='utf-8'))
def silhouette(q,ff,cam):
    M=np.array(cam['matrix']);local=(q-M[:3,3])@M[:3,:3];xy=np.c_[local[:,0]/cam['ortho_scale']*640+320,320-local[:,1]/cam['ortho_scale']*640];ee=np.unique(np.sort(np.concatenate([ff[:,[0,1]],ff[:,[1,2]],ff[:,[2,0]]]),axis=1),axis=0);a=xy[ee[:,0]];b=xy[ee[:,1]];out=[]
    for yy in range(80,321,4):
        ids=np.flatnonzero((np.minimum(a[:,1],b[:,1])<=yy)&(np.maximum(a[:,1],b[:,1])>=yy)&(abs(b[:,1]-a[:,1])>1e-9))
        xx=a[ids,0]+(yy-a[ids,1])*(b[ids,0]-a[ids,0])/(b[ids,1]-a[ids,1]);out.append([yy,float(xx.min()),float(xx.max())] if len(xx) else [yy,None,None])
    return out
silhouettes=[]
for view in ['back180','rear140','rear220','rearhigh140','rearlow140','front','profile']:
    cam=next(r['camera'] for r in (corefixtures if view in ['front','profile'] else auditfixtures) if r['view']==view and r.get('state','E')=='E' and r.get('mode','gray')=='gray')
    s0=silhouette(v0,f0,cam);s1=silhouette(v,f,cam);diff=[abs(x-y) for a,b in zip(s0,s1) if a[1] is not None and b[1] is not None for x,y in zip(a[1:],b[1:])]
    silhouettes.append(dict(view=view,region='Full design outer left/right silhouettes at actual frozen-camera rows80..320 every4pixels; upper/broad mass envelope, not inner axillary gap',maximum_edge_change_pixels=max(diff),before=s0,after=s1))
protected=json.loads((P/'protected-input-hashes.json').read_text(encoding='utf-8'))
for path,h in protected.items():assert sha(path)==h,path
report=dict(status='CPU mesh data measured; actual FORM/ART UNVERIFIED',mesh_sha256=sha(P/'posterior09.npz'),vertices=len(v),triangles=len(f),finite=True,connected_components=components,boundary_edges=int((count==1).sum()),nonmanifold_edges=int((count>2).sum()),inconsistent_edge_winding=int(np.count_nonzero(winding)),euler_characteristic=int(len(v)-len(edges)+len(f)),signed_volume_m3=g.volume(v.astype(float),f),E_volume_m3=g.volume(v0.astype(float),f0),volume_delta_m3=g.volume(v.astype(float),f)-g.volume(v0.astype(float),f0),minimum_double_area_m2=float(area.min()),
    changed_physical_triangles=len(changed_faces),new_nonadjacent_intersections=intersections,narrow_phase_pairs=tested,positive_intersection_control=True,intersection_limit='All changed/new physical triangles against whole09 mesh; unchanged inherited E region is not recertified globally. Shared-vertex pairs excluded.',
    breast_surface=breast,neck_surface=neck,actual_broad_surface_guards=guards,actual_silhouette_guards=silhouettes,actual_gap_planes=gaps,main_lower_passage_open=main_open,actual_roof_curves=roofs,protected_files_checked=len(protected),native_saved=False,GPU_used=False)
(P/'CPU-audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print('POSTERIOR09_CPU',json.dumps({k:report[k] for k in ['vertices','triangles','finite','connected_components','volume_delta_m3','changed_physical_triangles','narrow_phase_pairs','main_lower_passage_open']}),flush=True)
for r in guards:print('BROAD',r['name'],[v['surface_distance_mm'] for v in r['directions']],flush=True)
for r in gaps:print('GAP',r['z'],r['y'],[s['widths_mm'] for s in r['states']],flush=True)
for r in silhouettes:print('SILHOUETTE',r['view'],r['maximum_edge_change_pixels'],flush=True)
