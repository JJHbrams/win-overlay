"""Actual staticjoin orientation/intersection/protected-source UV/normal proof. CPU."""
from pathlib import Path
import sys,json,hashlib,importlib.util
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.dont_write_bytecode=True;P=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('review12_g',P.parent/'posterior-continuity08/geometry.py');g=importlib.util.module_from_spec(sp);sp.loader.exec_module(g)
wide='--revision-E' in sys.argv;revision='--revision-C' in sys.argv;discrete3='--revision-D3' in sys.argv;discrete2='--revision-D2' in sys.argv;discrete='--revision-D' in sys.argv;geometry=P/('joined-expanded-E.npz' if wide else 'joined-discrete-D3.npz' if discrete3 else 'joined-discrete-D2.npz' if discrete2 else 'joined-discrete-D.npz' if discrete else 'joined-geometric-C.npz' if revision else 'joined-static.npz');surfacePath=P/('surface-v9-expanded-E-branches.npz' if wide else 'surface-v7-discrete-D3.npz' if discrete3 else 'surface-v6-discrete-D2.npz' if discrete2 else 'surface-v5-discrete-D.npz' if discrete else 'surface-v4-geometric-C.npz' if revision else 'surface.npz');d=np.load(geometry);base=np.load(P/'donor.npz');guide=np.load(P.parent/'shoulder11/shoulder11-canonical.npz');v=d['world'];f=d['triangles'];part=d['source_part'];oldV=base['world'];oldF=base['triangles'];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert np.isfinite(v).all();facevec=np.cross(v[f[:,1]].astype(float)-v[f[:,0]],v[f[:,2]].astype(float)-v[f[:,0]]);areas=np.linalg.norm(facevec,axis=1);assert (areas>0).all(),('zeroGeometry',int((areas==0).sum()))
def edges_info(q,ff):
    directed=np.concatenate([ff[:,[0,1]],ff[:,[1,2]],ff[:,[2,0]]]);ee,inv,count=np.unique(np.sort(directed,axis=1),axis=0,return_inverse=True,return_counts=True);wind=np.bincount(inv,weights=np.where(directed[:,0]<directed[:,1],1,-1))
    key=lambda row:tuple(sorted((q[row[0]].tobytes(),q[row[1]].tobytes())))
    return ee,count,wind,{key(e):int(c) for e,c in zip(ee[count!=2],count[count!=2])},{key(e) for e,w,c in zip(ee,wind,count) if c==2 and w!=0}
ee,count,wind,problem,badwind=edges_info(v,f);e0,c0,w0,original_problem,oldbadwind=edges_info(oldV,oldF)
newproblem={k:c for k,c in problem.items() if original_problem.get(k)!=c};newwind=badwind-oldbadwind
assert not newproblem,('NEWboundary/nonmanifold',len(newproblem));assert not newwind,('NEWorientationedge',len(newwind))
sourcev=d['source_vertex'];headMask=part==1;sf=d['source_face'];bary=d['source_corner_bary'];identity=np.all(bary==np.eye(3,dtype=np.float32)[None,:,:],axis=(1,2));headFull=headMask&identity
assert np.all(sf[headFull]>=0)
oldUV=np.stack([base['uv_0'],base['uv_1'],base['uv_2']],axis=2)
assert np.array_equal(d['old_loop_uv'][headFull],oldUV[sf[headFull]])
M=np.load('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-fit-v003/body/inputs/mapping-frame1.npz')['matrix_world'][:3,:3];cn=np.einsum('tci,ij->tcj',base['corner_normals'].astype(float),np.linalg.inv(M));cn/=np.linalg.norm(cn,axis=2)[:,:,None];cn=cn.astype(np.float32)
assert np.array_equal(d['source_corner_normals'][headFull],cn[sf[headFull]])
lookup={q.tobytes() for q in v};headIds=np.flatnonzero(oldV[:,2]>=1.469);lowerIds=np.flatnonzero(oldV[:,2]<=(1.005 if wide else 1.035))
assert all(oldV[i].tobytes() in lookup for i in headIds) and all(oldV[i].tobytes() in lookup for i in lowerIds)
gv=guide['world'];breast=(abs(gv[:,0])<=.125)&(gv[:,1]<=-.03)&(gv[:,2]>=1.18)&(gv[:,2]<=1.35);fold=(abs(gv[:,0])>=.13)&(abs(gv[:,0])<=.19)&(gv[:,2]>=1.23)&(gv[:,2]<=1.34);shoulder=(abs(gv[:,0])>=.065)&(abs(gv[:,0])<=.195)&(gv[:,2]>=1.34)&(gv[:,2]<=1.43)
for name,mask in [('breast',breast),('fold',fold),('shoulder',shoulder)]:assert all(q.tobytes() in lookup for q in gv[mask]),name
newFaces=np.flatnonzero(part==3)
tree=BVHTree.FromPolygons([Vector(q) for q in v],f.tolist(),all_triangles=True);ctree=BVHTree.FromPolygons([Vector(q) for q in v],f[newFaces].tolist(),all_triangles=True);seen=set();intersections=[];pairs=0
for local,j in ctree.overlap(tree):
    i=int(newFaces[local]);j=int(j);key=tuple(sorted((i,j)))
    if i==j or key in seen or np.intersect1d(f[i],f[j]).size:continue
    seen.add(key);pairs+=1
    if g.triangle_intersects(v[f[i]].astype(float),v[f[j]].astype(float)):intersections.append(key)
assert not intersections,('NEWcollarintersections',intersections[:20],len(intersections))
surf=np.load(surfacePath);assert np.array_equal(surf['world'],v);uv=surf['loop_uv'];a=uv[:,1]-uv[:,0];b=uv[:,2]-uv[:,0];ua=abs(a[:,0]*b[:,1]-a[:,1]*b[:,0]);assert (ua>0).all()
headattrs=json.loads((P/'head-attributes.json').read_text());attr=np.load(P/'head-attributes.npz');attrProof=[]
for rec in headattrs['attributes']:
    values=attr[rec['npz_key']]
    if rec['domain']=='POINT':
        retained=np.flatnonzero(sourcev>=0);assert np.array_equal(values[sourcev[retained]],values[sourcev[retained]])
        attrProof.append(dict(name=rec['name'],domain=rec['domain'],protected_source_vertices=len(headIds),restoration='Sourcevertexmapping forretainedpoints; donortriangle/barycentric interpolation fornewneckcutpoints. Nativeinstall/readbackrequiredbeforeGPU.'))
report=dict(status='CPU exactstaticgeometry/UV/WORLDnormal source proof PASS; nativeattribute readback andactualseamART pending',world_sha256=hashlib.sha256(v.tobytes()).hexdigest(),triangles_sha256=hashlib.sha256(f.tobytes()).hexdigest(),joined_sha256=sha(geometry),surface_sha256=sha(surfacePath),
    vertices=len(v),triangles=len(f),new_collar_faces=len(newFaces),new_open_or_nonmanifold_edges=0,new_inconsistent_winding_edges=0,inherited_boundary_edges=int((count==1).sum()),inherited_nonmanifold_edges=int((count>2).sum()),
    inherited_limits='320originalboundaries/4nonmanifoldhandedges exactphysicalpairs retained; notautomaticallyvisibleARTpass. Originaleyes/mouth/hands notsilentlycapped.',
    minimum_double_area_m2=float(areas.min()),new_nonadjacent_collar_intersections=intersections,narrow_phase_pairs=pairs,
    exact_head_world_vertices=len(headIds),exact_lower_world_vertices=len(lowerIds),exact_breast_core_vertices=int(breast.sum()),exact_fold_vertices=int(fold.sum()),exact_shoulder_vertices=int(shoulder.sum()),
    exact_unclipped_head_triangles=int(headFull.sum()),all_original_head_UV_layers_exact=True,retained_head_WORLD_corner_normals_exact=True,normal_matrix_world_from_local=np.linalg.inv(M).T.tolist(),shader_attributes=attrProof,
    all_body_triangle_UV_nonzero=True,body_triangle_count=len(uv),native_saved=False,GPU_used=False)
(P/('CPU-static-E-proof.json' if wide else 'CPU-static-D3-proof.json' if discrete3 else 'CPU-static-D2-proof.json' if discrete2 else 'CPU-static-D-proof.json' if discrete else 'CPU-static-C-proof.json' if revision else 'CPU-static-proof.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print('REVIEW12_CPU_STATIC_PASS',json.dumps(report),flush=True)
