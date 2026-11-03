"""One small actual-light toon/flow-UV prototype for the owned rear locks only.

Palette is an appearance swatch sampled from the unchanged R3b target render,
not a recovered physical albedo. sRGB values are converted to linear explicitly.
No original material or source texture is copied or altered.
"""
from pathlib import Path
import hashlib
import json
import math
import bpy
import numpy as np

ROOT=Path('D:/MiaWorkCache/mia-reference-work/win-overlay')
NAME='MIA_Hair_CurvedRear03_TargetTonePrototype'


def linear(rgb):
    c=np.asarray(rgb,float)/255
    return np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)


def build():
    assert bpy.data.materials.get(NAME) is None, 'Do not stack look prototypes'
    ma=bpy.data.materials.new(NAME);ma.use_nodes=True
    pigment=tuple(linear((111,101,101)))
    ma.diffuse_color=(*pigment,1)
    ma['MIA_status']='Early actual-light/flow-UV look prototype. Not final paint, normals or source ART.'
    ma['MIA_palette_source']='Unchanged R3b ratio-baseline/back.png ROI245:395,75:220, warm-gray filtered75th percentile [111,101,101]sRGB. Appearance swatch, not physical albedo.'
    ma['MIA_palette_render_sha256']='a6d0f221ff773e1d54695d95554bb343be7de0cd1cb69fa906084e916b4e9f5b'
    n=ma.node_tree.nodes;n.clear();l=ma.node_tree.links
    out=n.new('ShaderNodeOutputMaterial')
    uv=n.new('ShaderNodeUVMap');uv.uv_map='LockParamUV';uv.label='Actual perimeter U / arc-length V'
    split=n.new('ShaderNodeSeparateXYZ');l.new(uv.outputs['UV'],split.inputs[0])
    freq=n.new('ShaderNodeMath');freq.operation='MULTIPLY';freq.inputs[1].default_value=2*math.pi*34;l.new(split.outputs['X'],freq.inputs[0])
    vfreq=n.new('ShaderNodeMath');vfreq.operation='MULTIPLY';vfreq.inputs[1].default_value=7;l.new(split.outputs['Y'],vfreq.inputs[0])
    vsine=n.new('ShaderNodeMath');vsine.operation='SINE';l.new(vfreq.outputs[0],vsine.inputs[0])
    drift=n.new('ShaderNodeMath');drift.operation='MULTIPLY';drift.inputs[1].default_value=.16;l.new(vsine.outputs[0],drift.inputs[0])
    phase=n.new('ShaderNodeMath');phase.operation='ADD';l.new(freq.outputs[0],phase.inputs[0]);l.new(drift.outputs[0],phase.inputs[1])
    wave=n.new('ShaderNodeMath');wave.operation='SINE';l.new(phase.outputs[0],wave.inputs[0])
    ink=n.new('ShaderNodeMapRange');ink.clamp=True;ink.inputs['From Min'].default_value=.90;ink.inputs['From Max'].default_value=1.;ink.inputs['To Min'].default_value=1.;ink.inputs['To Max'].default_value=.935;l.new(wave.outputs[0],ink.inputs['Value'])
    diffuse=n.new('ShaderNodeBsdfDiffuse');diffuse.inputs['Color'].default_value=(1,1,1,1);diffuse.inputs['Roughness'].default_value=1.
    rgb=n.new('ShaderNodeShaderToRGB');l.new(diffuse.outputs[0],rgb.inputs[0])
    bw=n.new('ShaderNodeRGBToBW');l.new(rgb.outputs['Color'],bw.inputs[0])
    shade=n.new('ShaderNodeMapRange');shade.clamp=True
    shade.inputs['From Min'].default_value=.15;shade.inputs['From Max'].default_value=1.25
    shade.inputs['To Min'].default_value=.64;shade.inputs['To Max'].default_value=1.
    l.new(bw.outputs[0],shade.inputs['Value'])
    factor=n.new('ShaderNodeMath');factor.operation='MULTIPLY';l.new(shade.outputs['Result'],factor.inputs[0]);l.new(ink.outputs['Result'],factor.inputs[1])
    color=n.new('ShaderNodeVectorMath');color.operation='SCALE';color.inputs[0].default_value=pigment;l.new(factor.outputs[0],color.inputs['Scale'])
    emission=n.new('ShaderNodeEmission');emission.inputs['Strength'].default_value=1.;l.new(color.outputs['Vector'],emission.inputs['Color'])
    spec=n.new('ShaderNodeBsdfPrincipled');spec.inputs['Base Color'].default_value=(0,0,0,1)
    spec.inputs['Roughness'].default_value=.62;spec.inputs['IOR'].default_value=1.45
    spec.inputs['Specular IOR Level'].default_value=.15
    mix=n.new('ShaderNodeMixShader');mix.inputs[0].default_value=.02;l.new(emission.outputs[0],mix.inputs[1]);l.new(spec.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface'])
    return ma,dict(palette_sRGB=[111,101,101],palette_linear=list(pigment),flow_UV='LockParamUV',
                   U_integer_frequency=34,U0_U1_flow_seam_periodic=True,actual_light_path='Diffuse→ShaderToRGB→controlled shade×linear pigment×subtle flow ink→Emission plus restrained actual specular',
                   final_maps=False,ART=False)


def apply_to_live():
    ns=bpy.app.driver_namespace;state=ns['MIA_CurvedRear03Base']
    assert state['provisional_keep'] and 'MIA_HairTonePrototype' not in ns
    body=bpy.data.objects['MIA_Review12_H_LiveRepair']
    before_body=hashlib.sha256(np.array([v.co[:] for v in body.data.vertices],np.float32).tobytes()).hexdigest()
    old={};geometry={}
    for ob in state['objects']:
        if ob.name.endswith('_RemainingMain'):continue
        assert 'LockParamUV' in ob.data.uv_layers and len(ob.data.materials)==1
        geometry[ob.name]=hashlib.sha256(np.array([v.co[:] for v in ob.data.vertices],np.float32).tobytes()).hexdigest()
        old[ob.name]=ob.data.materials[0]
    ma,report=build();state['materials'].append(ma)
    try:
        for name in old:bpy.data.objects[name].data.materials[0]=ma
        bpy.context.view_layer.update()
        assert before_body==hashlib.sha256(np.array([v.co[:] for v in body.data.vertices],np.float32).tobytes()).hexdigest()
        for name,expected in geometry.items():
            actual=hashlib.sha256(np.array([v.co[:] for v in bpy.data.objects[name].data.vertices],np.float32).tobytes()).hexdigest()
            assert actual==expected, name
    except Exception:
        for name,previous in old.items():bpy.data.objects[name].data.materials[0]=previous
        state['materials'].remove(ma);bpy.data.materials.remove(ma)
        raise
    ns['MIA_HairTonePrototype']=dict(material=ma,previous=old,geometry=geometry)
    report.update(actual_live_material_install=True,actors=len(old),geometry_unchanged=True,
                  body_sha256=before_body,original_R3b_materials_untouched=True,native_saved=False)
    p=ROOT/'.mia-cache/face-live/curved-rear03/tone-prototype';p.mkdir(parents=True,exist_ok=True)
    (p/'live-install.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    return report


def restore_live():
    ns=bpy.app.driver_namespace;state=ns['MIA_HairTonePrototype']
    for name,expected in state['geometry'].items():
        actual=hashlib.sha256(np.array([v.co[:] for v in bpy.data.objects[name].data.vertices],np.float32).tobytes()).hexdigest()
        assert actual==expected, 'Hair geometry changed after look install: '+name
    for name,old in state['previous'].items():bpy.data.objects[name].data.materials[0]=old
    bpy.context.view_layer.update()
    ns['MIA_CurvedRear03Base']['materials'].remove(state['material'])
    bpy.data.materials.remove(state['material'])
    del ns['MIA_HairTonePrototype']
    ns.pop('MIA_HairTonePrototypeModule',None)
    return dict(previous_owned_material_restored=True,native_saved=False)
