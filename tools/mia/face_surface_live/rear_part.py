"""Live installation of one explicitly unaccepted, separate central rear assembly.

The original Main is never edited. A derived Main omits declared fin/loop faces;
the new part retains the identity-tested exterior assembly's UV and paint data.
"""
from pathlib import Path
import hashlib
import json
import bpy
import numpy as np

ROOT=Path('D:/MiaWorkCache/mia-reference-work/win-overlay')
FOLDER=ROOT/'.mia-cache/face-live/rear-part01'
PREFIX='MIA_Live_RearPart01'


def fingerprint(ob):
    me=ob.data
    return dict(co=hashlib.sha256(np.array([v.co[:] for v in me.vertices],np.float32).tobytes()).hexdigest(),
                topology=hashlib.sha256(np.array([p.vertices[:] for p in me.polygons],np.int32).tobytes()).hexdigest(),
                uv={u.name:hashlib.sha256(np.array([v.uv[:] for v in u.data],np.float32).tobytes()).hexdigest() for u in me.uv_layers},
                materials=[ma.name if ma else None for ma in me.materials],
                indices=hashlib.sha256(np.array([p.material_index for p in me.polygons],np.int32).tobytes()).hexdigest())


def apply(runtime='live_mcp'):
    assert runtime in ('live_mcp','background_cpu')
    ns=bpy.app.driver_namespace
    assert 'MIA_HairReviewState' in ns, 'Needs the exclusive borrowed live bundle'
    assert PREFIX not in ns and bpy.data.objects.get(PREFIX) is None
    cfg=json.loads((FOLDER/'candidate.json').read_text())
    assert hashlib.sha256((FOLDER/'ownership.npz').read_bytes()).hexdigest()==cfg['ownership_sha256']
    data=np.load(FOLDER/'ownership.npz')
    source=bpy.data.objects['MIA_V17_PIXAL_DetailedHair']; original=fingerprint(source)
    assert original['co']==cfg['source_main_raw_sha256']
    assert not source.data.shape_keys, 'Do not silently combine an unreviewed fringe key'
    assert np.allclose(np.array(source.matrix_world),np.eye(4),atol=1e-7)
    fids=data['donor_face_ids']; used=data['donor_point_ids']; hidden=data['hidden_faces']
    faces=np.array([p.vertices[:] for p in source.data.polygons],np.int32)
    assert np.array_equal(faces[fids],data['expected_donor_triangles'])
    assert np.array_equal(faces[hidden],data['expected_hidden_triangles'])
    state=dict(original_visibility=(source.hide_get(),source.hide_render), fingerprint=original,
               created_objects=[],created_meshes=[],created_nodegroups=[])
    ns[PREFIX]=state
    # Exact raw copy; only its declared FACE mask and one GN modifier are new.
    derived=source.copy(); derived.data=source.data.copy(); derived.name=PREFIX+'_RemainingMain'
    bpy.context.scene.collection.objects.link(derived)
    state['created_objects'].append(derived); state['created_meshes'].append(derived.data)
    field=derived.data.attributes.new(name=PREFIX+'_RemoveFace',type='BOOLEAN',domain='FACE')
    mask=np.zeros(len(faces),np.int32);mask[hidden]=1;field.data.foreach_set('value',mask)
    ng=bpy.data.node_groups.new(PREFIX+'_DeclaredFaceDeletion','GeometryNodeTree')
    state['created_nodegroups'].append(ng)
    ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    ni=ng.nodes.new('NodeGroupInput'); no=ng.nodes.new('NodeGroupOutput')
    attr=ng.nodes.new('GeometryNodeInputNamedAttribute');attr.data_type='BOOLEAN';attr.inputs['Name'].default_value=field.name
    delete=ng.nodes.new('GeometryNodeDeleteGeometry');delete.domain='FACE'
    ng.links.new(ni.outputs['Geometry'],delete.inputs['Geometry']);ng.links.new(attr.outputs['Attribute'],delete.inputs['Selection'])
    ng.links.new(delete.outputs['Geometry'],no.inputs['Geometry'])
    mod=derived.modifiers.new(PREFIX+'_Mask','NODES');mod.node_group=ng
    # Source-coordinate exterior assembly, complete skins and backings together.
    deps=bpy.context.evaluated_depsgraph_get();ev=source.evaluated_get(deps)
    sm=ev.to_mesh(preserve_all_data_layers=True,depsgraph=deps)
    assert len(sm.vertices)==len(source.data.vertices) and len(sm.polygons)==len(faces)
    remap=np.full(len(sm.vertices),-1,np.int32);remap[used]=np.arange(len(used))
    local_faces=remap[faces[fids]]
    coords=data['candidate_world']
    mesh=bpy.data.meshes.new(PREFIX+'_ExteriorMesh');mesh.from_pydata(coords.tolist(),[],local_faces.tolist());mesh.update()
    rear=bpy.data.objects.new(PREFIX,mesh);bpy.context.scene.collection.objects.link(rear)
    state['created_objects'].append(rear);state['created_meshes'].append(mesh)
    for ma in source.data.materials:mesh.materials.append(ma)
    for p,i in zip(mesh.polygons,fids):p.material_index=sm.polygons[int(i)].material_index;p.use_smooth=sm.polygons[int(i)].use_smooth
    loop_ids=np.array([li for i in fids for li in sm.polygons[int(i)].loop_indices],np.int32)
    uv_exact=[]
    for layer in sm.uv_layers:
        uv=mesh.uv_layers.new(name=layer.name)
        values=np.array([layer.data[int(i)].uv[:] for i in loop_ids],np.float32)
        uv.data.foreach_set('uv',values.ravel())
        assert np.array_equal(values,np.array([x.uv[:] for x in uv.data],np.float32));uv_exact.append(layer.name)
    mesh.uv_layers.active_index=source.data.uv_layers.active_index
    mesh.uv_layers[next(u.name for u in source.data.uv_layers if u.active_render)].active_render=True
    fields=[]
    for a in sm.attributes:
        if a.name=='position' or a.name.startswith('.') or a.name in mesh.attributes:continue
        indices=used if a.domain=='POINT' else fids if a.domain=='FACE' else None
        if indices is None:continue
        prop='color' if a.data_type in ('FLOAT_COLOR','BYTE_COLOR') else 'vector' if a.data_type=='FLOAT_VECTOR' else 'value'
        values=np.array([getattr(a.data[int(i)],prop) for i in indices])
        target=mesh.attributes.new(name=a.name,type=a.data_type,domain=a.domain)
        target.data.foreach_set(prop,values.astype(np.int32 if a.data_type in ('INT','BOOLEAN') else np.float32).ravel())
        fields.append(a.name)
    a=np.array(cfg['affine']); normals=np.array([sm.corner_normals[int(i)].vector[:] for i in loop_ids],float)
    normals=normals@np.linalg.inv(a);normals/=np.linalg.norm(normals,axis=1)[:,None]
    mesh.normals_split_custom_set(normals.tolist())
    # Keep source named weights as an initial static binding only. New rest fit
    # requires later pose correction; this is deliberately not rig acceptance.
    for group in source.vertex_groups:rear.vertex_groups.new(name=group.name)
    for new_id,old_id in enumerate(used):
        for weight in source.data.vertices[int(old_id)].groups:
            rear.vertex_groups[weight.group].add([new_id],weight.weight,'REPLACE')
    for old in source.modifiers:
        if old.type=='ARMATURE':
            m=rear.modifiers.new(PREFIX+'_ProvisionalSourceBinding','ARMATURE');m.object=old.object
            m.use_deform_preserve_volume=old.use_deform_preserve_volume
    rear['mia_component']='hair';rear['MIA_role']='UNACCEPTED separate central rear exterior assembly'
    rear['MIA_source_identity_proof']=cfg['donor_identity_proof']
    rear['MIA_deformation_status']='Static-only initial named weights; production pose/contact not validated'
    derived['mia_component']='hair';derived['MIA_role']='Derived Main with explicit fin/loop omission; original retained'
    ev.to_mesh_clear()
    source.hide_set(True);source.hide_render=True
    derived.hide_set(False);derived.hide_render=False;rear.hide_set(False);rear.hide_render=False
    bpy.context.view_layer.update()
    assert fingerprint(source)==original
    body=bpy.data.objects['MIA_Review12_H_LiveRepair']
    body_sha=hashlib.sha256(np.array([v.co[:] for v in body.data.vertices],np.float32).tobytes()).hexdigest()
    assert body_sha==ns['MIA_HairReviewState']['body_sha256']
    report=dict(candidate='rear-part01',installed_live=runtime=='live_mcp',runtime=runtime,adopted=False,ART=False,
                vertices=len(coords),faces=len(fids),declared_hidden_faces=len(hidden),
                original_Main_fingerprint_exact=True,UV_exact=uv_exact,point_face_fields=fields,
                normal_transform='inverse transpose of the declared positive affine; no normal-texture bake',
                body_sha256=body_sha,native_saved=False)
    (FOLDER/('live-install.json' if runtime=='live_mcp' else 'cpu-install.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    return report


def restore():
    ns=bpy.app.driver_namespace;state=ns[PREFIX];source=bpy.data.objects['MIA_V17_PIXAL_DetailedHair']
    assert fingerprint(source)==state['fingerprint']
    for ob in state['created_objects']:bpy.data.objects.remove(ob,do_unlink=True)
    for me in state['created_meshes']:
        if me.users==0:bpy.data.meshes.remove(me)
    for ng in state['created_nodegroups']:
        if ng.users==0:bpy.data.node_groups.remove(ng)
    source.hide_set(state['original_visibility'][0]);source.hide_render=state['original_visibility'][1]
    bpy.context.view_layer.update();del ns[PREFIX]
    return dict(only_owned_derived_actors_removed=True,original_Main_exact=True,native_saved=False)


if __name__=='__main__': print(json.dumps(apply()))
