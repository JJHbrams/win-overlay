"""First connected local design prototype. Static posed; migration UNVERIFIED.

Edits an actual surface/control network and replaces irregular local stars.
No torso-angle chart, Gaussian transport, or old05 interior-coordinate seed.
"""
from pathlib import Path
from collections import defaultdict,deque,Counter
import json,hashlib,math
import numpy as np

P=Path(__file__).resolve().parent;B=P.parent
top=np.load(B/'posed-target/control-topology.npz');old=np.load(B/'inputs/mapping-frame1.npz')
base=np.load(B/'posed-target/target-01.npz');current=np.load(B/'posed-target/target-05.npz')
W=np.load(B/'current-body-weights.npz');G=np.load(B/'current-body-limit.npz')
q0=old['q0_world'];q1=base['target_world'];R=old['matrix_world'][:3,:3]
core=q0-np.einsum('nij,nj->ni',old['J_world_from_local'],G['soft_G']@np.linalg.inv(R).T)
sizes=top['polygon_sizes'];offset=np.r_[0,np.cumsum(sizes)]
faces=[list(map(int,top['loop_vertices'][offset[i]:offset[i+1]])) for i in range(len(sizes))]
mats=list(map(int,top['polygon_materials']));n=len(q0)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def adjacency(ff):
    ef=defaultdict(list);vf=defaultdict(list);ne=defaultdict(set)
    for i,f in enumerate(ff):
        for a,b in zip(f,f[1:]+f[:1]):
            ef[tuple(sorted((a,b)))].append(i);ne[a].add(b);ne[b].add(a);vf[a].append(i)
    return ef,vf,ne
ef,vf,ne=adjacency(faces)
def boundary(selected):
    directed=[]
    for fi in selected:
        f=faces[fi]
        for a,b in zip(f,f[1:]+f[:1]):
            if sum(j in selected for j in ef[tuple(sorted((a,b)))])==1:directed.append((a,b))
    nexts={a:b for a,b in directed}
    if len(nexts)!=len(directed):raise ValueError('Branching boundary')
    start=min(nexts);loop=[start];x=nexts[start]
    while x!=start and len(loop)<=len(directed):loop.append(x);x=nexts[x]
    if x!=start or len(loop)!=len(directed):raise ValueError('Not a single disk boundary')
    return loop
def star_region(seed):
    selected=set(vf[seed]);loop=boundary(selected)
    if len(loop)%2:
        queue=deque([(selected,[])])
        while queue:
            test,path=queue.popleft()
            if len(path)>4:continue
            candidates=set(j for fi in test for a,b in zip(faces[fi],faces[fi][1:]+faces[fi][:1]) for j in ef[tuple(sorted((a,b)))])-test
            for fi in sorted(candidates,key=lambda i:(len(faces[i])!=3,i)):
                if any(v>=3957 for v in faces[fi]) or max(q0[faces[fi],2])>=1.425:continue
                new=test|{fi}
                try:ring=boundary(new)
                except ValueError:continue
                if len(ring)%2==0:return new,ring,path+[fi]
                queue.append((new,path+[fi]))
        raise ValueError(('Cannot balance star',seed))
    return selected,loop,[]

# Literal 3D design cross-curves. Heights/projection/width are bounded by the
# user's v06 and E2/F2 support envelopes, not copied from rejected05 surface.
# Each row is an anterior surface curve from sternum through rounded breast
# mass to the lateral thorax. These curves stop at the socket branch.
zstation=np.array([1.145,1.170,1.185,1.200,1.220,1.245,1.265,1.285,1.310,1.335,1.360,1.385,1.410])
xstation=np.array([0.,.025,.055,.080,.105,.125,.145])
ycurves=np.array([
[-.104,-.100,-.090,-.065,-.028,.005,.025],
[-.103,-.102,-.098,-.080,-.040,-.005,.015],
[-.100,-.110,-.114,-.102,-.063,-.015,.010],
[-.099,-.125,-.132,-.125,-.086,-.035,.000],
[-.097,-.137,-.150,-.146,-.112,-.054,-.010],
[-.093,-.143,-.164,-.159,-.126,-.070,-.018],
[-.088,-.136,-.160,-.157,-.126,-.072,-.020],
[-.081,-.117,-.138,-.136,-.111,-.065,-.020],
[-.075,-.088,-.099,-.100,-.083,-.044,-.015],
[-.071,-.075,-.079,-.072,-.049,-.021,-.010],
[-.067,-.068,-.065,-.053,-.035,-.016,-.005],
[-.063,-.060,-.050,-.037,-.021,-.010,.000],
[-.045,-.040,-.027,-.015,.000,.005,.010]])
def pchip(x,y,xx):
    """Shape-preserving1D sampling only; final lip/curvature needs evaluation."""
    x=np.asarray(x);y=np.asarray(y);h=np.diff(x);d=np.diff(y)/h;m=np.zeros_like(y);m[0]=d[0];m[-1]=d[-1]
    for i in range(1,len(x)-1):
        if d[i-1]*d[i]>0:
            w1=2*h[i]+h[i-1];w2=h[i]+2*h[i-1];m[i]=(w1+w2)/(w1/d[i-1]+w2/d[i])
    i=np.clip(np.searchsorted(x,xx)-1,0,len(x)-2);t=np.clip((xx-x[i])/h[i],0,1)
    return (2*t**3-3*t**2+1)*y[i]+(t**3-2*t**2+t)*h[i]*m[i]+(-2*t**3+3*t**2)*y[i+1]+(t**3-t**2)*h[i]*m[i+1]
def front_y(x,z):
    yy=np.array([pchip(xstation,row,x) for row in ycurves]);return pchip(zstation,yy,z)

design=q1.copy();regions=np.zeros(n,np.int32);front=[]
for i in range(3957):
    # The branch is NOT frozen: it receives the separate connected socket
    # construction below. This front chart does not cross the arm junction.
    if 1.145<core[i,2]<1.410 and abs(q1[i,0])<.145 and q0[i,1]<-.030 and W['arm_sum'][i]<.50:
        design[i,2]=core[i,2];design[i,1]=front_y(abs(q1[i,0]),core[i,2]);front.append(i);regions[i]=1

# Actual connected semantic rails: anterior pec/root->humerus under deltoid,
# small curved axillary floor, and distinct posterior lat/teres wall. Targets
# are broad exterior volume relationships, never etched muscle grooves.
rails={
 'anterior':[(76,[.092,-.061,1.350]),(585,[.132,-.041,1.339]),(490,[.143,-.035,1.341]),(484,[.150,-.031,1.351]),(477,[.154,-.024,1.367]),(481,[.140,-.039,1.367]),(482,[.138,-.030,1.386])],
 'floor':[(155,[.112,-.004,1.329]),(503,[.118,-.002,1.313]),(153,[.106,.016,1.337])],
 'posterior':[(555,[.138,.029,1.282]),(554,[.128,.036,1.315]),(568,[.118,.034,1.337]),(547,[.134,.034,1.350]),(549,[.135,.033,1.365]),(552,[.127,.035,1.380]),(553,[.123,.033,1.391])]}
center=-.0004777
mirror={}
for i in range(3957):
    if q0[i,0]>0:
        p=q0[i].copy();p[0]=2*center-p[0];j=int(np.linalg.norm(q0[:3957]-p,axis=1).argmin());mirror[i]=j
handles={};semantic={}
for name,items in rails.items():
    for i,p in items:
        handles[i]=np.array(p);semantic[i]=name
        j=mirror[i];p=np.array(p);p[0]=2*center-p[0];handles[j]=p;semantic[j]=name
branch=set(handles)
for _ in range(2):branch|={v for u in branch for v in ne[u] if v<3957 and q0[v,2]<1.425 and q0[v,2]>1.235}
for i in branch:
    if i not in front:regions[i]=2
for i,p in handles.items():design[i]=p
# Harmonic interpolation of the actual branch control network, with explicit
# positional constraints and fixed exterior. This is not an ambient kernel.
for _ in range(100):
    prev=design.copy()
    for i in sorted(branch):
        if i in handles or i in front:continue
        adj=list(ne[i]);design[i]=.25*q1[i]+.75*prev[adj].mean(0)

# Freeze two exterior control rings of the COMPLETE construction region.
# This feather exists only at the exterior, never at internal triangles.
roi=set(front)|branch
for _ in range(2):roi|={v for u in roi for v in ne[u] if v<3957 and q0[v,2]<1.425 and q0[v,2]>1.10}
distance={v:0 for v in roi if any(u not in roi for u in ne[v])};queue=deque(distance)
while queue:
    u=queue.popleft()
    for v in ne[u]:
        if v in roi and v not in distance:distance[v]=distance[u]+1;queue.append(v)
for i in roi:
    f=np.clip((distance.get(i,0)-1)/3,0,1);f=f*f*(3-2*f)
    design[i]=q1[i]+f*(design[i]-q1[i])

# Distal socket stitch and two existing outside arm rows are exact01 context.
# This is a boundary-scope correction, not an anatomical form iteration.
armcycle=[459,464,466,492,496,499,501,556,555,542,540,457]
armhead=np.array([.10820262879133224,.003847315441817045,1.378481149673462]);armtail=np.array([.20236685872077942,-.006012566853314638,1.1807259321212769]);axis=armtail-armhead;limbt=((q0-armhead)@axis)/(axis@axis)
pins=set(armcycle)
for _ in range(2):pins|={v for u in pins for v in ne[u] if q0[v,0]>.10 and limbt[v]>.405}
pins|={mirror[i] for i in list(pins) if i in mirror}
for i in pins:design[i]=q1[i]

points=list(design);sourcepoints=list(q0);newfaces=[];removed=set();patches=[]
def grid_patch(selected,loop,seed):
    count=len(loop);choices=[]
    for m in range(2,count//2-1):
        nn=count//2-m
        if nn<2:continue
        for phase in range(count):
            ring=loop[phase:]+loop[:phase];coords={};k=0
            ids=[(i,0) for i in range(m+1)]+[(m,j) for j in range(1,nn+1)]+[(i,nn) for i in range(m-1,-1,-1)]+[(0,j) for j in range(nn-1,0,-1)]
            for ij,v in zip(ids,ring):coords[ij]=np.array(points[v])
            for i in range(1,m):
                for j in range(1,nn):
                    u=i/m;v=j/nn
                    coords[i,j]=(1-v)*coords[i,0]+v*coords[i,nn]+(1-u)*coords[0,j]+u*coords[m,j]-((1-u)*(1-v)*coords[0,0]+u*(1-v)*coords[m,0]+u*v*coords[m,nn]+(1-u)*v*coords[0,nn])
            score=0
            for i in range(m):
                for j in range(nn):
                    a,b,c,d=[coords[k] for k in [(i,j),(i+1,j),(i+1,j+1),(i,j+1)]];n1=np.cross(b-a,c-a);n2=np.cross(c-a,d-a)
                    score+=max(0,-float(n1@n2))*1e12
                    lengths=[np.linalg.norm(b-a),np.linalg.norm(c-b),np.linalg.norm(d-c),np.linalg.norm(a-d)]
                    score+=(max(lengths)/max(min(lengths),1e-8))**2
            choices.append((score,m,nn,ring,coords,ids))
    score,m,nn,ring,coords,ids=min(choices,key=lambda t:t[0]);mapping={ij:v for ij,v in zip(ids,ring)};appended=[]
    for i in range(1,m):
        for j in range(1,nn):
            idx=len(points);mapping[i,j]=idx;points.append(coords[i,j]);appended.append(idx)
            # Same Coons chart on the ORIGINAL local boundary is the transfer
            # seed. It never searches across the opposite axillary wall.
            u=i/m;v=j/nn
            def q(ij):return q0[mapping[ij]]
            sp=(1-v)*q((i,0))+v*q((i,nn))+(1-u)*q((0,j))+u*q((m,j))-((1-u)*(1-v)*q((0,0))+u*(1-v)*q((m,0))+u*v*q((m,nn))+(1-u)*v*q((0,nn)))
            sourcepoints.append(sp)
    ff=[[mapping[i,j],mapping[i+1,j],mapping[i+1,j+1],mapping[i,j+1]] for i in range(m) for j in range(nn)]
    return ff,dict(seed=seed,removed_faces=sorted(selected),boundary=loop,boundary_edges=len(loop),grid=[m,nn],new_vertices=appended,new_quads=len(ff),coons_quality_score=score)

for seed in [164,158,558,mirror[164],mirror[158],mirror[558]]:
    selected,loop,extra=star_region(seed)
    assert not selected&removed,('Patch stars overlap',seed,selected&removed)
    ff,report=grid_patch(selected,loop,seed);removed|=selected;newfaces+=ff;report['parity_expansion_faces']=extra;patches.append(report)
kept=[i for i in range(len(faces)) if i not in removed]
resultfaces=[faces[i] for i in kept]+newfaces;resultmats=[mats[i] for i in kept]+[1]*len(newfaces)
points=np.asarray(points);sourcepoints=np.asarray(sourcepoints)
assert np.array_equal(points[3957:4647],q1[3957:4647])
assert np.array_equal(q1[3957:4647],q0[3957:4647])
ef2,vf2,ne2=adjacency(resultfaces)
newedges={tuple(sorted((a,b))) for f in newfaces for a,b in zip(f,f[1:]+f[:1])}
assert all(len(ef2[e])==2 for e in newedges),[(e,len(ef2[e])) for e in newedges if len(ef2[e])!=2][:10]
badwinding=[]
for e in newedges:
    directions=[]
    for fi in ef2[e]:
        f=resultfaces[fi];directions.extend((a,b) for a,b in zip(f,f[1:]+f[:1]) if tuple(sorted((a,b)))==e)
    if directions[0]!=directions[1][::-1]:badwinding.append(e)
assert not badwinding,badwinding[:10]
armedges=[tuple(sorted((a,b))) for a,b in zip(armcycle,armcycle[1:]+armcycle[:1])]
assert all(e in ef2 and len(ef2[e])==len(ef[e]) for e in armedges)
assert np.array_equal(points[armcycle],q1[armcycle])
families={'cup':[3923,3924,3925,3926,3927,3928,3929,3930,3931,3932,3933,3947,3948,3949,3950], 'cap':[874,1872,870,2959]}
for family,ids in families.items():assert all(i in kept for i in ids),(family,set(ids)&removed)
def route(start,targets):
    previous={start:None};queue=deque([start]);end=None
    while queue:
        u=queue.popleft()
        if u in targets:end=u;break
        for v in ne2[u]:
            if v not in previous and points[v,2]>1.235 and points[v,2]<1.425 and points[v,0]>.07:
                previous[v]=u;queue.append(v)
    assert end is not None
    path=[]
    while end is not None:path.append(end);end=previous[end]
    return path[::-1]
paths={str(p['seed']):route(p['new_vertices'][0],set(armcycle)) for p in patches if p['seed'] in [158,558]}

def closest(p,tri):
    a,b,c=tri;ab=b-a;ac=c-a;d=p-a;gram=np.array([[ab@ab,ab@ac],[ab@ac,ac@ac]])
    candidates=[]
    if np.linalg.det(gram)>1e-20:
        uv=np.linalg.solve(gram,[ab@d,ac@d]);bar=np.array([1-uv.sum(),uv[0],uv[1]])
        if min(bar)>=0:candidates.append((np.linalg.norm(bar@tri-p),bar))
    for ia,ib in [(0,1),(1,2),(2,0)]:
        v=tri[ib]-tri[ia];t=np.clip((p-tri[ia])@v/max(v@v,1e-30),0,1);bar=np.zeros(3);bar[ia]=1-t;bar[ib]=t;candidates.append((np.linalg.norm(bar@tri-p),bar))
    return min(candidates,key=lambda x:x[0])
rawtri=top['triangles'];correspondence=[]
for patch in patches:
    candidates=[]
    for fi in patch['removed_faces']:
        for tid in np.flatnonzero(np.isin(rawtri,faces[fi]).all(1)):candidates.append((int(tid),fi))
    for vid in patch['new_vertices']:
        choices=[]
        for tid,fi in candidates:
            error,bar=closest(sourcepoints[vid],q0[rawtri[tid]]);choices.append((error,tid,fi,bar))
        error,tid,fi,bar=min(choices,key=lambda x:x[0]);correspondence.append(dict(new_id=vid,semantic_patch_seed=patch['seed'],source_raw_triangle=tid,source_raw_polygon=fi,barycentric=bar.tolist(),source_error_mm=float(error*1000)))
lengths=np.array([len(f) for f in resultfaces],np.int32);flat=np.array([v for f in resultfaces for v in f],np.int32)
np.savez_compressed(P/'prototype06.npz',world=points,source_world=sourcepoints,loop_vertices=flat,polygon_sizes=lengths,polygon_materials=np.array(resultmats,np.int32),kept_original_faces=np.array(kept,np.int32),retired_original_faces=np.array(sorted(removed),np.int32),original_world=q0,regions=np.r_[regions,np.full(len(points)-n,3,np.int32)])
constraint=json.loads((B/'source-binding/constraints.json').read_text())
report=dict(status='STATIC DESIGN PROTOTYPE; migration/rig/UV/art UNVERIFIED',base_native_sha256='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1',
    method='Actual front control cross-curves + connected anterior/floor/posterior branch network; explicit local quad-star replacement. No radial torso chart/Gaussian/old05 interior restore.',
    source_constraints_sha256=sha(B/'source-binding/constraints.json'),source_notes='v06 global height/profile and E2/F2 rounded supported envelope govern broad manually authored 3D curves; cloth edge is not a naked crease. Values are design hypothesis, not measured unique anatomy.',
    source_support_widths=constraint.get('source_sections',constraint.get('sections',[])),design_heights=zstation.tolist(),design_x=xstation.tolist(),design_front_y=ycurves.tolist(),semantic_rails=rails,
    original_vertices=n,appended_vertices=len(points)-n,retired_faces=len(removed),new_quad_faces=len(newfaces),patches=patches,
    retained_cap_and_cup_verified_faces=families,preserved_arm_cycle=armcycle,preserved_arm_cycle_edges_verified=True,preserved_arm_cycle_positions_exact_to01=True,distal_arm_pin_ids=sorted(pins),new_anterior_posterior_to_arm_paths=paths,
    face690_raw_exact=True,all_new_edges_two_incidents=True,new_edge_winding_consistent=True,exterior_two_control_rings_exact_to_context01=True,
    context='target01 exterior and25percent q1 positional bias in the branch harmonic solve. Rejected05 interior is not used.',new_vertex_correspondence=correspondence,
    original47_UV_weights_archived_in_exact_current_native=True,migration='UNVERIFIED; source_world seeds restricted to each removed local patch. New raw triangle/loop barycentric UV and freshArmature inverse are next gate.',
    prototype_sha256=sha(P/'prototype06.npz'),gpu_used=False,native_saved=False)
(P/'construction.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('PATCH06_STATIC_CONSTRUCTION_DONE',json.dumps(dict(vertices=len(points),new_quads=len(newfaces),retired_faces=len(removed),patches=[dict(seed=p['seed'],boundary=p['boundary_edges'],grid=p['grid']) for p in patches])),flush=True)
