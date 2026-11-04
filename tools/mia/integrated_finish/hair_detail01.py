"""One reversible copied-material detail trial on the18 NEW locks only.

Inert import. Root live MCP: inspect(expected_body_sha256, root), then
apply(expected_body_sha256, root), and restore(root). Body SHA is read/checked
dynamically, never hardcoded. No meshes/UVs/maps/cameras/lights/native writes.
This is early pigment/line look only, not a solution to rejected M2 grooming.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import runpy

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
KEY = 'MIA_HairDetail01'
MATERIAL = 'MIA_HairDetail01_UVInk_WIP'
ORIGINAL = 'MIA_HairLockLook01_UVToon_WIP'
NATIVE_SHA = '0d62eff09b4e95809a9f852d3e68654c1bb5a9e35fe70c065a939bc433e017ed'
BODY = 'MIA_Review12_H_LiveRepair'


def _libraries(root):
    root = Path(root)
    recipe = runpy.run_path(str(root/'tools/mia/integrated_finish/hair_detail01_recipe.py'))
    guard = runpy.run_path(str(root/'tools/mia/face_surface_live/v29_pigment_current.py'))
    return recipe,guard


def _bpy():
    import bpy
    return bpy


def _slot_record(ob):
    return [(s.link,s.material.as_pointer() if s.material else None) for s in ob.material_slots]


def _objects(guard,fingerprint):
    """All actual scene datablock objects, deduplicating shared mesh readback."""
    bpy = _bpy()
    result = {}; mesh_cache = {}
    for ob in bpy.data.objects:
        row = dict(pointer=ob.as_pointer(), type=ob.type,
                   data=ob.data.as_pointer() if ob.data else None,
                   matrix=guard['digest'](np.asarray(ob.matrix_world,np.float32)),
                   parent=ob.parent.as_pointer() if ob.parent else None,
                   hidden=bool(ob.hide_get()) if ob.name in bpy.context.view_layer.objects else None,
                   hide_render=bool(ob.hide_render), slots_count=len(ob.material_slots),
                   modifiers=guard['_modifiers'](ob))
        if ob.type == 'MESH':
            pointer = ob.data.as_pointer()
            if pointer not in mesh_cache:
                # fingerprint's final matrix is object-specific, excluded here.
                fp = fingerprint(ob)
                mesh_cache[pointer] = {k:v for k,v in fp.items() if k != 'matrix'}
                mesh_cache[pointer]['payload'] = guard['_mesh_payload'](ob.data)
                mesh_cache[pointer]['UV_flags'] = guard['_uv_state'](ob.data)
                mesh_cache[pointer]['data_materials'] = [m.as_pointer() if m else None for m in ob.data.materials]
            row['mesh'] = mesh_cache[pointer]
        result[ob.name] = row
    return result


def _snapshot(root,guard):
    return _objects(guard,guard['_helpers'](root)['fingerprint'])


def _all_slots():
    return {ob.name:_slot_record(ob) for ob in _bpy().data.objects if len(ob.material_slots)}


def _targets():
    bpy = _bpy(); actors = list(bpy.app.driver_namespace['MIA_CurvedRear03Base']['objects'])
    targets = [ob for ob in actors if ob.name != 'MIA_Hair_CurvedRear03Base_RemainingMain']
    assert len(actors) == 19 and len(targets) == 18 and len({ob.as_pointer() for ob in targets}) == 18
    assert all(ob.type == 'MESH' and ob.name.startswith('MIA_Hair_CurvedRear03Base_') for ob in targets)
    return targets


def _receipt(root,kind,report):
    folder = Path(root)/'.mia-cache/integrated-finish/hair-detail01'; folder.mkdir(parents=True,exist_ok=True)
    assert sum(p.stat().st_size for p in folder.iterdir() if p.is_file()) < 15*1024**2
    path = folder/(kind+'-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json')
    text = json.dumps(report,indent=2)+'\n'; assert len(text.encode()) < 1024**2
    with path.open('x',encoding='utf8') as stream: stream.write(text)
    return str(path)


def inspect(expected_body_sha256=None,root=ROOT):
    bpy = _bpy(); root = Path(root).resolve(); recipe,guard = _libraries(root)
    assert bpy.context.mode == 'OBJECT' and bpy.context.scene.render.engine == 'BLENDER_EEVEE'
    assert KEY not in bpy.app.driver_namespace
    native = root/'.mia-cache/migration-to-C/Mia_Current_STATIC_WIP.blend'
    assert Path(bpy.data.filepath).resolve() == native.resolve() and guard['file_sha'](native) == NATIVE_SHA
    targets = _targets(); source = bpy.data.materials[ORIGINAL]
    for ob in targets:
        assert len(ob.material_slots) == 1 and ob.material_slots[0].material == source
        assert recipe['UV_NAME'] in ob.data.uv_layers
        assert all(p.material_index == 0 for p in ob.data.polygons)
    nodes = source.node_tree.nodes
    assert nodes['LockLook01_ExplicitUV'].uv_map == recipe['UV_NAME']
    pigment = nodes['LockLook01_PigmentTimesLight']
    assert len(pigment.inputs[0].links) == len(pigment.inputs[1].links) == 1
    assert pigment.inputs[0].links[0].from_node == nodes['LockLook01_SourcePalette']
    assert pigment.inputs[1].links[0].from_node == nodes['LockLook01_SoftToonLight']
    # Pin the RNA class used by lock_look01.build(), not its version-dependent
    # short node.type enum. Also verify this node consumes the actual Diffuse.
    assert nodes['LockLook01_ActualLight'].bl_idname == 'ShaderNodeBsdfDiffuse'
    light_rgb = nodes['LockLook01_LightRGB']
    assert light_rgb.bl_idname == 'ShaderNodeShaderToRGB'
    assert len(light_rgb.inputs[0].links) == 1
    assert light_rgb.inputs[0].links[0].from_node == nodes['LockLook01_ActualLight']
    body = _snapshot(root,guard)[BODY]['mesh']['coordinates']
    if expected_body_sha256 is not None: assert body == expected_body_sha256, 'Expected live body SHA changed'
    return dict(scope='ONE18-lock copied-material early pigment detail trial; not M2 geometry/ART',
                targets=[ob.name for ob in targets], observed_body_sha256=body,
                original_material=source.name, original_graph=guard['graph_signature'](source.node_tree),
                UV=recipe['UV_NAME'], UV_direction='U periodic circumference; V root0 to tip1',
                numeric=recipe['verify'](), actual_light_route='Original Diffuse→ShaderToRGB→toon×pigment retained',
                source_rationale='v22 broad ash masses / uneven finite charcoal groups / sparse fine ink / restrained soft highlight',
                geometry_UV_changed=False, maps_generated=False, native_saved=False, ART=False,
                compile='NOT TESTED; actual EEVEE and fixed/moved-light output required')


def _build(material,recipe):
    material.name = MATERIAL; material.use_fake_user = False
    nodes,links = material.node_tree.nodes,material.node_tree.links
    def math_node(name,operation,*values):
        node = nodes.new('ShaderNodeMath'); node.name = 'HairDetail01_'+name; node.operation = operation
        for i,value in enumerate(values):
            if isinstance(value,(int,float)): node.inputs[i].default_value = value
            else: links.new(value,node.inputs[i])
        return node.outputs[0]
    def fade(name,value,first,last,to_first,to_last):
        node = nodes.new('ShaderNodeMapRange'); node.name = 'HairDetail01_'+name
        node.interpolation_type = 'SMOOTHSTEP'; node.clamp = True
        links.new(value,node.inputs['Value'])
        for key,value in [('From Min',first),('From Max',last),('To Min',to_first),('To Max',to_last)]:
            if isinstance(value,(int,float)): node.inputs[key].default_value = value
            else: links.new(value,node.inputs[key])
        return node.outputs['Result']
    u = nodes['LockLook01_UVComponents'].outputs['X']; v = nodes['LockLook01_UVComponents'].outputs['Y']
    dark = 0.; highlight = 0.
    for name,kind,controls,radius,window,gain in recipe['BANDS']:
        a,b,c,d = recipe['bezier_coefficients'](controls)
        curve = math_node(name+'_Cubic1','ADD',math_node(name+'_Cubic0','MULTIPLY',v,d),c)
        curve = math_node(name+'_Cubic3','ADD',math_node(name+'_Cubic2','MULTIPLY',v,curve),b)
        curve = math_node(name+'_Centre','ADD',math_node(name+'_Cubic4','MULTIPLY',v,curve),a)
        gate_a = fade(name+'_Start',v,window[0],window[1],0.,1.)
        gate_b = fade(name+'_End',v,window[2],window[3],1.,0.)
        gate = math_node(name+'_LengthGate','MULTIPLY',gate_a,gate_b)
        delta = math_node(name+'_UOffset','SUBTRACT',u,curve)
        wrapped = math_node(name+'_Fract','FRACT',math_node(name+'_Shift','ADD',delta,.5))
        distance = math_node(name+'_PeriodicDistance','ABSOLUTE',math_node(name+'_SignedWrap','SUBTRACT',wrapped,.5))
        scale = math_node(name+'_TaperScale','ADD',math_node(name+'_TaperGain','MULTIPLY',gate,.45),.55)
        inner = math_node(name+'_CoreWidth','MULTIPLY',scale,radius*.35)
        outer = math_node(name+'_OuterWidth','MULTIPLY',scale,radius)
        across = fade(name+'_Across',distance,inner,outer,1.,0.)
        value = math_node(name+'_Amplitude','MULTIPLY',math_node(name+'_Mask','MULTIPLY',across,gate),gain)
        if kind == 'dark': dark = math_node(name+'_DarkSum','ADD',dark,value)
        else: highlight = math_node(name+'_HighlightSum','ADD',highlight,value)
    dark = math_node('BoundedDark','MINIMUM',dark,.45)
    inverse = math_node('BaseMinusInk','SUBTRACT',1.,dark)
    light_gate = math_node('InkProtectsHighlight','SUBTRACT',1.,math_node('HighlightInkGain','MULTIPLY',dark,.7))
    factor = math_node('PigmentFactor','ADD',inverse,math_node('SoftHighlight','MULTIPLY',highlight,light_gate))
    factor = math_node('FactorMinimum','MAXIMUM',factor,.55)
    factor = math_node('FactorMaximum','MINIMUM',factor,1.065)
    multiply = nodes.new('ShaderNodeVectorMath'); multiply.name = 'HairDetail01_PigmentDetail'; multiply.operation = 'SCALE'
    links.new(nodes['LockLook01_SourcePalette'].outputs['Color'],multiply.inputs[0]); links.new(factor,multiply.inputs['Scale'])
    links.new(multiply.outputs['Vector'],nodes['LockLook01_PigmentTimesLight'].inputs[0])
    material['MIA_scope'] = 'New18 only; early UV pigment ink/highlight, no geometry/maps/groom/ART approval'
    return material


def _restore_bindings(state):
    bpy = _bpy(); material = state['material']
    # Validate every slot before changing any; unexpected later edits stay intact.
    for name,(link,old) in state['previous'].items():
        slot = bpy.data.objects[name].material_slots[0]
        assert (slot.link == 'OBJECT' and slot.material == material) or (slot.link == link and slot.material == old)
        if link == 'DATA': assert bpy.data.objects[name].data.materials[0] == old
    for name,(link,old) in state['previous'].items():
        slot = bpy.data.objects[name].material_slots[0]
        if link == 'DATA':
            if slot.link == 'OBJECT': slot.material = None
            slot.link = 'DATA'; assert slot.material == old
        else: slot.link = link; slot.material = old


def apply(expected_body_sha256,root=ROOT):
    bpy = _bpy(); root = Path(root).resolve(); recipe,guard = _libraries(root)
    assert isinstance(expected_body_sha256,str) and len(expected_body_sha256) == 64
    report = inspect(expected_body_sha256,root)
    assert bpy.data.materials.get(MATERIAL) is None
    before,graphs,slots = _snapshot(root,guard),guard['materials_signature'](),_all_slots()
    source = bpy.data.materials[ORIGINAL]; targets = _targets()
    state = dict(root=str(root),before=before,graphs=graphs,slots=slots,
                 previous={ob.name:(ob.material_slots[0].link,ob.material_slots[0].material) for ob in targets},
                 source=source,source_graph=guard['graph_signature'](source.node_tree),material=None)
    bpy.app.driver_namespace[KEY] = state
    try:
        # Exactly one material copy; no geometry or source shader changes.
        material = source.copy(); state['material'] = material
        # Build into the already-owned copy, so failure cleanup cannot lose it.
        _build(material,recipe)
        for ob in targets:
            ob.material_slots[0].link = 'OBJECT'; ob.material_slots[0].material = material
        bpy.context.view_layer.update()
        assert _snapshot(root,guard) == before
        after_graphs = guard['materials_signature']()
        assert {name:after_graphs[name] for name in graphs} == graphs
        after_slots = _all_slots()
        assert {n:s for n,s in after_slots.items() if n not in state['previous']} == {n:s for n,s in slots.items() if n not in state['previous']}
        state['owned_graph'] = guard['graph_signature'](material.node_tree)
        state['after_slots'] = after_slots
        report.update(status='APPLIED_EARLY_HAIR_DETAIL_WIP',copied_material=material.name,
                      all_original_objects_geometry_UV_exact=True,all_original_material_graphs_exact=True,
                      source_graphs={name:row['graph'] for name,row in graphs.items()})
        report['receipt'] = _receipt(root,'apply',report)
        return report
    except BaseException:
        if state['material'] is not None:
            _restore_bindings(state); assert state['material'].users == 0
            bpy.data.materials.remove(state['material'],do_unlink=False)
        bpy.app.driver_namespace.pop(KEY,None)
        bpy.context.view_layer.update()
        assert _snapshot(root,guard) == before and guard['materials_signature']() == graphs
        raise


def restore(root=None):
    bpy = _bpy(); state = bpy.app.driver_namespace[KEY]
    root = Path(state['root'] if root is None else root).resolve(); assert str(root) == state['root']
    assert bpy.context.mode == 'OBJECT'; _,guard = _libraries(root)
    material = state['material']
    owned_pointer = material.as_pointer()
    assert guard['graph_signature'](material.node_tree) == state['owned_graph']
    assert guard['graph_signature'](state['source'].node_tree) == state['source_graph']
    # Other scopes may have advanced since apply. Preserve their CURRENT state;
    # the detail trial never rolls body geometry, cameras or other materials back.
    before,graphs,slots = _snapshot(root,guard),guard['materials_signature'](),_all_slots()
    for name in state['previous']:
        assert before[name] == state['before'][name], 'Restore later hair geometry/UV edits first: '+name
    actual_users = sum(bpy.data.objects[n].material_slots[0].material == material for n in state['previous'])
    assert material.users == actual_users and not material.use_fake_user and not material.use_extra_user
    _restore_bindings(state); bpy.context.view_layer.update()
    assert _snapshot(root,guard) == before
    after_slots = _all_slots()
    assert {n:s for n,s in after_slots.items() if n not in state['previous']} == {n:s for n,s in slots.items() if n not in state['previous']}
    assert material.users == 0
    bpy.data.materials.remove(material,do_unlink=False)
    assert guard['materials_signature']() == {name:row for name,row in graphs.items() if row['pointer'] != owned_pointer}
    del bpy.app.driver_namespace[KEY]
    report = dict(status='RESTORED_ORIGINAL18_SLOT_BINDINGS',all_current_geometry_UV_other_materials_held=True,
                  dynamic_body_sha256=before[BODY]['mesh']['coordinates'],native_saved=False,ART=False)
    report['receipt'] = _receipt(root,'restore',report)
    return report
