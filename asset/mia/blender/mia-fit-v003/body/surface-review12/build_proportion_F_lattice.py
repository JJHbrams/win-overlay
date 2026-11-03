"""ONE small-lattice F hypothesis, held E topology/UV and exact VG-zero pins.

One 13x5x12 control grid is evaluated by coordinate component. This permits
different physical compression/stretch supports for X and Z without shrinking
the entire neck or restoring pins after deformation. Y is identity by model.
No native save, render or original-data mutation.
"""
from pathlib import Path
import sys,json,hashlib,importlib.util,time,shutil
import bpy,numpy as np
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import build_proportion_F as cage
O=P/'proportion-F-lattice';sha=cage.sha;write=cage.write;sm=cage.smooth5
def main():
    assert '--execute' in sys.argv
    source=P/'joined-expanded-E.npz';assert sha(source)==cage.SOURCE_SHA
    O.mkdir(exist_ok=True);assert not (O/'geometry.npz').exists(),'Do not overwrite frozen one-candidate F'
    data=np.load(source);surface=np.load(P/'surface-v10-expanded-E-source-branches.npz');v,f,free,fixed,handles,requested,patch_ids,patch_f,report=cage.make_cage(data,surface);N=len(v)
    edges,ptr,dst,length=cage.graph(v,f);bits=np.zeros(N,np.uint32)
    for k in range(3):np.bitwise_or.at(bits,surface['triangles'][:,k],np.left_shift(np.uint32(1),surface['face_region'].astype(np.uint32)))
    sourceHead=np.zeros(N,bool);sourceHead[np.unique(f[data['source_part']==1])]=True
    sourceLower=np.zeros(N,bool);sourceLower[np.unique(f[data['source_part']==0])]=True
    rows=np.load(P/'collar-rows-E.npz');waist=np.zeros(N,bool);waist[rows['waist'].ravel()]=True
    headPins=sourceHead|(fixed&((bits&(1<<12))!=0)&(v[:,2]>1.45))
    lowerPins=sourceLower|waist
    compressionPins=fixed&~headPins&~lowerPins
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    from mathutils.kdtree import KDTree
    def physical_distance(mask):
        pinids=np.flatnonzero(mask);assert len(pinids)>0
        kd=KDTree(len(pinids))
        for j,i in enumerate(pinids):kd.insert(Vector(v[i]),j)
        kd.balance();ff=f[np.all(mask[f],axis=1)]
        tree=BVHTree.FromPolygons([Vector(p) for p in v],ff.tolist(),all_triangles=True) if len(ff) else None
        result=np.zeros(N)
        for i in np.flatnonzero(free):
            point=Vector(v[i]);distance=kd.find(point)[2]
            if tree is not None:
                found=tree.find_nearest(point)
                if found[0] is not None:distance=min(distance,found[3])
            result[i]=distance
        return result
    # Actual protected surface distance is ambient1-Lipschitz. This is only a
    # scalar protection support, not nearest-surface geometry projection.
    dCore=physical_distance(compressionPins);dHead=physical_distance(headPins);dLower=physical_distance(lowerPins)
    headStretch=sm(dHead/.020);lowerJoin=sm(dLower/.035)
    wz=sm(dCore/.065)*headStretch*lowerJoin;wx=sm(dCore/.025)*headStretch*lowerJoin
    wz[fixed]=0;wx[fixed]=0
    # Dirichlet heat conditioning of the scalar supports only. Never average
    # body positions. Pin-zero and existing roof plateaus are constraints.
    edgeLength=np.linalg.norm(v[edges[:,0]]-v[edges[:,1]],axis=1);edgeWeight=1/np.maximum(edgeLength,1e-12);degree=np.bincount(edges[:,0],weights=edgeWeight,minlength=N)+np.bincount(edges[:,1],weights=edgeWeight,minlength=N)
    localStep2=(np.bincount(edges[:,0],weights=edgeWeight*edgeLength**2,minlength=N)+np.bincount(edges[:,1],weights=edgeWeight*edgeLength**2,minlength=N))/np.maximum(degree,1e-20)
    sigma=.006;factor=.35;iterations=int(np.ceil(2*sigma*sigma/(factor*np.median(localStep2[free]))));conditioning={}
    def condition(weights,label,interior):
        initial=weights.copy();plateau=(weights==1.)&interior;transition=free&~plateau
        for _ in range(iterations):
            avg=(np.bincount(edges[:,0],weights=edgeWeight*weights[edges[:,1]],minlength=N)+np.bincount(edges[:,1],weights=edgeWeight*weights[edges[:,0]],minlength=N))/np.maximum(degree,1e-20)
            weights[transition]=(1-factor)*weights[transition]+factor*avg[transition]
        assert np.all(weights[fixed]==0) and np.all(weights[plateau]==1)
        conditioning[label]=dict(iterations=iterations,neighbor_blend=factor,target_median_sigma_m=sigma,effective_sigma_percentiles_m=np.percentile(np.sqrt(iterations*factor*localStep2[free]/2),[5,50,95]).tolist(),plateau_constraints=int(plateau.sum()),maximum_weight_change=float(abs(weights-initial).max()))
        return weights
    conditioning=dict(metric='Euclidean distance to actual protected triangles and isolated pin vertices, BVH/KD; smooth5 physical transitions',graph_geodesic_support_replaced_due_to_skinny_face_alias=True,graph_heat_filter_applied=False,position_projection=False)
    report.update(method='ONE small Blender B-spline lattice grid, separable X/Z components and predeclared anatomical VG supports',lattice_points=[13,5,12],head_stretch_transition_m=.020,core_vertical_compression_transition_m=.065,core_transverse_transition_m=.025,lower_join_transition_m=.035,support_scalar_conditioning=conditioning,Y_identity=True,posthoc_pin_restore=False)
    np.savez_compressed(O/'support.npz',editable_vertex_ids=np.flatnonzero(free).astype(np.int32),protected_vertex_ids=np.flatnonzero(fixed).astype(np.int32),handle_reference_vertex_ids=np.flatnonzero(handles).astype(np.int32),x_weights=wx.astype(np.float32),z_weights=wz.astype(np.float32),compression_pin_ids=np.flatnonzero(compressionPins).astype(np.int32),head_pin_ids=np.flatnonzero(headPins).astype(np.int32),lower_pin_ids=np.flatnonzero(lowerPins).astype(np.int32))
    bpy.ops.wm.read_factory_settings(use_empty=True);mesh=bpy.data.meshes.new('F_EIdentityInput');mesh.from_pydata(v.tolist(),[],f.tolist());mesh.update();body=bpy.data.objects.new(mesh.name,mesh);bpy.context.scene.collection.objects.link(body);bpy.context.view_layer.objects.active=body;body.select_set(True)
    groups={}
    for label,weights in [('X',wx),('Z',wz)]:
        group=body.vertex_groups.new(name='F_'+label+'_AnatomicalC2Support');groups[label]=group
        for i in np.flatnonzero(weights>0):group.add([int(i)],float(weights[i]),'REPLACE')
    lat=bpy.data.lattices.new('F_OneControlGrid');lat.points_u=13;lat.points_v=5;lat.points_w=12
    lat.interpolation_type_u=lat.interpolation_type_v=lat.interpolation_type_w='KEY_BSPLINE'
    ob=bpy.data.objects.new(lat.name,lat);bpy.context.scene.collection.objects.link(ob)
    rest=np.asarray([p.co_deform[:] for p in lat.points],float);intendedMin=np.array([-.315,-.150,1.050]);intendedMax=np.array([.315,.105,1.600]);scale=(intendedMax-intendedMin)/(rest.max(0)-rest.min(0));ob.scale=scale;ob.location=(intendedMin+intendedMax)/2-(rest.min(0)+rest.max(0))/2*scale;bpy.context.view_layer.update()
    world=np.asarray([ob.matrix_world@p.co_deform for p in lat.points],float);assert np.allclose(world.min(0),intendedMin,atol=1e-7,rtol=0) and np.allclose(world.max(0),intendedMax,atol=1e-7,rtol=0)
    dx=-np.sign(world[:,0])*cage.INWARD*sm((abs(world[:,0])-.040)/.060)
    dz=-cage.DOWN*sm((world[:,2]-1.150)/.200)
    # All outer columns remain at the full inward coefficient. No outer-X fade.
    assert np.allclose(abs(dx[abs(world[:,0])>=.105]),cage.INWARD)
    mod=body.modifiers.new('F_OneLatticeField','LATTICE');mod.object=ob;mod.strength=1.
    outputs={};unweighted={};start=time.time()
    for axis,delta,index in [('X',dx,0),('Z',dz,2)]:
        coords=rest.copy();coords[:,index]+=delta/ob.scale[index]
        for p,q in zip(lat.points,coords):p.co_deform=q
        mod.vertex_group='';mesh.update();bpy.context.view_layer.update();depsgraph=bpy.context.evaluated_depsgraph_get();evaluated=body.evaluated_get(depsgraph);me=evaluated.to_mesh();unweighted[axis]=np.asarray([p.co[:] for p in me.vertices],np.float32);evaluated.to_mesh_clear()
        mod.vertex_group=groups[axis].name;mesh.update();bpy.context.view_layer.update();depsgraph=bpy.context.evaluated_depsgraph_get();evaluated=body.evaluated_get(depsgraph);me=evaluated.to_mesh();q=np.asarray([p.co[:] for p in me.vertices],np.float32);evaluated.to_mesh_clear()
        assert np.array_equal(q[fixed],data['world'][fixed]),('VG0 source pin changed',axis)
        outputs[axis]=q
    out=data['world'].copy();out[:,0]=outputs['X'][:,0];out[:,2]=outputs['Z'][:,2]
    assert np.array_equal(out[fixed],data['world'][fixed]) and np.array_equal(out[:,1],data['world'][:,1])
    displacement=out.astype(float)-v;changed=np.any(out!=data['world'],axis=1);changed_faces=np.flatnonzero(changed[f].any(1));oldcross=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]);newcross=np.cross(out[f[:,1]].astype(float)-out[f[:,0]],out[f[:,2]].astype(float)-out[f[:,0]])
    localJ=np.einsum('ij,ij->i',newcross,oldcross)/np.einsum('ij,ij->i',oldcross,oldcross)
    # ONE analytic amplitude bound, not a sequence of geometry trials.
    e1=v[f[:,1]]-v[f[:,0]];e2=v[f[:,2]]-v[f[:,0]];u1=displacement[f[:,1]]-displacement[f[:,0]];u2=displacement[f[:,2]]-displacement[f[:,0]];den=np.einsum('ij,ij->i',oldcross,oldcross)
    A=np.einsum('ij,ij->i',np.cross(u1,e2)+np.cross(e1,u2),oldcross)/den;B=np.einsum('ij,ij->i',np.cross(u1,u2),oldcross)/den
    assert np.allclose(localJ,1+A+B,atol=1e-10,rtol=1e-10)
    floor=.25;roots=np.full(len(f),np.inf);linear=abs(B)<1e-12;take=linear&(A<0);roots[take]=-(1-floor)/A[take];disc=A*A-4*B*(1-floor);quad=~linear&(disc>=0)
    ix=np.flatnonzero(quad);rd=np.sqrt(disc[ix]);r1=(-A[ix]-rd)/(2*B[ix]);r2=(-A[ix]+rd)/(2*B[ix]);r1[r1<=0]=np.inf;r2[r2<=0]=np.inf;roots[ix]=np.minimum(r1,r2)
    limiting=int(np.argmin(roots));critical=float(roots[limiting]);amplitude=min(1.,.99*critical)
    np.savez_compressed(O/'raw-proposal-and-J.npz',raw_displacement_world=displacement.astype(np.float32),A=A,B=B,critical_roots=roots)
    report['raw_full_amplitude_min_J']=float(localJ.min());report['raw_full_amplitude_nonpositive_faces']=int((localJ<=0).sum())
    if amplitude<1:
        # A small representation sliver must not dictate an artist amplitude.
        assert np.linalg.norm(oldcross[limiting])>=1e-7,('Numerical/support sliver remains limiting; stop, no amplitude mask',limiting,float(np.linalg.norm(oldcross[limiting])))
        out=(v+amplitude*displacement).astype(np.float32);displacement=out.astype(float)-v;newcross=np.cross(out[f[:,1]].astype(float)-out[f[:,0]],out[f[:,2]].astype(float)-out[f[:,0]]);localJ=np.einsum('ij,ij->i',newcross,oldcross)/den
    report['analytic_amplitude_limit']=dict(projected_J_floor=floor,nearest_positive_root=critical,limiting_face=limiting,limiting_old_double_area_m2=float(np.linalg.norm(oldcross[limiting])),selected_scale=amplitude,safety_margin_of_root=.01,selected_nominal_down_m=cage.DOWN*amplitude,selected_nominal_inward_m=cage.INWARD*amplitude,rule='Nearest positive root of1+aA+a²B=.25 over actual E triangles, one99% root-margin scale, no grid search')
    assert np.array_equal(out[fixed],data['world'][fixed]) and np.all(localJ>=floor)
    bad=np.flatnonzero(localJ<=0);details=[]
    for fi in bad:
        vv=f[fi];details.append(dict(face=int(fi),source_part=int(data['source_part'][fi]),source_face=int(data['source_face'][fi]),vertex_ids=vv.tolist(),world_before=v[vv].tolist(),world_after=out[vv].tolist(),old_double_area_m2=float(np.linalg.norm(oldcross[fi])),local_J=float(localJ[fi]),x_weights=wx[vv].tolist(),z_weights=wz[vv].tolist(),fixed=fixed[vv].tolist(),core_distance_m=dCore[vv].tolist(),head_distance_m=dHead[vv].tolist(),lower_distance_m=dLower[vv].tolist()))
    report.update(solver_seconds=time.time()-start,changed_vertices=int(changed.sum()),maximum_delta_m=float(np.linalg.norm(displacement,axis=1).max()),maximum_y_delta_m=0.,protected_vertices_byte_exact=True,topology_UV_head_exact=True,actual_lattice_rest_bounds=[rest.min(0).tolist(),rest.max(0).tolist()],actual_lattice_control_world_bounds=[world.min(0).tolist(),world.max(0).tolist()],intended_physical_control_bounds=[[-.315,-.150,1.050],[.315,.105,1.600]],unweighted_actual_X_translation_max_m=float(abs(unweighted['X'][:,0].astype(float)-v[:,0]).max()),unweighted_actual_Z_translation_max_m=float(abs(unweighted['Z'][:,2].astype(float)-v[:,2]).max()),local_J_scope='Per-triangle affine prism extension keeps original normal direction; positive projected oriented area, not an interior-volume diffeomorphism claim',local_J_min=float(localJ.min()),negative_or_zero_J_faces=int((localJ<=0).sum()),negative_faces=details,actual_handle_down_percentiles_m=np.percentile(-displacement[handles,2],[0,5,50,95,100]).tolist(),actual_handle_inward_percentiles_m=np.percentile(-np.sign(v[handles,0])*displacement[handles,0],[0,5,50,95,100]).tolist())
    write(O/'CPU-proof.json',report)
    assert np.isfinite(out).all() and np.all(localJ>0),('F local orientation failed',float(localJ.min()))
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    spec=importlib.util.spec_from_file_location('F_lattice_intersections',P.parent/'posterior-continuity08/geometry.py');geom=importlib.util.module_from_spec(spec);spec.loader.exec_module(geom)
    tree=BVHTree.FromPolygons([Vector(p) for p in out],f.tolist(),all_triangles=True);ctree=BVHTree.FromPolygons([Vector(p) for p in out],f[changed_faces].tolist(),all_triangles=True);seen=set();crossings=[]
    for local,j in ctree.overlap(tree):
        i=int(changed_faces[local]);j=int(j);key=tuple(sorted((i,j)))
        if i==j or key in seen or np.intersect1d(f[i],f[j]).size:continue
        seen.add(key)
        if geom.triangle_intersects(out[f[i]].astype(float),out[f[j]].astype(float)):crossings.append(key)
    report['new_nonadjacent_intersections']=crossings;write(O/'CPU-proof.json',report);assert not crossings,('F intersection',crossings[:10])
    payload={k:data[k] for k in data.files};payload['world']=out;np.savez_compressed(O/'geometry.npz',**payload);np.savez_compressed(O/'surface.npz',world=out,triangles=surface['triangles'],loop_uv=surface['loop_uv'],face_region=surface['face_region'],meshfaceid=surface['meshfaceid'])
    meta=json.loads((P/'surface-v10-expanded-E-source-branches.json').read_text());meta.update(payload_version='F-one-anatomical-lattice',surface_npz_path=str(O/'surface.npz'),surface_npz_sha256=sha(O/'surface.npz'),geometry_world_sha256=hashlib.sha256(out.tobytes()).hexdigest(),assembly_geometry_path=str(O/'geometry.npz'),F_CPU_proof=str(O/'CPU-proof.json'),F_support_path=str(O/'support.npz'),ART_status='UNSELECTED until Fgray/source actual review')
    write(O/'surface.json',meta);report.update(geometry_sha256=sha(O/'geometry.npz'),surface_sha256=sha(O/'surface.npz'),native_saved=False,GPU_used=False);write(O/'CPU-proof.json',report);assert sha(source)==cage.SOURCE_SHA
    print('F_ONE_LATTICE_CPU',json.dumps(report),flush=True)
if __name__=='__main__':main()
