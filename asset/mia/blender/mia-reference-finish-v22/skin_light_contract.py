"""Shared scene-linear skin contract for EEVEE; UV pigment is distinct from illumination."""
import bpy

BASE_LINEAR = (.92, .69, .60, 1)
PIGMENT_NEUTRAL = (.9411765337, .8784314394, .8509804606, 1)
LIGHT_STOPS = [(.10, (.48, .36, .34, 1)),
               (.70, (.72, .63, .60, 1)),
               (2.20, (1, 1, 1, 1)),
               (3.80, (1.06, 1.04, 1.02, 1))]


def build_skin_material(name, image=None, uv_name='UVMap', pigment_neutral=PIGMENT_NEUTRAL):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    n, links = mat.node_tree.nodes, mat.node_tree.links
    n.clear()
    white = n.new('ShaderNodeBsdfDiffuse'); white.name = 'MeasuredWhiteDiffuse'
    white.inputs['Color'].default_value = (1,1,1,1)
    rgb = n.new('ShaderNodeShaderToRGB'); rgb.name = 'ActualSceneLighting'
    links.new(white.outputs[0], rgb.inputs[0])
    luminance = n.new('ShaderNodeRGBToBW'); links.new(rgb.outputs[0], luminance.inputs[0])
    normalize = n.new('ShaderNodeMath'); normalize.operation = 'DIVIDE'; normalize.inputs[1].default_value = 4
    links.new(luminance.outputs[0], normalize.inputs[0])
    ramp = n.new('ShaderNodeValToRGB'); ramp.name = 'MIA_CommonSkinLightRamp'
    ramp.color_ramp.interpolation = 'EASE'
    for e in list(ramp.color_ramp.elements)[1:]: ramp.color_ramp.elements.remove(e)
    for i,(value,color) in enumerate(LIGHT_STOPS):
        e = ramp.color_ramp.elements[0] if i==0 else ramp.color_ramp.elements.new(value/4)
        e.position = value/4; e.color = color
    links.new(normalize.outputs[0], ramp.inputs[0])
    base = n.new('ShaderNodeRGB'); base.name = 'MIA_CommonSkinBaseLinear'; base.outputs[0].default_value = BASE_LINEAR
    pigment = base.outputs[0]
    if image:
        uv = n.new('ShaderNodeUVMap'); uv.uv_map = uv_name
        tex = n.new('ShaderNodeTexImage'); tex.name = 'AuthoredUVPigment'; tex.image = image; tex.interpolation = 'Linear'
        links.new(uv.outputs[0], tex.inputs['Vector'])
        divide = n.new('ShaderNodeMixRGB'); divide.name = 'RemoveOldNeutralMultiplier'; divide.blend_type = 'DIVIDE'; divide.inputs[0].default_value = 1
        links.new(tex.outputs['Color'],divide.inputs[1]); divide.inputs[2].default_value = pigment_neutral
        color = n.new('ShaderNodeMixRGB'); color.blend_type = 'MULTIPLY'; color.inputs[0].default_value = 1
        links.new(base.outputs[0],color.inputs[1]); links.new(divide.outputs[0],color.inputs[2]); pigment=color.outputs[0]
    multiply = n.new('ShaderNodeMixRGB'); multiply.name = 'PigmentTimesControlledLight'; multiply.blend_type = 'MULTIPLY'; multiply.inputs[0].default_value=1
    links.new(pigment,multiply.inputs[1]); links.new(ramp.outputs['Color'],multiply.inputs[2])
    em = n.new('ShaderNodeEmission'); links.new(multiply.outputs[0],em.inputs['Color'])
    output = n.new('ShaderNodeOutputMaterial'); links.new(em.outputs[0],output.inputs['Surface'])
    mat['surface_contract']='EEVEE white diffuse -> RGB -> luminance/4 -> shared ramp; explicit linear base and UV pigment. Not a PBR albedo extraction.'
    return mat
