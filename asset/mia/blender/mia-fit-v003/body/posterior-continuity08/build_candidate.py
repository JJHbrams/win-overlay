"""One measured posterior roof-rail form correction; CPU only, no smoothing."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
import json,hashlib,heapq
import numpy as np
from geometry import normals,roof,volume
P=Path(__file__).resolve().parent
CAN=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia')
E=CAN/'blender/mia-fit-v003/body/design-sculpt07/E';D=E.parent/'D'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
expected={'breast-step.npz':'1ea39f3ee1f56b32bc52c05263f5a4c74c11d5f849d2843a8db69907133d5e9e',
          'sculpt07-E.npz':'4c4b8c74baf3daedc86866a3cd2c7db90dfa1d22ed95c15e4e20afb08992f9da'}
for name,h in expected.items():assert sha(E/name)==h
assert sha(D/'sculpt07-D.npz')=='2a562dd1428dfcbad6a85068313154642112e54d1f26a7b3a00cb8f53a2ce5ef'
assert not (P/'posterior08.npz').exists(),'One frozen candidate; do not overwrite or sweep'
protected={str(p):sha(p) for folder in [D,E] for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and 'bra-diagnostic' not in p.parts}
data=np.load(E/'breast-step.npz');old=data['world'];v=old.astype(float);f=data['triangles'];d=np.load(D/'sculpt07-D.npz');dv=d['world'];df=d['triangles'];face,vn=normals(v,f)
edges=np.unique(np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1),axis=0)
adj=[[] for _ in v]
for a,b in edges:
    ll=float(np.linalg.norm(v[a]-v[b]));adj[a].append((int(b),ll));adj[b].append((int(a),ll))
lookup={tuple(q):i for i,q in enumerate(old)}
def vertices_for(ids):
    return np.unique([lookup[tuple(dv[i])] for fi in ids for i in df[fi]])
def distance(seeds,allowed,cutoff=.05):
    out=np.full(len(v),np.inf);queue=[]
    for i in seeds:
        if allowed[i]:out[i]=0.;heapq.heappush(queue,(0.,int(i)))
    while queue:
        dd,i=heapq.heappop(queue)
        if dd!=out[i] or dd>cutoff:continue
        for j,ll in adj[i]:
            nd=dd+ll
            if allowed[j] and nd<out[j] and nd<=cutoff:out[j]=nd;heapq.heappush(queue,(nd,j))
    return out
def smooth(x):x=np.clip(x,0,1);return x**3*(10-15*x+6*x*x)
def compact(x):return np.maximum(0,1-x*x)**3*(abs(x)<1)
source_ownership=json.loads((E/'posterior-fair-audit.json').read_text(encoding='utf-8'))['ownership']
weight=np.zeros(len(v));delta=np.zeros_like(v);rows=[];fixed_all=[];domains=[]
for source in source_ownership:
    sign=source['side_sign'];seeds=vertices_for(source['seed_D_triangles']);fixed=vertices_for(source['fixed_D_triangles'])
    allowed=(sign*v[:,0]>.132)&(sign*v[:,0]<.171)&(v[:,1]>.012)&(v[:,1]<.050)&(v[:,2]>1.255)&(v[:,2]<1.289)&(vn[:,1]>.25)
    ds=distance(seeds,allowed,.030);domain=np.isfinite(ds);boundary=np.zeros(len(v),bool)
    for i in np.flatnonzero(domain):boundary[i]=any(not domain[j] for j,_ in adj[i])
    boundary[fixed]=True;fixed_ids=np.flatnonzero(boundary);bd=distance(fixed_ids,domain,.050)
    # Actual roof-leg normals, projected into its fixed-Y physical section.
    inner=roof(v,f,sign*.1425,.020);outer=roof(v,f,sign*.1575,.020);assert inner and outer
    legs=np.array([inner['normal'],outer['normal']]);legs[:,1]=0.;legs/=np.linalg.norm(legs,axis=1)[:,None]
    direction=legs.sum(0);direction/=np.linalg.norm(direction);assert direction[2]<-.9 and abs(direction[1])<1e-12
    w=compact((sign*v[:,0]-.151)/.020)*compact((v[:,2]-1.268)/.022)*smooth(bd/.003)
    w[~domain]=0.;w[boundary]=0.;assert w.max()>.05;w/=w.max()
    delta+=.0017*w[:,None]*direction;weight=np.maximum(weight,w);fixed_all.extend(fixed_ids);domains.extend(np.flatnonzero(domain))
    rail=[]
    for y in [.018,.020,.025,.030]:
        for x in [sign*.145,sign*.150,sign*.155]:
            h=roof(v,f,x,y)
            if h:rail.append(h)
    rows.append(dict(side_sign=sign,source_D_seed_triangles=source['seed_D_triangles'],source_D_fixed_triangles=source['fixed_D_triangles'],
        domain_vertices=int(domain.sum()),active_vertices=int((w>0).sum()),fixed_boundary_vertices=len(fixed_ids),
        actual_section_y=.020,inner_roof_anchor=inner,outer_roof_anchor=outer,target_direction_world=direction.tolist(),
        C2_profile='1.7mm * compact((sideX-.151)/.020) * compact((Z-1.268)/.022) * quintic(distance_to_fixed_band/.003), normalized once per side; compact(t)=(1-t²)^3 for|t|<1, else0',
        direction_reason='Unit XZ-normal bisector of actual roof legs; moves mainly down with a small medial component. No posterior-Y inflation or Laplacian/Taubin passes.',actual_source_roof_rail=rail))
active=np.flatnonzero(weight>0);new=old.copy();new[active]=(v[active]+delta[active]).astype(np.float32)
assert np.array_equal(new[weight==0],old[weight==0])
np.savez_compressed(P/'posterior08.npz',world=new,triangles=f)
np.savez_compressed(P/'delta.npz',indices=active,delta_world=new[active]-old[active],weights=weight[active].astype(np.float32),fixed_indices=np.unique(fixed_all),domain_indices=np.unique(domains))
for name,h in protected.items():assert sha(name)==h
report=dict(status='ONE CPU-built form hypothesis; ART UNVERIFIED',source_breast_step=dict(path=str(E/'breast-step.npz'),sha256=expected['breast-step.npz']),failed_Taubin_comparison=dict(path=str(E/'sculpt07-E.npz'),sha256=expected['sculpt07-E.npz']),
    candidate_sha256=sha(P/'posterior08.npz'),delta_sha256=sha(P/'delta.npz'),vertices=len(v),triangles=len(f),active_vertices=len(active),maximum_displacement_mm=float(np.linalg.norm(new-old,axis=1).max()*1000),
    median_active_displacement_mm=float(np.median(np.linalg.norm(new[active]-old[active],axis=1))*1000),
    volume_before_m3=volume(v,f),volume_after_m3=volume(new.astype(float),f),volume_delta_m3=volume(new.astype(float),f)-volume(v,f),
    ownership=rows,topology_unchanged=True,input='E breast-step only; replaces failed Taubin, never stacks it',native_saved=False,GPU_used=False)
(P/'build-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
(P/'protected-input-hashes.json').write_text(json.dumps(protected,indent=2)+'\n',encoding='utf-8',newline='\n')
print('POSTERIOR08_BUILT',json.dumps({k:report[k] for k in ['active_vertices','maximum_displacement_mm','median_active_displacement_mm','volume_delta_m3']}),flush=True)
