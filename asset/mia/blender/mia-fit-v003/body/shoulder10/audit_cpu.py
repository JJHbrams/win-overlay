"""Actual same-topology mesh, map Jacobian, sections and intersections; CPU."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a=np.load(BASE/'posterior09.npz'); b=np.load(P/'shoulder10.npz')
v0=a['world'];v=b['world'];f=b['triangles'];assert np.array_equal(f,a['triangles'])
changed=np.any(v!=v0,axis=1);cf=np.flatnonzero(changed[f].any(1));assert np.isfinite(v).all()
n0,vn0=g.normals(v0.astype(float),f);n,vn=g.normals(v.astype(float),f)
J=jacobians(v0.astype(float));det=np.linalg.det(J);assert det.min()>0
center=v0[f].mean(1).astype(float);jc=jacobians(center)
transport=np.linalg.solve(jc.transpose(0,2,1),n0[:,:,None])[:,:,0];transport/=np.linalg.norm(transport,axis=1)[:,None]
transport_dot=np.einsum('ij,ij->i',transport,n);assert transport_dot.min()>.95
normal_dot=np.einsum('ij,ij->i',n0,n);assert normal_dot.min()>0
angle=np.degrees(np.arccos(np.clip(normal_dot,-1,1)))
area=np.linalg.norm(np.cross(v[f[:,1]].astype(float)-v[f[:,0]],v[f[:,2]].astype(float)-v[f[:,0]]),axis=1)
assert area.min()>1e-12
directed=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);ee,inv,count=np.unique(np.sort(directed,axis=1),axis=0,return_counts=True,return_inverse=True)
winding=np.bincount(inv,weights=np.where(directed[:,0]<directed[:,1],1,-1));assert np.all(count==2) and not np.any(winding)
parent=np.arange(len(v))
def root(i):
    while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
    return i
for x,y in ee:
    x=root(x);y=root(y)
    if x!=y:parent[x]=y
components=len({root(i) for i in range(len(v))});assert components==1
def tree(q,ff):return BVHTree.FromPolygons([Vector(x) for x in q],ff.tolist(),all_triangles=True)
alltree=tree(v,f);ctree=tree(v,f[cf]);seen=set();intersections=[];tested=0
for local,j in ctree.overlap(alltree):
    i=int(cf[local]);j=int(j);pair=tuple(sorted((i,j)))
    if i==j or pair in seen or np.intersect1d(f[i],f[j]).size:continue
    seen.add(pair);tested+=1
    if g.triangle_intersects(v[f[i]].astype(float),v[f[j]].astype(float)):intersections.append(pair)
assert not intersections,intersections[:20]
assert g.triangle_intersects(np.array([[0,0,0],[.01,0,0],[0,.01,0]]),np.array([[.002,.002,-.002],[.002,.002,.002],[.008,.002,0.]]))
def exact_set(name,mask):
    ids=np.flatnonzero(mask);faces=np.flatnonzero(mask[f].all(1));assert np.array_equal(v[ids],v0[ids])
    return dict(name=name,vertices=len(ids),triangles=len(faces),coords_exact=True,triangles_exact=True)
guards=[exact_set('allZ<=1.36 breast/fold/corridor/lowerbody',v0[:,2]<=1.36),exact_set('allZ>=1.465 upperneck/topseam',v0[:,2]>=1.465),
        exact_set('innernecksafety |X|<=.025',abs(v0[:,0])<=.025),exact_set('outerarm |X|>=.195',abs(v0[:,0])>=.195),
        exact_set('E breast envelope |X|<=.125,Y<=-.030,Z1.18..1.35',(abs(v0[:,0])<=.125)&(v0[:,1]<=-.030)&(v0[:,2]>=1.18)&(v0[:,2]<=1.35))]
assert np.array_equal(v[:,:2],v0[:,:2])
gaps=[]
for z,y in [(1.26,0.),(1.25,0.),(1.24,0.),(1.28,.035),(1.26,.020),(1.265,.025)]:
    hs0=g.line_hits(v0,f,0,{1:y,2:z});hs=g.line_hits(v,f,0,{1:y,2:z})
    assert hs==hs0
    positive=[h for h in hs if 0<h['world'][0]<.30]
    intervals=[[positive[i]['world'][0],positive[i+1]['world'][0]] for i in range(0,len(positive)-1,2)]
    gaps.append(dict(z=z,y=y,allhits_exact=True,hits=hs,air_intervals=intervals,widths_mm=[1000*(bb-aa) for aa,bb in intervals]))
assert gaps[0]['widths_mm'][0]>9.3
roofs=[]
for y in [-.025,0,.025,.045]:
    samples=[]
    for x in np.arange(.025,.1876,.0025):
        before=g.line_hits(v0,f,2,{0:float(x),1:y});after=g.line_hits(v,f,2,{0:float(x),1:y})
        if before and after:
            p0=before[-1];p1=after[-1];samples.append(dict(x=float(x),before=p0,after=p1,delta_z_mm=1000*(p1['world'][2]-p0['world'][2])))
    row=dict(y=y,samples=samples)
    for key in ['before','after']:
        curve=np.array([s[key]['world'] for s in samples]);dx=np.diff(curve[:,0]);slope=np.diff(curve[:,2])/dx
        tangent=np.arctan(slope);turn=np.degrees(abs(np.diff(tangent)))
        row[key+'_tangent_diagnostics']=dict(maximum_adjacent_tangent_turn_degrees=float(turn.max()),slope_range=[float(slope.min()),float(slope.max())],
                 limit='Actual2.5mm XZ polyline at fixedY, not source-corresponding surface points or automatic curvature/art acceptance.')
    roofs.append(row)
sections=[]
for z in [1.36,1.365,1.38,1.40,1.42,1.44,1.465]:
    row=dict(z=z,states=[])
    for name,q in [('09',v0),('10',v)]:
        widths={};depths={}
        for y in [-.025,0,.025,.045]:
            hs=g.line_hits(q,f,0,{1:y,2:z});widths[str(y)]=dict(hits=hs,total_outer_span_mm=1000*(hs[-1]['world'][0]-hs[0]['world'][0]) if hs else None)
        for x in [.04,.08,.12,.16]:
            hs=g.line_hits(q,f,1,{0:x,2:z});depths[str(x)]=dict(hits=hs,total_outer_span_mm=1000*(hs[-1]['world'][1]-hs[0]['world'][1]) if hs else None)
        row['states'].append(dict(state=name,widths=widths,depths=depths))
    sections.append(row)
protected=read(P/'protected-input-hashes.json')
for path,h in protected.items():assert sha(path)==h,path
report=dict(status='CPU technical guards PASS; shape/source ART UNVERIFIED',baseline_sha256=sha(BASE/'posterior09.npz'),candidate_sha256=sha(P/'shoulder10.npz'),
    vertices=len(v),triangles=len(f),finite=True,triangles_exact=True,X_Y_coordinates_exact=True,connected_components=components,euler_characteristic=len(v)-len(ee)+len(f),
    boundary_edges=int((count==1).sum()),nonmanifold_edges=int((count>2).sum()),inconsistent_winding=int(np.count_nonzero(winding)),minimum_double_area_m2=float(area.min()),
    Jacobian=dict(analytical_global_lower_bound=1-.032*1.875/.085,actual_vertex_determinant_range=[float(det.min()),float(det.max())],
                  actual_vertex_condition_max=float(np.linalg.cond(J).max()),actual_triangle_transport_dot_min=float(transport_dot.min()),
                  global_injectivity='For eachfixedX,Y Zmap strictly increasing, identity outsideinterval. Discrete renderedtriangles also checked.'),
    actual_triangle_original_normal_dot_min=float(normal_dot.min()),actual_normal_change_degrees=np.percentile(angle[cf],[50,95,99,100]).tolist(),
    changed_vertices=int(changed.sum()),changed_triangles=len(cf),new_nonadjacent_intersections=intersections,narrow_phase_pairs=tested,positive_crossing_control=True,
    protected_sets=guards,protected_files_checked=len(protected),signed_volume_m3=g.volume(v.astype(float),f),volume_delta_mL=1e6*(g.volume(v.astype(float),f)-g.volume(v0.astype(float),f)),
    actual_gap_planes=gaps,actual_crossY_roofs=roofs,actual_fixedZ_sections=sections,
    scope='Static09 upperroof reshaping only. X/Ypointcoords exact, physicalfixedZ widths/depths change; no sourcewidth authority inferred.',
    native_saved=False,GPU_used=False)
write(P/'CPU-audit.json',report)
print('SHOULDER10_CPU_GUARDS',json.dumps({k:report[k] for k in ['changed_vertices','changed_triangles','narrow_phase_pairs','actual_normal_change_degrees','volume_delta_mL','Jacobian']}),flush=True)
for row in roofs:print('CROSSY_TANGENT',row['y'],row['before_tangent_diagnostics'],row['after_tangent_diagnostics'],flush=True)
for row in sections:
    print('PHYSICAL_Z',row['z'],[(s['state'],s['widths']['0']['total_outer_span_mm'],s['depths']['0.08']['total_outer_span_mm']) for s in row['states']],flush=True)
