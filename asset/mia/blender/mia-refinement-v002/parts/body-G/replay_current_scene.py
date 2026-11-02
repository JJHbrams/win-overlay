"""Body v002 G portable current-scene delta; never opens or saves a scene.

Original42 are guarded by name. Additional face-only keys migrate their
unchanged body coordinates onto the same final Basis. All other owners,
saved pose channels, cameras and source lights remain caller-owned.
"""
import bpy,numpy as np,json
from pathlib import Path
P=Path(__file__).resolve().parent

def array(data,field='co',width=3):
 a=np.empty(len(data)*width,np.float32);data.foreach_get(field,a);return a.reshape(-1,width)

def image(name,filename,space):
 im=bpy.data.images.load(str(P/filename),check_existing=False);im.name='MIA_V002_G_'+name;im.colorspace_settings.name=space;im.pack();return im

def apply():
 o=bpy.data.objects['MIA_V27_SharedHeadBody'];m=o.data;d=np.load(P/'body-final-delta.npz');idx=d['indices'];keys=m.shape_keys.key_blocks;mapping={k.name:k for k in keys};names=list(map(str,d['key_names']));assert len(m.vertices)==4647 and len(m.polygons)==5486 and len(m.loops)==20148
 assert max(idx)<3957 and set(names).issubset(mapping)
 assert np.array_equal(np.array([e.vertices[:] for e in m.edges]),d['edges']),'Topology differs; migration review required'
 assert np.array_equal(np.array([l.vertex_index for l in m.loops]),d['loop_vertices'])
 for j,name in enumerate(['UVMap','MIA_BODY_V23_UV']):assert name in m.uv_layers and np.array_equal(array(m.uv_layers[name].data,'uv',2),d['uv_'+str(j)]),'Original UV differs'
 assert 'MIA_V002_UnderwearUV' not in m.uv_layers,'Body delta already applied'
 for j,name in enumerate(names):assert np.array_equal(array(mapping[name].data)[idx],d['baseline_selected42'][j]),'Source body coordinates differ in '+name
 extra=[k for k in keys if k.name not in names]
 for k in extra:assert np.max(abs(array(k.data)[idx]-d['baseline_selected42'][0]))<1e-7,'Additional key owns body vertices: '+k.name
 assert np.array_equal(array(m.vertices)[idx],d['baseline_selected42'][0]),'Source body raw cache differs'
 wd=json.loads((P/'body-weight-delta.json').read_text(encoding='utf8'));arm=next(x.object for x in o.modifiers if x.type=='ARMATURE');bone_names=set(arm.data.bones.keys());group_names=[g.name for g in o.vertex_groups]
 for i in wd['indices']:
  now={group_names[g.group]:g.weight for g in m.vertices[i].groups if group_names[g.group] in bone_names};assert now==wd['original'][str(i)],'Source named bone weights differ at '+str(i)
 original_nodes=m.materials[1].node_tree.nodes;assert all(name in original_nodes for name in ['PigmentTimesControlledLight','MeasuredWhiteDiffuse','AuthoredUVPigment']),'Source body shader differs';assert any(q.type=='OUTPUT_MATERIAL' and q.is_active_output for q in original_nodes)
 assert all(name in o.vertex_groups and name in bone_names for target in wd['target'].values() for name in target),'Named target weights unavailable'
 # All preconditions precede mutation.
 for j,name in enumerate(names):
  k=mapping[name];a=array(k.data);a[idx]=d['target_selected42'][j];k.data.foreach_set('co',a.ravel())
 for k in extra:
  a=array(k.data);a[idx]=d['target_selected42'][0];k.data.foreach_set('co',a.ravel())
 raw=array(m.vertices);raw[idx]=d['target_selected42'][0];m.vertices.foreach_set('co',raw.ravel())
 for i in wd['indices']:
  for name in wd['original'][str(i)]:o.vertex_groups[name].remove([i])
  for name,w in wd['target'][str(i)].items():o.vertex_groups[name].add([i],w,'REPLACE')
 old_active=m.uv_layers.active_index;new=m.uv_layers.new(name='MIA_V002_UnderwearUV');new.data.foreach_set('uv',np.load(P/'underwear-uv.npy').ravel());m.uv_layers.active_index=old_active
 mat=m.materials[1].copy();mat.name='MIA_V002_D_Body_SourceSupport';mat['MiaScope']='DactualLresampledsoft onfixedG3thorax + continuouspelvis/thigh/calfvolume + actual-limit sourceplaced underwear; safeabs/limbpaintonly, oldupperpaintdisabled; noARTapproval';m.materials[1]=mat
 n=mat.node_tree.nodes;lk=mat.node_tree.links
 uv=n.new('ShaderNodeUVMap');uv.name='V002_UnderwearUV';uv.uv_map='MIA_V002_UnderwearUV';uv.location=(-850,400)
 co=image('MIA_V002_Underwear_Pigment_sRGB','Mia_BodyUnderwear_Color_2048.png','sRGB')
 he=image('MIA_V002_Seam_Height_NonColor','Mia_Body_SeamHeight_2048.png','Non-Color')
 ro=image('MIA_V002_Fabric_Roughness_NonColor','Mia_Body_Roughness_2048.png','Non-Color')
 textures=[]
 for label,im,y in [('Pigment',co,500),('Height',he,200),('Roughness',ro,-100)]:
  q=n.new('ShaderNodeTexImage');q.name='V002_'+label;q.image=im;q.extension='EXTEND';q.location=(-650,y);lk.new(uv.outputs['UV'],q.inputs['Vector']);textures.append(q)
 pigment,height,rough=textures
 original=n['PigmentTimesControlledLight'];old=original.inputs[1].links[0].from_socket
 combine=n.new('ShaderNodeCombineColor');combine.name='V002_C_Generated_Pigment_RGB';combine.mode='RGB'
 for j,ch in enumerate('RGB'):
  im=image('MIA_V002_C_BodyPigment_'+ch+'_NonColor','Mia_BodyPigment_'+ch+'_2048.png','Non-Color');tex=n.new('ShaderNodeTexImage');tex.name='V002_C_BodyPigment_'+ch;tex.image=im;tex.extension='EXTEND';lk.new(uv.outputs['UV'],tex.inputs['Vector']);decode=n.new('ShaderNodeMath');decode.operation='MULTIPLY';decode.inputs[1].default_value=2;lk.new(tex.outputs['Color'],decode.inputs[0]);lk.new(decode.outputs[0],combine.inputs[j])
 cosmetic=n.new('ShaderNodeMixRGB');cosmetic.name='V002_C_Generated_Body_Pigment_Multiplier';cosmetic.blend_type='MULTIPLY';cosmetic.inputs[0].default_value=1;lk.new(old,cosmetic.inputs[1]);lk.new(combine.outputs['Color'],cosmetic.inputs[2]);old=cosmetic.outputs[0]
 mix=n.new('ShaderNodeMixRGB');mix.name='V002_Fabric_Over_OriginalSkin';mix.blend_type='MIX';mix.location=(-300,500);lk.new(pigment.outputs['Alpha'],mix.inputs[0]);lk.new(old,mix.inputs[1]);lk.new(pigment.outputs['Color'],mix.inputs[2]);lk.new(mix.outputs[0],original.inputs[1])
 bump=n.new('ShaderNodeBump');bump.name='V002_Actual_Seam_Normal';bump.location=(-250,100);bump.inputs['Strength'].default_value=.65;bump.inputs['Distance'].default_value=.0004;lk.new(height.outputs['Color'],bump.inputs['Height']);lk.new(bump.outputs['Normal'],n['MeasuredWhiteDiffuse'].inputs['Normal'])
 # A small actual BSDF fabric response lets roughness be observable, while
 # preserving the original scene-lit toon ramp as the dominant appearance.
 bs=n.new('ShaderNodeBsdfPrincipled');bs.name='V002_Fabric_BSDF';bs.location=(0,-150);bs.inputs['IOR'].default_value=1.45;bs.inputs['Metallic'].default_value=0;bs.inputs['Specular IOR Level'].default_value=.3
 lk.new(mix.outputs[0],bs.inputs['Base Color']);lk.new(rough.outputs['Color'],bs.inputs['Roughness']);lk.new(bump.outputs['Normal'],bs.inputs['Normal'])
 factor=n.new('ShaderNodeMath');factor.name='V002_Fabric_Reflection_Weight';factor.operation='MULTIPLY';factor.inputs[1].default_value=.04;lk.new(pigment.outputs['Alpha'],factor.inputs[0]);skin=n.new('ShaderNodeMath');skin.name='V002_C_Skin_Reflection_Weight';skin.operation='ADD';skin.inputs[1].default_value=.015;lk.new(factor.outputs[0],skin.inputs[0])
 out=next(q for q in n if q.type=='OUTPUT_MATERIAL' and q.is_active_output);original_shader=out.inputs['Surface'].links[0].from_socket
 blend=n.new('ShaderNodeMixShader');blend.name='V002_Toon_Plus_Fabric_Response';blend.location=(450,250);lk.new(skin.outputs[0],blend.inputs[0]);lk.new(original_shader,blend.inputs[1]);lk.new(bs.outputs['BSDF'],blend.inputs[2]);lk.new(blend.outputs[0],out.inputs['Surface'])
 old=n['V002_Fabric_BSDF'];n.remove(old);gloss=n.new('ShaderNodeBsdfGlossy');gloss.name='V002_Fabric_BSDF';gloss.label='Specular only: avoids full diffuse light amplification';gloss.inputs['Color'].default_value=(.04,.04,.04,1);lk.new(n['V002_Roughness'].outputs['Color'],gloss.inputs['Roughness']);lk.new(n['V002_Actual_Seam_Normal'].outputs['Normal'],gloss.inputs['Normal']);blend=n['V002_Toon_Plus_Fabric_Response'];lk.new(gloss.outputs['BSDF'],blend.inputs[2])
 geo=n.new('ShaderNodeNewGeometry');geo.name='V002_F2_ShaderPosition';sep=n.new('ShaderNodeSeparateXYZ');lk.new(geo.outputs['Position'],sep.inputs[0]);fade=n.new('ShaderNodeMapRange');fade.name='V002_F2_NeckReflectionFade';fade.clamp=True;fade.interpolation_type='SMOOTHERSTEP';fade.inputs['From Min'].default_value=1.35;fade.inputs['From Max'].default_value=1.39;fade.inputs['To Min'].default_value=1;fade.inputs['To Max'].default_value=0;lk.new(sep.outputs['Z'],fade.inputs['Value']);factor=n.new('ShaderNodeMath');factor.operation='MULTIPLY';factor.name='V002_F2_FadedReflectionWeight';lk.new(n['V002_C_Skin_Reflection_Weight'].outputs[0],factor.inputs[0]);lk.new(fade.outputs['Result'],factor.inputs[1]);lk.new(factor.outputs[0],blend.inputs[0])
 # F body head-blend factor is identically zero in actual ablation.
 # Omit duplicated head shader to preserve independent face ownership.
 out=next(q for q in n if q.type=='OUTPUT_MATERIAL' and q.is_active_output);lk.new(blend.outputs[0],out.inputs['Surface'])
 mat.name='MIA_V002_G_Body_ContinuousSupport';mat['MiaScope']='BodyG:1255sourcebodycoordinatecontrols including129fairlower-softsupport controls withpreservedvolume;162namednormalizedaxilla/upperarm/chestweights; original8staticworkaroundremoved; explicitnewfullbodyUV; actualactive6maps; specular-onlyfabricresponse; protectedface/hair/oldUV/pose; no whole ART approval.'
 o['MIA_V002_BodySupport']=mat['MiaScope']
 o['MIA_V002_WeightRepair']='162namedaxilla/upperarm/chest normalizedweights; causal continuity repair; no newkeys/drivers or nail deletion. Mechanical straight -20 distalpose remains invalid.'
 bpy.context.view_layer.update();return {'body':o.name,'coordinate_indices':idx.tolist(),'coordinate_count':len(idx),'original_key_names':names,'migrated_additional_face_keys':[k.name for k in extra],'weight_indices':wd['indices'],'weight_count':len(wd['indices']),'material':mat.name,'new_uv':new.name,'active_image_files':[str(P/x) for x in ['Mia_BodyUnderwear_Color_2048.png','Mia_Body_SeamHeight_2048.png','Mia_Body_Roughness_2048.png']+['Mia_BodyPigment_'+ch+'_2048.png' for ch in 'RGB']],'scene_opened_or_saved':False,'ART':'Bounded body improvement; G lowerreturn/clavicle/fingers require actual final visual judgment. Mechanical straight-arm-20 remains invalid, not accepted.'}
