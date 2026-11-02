"""Current-scene component API; never opens/saves a scene or removes other keys.

The B brow is independently usable. C fringe is a provisional geometry trial;
root must select it after the source-paired views, not from CPU visibility.
Historical apply_candidate.py remains unchanged for exact B render provenance.
"""
from pathlib import Path
import hashlib
import json
import bpy
import numpy as np

P = Path(__file__).resolve().parent
PREFIX = 'V003_SourceBrowFringe_'


def _hash(a):
    return hashlib.sha256(np.asarray(a, np.float32).tobytes()).hexdigest()


def _config(variant):
    assert variant in ('B', 'C')
    return json.loads((P / ('candidate-' + variant + '.json')).read_text())


def apply_brows():
    """Install exactly the provisional B/C actual-rendered brow correction.

    Existing original/unknown shape keys, drivers, UVs, armature and final
    Shrinkwrap are retained. Width runs on deformed geometry immediately before
    final Shrinkwrap; the current center row is sampled without a brow lift.
    """
    cfg = _config('B')
    contract = json.loads((P / 'brow-contract.json').read_text())
    prepared = []
    for side in (-1, 1):
        ob = bpy.data.objects['V31_SourceBrow_' + str(side)]
        expected = contract[str(side)]
        assert len(ob.data.vertices) == 195
        assert _hash([v.co[:] for v in ob.data.vertices]) == expected['raw_sha256']
        assert _hash([v.uv[:] for v in ob.data.uv_layers['BrowParamUV'].data]) == expected['uv_sha256']
        assert ob.data.shape_keys
        for name, digest in expected['original_key_sha256'].items():
            assert _hash([v.co[:] for v in ob.data.shape_keys.key_blocks[name].data]) == digest
        case = cfg['brow_width_case'][str(side)]
        lo, hi = case['observed_u']
        u = np.arange(65) / 64
        w = np.minimum(np.clip((u-lo+.08)/.08, 0, 1), np.clip((hi+.08-u)/.08, 0, 1))
        w = w*w*(3-2*w)
        factor = np.repeat(1+(case['factor']-1)*w, 3).astype(np.float32)
        modifiers = [m for m in ob.modifiers if m.name == PREFIX+'DynamicWidth']
        if modifiers:
            assert len(modifiers) == 1 and modifiers[0].type == 'NODES'
            attr = ob.data.attributes[PREFIX+'WidthFactor']
            assert np.array_equal(np.asarray([d.value for d in attr.data], np.float32), factor)
            assert ob.data.materials[0].name.startswith(PREFIX+'SourceInk_')
            assert next(i for i,m in enumerate(ob.modifiers) if m.type == 'SHRINKWRAP') > list(ob.modifiers).index(modifiers[0])
        else:
            assert PREFIX+'WidthFactor' not in ob.data.attributes, 'Partial brow installation'
            assert not ob.data.materials[0].name.startswith(PREFIX+'SourceInk_')
        prepared.append((side, ob, factor, bool(modifiers)))
    for side, ob, factor, installed in prepared:
        if installed:
            continue
        attr = ob.data.attributes.new(PREFIX+'WidthFactor', 'FLOAT', 'POINT')
        attr.data.foreach_set('value', factor)
        group = bpy.data.node_groups.new(PREFIX+'Width_'+str(side), 'GeometryNodeTree')
        group.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
        group.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
        n, l = group.nodes, group.links
        inp=n.new('NodeGroupInput'); out=n.new('NodeGroupOutput')
        pos=n.new('GeometryNodeInputPosition'); index=n.new('GeometryNodeInputIndex')
        div=n.new('ShaderNodeMath'); div.operation='DIVIDE'; div.inputs[1].default_value=3; l.new(index.outputs[0],div.inputs[0])
        floor=n.new('ShaderNodeMath'); floor.operation='FLOOR'; l.new(div.outputs[0],floor.inputs[0])
        mul=n.new('ShaderNodeMath'); mul.operation='MULTIPLY'; mul.inputs[1].default_value=3; l.new(floor.outputs[0],mul.inputs[0])
        add=n.new('ShaderNodeMath'); add.operation='ADD'; add.inputs[1].default_value=1; l.new(mul.outputs[0],add.inputs[0])
        sample=n.new('GeometryNodeSampleIndex'); sample.data_type='FLOAT_VECTOR'; sample.domain='POINT'
        l.new(inp.outputs['Geometry'],sample.inputs['Geometry']); l.new(pos.outputs[0],sample.inputs['Value']); l.new(add.outputs[0],sample.inputs['Index'])
        sub=n.new('ShaderNodeVectorMath'); sub.operation='SUBTRACT'; l.new(pos.outputs[0],sub.inputs[0]); l.new(sample.outputs['Value'],sub.inputs[1])
        field=n.new('GeometryNodeInputNamedAttribute'); field.data_type='FLOAT'; field.inputs['Name'].default_value=attr.name
        scale=n.new('ShaderNodeVectorMath'); scale.operation='SCALE'; l.new(sub.outputs[0],scale.inputs[0]); l.new(field.outputs['Attribute'],scale.inputs['Scale'])
        dest=n.new('ShaderNodeVectorMath'); dest.operation='ADD'; l.new(sample.outputs['Value'],dest.inputs[0]); l.new(scale.outputs[0],dest.inputs[1])
        setpos=n.new('GeometryNodeSetPosition'); l.new(inp.outputs['Geometry'],setpos.inputs['Geometry']); l.new(dest.outputs[0],setpos.inputs['Position']); l.new(setpos.outputs['Geometry'],out.inputs['Geometry'])
        mod=ob.modifiers.new(PREFIX+'DynamicWidth','NODES'); mod.node_group=group
        shrink=next(i for i,m in enumerate(ob.modifiers) if m.type=='SHRINKWRAP')
        with bpy.context.temp_override(object=ob,active_object=ob):
            bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=shrink)
        material=ob.data.materials[0].copy(); material.name=PREFIX+'SourceInk_'+str(side)
        for node in material.node_tree.nodes:
            if node.type=='EMISSION': node.inputs['Color'].default_value=cfg['brow_ink_linear_rgba']
        ob.data.materials[0]=material
    bpy.context.view_layer.update()
    return {'component':'B brow only', 'owners':[o.name for _,o,_,_ in prepared],
            'already_applied':all(a for _,_,_,a in prepared), 'centerline_lift':False,
            'Main_changed':False, 'projected_overlay':False, 'ART':'provisional scoped thickness improvement'}


def apply_fringe(variant='C'):
    """Add only the guarded Main sparse relative key; never clear other keys.

    Other relative keys may coexist and their arrays/values are not changed.
    Overlapping other geometry can alter appearance and requires root's combined
    evaluation. A prior trial from this folder is rejected rather than stacked.
    """
    cfg=_config(variant); path=P/('fringe-'+variant+'.npz')
    assert hashlib.sha256(path.read_bytes()).hexdigest()==cfg['payload_sha256']
    a=np.load(path,allow_pickle=False); main=bpy.data.objects[cfg['owner']]; mesh=main.data
    key_name='V003_SourceFringeFine_'+variant
    keys=mesh.shape_keys
    assert not keys or keys.use_relative, 'Absolute keys need an explicit integration policy'
    assert not keys or not any(k.name.startswith('V003_SourceFringeFine_') and k.name!=key_name for k in keys.key_blocks), 'Do not stack fringe trials'
    base=np.asarray([v.co[:] for v in (keys.key_blocks[0].data if keys else mesh.vertices)],np.float32)
    assert _hash(base)==cfg['base_raw_sha256']
    assert len(mesh.vertices)==cfg['original_vertices'] and len(mesh.polygons)==cfg['original_faces']
    topo=np.asarray([f.vertices[:] for f in mesh.polygons],np.int32)
    assert hashlib.sha256(topo.tobytes()).hexdigest()==cfg['base_topology_sha256']
    for name,digest in cfg['original_six_UV_hashes'].items():
        assert _hash([v.uv[:] for v in mesh.uv_layers[name].data])==digest
    assert np.array_equal(base[a['indices']],a['expected_basis'])
    assert np.array_equal(topo[a['owned_face_ids']],a['expected_owned_faces'])
    assert np.array_equal(np.asarray([mesh.attributes['MIA_SOURCE_POLYGON'].data[int(i)].value for i in a['owned_face_ids']]),a['expected_source_ids'])
    target=base.copy(); target[a['indices']]+=a['delta_local']
    if keys and key_name in keys.key_blocks:
        assert np.array_equal(np.asarray([v.co[:] for v in keys.key_blocks[key_name].data],np.float32),target)
        return {'component':'fringe '+variant,'already_applied':True,'key':key_name}
    if not keys: main.shape_key_add(name='Basis')
    key=main.shape_key_add(name=key_name); key.relative_key=mesh.shape_keys.key_blocks[0]
    key.data.foreach_set('co',target.ravel()); key.value=1
    main[PREFIX+'LogicalRoots']=json.dumps([{'family':x['family'],'source_polygon_ids':x['source_polygon_ids'],'root_ids':x.get('fixed_root_or_tip_ids',[])} for x in cfg['logical_clumps']])
    bpy.context.view_layer.update()
    return {'component':'fringe '+variant,'key':key_name,'points':len(a['indices']),
            'families':len(cfg['logical_clumps']),'maximum_move_mm':cfg['max_move_mm'],
            'ART':'UNVERIFIED: actual source-paired views required'}


def apply(variant=None):
    """Default to the useful brow only; rejected fringe requires explicit opt-in."""
    result={'brow':apply_brows(),'native_saved':False}
    if variant is not None:result['fringe']=apply_fringe(variant)
    return result
