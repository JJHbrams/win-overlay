"""Reversible UV-bound ash/toon look for the 18 new rear locks only.

This is a color/light diagnostic, not final paint/normal maps or grooming ART.
Original materials and image atlases are read only. Run through live MCP.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import math

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'.mia-cache/face-live/live/lock-look01'
KEY = 'MIA_HairLockLook01'
MATERIAL = 'MIA_HairLockLook01_UVToon_WIP'
SOURCE_MATERIAL = 'MIA_v002_R_SideNape_SourceAshEnvelope'
BASE_MATERIAL = 'MIA_Hair_CurvedRear03Base_GeometryOnly'
BODY_SHA = '69d4d4f0ea907da2474bc74f4b55312971d137f0911bdf9089fc02509a6bf25a'
UV_NAME = 'LockParamUV'
PIGMENT_BASE, LENGTH_AMPLITUDE, TRANSVERSE_AMPLITUDE = .027, .013, .0007
LIGHT_POINTS = [(0.1, (.45, .45, .45, 1.)),
                (.7, (.7, .7, .7, 1.)), (1., (1., 1., 1., 1.))]


def array_sha(value):
    return hashlib.sha256(np.ascontiguousarray(value).tobytes()).hexdigest()


def file_sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(4*1024*1024): result.update(block)
    return result.hexdigest()


def coordinates(ob):
    values = np.empty((len(ob.data.vertices), 3), np.float32)
    ob.data.vertices.foreach_get('co', values.ravel())
    return values


def fingerprint(ob):
    mesh = ob.data
    loops = np.empty(len(mesh.loops), np.int32)
    mesh.loops.foreach_get('vertex_index', loops)
    # foreach_get needs contiguous output, so collect each polygon property.
    starts, totals = np.empty(len(mesh.polygons), np.int32), np.empty(len(mesh.polygons), np.int32)
    mesh.polygons.foreach_get('loop_start', starts); mesh.polygons.foreach_get('loop_total', totals)
    material_indices = np.empty(len(mesh.polygons), np.int32)
    mesh.polygons.foreach_get('material_index', material_indices)
    normals = np.empty((len(mesh.corner_normals), 3), np.float32)
    mesh.corner_normals.foreach_get('vector', normals.ravel())
    uv = {}
    for layer in mesh.uv_layers:
        values = np.empty((len(layer.data), 2), np.float32)
        layer.data.foreach_get('uv', values.ravel()); uv[layer.name] = array_sha(values)
    return dict(coordinates=array_sha(coordinates(ob)),
                topology=array_sha(np.r_[loops, starts, totals]),
                face_material_indices=array_sha(material_indices), corner_normals=array_sha(normals),
                UV=uv, UV_active=mesh.uv_layers.active_index,
                UV_render=[layer.name for layer in mesh.uv_layers if layer.active_render],
                matrix=array_sha(np.asarray(ob.matrix_world, np.float32)))


def slots(ob):
    return [(slot.link, slot.material.name if slot.material else None) for slot in ob.material_slots]


def palette_points():
    material = bpy.data.materials[SOURCE_MATERIAL]
    node = material.node_tree.nodes['V22_OwnedAshPalette']
    assert node.type == 'VALTORGB'
    return [(float(e.position), tuple(e.color)) for e in node.color_ramp.elements], node.color_ramp.interpolation


def set_ramp(node, points, interpolation='LINEAR'):
    ramp = node.color_ramp
    while len(ramp.elements) > 2: ramp.elements.remove(ramp.elements[-1])
    for index, (position, color) in enumerate(points):
        element = ramp.elements[index] if index < 2 else ramp.elements.new(position)
        element.position = position; element.color = color
    ramp.interpolation = interpolation


def build(material, points, interpolation):
    material.use_nodes = True
    material['MIA_scope'] = '18-owned-lock early UV color/light diagnostic; not final maps, grooming or ART'
    pigment = tuple(np.interp(.034, [p for p, _ in points], [c[k] for _, c in points]) for k in range(3))
    material.diffuse_color = (*pigment, 1.)
    nodes = material.node_tree.nodes; nodes.clear(); links = material.node_tree.links
    def node(kind, name):
        result = nodes.new(kind); result.name = name; return result
    def math_node(name, operation, second=None):
        result = node('ShaderNodeMath', name); result.operation = operation
        if second is not None: result.inputs[1].default_value = second
        return result
    output = node('ShaderNodeOutputMaterial', 'LockLook01_Output'); output.target = 'ALL'
    uv = node('ShaderNodeUVMap', 'LockLook01_ExplicitUV'); uv.uv_map = UV_NAME
    split = node('ShaderNodeSeparateXYZ', 'LockLook01_UVComponents'); links.new(uv.outputs['UV'], split.inputs[0])
    length_phase = math_node('LockLook01_LengthPhase', 'MULTIPLY', math.pi)
    length_wave = math_node('LockLook01_LengthWave', 'SINE')
    length_gain = math_node('LockLook01_LengthGain', 'MULTIPLY', LENGTH_AMPLITUDE)
    links.new(split.outputs['Y'], length_phase.inputs[0]); links.new(length_phase.outputs[0], length_wave.inputs[0])
    links.new(length_wave.outputs[0], length_gain.inputs[0])
    perimeter_phase = math_node('LockLook01_PerimeterPhase', 'MULTIPLY', 2*math.pi)
    perimeter_wave = math_node('LockLook01_PerimeterWave', 'COSINE')
    perimeter_gain = math_node('LockLook01_PerimeterGain', 'MULTIPLY', TRANSVERSE_AMPLITUDE)
    links.new(split.outputs['X'], perimeter_phase.inputs[0]); links.new(perimeter_phase.outputs[0], perimeter_wave.inputs[0])
    links.new(perimeter_wave.outputs[0], perimeter_gain.inputs[0])
    length_base = math_node('LockLook01_LengthBase', 'ADD', PIGMENT_BASE)
    scalar = math_node('LockLook01_PaletteInput', 'ADD')
    links.new(length_gain.outputs[0], length_base.inputs[0]); links.new(length_base.outputs[0], scalar.inputs[0])
    links.new(perimeter_gain.outputs[0], scalar.inputs[1])
    palette = node('ShaderNodeValToRGB', 'LockLook01_SourcePalette'); set_ramp(palette, points, interpolation)
    links.new(scalar.outputs[0], palette.inputs['Fac'])
    diffuse = node('ShaderNodeBsdfDiffuse', 'LockLook01_ActualLight')
    diffuse.inputs['Color'].default_value = (1., 1., 1., 1.); diffuse.inputs['Roughness'].default_value = 1.
    light_rgb = node('ShaderNodeShaderToRGB', 'LockLook01_LightRGB')
    light_bw = node('ShaderNodeRGBToBW', 'LockLook01_LightValue')
    light = node('ShaderNodeValToRGB', 'LockLook01_SoftToonLight'); set_ramp(light, LIGHT_POINTS)
    links.new(diffuse.outputs[0], light_rgb.inputs[0]); links.new(light_rgb.outputs['Color'], light_bw.inputs[0])
    links.new(light_bw.outputs[0], light.inputs['Fac'])
    multiply = node('ShaderNodeVectorMath', 'LockLook01_PigmentTimesLight'); multiply.operation = 'MULTIPLY'
    links.new(palette.outputs['Color'], multiply.inputs[0]); links.new(light.outputs['Color'], multiply.inputs[1])
    emission = node('ShaderNodeEmission', 'LockLook01_FinalColor'); emission.inputs['Strength'].default_value = 1.
    links.new(multiply.outputs['Vector'], emission.inputs['Color']); links.new(emission.outputs[0], output.inputs['Surface'])
    return material


def graph_readback(material):
    tree = material.node_tree
    return dict(material=material.name, viewport_color=list(material.diffuse_color),
                source_palette=[(float(e.position), list(e.color)) for e in tree.nodes['LockLook01_SourcePalette'].color_ramp.elements],
                light_ramp=[(float(e.position), list(e.color)) for e in tree.nodes['LockLook01_SoftToonLight'].color_ramp.elements],
                UV=tree.nodes['LockLook01_ExplicitUV'].uv_map,
                pigment_scalar=dict(base=tree.nodes['LockLook01_LengthBase'].inputs[1].default_value,
                                    length_amplitude=tree.nodes['LockLook01_LengthGain'].inputs[1].default_value,
                                    transverse_amplitude=tree.nodes['LockLook01_PerimeterGain'].inputs[1].default_value,
                                    transverse_cycles=1, expected_range=[.0263, .0407]),
                output=dict(target=tree.nodes['LockLook01_Output'].target, active=tree.nodes['LockLook01_Output'].is_active_output),
                links=[(link.from_node.name, link.from_socket.name, link.to_node.name, link.to_socket.name) for link in tree.links])


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def shader_signature(material):
    """Hash render semantics, not datablock names or node-editor placement."""
    nodes = []
    for node in sorted(material.node_tree.nodes, key=lambda item: item.name):
        row = dict(name=node.name, kind=node.bl_idname, mute=node.mute, inputs=[])
        for key in ['operation', 'use_clamp', 'uv_map', 'from_instancer', 'target', 'is_active_output']:
            if hasattr(node, key): row[key] = getattr(node, key)
        for index, socket in enumerate(node.inputs):
            if not hasattr(socket, 'default_value'): continue
            value = socket.default_value
            if not isinstance(value, (str, int, float, bool, type(None))): value = list(value)
            row['inputs'].append((index, socket.identifier, value))
        if hasattr(node, 'color_ramp'):
            ramp = node.color_ramp
            row['ramp'] = dict(mode=ramp.color_mode, interpolation=ramp.interpolation,
                               hue_interpolation=ramp.hue_interpolation,
                               points=[(float(e.position), list(e.color)) for e in ramp.elements])
        nodes.append(row)
    semantics = dict(nodes=nodes,
                     links=sorted((link.from_node.name, link.from_socket.identifier,
                                   link.to_node.name, link.to_socket.identifier, link.is_muted)
                                  for link in material.node_tree.links),
                     use_nodes=material.use_nodes, viewport_color=list(material.diffuse_color))
    for key in ['surface_render_method', 'use_backface_culling', 'use_transparency_overlap']:
        if hasattr(material, key): semantics[key] = getattr(material, key)
    return hashlib.sha256(canonical(semantics).encode()).hexdigest()


def certify_recipe_graph(material, recipe, points, interpolation):
    """Certify legacy unrecorded inputs against the unchanged builder, not RAM alone."""
    assert canonical(graph_readback(material)) == canonical(recipe['shader']), 'Recorded graph fields changed'
    name = MATERIAL+'_UnassignedReplayReference'
    assert bpy.data.materials.get(name) is None
    reference = bpy.data.materials.new(name)
    try:
        build(reference, points, interpolation)
        signature = shader_signature(material)
        assert signature == shader_signature(reference), 'Owned graph differs from the unchanged recipe builder'
        return signature
    finally:
        assert reference.users == 0
        bpy.data.materials.remove(reference)


def timestamp_receipt(kind):
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    path = OUT/(kind+'-'+stamp+'.json')
    assert not path.exists()
    return path


def validate_replay(recipe, binding, observed, recipe_sha):
    """Fail closed on scene, binding, palette or ownership drift before assignment."""
    if binding is not recipe:
        assert binding['apply_receipt_sha256'] == recipe_sha, 'Legacy restore binding belongs to another recipe'
    assert recipe['actors'] == 18 and recipe['targets'] == observed['targets']
    assert recipe['body_sha256'] == observed['body_sha256']
    assert recipe['source_native_sha256'] == observed['native_sha256']
    assert recipe['fingerprints'] == observed['fingerprints'], 'Geometry/UV/normal/transform drift since accepted look'
    for key in ['baseline_slots', 'actor_names', 'source_palette_sha256', 'source_palette_interpolation']:
        assert canonical(binding[key]) == canonical(observed[key]), 'Replay binding differs: '+key
    assert canonical(recipe['shader']['source_palette']) == canonical(observed['source_palette'])
    assert binding['shader_signature'], 'Missing full shader recipe signature'


def main():
    assert globals().get('MIA_EDIT_PHASE', 'apply') == 'apply'
    namespace = bpy.app.driver_namespace
    assert KEY not in namespace and bpy.context.scene.render.engine == 'BLENDER_EEVEE'
    replay = globals().get('MIA_LOCK_LOOK01_REPLAY', False)
    assert isinstance(replay, bool), 'Replay requires the explicit boolean True flag'
    original_receipt = OUT/'apply.json'
    recipe = binding = recipe_sha = None
    if replay:
        recipe = json.loads(original_receipt.read_text(encoding='utf8')); recipe_sha = file_sha(original_receipt)
        binding = recipe if 'baseline_slots' in recipe and 'shader_signature' in recipe else json.loads((OUT/'restore.json').read_text(encoding='utf8'))
        receipt = timestamp_receipt('replay')
    else:
        receipt = original_receipt
        assert not receipt.exists(), 'Preserve the immutable diagnostic receipt; exact replay requires MIA_LOCK_LOOK01_REPLAY=True'
    current = json.loads((ROOT/'asset/mia/CURRENT_STATE.json').read_text(encoding='utf8'))['active_live_checkpoint']
    native = (ROOT/current['path']).resolve()
    assert Path(bpy.data.filepath).resolve() == native and file_sha(native) == current['sha256']
    body = bpy.data.objects['MIA_Review12_H_LiveRepair']; assert array_sha(coordinates(body)) == BODY_SHA
    rear = namespace['MIA_CurvedRear03Base']; assert rear['provisional_keep']
    actors = list(rear['objects']); assert len(actors) == 19 and len({ob.name for ob in actors}) == 19
    targets = [ob for ob in actors if not ob.name.endswith('_RemainingMain')]
    assert len(targets) == 18 and all(ob.type == 'MESH' for ob in actors)
    watched = actors+[bpy.data.objects['MIA_V17_PIXAL_DetailedHair']]
    before = {ob.name: fingerprint(ob) for ob in watched}
    before_slots = {ob.name: slots(ob) for ob in watched+[body]}
    previous = {}
    for ob in targets:
        assert ob.name.startswith('MIA_Hair_CurvedRear03Base_') and len(ob.material_slots) == 1
        slot = ob.material_slots[0]
        assert slot.material and slot.material.name == BASE_MATERIAL, 'Unexpected live look: '+ob.name
        assert UV_NAME in ob.data.uv_layers
        uv = np.array([v.uv[:] for v in ob.data.uv_layers[UV_NAME].data], np.float32)
        assert np.isfinite(uv).all() and uv.min() >= -1e-6 and uv.max() <= 1.000001
        if slot.link == 'DATA':
            users = [other for other in bpy.data.objects if other.type == 'MESH' and other.data == ob.data]
            assert all(other in targets for other in users), 'A DATA material would affect an unowned actor'
        previous[ob.name] = dict(link=slot.link, material=slot.material)
    points, interpolation = palette_points()
    palette_before = hashlib.sha256(json.dumps([points, interpolation]).encode()).hexdigest()
    if replay:
        validate_replay(recipe, binding, dict(targets=list(previous), body_sha256=BODY_SHA,
                        native_sha256=current['sha256'], fingerprints=before, baseline_slots=before_slots,
                        actor_names=[ob.name for ob in actors], source_palette_sha256=palette_before,
                        source_palette_interpolation=interpolation, source_palette=points), recipe_sha)
    assert bpy.data.materials.get(MATERIAL) is None, 'Refuse to replace another look'
    material = None
    try:
        material = bpy.data.materials.new(MATERIAL)
        build(material, points, interpolation)
        signature = shader_signature(material)
        if replay:
            assert canonical(graph_readback(material)) == canonical(recipe['shader']), 'Rebuilt recorded shader changed'
            assert signature == binding['shader_signature'], 'Rebuilt full shader semantics changed'
        for ob in targets: ob.material_slots[0].material = material
        bpy.context.view_layer.update()
        assert before == {ob.name: fingerprint(ob) for ob in watched}
        assert array_sha(coordinates(body)) == BODY_SHA and slots(body) == before_slots[body.name]
        for ob in watched:
            if ob not in targets: assert slots(ob) == before_slots[ob.name]
        assert all(ob.material_slots[0].material == material and ob.material_slots[0].link == previous[ob.name]['link'] for ob in targets)
        assert palette_before == hashlib.sha256(json.dumps(list(palette_points())).encode()).hexdigest()
        assert file_sha(native) == current['sha256']
        if replay: assert file_sha(original_receipt) == recipe_sha, 'Immutable apply recipe changed during replay'
        state = dict(material=material, previous=previous, fingerprints=before, before_slots=before_slots,
                     body_sha256=BODY_SHA, native=str(native), native_sha256=current['sha256'],
                     source_palette_sha256=palette_before, actor_names=[ob.name for ob in actors],
                     replay=replay, apply_receipt_sha256=recipe_sha, shader_signature=signature)
        report = dict(recipe_version=2, scope='Actual live COLOR/LIGHT diagnostic only; no final maps, grooming, M2/ART approval',
                      targets=list(previous), actors=len(targets), geometry_UV_normals_and_transforms_unchanged=True,
                      fingerprints=before, body_sha256=BODY_SHA, source_native_sha256=current['sha256'],
                      original_Main_and_RemainingMain_materials_unchanged=True, original_palette_unchanged=True,
                      baseline_slots=before_slots, actor_names=state['actor_names'], shader_signature=signature,
                      source_palette_sha256=palette_before, source_palette_interpolation=interpolation,
                      shader=graph_readback(material), native_saved=False, final_maps=False, ART=False)
        if replay:
            report = dict(status='EXACT_ACCEPTED_LOOK_REPLAY_NOT_NEW_CANDIDATE',
                          apply_receipt=dict(path=str(original_receipt), sha256=recipe_sha),
                          actors=18, body_sha256=BODY_SHA, source_native_sha256=current['sha256'],
                          fingerprints_sha256=hashlib.sha256(canonical(before).encode()).hexdigest(),
                          baseline_slots_sha256=hashlib.sha256(canonical(before_slots).encode()).hexdigest(),
                          shader_signature=signature, exact_recipe_and_bindings=True,
                          native_saved=False, final_maps=False, ART=False)
        OUT.mkdir(parents=True, exist_ok=True)
        rear['materials'].append(material); namespace[KEY] = state
        with receipt.open('x', encoding='utf8') as stream: stream.write(json.dumps(report, indent=2)+'\n')
    except Exception:
        for name, prior in previous.items():
            if bpy.data.objects[name].material_slots[0].material == material:
                bpy.data.objects[name].material_slots[0].material = prior['material']
        if KEY in namespace and namespace[KEY].get('material') == material: del namespace[KEY]
        if material is not None and material in rear['materials']: rear['materials'].remove(material)
        if material is not None and material.users == 0: bpy.data.materials.remove(material)
        raise
    print(json.dumps(dict(status='EXACT_LOOK_REPLAY_NOT_ART' if replay else 'APPLIED_LOOK_DIAGNOSTIC_NOT_ART', actors=18, material=material.name,
                          geometry_UV_unchanged=True, body_sha256=BODY_SHA, receipt=str(receipt), native_saved=False)))


if not globals().get('MIA_LOCK_LOOK01_LIBRARY_ONLY', False): main()
