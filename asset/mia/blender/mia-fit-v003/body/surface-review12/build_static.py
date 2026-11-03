"""One private static assembly, exact donorhead/lowerbody and11core, realcollars."""
from pathlib import Path
import sys,json,hashlib,importlib.util
import numpy as np
sys.dont_write_bytecode=True;P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));from mesh_ops import Mesh,SectionSource,minimum_bending_rows
sp=importlib.util.spec_from_file_location('review12_geometry',P.parent/'posterior-continuity08/geometry.py');g=importlib.util.module_from_spec(sp);sp.loader.exec_module(g)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();write=lambda p,d:Path(p).write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8',newline='\n')
wide='--revision-E' in sys.argv;waistGuide=1.145 if wide else 1.115;waistDonor=1.005 if wide else 1.035
d=np.load(P/'donor.npz');gd=np.load(P.parent/'shoulder11/shoulder11-canonical.npz');v0=d['world'];f0=d['triangles'];vg=gd['world'];fg=gd['triangles'];offset=len(v0)
meta=json.loads((P/'donor.json').read_text());matBody=len(meta['material_slots']);assert len(v0)==80771 and sha(P.parent/'shoulder11/shoulder11-canonical.npz')=='9382e21638e35ce36e3818cc0eb8e060994cc05227a5c56b262dcea7f4b843e9'
normalMatrix=np.linalg.inv(np.load('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-fit-v003/body/inputs/mapping-frame1.npz')['matrix_world'][:3,:3])
worldCornerNormals=np.einsum('tci,ij->tcj',d['corner_normals'].astype(float),normalMatrix);worldCornerNormals/=np.maximum(np.linalg.norm(worldCornerNormals,axis=2)[:,:,None],1e-20);worldCornerNormals=worldCornerNormals.astype(np.float32)
W=np.column_stack([d[k] for k in ['armR','armL','legR','legL']]);N=np.zeros_like(v0,dtype=float)
for k in range(3):np.add.at(N,f0[:,k],worldCornerNormals[:,k])
N/=np.maximum(np.linalg.norm(N,axis=1)[:,None],1e-20);_,ng=g.normals(vg.astype(float),fg)
mesh=Mesh(np.vstack([v0,vg]),np.vstack([W,np.zeros((len(vg),4))]),np.vstack([N,ng]))
sourceEdges,sourceCounts=np.unique(np.sort(np.concatenate([f0[:,[0,1]],f0[:,[1,2]],f0[:,[2,0]]]),axis=1),axis=0,return_counts=True)
mesh.inherited_boundary={tuple(map(int,e)) for e in sourceEdges[sourceCounts==1]};mesh.inherited_nonmanifold={tuple(map(int,e)):int(c) for e,c in zip(sourceEdges[sourceCounts>2],sourceCounts[sourceCounts>2])}
uv=np.concatenate([d['uv_0'],d['uv_1'],d['uv_2'],worldCornerNormals,np.broadcast_to(np.eye(3),(len(f0),3,3))],axis=2)
ga=np.zeros((len(fg),3,12));ga[:,:,6:9]=ng[fg]
Z=np.array([0.,0,1.]);R=np.array([np.sin(np.deg2rad(25)),0,-np.cos(np.deg2rad(25))]);L=R*np.array([-1,1,1]);cGR=np.array([.236,0,1.17]);cDR=np.array([.25,0,1.13]);cGL=cGR*np.array([-1,1,1]);cDL=cDR*np.array([-1,1,1])
if wide:cGR=cGR-.020*R;cDR=cDR+.045*R;cGL=cGR*np.array([-1,1,1]);cDL=cDR*np.array([-1,1,1])
plane=lambda name,n,c:(name,np.asarray(n,float),float(c),None)
mesh.clipped(f0,uv,np.full(len(f0),matBody),0,[plane('donor_waist',-Z,waistDonor)])
mesh.clipped(f0,uv,d['triangle_materials'],1,[plane('donor_neck',Z,-1.465)])
mesh.clipped(f0,uv,np.full(len(f0),matBody),0,[plane('donor_waist',Z,-waistDonor),('donor_armR_semantic',None,.5,1),plane('donor_armR',R,-R@cDR)])
mesh.clipped(f0,uv,np.full(len(f0),matBody),0,[plane('donor_waist',Z,-waistDonor),('donor_armL_semantic',None,.5,0),plane('donor_armL',L,-L@cDL)])
mesh.clipped(fg+offset,ga,np.full(len(fg),matBody),2,[plane('guide_waist',Z,-waistGuide),plane('guide_neck',-Z,1.445),plane('guide_armR',-R,R@cGR),plane('guide_armL',-L,L@cGL)],source_offset=-len(f0))
loops,boundary=mesh.boundary_loops();classified={};inherited=[]
tests=dict(donor_waist=lambda q:abs(q[:,2]-waistDonor).max()<1e-7 and abs(q[:,0].mean())<.08,
 donor_neck=lambda q:abs(q[:,2]-1.465).max()<1e-7,guide_waist=lambda q:abs(q[:,2]-waistGuide).max()<1e-7,guide_neck=lambda q:abs(q[:,2]-1.445).max()<1e-7,
 donor_armR=lambda q:abs((q-cDR)@R).max()<1e-7 and q[:,0].mean()>.15,guide_armR=lambda q:abs((q-cGR)@R).max()<1e-7 and q[:,0].mean()>.15,
 donor_armL=lambda q:abs((q-cDL)@L).max()<1e-7 and q[:,0].mean()<-.15,guide_armL=lambda q:abs((q-cGL)@L).max()<1e-7 and q[:,0].mean()<-.15)
records=[]
for loop in loops:
    q=np.array(mesh.xyz)[loop];labels=[n for n,test in tests.items() if test(q)];name=labels[0] if len(labels)==1 else None
    if name:assert name not in classified;classified[name]=loop
    else:inherited.append(loop)
    records.append(dict(name=name or 'inherited_head_boundary',vertices=len(loop),bounds=[q.min(0).tolist(),q.max(0).tolist()],center=q.mean(0).tolist()))
discrete3='--revision-D3' in sys.argv or wide;discrete2='--revision-D2' in sys.argv or discrete3;discrete='--revision-D' in sys.argv or discrete2
write(P/('cut-loop-certification-E.json' if wide else 'cut-loop-certification-D3.json' if discrete3 else 'cut-loop-certification-D2.json' if discrete2 else 'cut-loop-certification-D.json' if discrete else 'cut-loop-certification.json'),dict(loops=records,required=list(tests),all_required_found=set(classified)==set(tests),inherited_boundary_loops=len(inherited)))
print('REVIEW12_CUT_LOOPS',json.dumps(records),flush=True);assert set(classified)==set(tests),list(classified)
collars={};collar_ranges={};revision='--revision-C' in sys.argv;sourceGuide=SectionSource(vg,fg) if revision or discrete else None;sourceDonor=SectionSource(v0,f0) if revision or discrete else None
for kind,axis in [('neck',Z),('waist',Z),('armR',R),('armL',L)]:
    provider=None;discreteProvider=None;bands=12
    if wide and kind!='neck':
        ordered0=mesh.ordered(classified['guide_'+kind],axis);ordered1=mesh.ordered(classified['donor_'+kind],axis)
        bands=int(np.ceil(abs((ordered1[2]-ordered0[2])@axis)/.004-1e-8))
    if revision:
        direction=-1 if kind=='waist' else 1
        def provider(a,b,angles,direction=direction):
            h0=sourceGuide.row_step(a);h1=sourceDonor.row_step(b);inner0=sourceGuide.sample(a,-direction*h0,angles);inner1=sourceDonor.sample(b,direction*h1,angles)
            return inner0,inner1,dict(source='ActualWORLDtriangle/plane adjacentsections; no customSHADINGnormal inlofttangent',guide_step_m=h0,donor_step_m=h1,handle_length_rule='ONEactualadjacentsectionchord asBezierhandle (Hermitederivative3*chord)',continuity='GeometricG1/tangent-aware; parameterC1notclaimed')
    if discrete:
        direction=-1 if kind=='waist' else 1
        def discreteProvider(a,b,angles,p0,p1,bands,direction=direction):
            rowSpacing=abs(float((b[2]-a[2])@a[-1]))/bands
            g1=sourceGuide.sample(a,-direction*rowSpacing,angles);g2=sourceGuide.sample(a,-direction*2*rowSpacing,angles)
            d1=sourceDonor.sample(b,direction*rowSpacing,angles);d2=sourceDonor.sample(b,direction*2*rowSpacing,angles)
            sigma=None;spacing=None
            if discrete3:
                def section_spacing(frame):
                    pts=np.asarray(mesh.xyz)[frame[0]];chord=np.linalg.norm(np.roll(pts,-1,axis=0)-pts,axis=1);return dict(median_m=float(np.median(chord)),p75_m=float(np.percentile(chord,75)))
                spacing=dict(guide=section_spacing(a),donor=section_spacing(b));sigma=2*max(spacing['guide']['p75_m'],spacing['donor']['p75_m'])
            q,info=minimum_bending_rows(p0,p1,(g1,g2),(d1,d2),bands,a[-1],fixed_end_rows=1 if discrete2 else 2,angular_sigma=sigma);info['physical_row_spacing_m']=rowSpacing
            if discrete3:info['angular_scale_basis']=dict(rule='One sigma equals two upper-quartile actual source cut-section facet chords; no sweep',section_chord_spacing=spacing)
            return q,info
    if wide and kind=='neck':
        def discreteProvider(a,b,angles,p0,p1,bands):
            old=np.load(P/'joined-discrete-D3.npz');ids=np.load(P/'collar-rows-D3.npz')['neck'];assert ids.shape==(bands-1,len(angles))
            return np.concatenate([p0[None],old['world'][ids].astype(float),p1[None]]),dict(method='Reuse accepted-for-comparison D3 neck rows EXACTLY; E changes only expanded waist/arm collars',source_geometry_sha256=sha(P/'joined-discrete-D3.npz'),source_rows='collar-rows-D3.npz:neck')
    startFace=len(mesh.faces);collars[kind]=mesh.collar(classified['guide_'+kind],classified['donor_'+kind],axis,matBody,3,bands=bands,section_provider=provider,discrete_provider=discreteProvider);collar_ranges[kind]=[startFace,len(mesh.faces)]
afterLoops,_=mesh.boundary_loops();assert len(afterLoops)==len(inherited),'New collarboundary remains'
faces=np.asarray(mesh.faces,np.int32);attrs=np.asarray(mesh.attrs,np.float32);world=np.asarray(mesh.xyz,np.float32);used=np.unique(faces);remap=np.full(len(world),-1,np.int32);remap[used]=np.arange(len(used));world=world[used];faces=remap[faces]
source_vertex=np.full(len(used),-1,np.int32);sel=used<len(v0);source_vertex[sel]=used[sel];guide_vertex=np.full(len(used),-1,np.int32);sel=(used>=offset)&(used<offset+len(vg));guide_vertex[sel]=used[sel]-offset
target=P/('joined-expanded-E.npz' if wide else 'joined-discrete-D3.npz' if discrete3 else 'joined-discrete-D2.npz' if discrete2 else 'joined-discrete-D.npz' if discrete else 'joined-geometric-C.npz' if revision else 'joined-static.npz')
np.savez_compressed(target,world=world,triangles=faces,old_loop_uv=attrs[:,:,:6].reshape(-1,3,3,2),source_corner_normals=attrs[:,:,6:9],source_corner_bary=attrs[:,:,9:12],
    triangle_materials=np.asarray(mesh.material,np.int16),source_part=np.asarray(mesh.part,np.int16),source_face=np.asarray(mesh.sourceface,np.int32),source_vertex=source_vertex,guide_vertex=guide_vertex,vertex_limb_weights=np.asarray(mesh.weights,np.float32)[used])
lookup={q.tobytes() for q in world};headids=np.flatnonzero(v0[:,2]>=1.469);lowerids=np.flatnonzero(v0[:,2]<=waistDonor)
assert all(v0[i].tobytes() in lookup for i in headids) and all(v0[i].tobytes() in lookup for i in lowerids)
core=(abs(vg[:,0])<=.125)&(vg[:,1]<=-.03)&(vg[:,2]>=1.18)&(vg[:,2]<=1.35);assert all(q.tobytes() in lookup for q in vg[core])
rowArrays={k:remap[np.asarray(info.pop('row_vertex_ids'),np.int32)] for k,info in collars.items()};np.savez_compressed(P/('collar-rows-E.npz' if wide else 'collar-rows-D3.npz' if discrete3 else 'collar-rows-D2.npz' if discrete2 else 'collar-rows-D.npz' if discrete else 'collar-rows-C.npz' if revision else 'collar-rows-B.npz'),**rowArrays)
report=dict(status='Static joined CPU candidate; actualseamART pending',vertices=len(world),triangles=len(faces),body_material_index=matBody,collars=collars,
    retained_head_vertices_exact=len(headids),retained_lower_vertices_exact=len(lowerids),breast_core_vertices_exact=int(core.sum()),inherited_source_boundary_edges=len(mesh.inherited_boundary),inherited_hand_nonmanifold_edges=len(mesh.inherited_nonmanifold),new_body_seam_boundaries=0,
    original_uv_layers=meta['uv_layers'],retained_corner_normals_space='WORLD: sourceLOCALnormals transformed inverse-transpose ofactual180degZowner matrix',joined_sha256=sha(target),native_saved=False,GPU_used=False)
report['collar_triangle_ranges']=collar_ranges
write(P/('assembly-E.json' if wide else 'assembly-D3.json' if discrete3 else 'assembly-D2.json' if discrete2 else 'assembly-D.json' if discrete else 'assembly-C.json' if revision else 'assembly.json'),report);print('REVIEW12_STATIC_JOINED',json.dumps(report),flush=True)
