"""ONE F anatomical cage hypothesis on E. CPU/background only, no native/GPU.

Uses Blender's built-in Laplacian Deform on a connected surface patch. Original
source files, topology, UV, head and protected anatomy are never edited. The
local prism Jacobian test is a surface deformation test, not a claim about an
unobserved interior volume. Root grants execution separately from code prep.
"""
from pathlib import Path
import sys,json,hashlib,heapq,importlib.util,time
import bpy,numpy as np
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;O=P/'proportion-F'
SOURCE_SHA='4ddfc843920f11b3d8e49efff0f36794684f3ab6505ee8812b17b76e4f653bc0'
DOWN=.025;INWARD=.009;PATCH_REACH=.065;DOWN_TRANSITION=.065;SIDE_TRANSITION=.025
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(path,data):Path(path).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8',newline='\n')
def smooth5(t):
    t=np.clip(t,0,1);return t*t*t*(10+t*(-15+6*t))
def graph(v,f):
    edges=np.unique(np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1),axis=0)
    length=np.linalg.norm(v[edges[:,0]]-v[edges[:,1]],axis=1);src=np.r_[edges[:,0],edges[:,1]];dst=np.r_[edges[:,1],edges[:,0]];distance=np.r_[length,length];order=np.argsort(src)
    return edges,np.r_[0,np.cumsum(np.bincount(src,minlength=len(v)))],dst[order],distance[order]
def geodesic(seeds,ptr,dst,length,limit=np.inf,barrier=None):
    out=np.full(len(ptr)-1,np.inf);out[seeds]=0;heap=[(0.,int(i)) for i in seeds];heapq.heapify(heap)
    while heap:
        d,i=heapq.heappop(heap)
        if d!=out[i] or d>limit:continue
        for k in range(ptr[i],ptr[i+1]):
            j=int(dst[k])
            if barrier is not None and barrier[j] and out[j]!=0:continue
            nd=d+length[k]
            if nd<out[j]:out[j]=nd;heapq.heappush(heap,(nd,j))
    return out
def grow(mask,edges,steps=1):
    out=mask.copy()
    for _ in range(steps):
        hit=out[edges].any(1);out[edges[hit].ravel()]=True
    return out
def vertex_normals(v,f):
    fn=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]);vn=np.zeros_like(v)
    for k in range(3):np.add.at(vn,f[:,k],fn)
    return vn/np.maximum(np.linalg.norm(vn,axis=1)[:,None],1e-30)
def component_ownership(v,guide_ids):
    spec=importlib.util.spec_from_file_location('F_source_components',P.parent/'shoulder11/field.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);_,reg=m.make(json.loads((P.parent/'shoulder11/parameters.json').read_text()))
    names=['curved_tapered_thorax_neck','breast_pair','shoulder_R','shoulder_L','upper_arm_R','upper_arm_L','anterior_fan_R','anterior_fan_L','posterior_wall_R','posterior_wall_L','trapezius_R','trapezius_L']
    q=v[guide_ids];score=np.column_stack([m.evaluate(reg[k],q) for k in names]);winner=np.argmin(score,axis=1)
    walls=np.min(score[:,6:10],axis=1);other=np.min(score[:,[0,1,2,3,4,5,10,11]],axis=1)
    return winner,walls<=other+.004,names
def make_cage(data,surface):
    v=data['world'].astype(float);f=data['triangles'];N=len(v);edges,ptr,dst,length=graph(v,f);normal=vertex_normals(v,f)
    bits=np.zeros(N,np.uint32)
    for k in range(3):np.bitwise_or.at(bits,surface['triangles'][:,k],np.left_shift(np.uint32(1),surface['face_region'].astype(np.uint32)))
    guide=np.flatnonzero(data['guide_vertex']>=0);winner,wall,names=component_ownership(v,guide);kind=np.full(N,-1);kind[guide]=winner
    head=np.zeros(N,bool);head[np.unique(f[data['source_part']==1])]=True
    retained=np.zeros(N,bool);retained[np.unique(f[data['source_part']==0])]=True
    core=np.zeros(N,bool);q=v[guide]
    core[guide]=wall|(winner==1)|((abs(q[:,0])<=.125)&(q[:,1]<=-.03)&(q[:,2]>=1.18)&(q[:,2]<=1.35))
    # New E collars are explicit topology, not a height-based limb exemption.
    rows=np.load(P/'collar-rows-E.npz');waist=np.zeros(N,bool);waist[rows['waist'].ravel()]=True
    upper_neck=np.zeros(N,bool);upper_neck[rows['neck'][-2:].ravel()]=True
    hard=head|retained|core|waist|upper_neck
    anatomical=((bits&sum(1<<r for r in [3,4,5,12,14,15]))!=0)|np.isin(kind,[2,3,4,5,10,11])
    seeds=np.flatnonzero(anatomical&~hard);reach=geodesic(seeds,ptr,dst,length,PATCH_REACH)
    source_pool=(data['guide_vertex']>=0)|((bits&sum(1<<r for r in [12,14,15]))!=0)
    allowed=(reach<=PATCH_REACH)&source_pool&~hard
    # Two real mesh rings around the outside give a fixed geometric boundary.
    crossing=allowed[edges[:,0]]!=allowed[edges[:,1]];boundary=np.zeros(N,bool);boundary[edges[crossing].ravel()]=True;boundary=grow(boundary,edges,1)&allowed
    free=allowed&~boundary;fixed=~free
    core_distance=geodesic(np.flatnonzero(core),ptr,dst,length,.20)
    # Roof controls are actual cap/trap upper surfaces. Near protected junctions
    # their target fades over measured broad surface distance, never a forced lip.
    roof=free&np.isin(kind,[2,3,10,11])&(normal[:,2]>.45)&(v[:,2]>1.375)
    neck_ring=np.zeros(N,bool)
    lo,hi=json.loads((P/'assembly-E.json').read_text())['collar_triangle_ranges']['neck']
    # Actual guide/collar shared loop, not an asserted skeletal notch landmark.
    neck_faces=np.arange(lo,hi);touched=np.unique(f[neck_faces]);neck_ring[touched[(data['guide_vertex'][touched]>=0)|(abs(v[touched,2]-1.445)<1e-7)]]=True;neck_ring&=free
    roof|=neck_ring
    # Complete lateral crest across front/side/back Y stations. No fade inside X.
    crest=np.zeros(N,bool);cap_candidates=np.flatnonzero(free&np.isin(kind,[2,3,4,5])&(v[:,2]>1.325)&(abs(v[:,0])>.135))
    for side in [-1,1]:
        sideids=cap_candidates[v[cap_candidates,0]*side>0]
        bins=np.floor(v[sideids,1]/.006).astype(int)
        for b in np.unique(bins):
            cand=sideids[bins==b];crest[cand[np.argmax(abs(v[cand,0]))]]=True
    crest=grow(crest,edges,1)&free&np.isin(kind,[2,3,4,5])
    handles=roof|crest;assert handles.sum()>100 and roof.sum()>100 and crest.sum()>20
    target=np.zeros_like(v)
    down_weight=smooth5(core_distance/DOWN_TRANSITION)
    # Outer crest is lower than the roof; move its fractional cap height rather
    # than translating the entire joint through the preserved axillary wall.
    cap_fraction=np.clip((v[:,2]-1.325)/.080,0,1)
    target[roof,2]=-DOWN*down_weight[roof]
    target[crest&~roof,2]=-DOWN*cap_fraction[crest&~roof]*down_weight[crest&~roof]
    transverse=smooth5((abs(v[:,0])-.050)/.090)*smooth5(core_distance/SIDE_TRANSITION)
    target[handles,0]=-np.sign(v[handles,0])*INWARD*transverse[handles]
    # Full outer crest transverse plateau, only source-protected proximity can
    # attenuate it. Report that attenuation, do not claim every point moved9mm.
    controls=fixed|handles
    patch=grow(free|handles,edges,2);patch_faces=np.all(patch[f],axis=1);patch_ids=np.unique(f[patch_faces]);remap=np.full(N,-1,np.int32);remap[patch_ids]=np.arange(len(patch_ids))
    assert not np.any(hard&handles)
    report=dict(method='Blender built-in Laplacian Deform, connected anatomical surface patch, hard source boundary/core and whole roof/crest controls',source_component_limit='Primitive scores classify existing construction ownership, not measured anatomical bone boundaries or clearance.',down_hypothesis_m=DOWN,inward_hypothesis_m=INWARD,geodesic_patch_padding_m=PATCH_REACH,down_core_transition_m=DOWN_TRANSITION,inward_core_transition_m=SIDE_TRANSITION,component_names=names,free_vertices=int(free.sum()),hard_core_vertices=int(core.sum()),protected_vertices=int(fixed.sum()),roof_handles=int(roof.sum()),crest_handles=int(crest.sum()),patch_vertices=len(patch_ids),patch_triangles=int(patch_faces.sum()),handle_bounds=[v[handles].min(0).tolist(),v[handles].max(0).tolist()],roof_core_distance_percentiles_m=np.percentile(core_distance[roof],[0,5,50,95,100]).tolist(),crest_inward_requested_percentiles_m=np.percentile(abs(target[crest,0]),[0,5,50,95,100]).tolist(),upper_head_cut_fixed=True,hips_and_original_forearms_fixed=True,neck_guide_loop_is_not_skeletal_notch=True)
    return v,f,free,fixed,handles,target,patch_ids,remap[f[patch_faces]],report
def main():
    assert '--execute' in sys.argv,'Code preparation only. Root execution gate required.'
    assert sha(P/'joined-expanded-E.npz')==SOURCE_SHA
    O.mkdir(exist_ok=True);assert not (O/'geometry.npz').exists(),'Do not overwrite the one frozen F candidate'
    data=np.load(P/'joined-expanded-E.npz');surface=np.load(P/'surface-v10-expanded-E-source-branches.npz');v,f,free,fixed,handles,target,ids,patch_f,report=make_cage(data,surface)
    write(O/'cage-plan.json',report);np.savez_compressed(O/'cage.npz',free_vertex_ids=np.flatnonzero(free).astype(np.int32),protected_vertex_ids=np.flatnonzero(fixed).astype(np.int32),handle_vertex_ids=np.flatnonzero(handles).astype(np.int32),requested_handle_delta=target[handles],patch_vertex_ids=ids)
    bpy.ops.wm.read_factory_settings(use_empty=True);mesh=bpy.data.meshes.new('F_AnatomicalCagePatch');mesh.from_pydata(v[ids].tolist(),[],patch_f.tolist());mesh.update();ob=bpy.data.objects.new(mesh.name,mesh);bpy.context.scene.collection.objects.link(ob);bpy.context.view_layer.objects.active=ob;ob.select_set(True)
    group=ob.vertex_groups.new(name='F_FixedSourceAndActualHandles');anchor=np.flatnonzero((fixed|handles)[ids]);group.add(anchor.tolist(),1.,'REPLACE');mod=ob.modifiers.new('F_OneLaplacianCage','LAPLACIANDEFORM');mod.vertex_group=group.name;mod.iterations=10
    start=time.time();bpy.ops.object.laplaciandeform_bind(modifier=mod.name);assert mod.is_bind
    edited=v[ids].copy();edited[handles[ids]]+=target[ids[handles[ids]]];mesh.vertices.foreach_set('co',edited.astype(np.float32).ravel());mesh.update();bpy.context.view_layer.update()
    depsgraph=bpy.context.evaluated_depsgraph_get();evaluated=ob.evaluated_get(depsgraph);result=evaluated.to_mesh();q=np.asarray([x.co[:] for x in result.vertices],np.float32).astype(float);evaluated.to_mesh_clear()
    pin_local=fixed[ids];pin_error=np.linalg.norm(q[pin_local]-v[ids[pin_local]],axis=1);handle_local=handles[ids];handle_error=np.linalg.norm(q[handle_local]-edited[handle_local],axis=1)
    report['solver_seconds']=time.time()-start;report['fixed_anchor_readback_max_m']=float(pin_error.max());report['handle_readback_max_m']=float(handle_error.max());write(O/'solver-readback.json',report)
    # Bounded float32 anchor encoding may be canonicalized by construction;
    # any physical soft-constraint drift is a STOP, not an after-the-fact mask.
    assert pin_error.max()<=2.5e-7,('Soft-anchor drift is physical; stop for root review',float(pin_error.max()))
    assert handle_error.max()<=2.5e-7,('Handle not honored at numeric floor',float(handle_error.max()))
    out=v.copy();editable=free[ids]|handles[ids];out[ids[editable]]=q[editable];out=out.astype(np.float32)
    assert np.array_equal(out[fixed],data['world'][fixed])
    olde1=v[f[:,1]]-v[f[:,0]];olde2=v[f[:,2]]-v[f[:,0]];oldcross=np.cross(olde1,olde2);newcross=np.cross(out[f[:,1]].astype(float)-out[f[:,0]],out[f[:,2]].astype(float)-out[f[:,0]])
    local_j=np.einsum('ij,ij->i',newcross,oldcross)/np.einsum('ij,ij->i',oldcross,oldcross);assert np.all(local_j>0),('Local surface/prism orientation failed',float(local_j.min()))
    report['local_J_scope']='Per-triangle affine extension keeping old normal direction fixed. Positive projected oriented area, not a global interior-volume diffeomorphism proof.';report['local_J_min']=float(local_j.min());report['maximum_delta_m']=float(np.linalg.norm(out.astype(float)-v,axis=1).max());report['topology_UV_sourcehead_exact']=True
    # Global changed-face intersection proof is separate from positive local J.
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    spec=importlib.util.spec_from_file_location('F_intersections',P.parent/'posterior-continuity08/geometry.py');geom=importlib.util.module_from_spec(spec);spec.loader.exec_module(geom)
    changed=np.any(out!=data['world'],axis=1);changed_faces=np.flatnonzero(changed[f].any(1));tree=BVHTree.FromPolygons([Vector(p) for p in out],f.tolist(),all_triangles=True);ctree=BVHTree.FromPolygons([Vector(p) for p in out],f[changed_faces].tolist(),all_triangles=True);seen=set();crossings=[]
    for local,j in ctree.overlap(tree):
        i=int(changed_faces[local]);j=int(j);key=tuple(sorted((i,j)))
        if i==j or key in seen or np.intersect1d(f[i],f[j]).size:continue
        seen.add(key)
        if geom.triangle_intersects(out[f[i]].astype(float),out[f[j]].astype(float)):crossings.append(key)
    report['new_nonadjacent_intersections']=crossings;write(O/'CPU-proof.json',report);assert not crossings,('New F intersection',crossings[:10])
    payload={k:data[k] for k in data.files};payload['world']=out;np.savez_compressed(O/'geometry.npz',**payload)
    np.savez_compressed(O/'surface.npz',world=out,triangles=surface['triangles'],loop_uv=surface['loop_uv'],face_region=surface['face_region'],meshfaceid=surface['meshfaceid'])
    meta=json.loads((P/'surface-v10-expanded-E-source-branches.json').read_text());meta.update(payload_version='F-one-anatomical-cage',surface_npz_path=str(O/'surface.npz'),surface_npz_sha256=sha(O/'surface.npz'),geometry_world_sha256=hashlib.sha256(out.tobytes()).hexdigest(),assembly_geometry_path=str(O/'geometry.npz'),F_CPU_proof=str(O/'CPU-proof.json'),ART_status='UNSELECTED until actual Fgray/source review')
    write(O/'surface.json',meta);report.update(geometry_sha256=sha(O/'geometry.npz'),surface_sha256=sha(O/'surface.npz'),native_saved=False,GPU_used=False);write(O/'CPU-proof.json',report)
    assert sha(P/'joined-expanded-E.npz')==SOURCE_SHA;print('F_CPU_ONE_CANDIDATE',json.dumps(report),flush=True)
if __name__=='__main__':main()
