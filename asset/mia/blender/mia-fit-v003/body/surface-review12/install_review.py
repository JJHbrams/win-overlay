"""Install staticjoinedbody onCURRENT private savedR3b scene. Neveropen/save/render."""
from pathlib import Path
import json,hashlib
import bpy,numpy as np
P=Path(__file__).resolve().parent
def ah(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def scene_actor_fingerprint(exclude):
    dg=bpy.context.evaluated_depsgraph_get();out={}
    for ob in bpy.context.scene.objects:
        if ob.type!='MESH' or ob==exclude or ob.hide_render or ob.name.startswith('MIA_Review12_'):continue
        e=ob.evaluated_get(dg);me=e.to_mesh(preserve_all_data_layers=True,depsgraph=dg);co=np.asarray([v.co[:] for v in me.vertices],np.float32)
        uv={u.name:ah(np.asarray([v.uv[:] for v in u.data],np.float32)) for u in me.uv_layers}
        out[ob.name]=dict(local_coords_sha=ah(co),matrix=[list(r) for r in ob.matrix_world],corner_normals_sha=ah(np.asarray([n.vector[:] for n in me.corner_normals],np.float32)),uv=uv,materials=[m.name if m else None for m in ob.data.materials])
        e.to_mesh_clear()
    return out
def gray_material():
    m=bpy.data.materials.new('Review12_CPU_ActualGray');m.use_nodes=True;n=m.node_tree.nodes;n.clear();bs=n.new('ShaderNodeBsdfPrincipled');bs.inputs['Base Color'].default_value=(.23,.23,.23,1);bs.inputs['Roughness'].default_value=.85;o=n.new('ShaderNodeOutputMaterial');m.node_tree.links.new(bs.outputs[0],o.inputs['Surface']);return m
def apply(material=None,*,proof_path=None,geometry_path=None,packing_path=None,atlas_path=None):
    assert 'MIA_Review12_StaticJoinedBody' not in bpy.data.objects,'Do not stack reviewassembly'
    original=bpy.data.objects['MIA_V27_SharedHeadBody'];actors=scene_actor_fingerprint(original);native_before=hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest();assert native_before=='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'
    oldUVState=dict(active=original.data.uv_layers.active.name if original.data.uv_layers.active else None,render=[u.name for u in original.data.uv_layers if u.active_render])
    data=np.load(geometry_path or P/'joined-static.npz');atlasFile=Path(atlas_path or (P/'atlas-E.npz' if geometry_path and Path(geometry_path).name=='joined-expanded-E.npz' else P/'atlas.npz'));atlas=np.load(atlasFile);v=data['world'];f=data['triangles'];part=data['source_part'];head=part==1
    assert atlas['loop_uv'].shape==(len(f),3,2),'Atlas/geometry topology mismatch'
    mesh=bpy.data.meshes.new('Review12_StaticJoined_WORLD');mesh.from_pydata(v.tolist(),[],f.tolist());mesh.update();body=bpy.data.objects.new('MIA_Review12_StaticJoinedBody',mesh);bpy.context.scene.collection.objects.link(body)
    for m in original.data.materials:mesh.materials.append(m)
    bodymat=len(mesh.materials);mesh.materials.append(material or gray_material())
    for i,poly in enumerate(mesh.polygons):poly.material_index=int(data['triangle_materials'][i]) if head[i] else bodymat;poly.use_smooth=True
    names=json.loads((P/'donor.json').read_text())['uv_layers']
    for i,name in enumerate(names):u=mesh.uv_layers.new(name=name,do_init=False);u.data.foreach_set('uv',data['old_loop_uv'][:,:,i,:].ravel())
    u=mesh.uv_layers.new(name='MIA_Review12UV',do_init=False);u.data.foreach_set('uv',atlas['loop_uv'].ravel())
    actualReviewUV=np.asarray([x.uv[:] for x in u.data],np.float32).reshape(-1,3,2);assert np.array_equal(actualReviewUV,atlas['loop_uv']),'Installed ReviewUV differs from chosen atlas'
    if oldUVState['active'] is not None:mesh.uv_layers.active_index=list(mesh.uv_layers.keys()).index(oldUVState['active'])
    for name in oldUVState['render']:mesh.uv_layers[name].active_render=True
    actualUVState=dict(active=mesh.uv_layers.active.name if mesh.uv_layers.active else None,render=[u.name for u in mesh.uv_layers if u.active_render]);assert oldUVState==actualUVState
    custom=np.zeros((len(f),3,3),np.float32);custom[head]=data['source_corner_normals'][head];mesh.normals_split_custom_set(custom.reshape(-1,3).tolist())
    # Activehead shader namedattributes; exactretainedsourcepointscopy, cutcornersbarycentric.
    ameta=json.loads((P/'head-attributes.json').read_text());ad=np.load(P/'head-attributes.npz');donor=np.load(P/'donor.npz');sourceVertex=data['source_vertex'];sf=data['source_face'];bary=data['source_corner_bary'];attr_proof=[]
    for rec in ameta['attributes']:
        if rec['domain']!='POINT':raise RuntimeError('UnimplementedCORNERheadattribute: '+rec['name'])
        values=ad[rec['npz_key']];out=np.zeros((len(v),rec['dimension']),values.dtype);known=sourceVertex>=0;out[known]=values[sourceVertex[known]]
        for fi in np.flatnonzero(head):
            for k,vi in enumerate(f[fi]):
                if known[vi]:continue
                out[vi]=np.einsum('i,ij->j',bary[fi,k],values[donor['triangles'][sf[fi]]])
        attr=mesh.attributes.new(rec['name'],rec['data_type'],'POINT');attr.data.foreach_set(rec['property'],out.ravel());actual=np.empty_like(out);attr.data.foreach_get(rec['property'],actual.ravel());assert np.array_equal(actual,out)
        protected=np.flatnonzero(known&(v[:,2]>=1.469));assert np.array_equal(actual[protected],values[sourceVertex[protected]])
        attr_proof.append(dict(name=rec['name'],retained_point_values_exact=True,protected_vertices=len(protected),newneckcut='donortrianglebarycentric interpolation',actual_values_sha256=ah(actual)))
    # Read back WORLDnormal appearance, not untransformed oldLOCALbytevectors.
    actualNormals=np.asarray([n.vector[:] for n in mesh.corner_normals],np.float32).reshape(-1,3,3);expected=custom[head].astype(float);expected/=np.maximum(np.linalg.norm(expected,axis=2)[:,:,None],1e-20);actual=actualNormals[head].astype(float)
    vectorerror=np.linalg.norm(actual-expected,axis=2);angles=np.degrees(np.arctan2(np.linalg.norm(np.cross(actual,expected),axis=2),(actual*expected).sum(2)))
    protectedFaces=np.all(v[f[head],2]>=1.469,axis=1)
    headIds=np.flatnonzero(head);unclipped=np.all(bary[head]==np.eye(3,dtype=np.float32)[None,:,:],axis=(1,2));cutAdjacent=np.any(abs(v[f[head],2]-1.465)<1e-7,axis=1)
    normalGroups={}
    for label,mask in [('protected_ge_1_469',protectedFaces),('original_unclipped_head',unclipped),('clipped_interpolated_neck',~unclipped),('neck_cut_adjacent',cutAdjacent)]:
        normalGroups[label]=dict(faces=int(mask.sum()),max_angle_degrees=float(angles[mask].max()) if mask.any() else None,max_vector_error=float(vectorerror[mask].max()) if mask.any() else None,corners_over_05deg=int((angles[mask]>.05).sum()),bounds=[v[f[headIds[mask]]].reshape(-1,3).min(0).tolist(),v[f[headIds[mask]]].reshape(-1,3).max(0).tolist()] if mask.any() else None)
    worst=np.unravel_index(np.argmax(angles),angles.shape);wf=int(headIds[worst[0]]);wc=int(worst[1])
    packing=dict(supplied_WORLD_vectors_exact_to_captured_source=True,actual_max_vector_error=float(vectorerror.max()),actual_max_angle_degrees=float(angles.max()),protected_face_max_angle_degrees=float(angles[protectedFaces].max()),
        groups=normalGroups,worst_corner=dict(joined_face=wf,corner=wc,source_face=int(sf[wf]),world_position=v[f[wf,wc]].tolist(),triangle_world=v[f[wf]].tolist(),source_barycentric=bary[wf,wc].tolist(),expected_normal=expected[worst].tolist(),actual_normal=actual[worst].tolist()),
        limit='Protected original face aboveZ1.469 customnormal readback <.05degree and8e-4vector, matching unchanged-topology source roundtrip. Changed clipped lower-neck/collar packing reported separately; no falsebitexactoutput or exactnecklook claim. Actualface/neckLOOK stillreviewed.')
    Path(packing_path or P/'head-normal-packing.json').write_text(json.dumps(packing,indent=2)+'\n',encoding='utf-8',newline='\n')
    assert angles[protectedFaces|unclipped].max()<.05 and vectorerror[protectedFaces|unclipped].max()<8e-4,('UncutProtectedHeadWORLDnormal packingreadback',packing)
    for i,name in enumerate(names):
        oldUV=np.asarray([d.uv[:] for d in mesh.uv_layers[name].data],np.float32).reshape(-1,3,2);assert np.array_equal(oldUV[head],data['old_loop_uv'][head,:,i,:])
    original.hide_render=True;bpy.context.view_layer.update();after=scene_actor_fingerprint(original);assert actors==after,'Savedface/hair/eye/lash/mouth actor changed'
    assert np.array_equal(np.asarray([q.co[:] for q in mesh.vertices],np.float32),v) and not body.modifiers and not mesh.shape_keys
    report=dict(status='CPU installedprivateR3b staticjoinedbody hardchecksPASS',joined_mesh_sha256=ah(v),ordered_triangles_sha256=ah(f),actual_old_head_UV_layers_exact=True,
        head_WORLD_corner_normal_vector_error_max=float(vectorerror.max()),head_WORLD_corner_normal_angle_degrees_max=float(angles.max()),normal_limit='NewMesh customnormal packing readback; preservedWORLDappearance input, not falseLOCALbyteclaim.',
        head_shader_attributes=attr_proof,unchanged_saved_actor_count=len(actors),saved_actor_fingerprints_before=actors,saved_actor_fingerprints_after=after,
        original_body_hidden_only=True,body_material_index=bodymat,head_material_slots_unchanged=True,source_old_UV_active_state=oldUVState,installed_old_UV_active_state=actualUVState,ReviewUV_atlas_path=str(atlasFile),ReviewUV_atlas_sha256=hashlib.sha256(atlasFile.read_bytes()).hexdigest(),ReviewUV_all_loops_sha256=ah(atlas['loop_uv']),source_native_sha256=native_before,new_body_has_no_rig_weights_keys=True,native_saved=False,GPU_used=False)
    if proof_path:Path(proof_path).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    return body,report
