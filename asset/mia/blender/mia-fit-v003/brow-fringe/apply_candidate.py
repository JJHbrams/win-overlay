"""Portable current-scene real Fringe and true brow correction. No open/save."""
from pathlib import Path
import hashlib,json
import bpy,numpy as np

P=Path(__file__).resolve().parent;KEY='V003_SourceFringeFine_B';PREFIX='V003_SourceBrowFringe_'
def _hash(array):return hashlib.sha256(np.asarray(array,dtype=np.float32).tobytes()).hexdigest()


def apply(variant='B'):
    cfg=json.loads((P/('candidate-'+variant+'.json')).read_text());payload=P/('fringe-'+variant+'.npz');key_name='V003_SourceFringeFine_'+variant
    assert hashlib.sha256(payload.read_bytes()).hexdigest()==cfg['payload_sha256'];a=np.load(payload,allow_pickle=False)
    main=bpy.data.objects[cfg['owner']];mesh=main.data
    already=bool(mesh.shape_keys and key_name in mesh.shape_keys.key_blocks)
    assert not mesh.shape_keys or not any(k.name.startswith('V003_SourceFringeFine_') and k.name!=key_name for k in mesh.shape_keys.key_blocks),'Compare variants in a fresh scene; do not stack fringe trials'
    assert len(mesh.vertices)==cfg['original_vertices'] and len(mesh.polygons)==cfg['original_faces']
    base=np.asarray([v.co[:] for v in (mesh.shape_keys.key_blocks[0].data if mesh.shape_keys else mesh.vertices)],np.float32)
    assert _hash(base)==cfg['base_raw_sha256'],'Main Basis changed; do not overwrite other geometry work'
    topo=np.asarray([f.vertices[:] for f in mesh.polygons],np.int32)
    assert hashlib.sha256(topo.tobytes()).hexdigest()==cfg['base_topology_sha256']
    for name,digest in cfg['original_six_UV_hashes'].items():
        assert _hash([v.uv[:] for v in mesh.uv_layers[name].data])==digest
    assert np.array_equal(base[a['indices']],a['expected_basis'])
    assert np.array_equal(topo[a['owned_face_ids']],a['expected_owned_faces'])
    assert np.array_equal(np.asarray([mesh.attributes['MIA_SOURCE_POLYGON'].data[int(i)].value for i in a['owned_face_ids']]),a['expected_source_ids'])
    if already:
        expected=base.copy();expected[a['indices']]+=a['delta_local']
        assert np.array_equal(np.asarray([v.co[:] for v in mesh.shape_keys.key_blocks[key_name].data],np.float32),expected)
        for side in [-1,1]:
            brow=bpy.data.objects['V31_SourceBrow_'+str(side)]
            assert sum(m.name==PREFIX+'DynamicWidth' for m in brow.modifiers)==1 and PREFIX+'WidthFactor' in brow.data.attributes
            assert brow.data.materials[0].name.startswith(PREFIX+'SourceInk_')
        return {'candidate':variant,'already_applied':True,'key':key_name}
    if not mesh.shape_keys:main.shape_key_add(name='Basis')
    key=main.shape_key_add(name=key_name);target=base.copy();target[a['indices']]+=a['delta_local'];key.data.foreach_set('co',target.ravel());key.value=1
    main[PREFIX+'LogicalRoots']=json.dumps([{'family':x.get('family',x.get('component')),'source_polygon_ids':x['source_polygon_ids'],'root_ids':x.get('fixed_root_or_tip_ids',x.get('fixed_root_or_boundary_ids',[]))} for x in cfg['logical_clumps']])
    created=[]
    for side in [-1,1]:
        ob=bpy.data.objects['V31_SourceBrow_'+str(side)];assert len(ob.data.vertices)==195 and 'BrowParamUV' in ob.data.uv_layers
        case=cfg['brow_width_case'][str(side)];u=np.arange(65)/64;lo,hi=case['observed_u'];feather=.08
        weight=np.minimum(np.clip((u-lo+feather)/feather,0,1),np.clip((hi+feather-u)/feather,0,1));weight=weight*weight*(3-2*weight)
        factor=np.repeat(1+(case['factor']-1)*weight,3).astype(np.float32)
        attr=ob.data.attributes.new(PREFIX+'WidthFactor','FLOAT','POINT');attr.data.foreach_set('value',factor)
        group=bpy.data.node_groups.new(PREFIX+'Width_'+str(side),'GeometryNodeTree')
        group.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');group.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
        n=group.nodes;l=group.links;inp=n.new('NodeGroupInput');out=n.new('NodeGroupOutput');pos=n.new('GeometryNodeInputPosition');index=n.new('GeometryNodeInputIndex')
        div=n.new('ShaderNodeMath');div.operation='DIVIDE';div.inputs[1].default_value=3;l.new(index.outputs[0],div.inputs[0])
        floor=n.new('ShaderNodeMath');floor.operation='FLOOR';l.new(div.outputs[0],floor.inputs[0])
        mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=3;l.new(floor.outputs[0],mul.inputs[0])
        add=n.new('ShaderNodeMath');add.operation='ADD';add.inputs[1].default_value=1;l.new(mul.outputs[0],add.inputs[0])
        sample=n.new('GeometryNodeSampleIndex');sample.data_type='FLOAT_VECTOR';sample.domain='POINT';l.new(inp.outputs['Geometry'],sample.inputs['Geometry']);l.new(pos.outputs[0],sample.inputs['Value']);l.new(add.outputs[0],sample.inputs['Index'])
        sub=n.new('ShaderNodeVectorMath');sub.operation='SUBTRACT';l.new(pos.outputs[0],sub.inputs[0]);l.new(sample.outputs['Value'],sub.inputs[1])
        field=n.new('GeometryNodeInputNamedAttribute');field.data_type='FLOAT';field.inputs['Name'].default_value=attr.name
        scale=n.new('ShaderNodeVectorMath');scale.operation='SCALE';l.new(sub.outputs[0],scale.inputs[0]);l.new(field.outputs['Attribute'],scale.inputs['Scale'])
        dest=n.new('ShaderNodeVectorMath');dest.operation='ADD';l.new(sample.outputs['Value'],dest.inputs[0]);l.new(scale.outputs[0],dest.inputs[1])
        setpos=n.new('GeometryNodeSetPosition');l.new(inp.outputs['Geometry'],setpos.inputs['Geometry']);l.new(dest.outputs[0],setpos.inputs['Position']);l.new(setpos.outputs['Geometry'],out.inputs['Geometry'])
        mod=ob.modifiers.new(PREFIX+'DynamicWidth','NODES');mod.node_group=group
        shrink=next(i for i,m in enumerate(ob.modifiers) if m.type=='SHRINKWRAP')
        with bpy.context.temp_override(object=ob,active_object=ob):bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=shrink)
        material=ob.data.materials[0].copy();material.name=PREFIX+'SourceInk_'+str(side)
        for node in material.node_tree.nodes:
            if node.type=='EMISSION':node.inputs['Color'].default_value=cfg['brow_ink_linear_rgba']
        ob.data.materials[0]=material;created.append(ob.name)
    bpy.context.view_layer.update()
    return {'candidate':variant,'key':key_name,'main_points':len(a['indices']),'maximum_fringe_move_mm':cfg['max_move_mm'],
            'logical_clumps':len(cfg['logical_clumps']),'brow_owners':created,'original_raw_topology_UV_preserved':True,
            'brow_centerline_lift':False,'brow_overlay_used':False,'native_saved':False,'ART':'UNVERIFIED'}
