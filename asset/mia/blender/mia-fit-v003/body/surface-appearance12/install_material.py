"""Body-only image material API. Does not assign or change face/hair materials."""
from pathlib import Path
import hashlib
import json


def _linear(rgb):
    return tuple(c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in rgb)


def _rgba_u8(rgb):
    return (*_linear([c / 255 for c in rgb]), 1.)


def _tag(node, role):
    node['mia12_role'] = role
    node.name = node.label = 'MIA12_' + role
    return node


def _value(nodes, role, value):
    node = _tag(nodes.new('ShaderNodeValue'), role)
    node.outputs[0].default_value = value
    return node


def _math(nodes, links, role, operation, a=None, b=None, a_value=0., b_value=0.):
    node = _tag(nodes.new('ShaderNodeMath'), role)
    node.operation = operation
    node.inputs[0].default_value = a_value
    node.inputs[1].default_value = b_value
    if a is not None: links.new(a, node.inputs[0])
    if b is not None: links.new(b, node.inputs[1])
    return node.outputs[0]


def create_material(map_dir, uv_layer='MIA_Review12UV', variant='skin', *,
                    clavicle_strength=1., ink_strength=.55, shade_strength=.16,
                    lighting_config=None, name=None):
    """Return a NEW material only; caller owns disjoint body-face assignment.

    Review12 maps are authored pigment, not physical albedo. Diffuse→RGB makes
    the toon shading actually scene-light responsive. A black-base BSDF adds
    restrained actual-light specular controlled by the same coverage map.
    """
    import bpy
    if variant not in ('skin', 'underwear'):
        raise ValueError('variant must be skin or underwear')
    p = Path(map_dir).resolve()
    material = bpy.data.materials.new(name or ('MIA12_Body_' + variant))
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    uv = _tag(nodes.new('ShaderNodeUVMap'), 'BodyUV')
    uv.uv_map = uv_layer
    specs = [('SkinBaseColor.png', 'SkinBase', 'sRGB'),
             ('UnderwearBaseColor.png', 'UnderwearColor', 'sRGB'),
             ('UnderwearCoverage.png', 'UnderwearCoverage', 'Non-Color'),
             ('ClavicleInk.png', 'ClavicleInk', 'Non-Color'),
             ('ClavicleShade.png', 'ClavicleShade', 'Non-Color')]
    textures = {}
    for file, role, space in specs:
        path = p / file
        if not path.is_file(): raise FileNotFoundError(path)
        image = bpy.data.images.load(str(path), check_existing=False)
        image.colorspace_settings.name = space
        image['mia12_source_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        tex = _tag(nodes.new('ShaderNodeTexImage'), role)
        tex.image = image
        tex.interpolation = 'Linear'
        tex.extension = 'EXTEND'
        links.new(uv.outputs['UV'], tex.inputs['Vector'])
        textures[role] = tex
    mode = _value(nodes, 'UnderwearMode', float(variant == 'underwear'))
    strength = _value(nodes, 'ClavicleStrength', clavicle_strength)
    ink_gain = _value(nodes, 'InkStrength', ink_strength)
    shade_gain = _value(nodes, 'ShadeStrength', shade_strength)
    color_only = _value(nodes, 'ColorOnly', 0.)
    ink = _math(nodes, links, 'InkTimesStrength', 'MULTIPLY', textures['ClavicleInk'].outputs['Color'], strength.outputs[0])
    ink = _math(nodes, links, 'InkTimesGain', 'MULTIPLY', ink, ink_gain.outputs[0])
    shade = _math(nodes, links, 'ShadeTimesStrength', 'MULTIPLY', textures['ClavicleShade'].outputs['Color'], strength.outputs[0])
    shade = _math(nodes, links, 'ShadeTimesGain', 'MULTIPLY', shade, shade_gain.outputs[0])
    shaded = _tag(nodes.new('ShaderNodeMixRGB'), 'AuthoredSoftPigment')
    links.new(shade, shaded.inputs[0])
    links.new(textures['SkinBase'].outputs['Color'], shaded.inputs[1])
    shaded.inputs[2].default_value = _rgba_u8((214.5, 156.5, 145.))
    lined = _tag(nodes.new('ShaderNodeMixRGB'), 'AuthoredClavicleInk')
    links.new(ink, lined.inputs[0])
    links.new(shaded.outputs[0], lined.inputs[1])
    lined.inputs[2].default_value = _rgba_u8((126, 86, 81))
    cloth = _math(nodes, links, 'CoverageTimesMode', 'MULTIPLY', textures['UnderwearCoverage'].outputs['Color'], mode.outputs[0])
    pigment = _tag(nodes.new('ShaderNodeMixRGB'), 'FinalBodyPigment')
    links.new(cloth, pigment.inputs[0])
    links.new(lined.outputs[0], pigment.inputs[1])
    links.new(textures['UnderwearColor'].outputs['Color'], pigment.inputs[2])
    diffuse = _tag(nodes.new('ShaderNodeBsdfDiffuse'), 'ActualSceneDiffuse')
    diffuse.inputs['Color'].default_value = (1, 1, 1, 1)
    if diffuse.inputs.get('Roughness') is not None:
        diffuse.inputs['Roughness'].default_value = 0.
    to_rgb = _tag(nodes.new('ShaderNodeShaderToRGB'), 'ActualSceneLightRGB')
    links.new(diffuse.outputs[0], to_rgb.inputs[0])
    luminance = _tag(nodes.new('ShaderNodeRGBToBW'), 'ActualSceneLightLuminance')
    links.new(to_rgb.outputs['Color'], luminance.inputs[0])
    ramp = _tag(nodes.new('ShaderNodeValToRGB'), 'CompatibleToonTransfer')
    config = lighting_config or {}
    stops = config.get('ramp_stops', [[.025, [.48, .36, .34, 1.]], [.175, [.72, .63, .60, 1.]], [.55, [1., 1., 1., 1.]], [.95, [1.06, 1.04, 1.02, 1.]]])
    while len(ramp.color_ramp.elements) > 2:
        ramp.color_ramp.elements.remove(ramp.color_ramp.elements[-1])
    for index, (position, color) in enumerate(stops):
        element = ramp.color_ramp.elements[index] if index < 2 else ramp.color_ramp.elements.new(position)
        element.position = position
        element.color = color
    ramp.color_ramp.interpolation = config.get('interpolation', 'EASE')
    light_scale = _math(nodes, links, 'CompatibleLightNormalization', 'MULTIPLY', luminance.outputs[0], b_value=config.get('light_scale', .25))
    links.new(light_scale, ramp.inputs[0])
    lit_color = _tag(nodes.new('ShaderNodeMixRGB'), 'SceneLitBodyPigment')
    lit_color.blend_type = 'MULTIPLY'
    lit_color.inputs[0].default_value = 1.
    links.new(pigment.outputs[0], lit_color.inputs[1])
    links.new(ramp.outputs['Color'], lit_color.inputs[2])
    emission = _tag(nodes.new('ShaderNodeEmission'), 'SceneLitToonEmission')
    links.new(lit_color.outputs[0], emission.inputs['Color'])
    rough_delta = _math(nodes, links, 'ClothRoughnessDelta', 'MULTIPLY', cloth, b_value=.24)
    rough = _math(nodes, links, 'ActualRoughness', 'ADD', rough_delta, b_value=.60)
    spec = _tag(nodes.new('ShaderNodeBsdfPrincipled'), 'ActualSceneSpecular')
    spec.inputs['Base Color'].default_value = (0, 0, 0, 1)
    spec.inputs['Metallic'].default_value = 0.
    links.new(rough, spec.inputs['Roughness'])
    level = spec.inputs.get('Specular IOR Level')
    if level is not None:
        delta = _math(nodes, links, 'ClothSpecularDelta', 'MULTIPLY', cloth, b_value=-.09)
        spec_level = _math(nodes, links, 'ActualSpecularLevel', 'ADD', delta, b_value=.18)
        links.new(spec_level, level)
    add = _tag(nodes.new('ShaderNodeAddShader'), 'ToonPlusActualSpecular')
    links.new(emission.outputs[0], add.inputs[0])
    links.new(spec.outputs[0], add.inputs[1])
    flat = _tag(nodes.new('ShaderNodeEmission'), 'ColorOnlyPigment')
    links.new(pigment.outputs[0], flat.inputs['Color'])
    switch = _tag(nodes.new('ShaderNodeMixShader'), 'ColorOnlyDiagnosticSwitch')
    links.new(color_only.outputs[0], switch.inputs[0])
    links.new(add.outputs[0], switch.inputs[1])
    links.new(flat.outputs[0], switch.inputs[2])
    out = _tag(nodes.new('ShaderNodeOutputMaterial'), 'ActualOutput')
    links.new(switch.outputs[0], out.inputs['Surface'])
    material['mia12_variant'] = variant
    material['mia12_uv_layer'] = uv_layer
    material['mia12_scope'] = 'Body-only static surface preview; authored pigment, not physical albedo or completed production maps.'
    return material


def set_controls(material, *, variant=None, clavicle_strength=None, color_only=None):
    nodes = {node.get('mia12_role'): node for node in material.node_tree.nodes}
    if variant is not None:
        if variant not in ('skin', 'underwear'): raise ValueError(variant)
        nodes['UnderwearMode'].outputs[0].default_value = float(variant == 'underwear')
        material['mia12_variant'] = variant
    if clavicle_strength is not None:
        nodes['ClavicleStrength'].outputs[0].default_value = float(clavicle_strength)
    if color_only is not None:
        nodes['ColorOnly'].outputs[0].default_value = float(color_only)


def audit_material(material):
    outputs = [node for node in material.node_tree.nodes if node.type == 'OUTPUT_MATERIAL' and node.is_active_output]
    if len(outputs) != 1: raise ValueError('Exactly one active material output required')
    seen, stack = set(), [outputs[0]]
    while stack:
        node = stack.pop()
        if node in seen: continue
        seen.add(node)
        for socket in node.inputs:
            stack.extend(link.from_node for link in socket.links)
    images = []
    for node in seen:
        if node.type == 'TEX_IMAGE':
            images.append(dict(role=node.get('mia12_role'), image=node.image.name,
                               filepath=node.image.filepath, color_space=node.image.colorspace_settings.name,
                               expected_file_sha256=node.image.get('mia12_source_sha256'),
                               UV_vector_linked=bool(node.inputs['Vector'].links)))
    roles = {node.get('mia12_role') for node in seen}
    required = {'BodyUV', 'SkinBase', 'UnderwearColor', 'UnderwearCoverage', 'ClavicleInk', 'ClavicleShade',
                'ActualSceneDiffuse', 'ActualSceneLightRGB', 'ActualRoughness', 'ActualOutput'}
    if not required.issubset(roles): raise ValueError('Missing active output ancestry: ' + repr(required - roles))
    return dict(material=material.name, variant=material.get('mia12_variant'), images=sorted(images, key=lambda row: row['role']),
                active_roles=sorted(role for role in roles if role),
                controls={node.get('mia12_role'): float(node.outputs[0].default_value) for node in seen if node.type == 'VALUE'},
                UV_layer=next(node.uv_map for node in seen if node.get('mia12_role') == 'BodyUV'))
