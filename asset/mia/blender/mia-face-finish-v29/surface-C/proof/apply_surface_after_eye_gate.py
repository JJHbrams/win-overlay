"""Deferred, guarded material-only candidate builder. Execute AFTER eye/lash gate.

Usage: blender -b --python this.py -- --native ACCEPTED --sha256 EXACT
       --output OWNED_NEW_BLEND --eye-lash-gate-passed
No execution on the f0dead preparation baseline is implied by this source file.
"""
import bpy,numpy as np,json,hashlib,argparse,sys
from pathlib import Path
P=Path(__file__).parent.resolve();ap=argparse.ArgumentParser();ap.add_argument('--native',required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--output',required=True);ap.add_argument('--eye-lash-gate-passed',action='store_true');a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);assert a.eye_lash_gate_passed,'Eye/lash gate must precede native application'
S=Path(a.native);O=Path(a.output).resolve();assert O.is_relative_to(P) and not O.exists();O.parent.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert sha(S)==a.sha256
MAPDIR=P/'native-control-maps-final';ART=P/'art-pigment-B/Mia_UVPigment_Art_B.png';assert ART.exists()
endpoint_validation=json.loads((P/'wall-fade-native-endpoint-validation.json').read_text());assert endpoint_validation['builder_sha256']==sha(Path(__file__)), 'Current material builder needs its CPU-native endpoint validation rerun';assert max(endpoint_validation['errors_m_or_linear_RGB'].values())<2e-6
bpy.ops.wm.open_mainfile(filepath=str(S),use_scripts=False)
def scalar(v):
 if isinstance(v,(str,bool,int,float)) or v is None:return v
 try:return list(v)
 except:return str(v)
def graph(tree,stack=()):
 if tree.name in stack:return {'recursive_group':tree.name}
 nodes=[]
 for n in tree.nodes:
  r={'name':n.name,'type':n.bl_idname,'mute':n.mute,'inputs':[(s.identifier,scalar(s.default_value)) for s in n.inputs if hasattr(s,'default_value')]}
  for k in ['is_active_output','operation','blend_type','uv_map','attribute_name','attribute_type','interpolation','extension','space','distribution']:
   if hasattr(n,k):r[k]=scalar(getattr(n,k))
  if n.type=='TEX_IMAGE' and n.image:r['image']={'name':n.image.name,'colorspace':n.image.colorspace_settings.name,'packed_sha':hashlib.sha256(n.image.packed_file.data).hexdigest() if n.image.packed_file else None}
  if n.type=='VALTORGB':r['ramp']=[(e.position,list(e.color)) for e in n.color_ramp.elements];r['ramp_interpolation']=n.color_ramp.interpolation
  if n.type=='RGB':r['constant']=list(n.outputs[0].default_value)
  if n.type=='VALUE':r['constant']=n.outputs[0].default_value
  if n.type=='GROUP' and n.node_tree:r['group']=graph(n.node_tree,stack+(tree.name,))
  nodes.append(r)
 return {'nodes':nodes,'links':[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in tree.links]}
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def original_material_graphs():return {m.name:digest(graph(m.node_tree)) for m in bpy.data.materials if m.use_nodes}
def geometry():
 out={}
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  m=o.data;parts=[np.array([list(v.co) for v in m.vertices],dtype='<f8').tobytes(),np.array([list(e.vertices) for e in m.edges],dtype='<i8').tobytes(),np.array([l.vertex_index for l in m.loops],dtype='<i8').tobytes()]
  if m.shape_keys:parts.append(np.array([[list(v.co) for v in k.data] for k in m.shape_keys.key_blocks],dtype='<f8').tobytes())
  for uv in m.uv_layers:parts+=[uv.name.encode(),np.array([list(x.uv) for x in uv.data],dtype='<f8').tobytes()]
  parts.append(json.dumps([[(o.vertex_groups[g.group].name,g.weight) for g in v.groups] for v in m.vertices]).encode())
  out[o.name]=hashlib.sha256(b''.join(parts)).hexdigest()
 return out
oldgraphs=original_material_graphs();oldgeometry=geometry();oldslots={o.name:[s.material.name if s.material else None for s in o.material_slots] for o in bpy.context.scene.objects if o.type=='MESH'}
world=bpy.context.scene.world;worldhash=digest(graph(world.node_tree)) if world and world.use_nodes else None
oldimages={im.name:(im.colorspace_settings.name,hashlib.sha256(im.packed_file.data).hexdigest() if im.packed_file else None) for im in bpy.data.images}
owner=bpy.data.objects['MIA_V27_SharedHeadBody'];assert len(owner.data.vertices)==4647 and len(owner.data.shape_keys.key_blocks)==42
assert digest(graph(owner.material_slots[0].material.node_tree))==endpoint_validation['original_face_graph_sha256'],'Accepted eye native changed the audited original face route'
for sign in [-1,1]:assert digest(graph(bpy.data.objects['V28G_InnerLid_'+str(sign)].material_slots[0].material.node_tree))==endpoint_validation['original_wall_graph_sha256'],'Accepted eye native changed the audited wall route'
uvhash=hashlib.sha256(np.array([list(x.uv) for x in owner.data.uv_layers['UVMap'].data],dtype='<f8').tobytes()).hexdigest();manifest=json.loads((MAPDIR/'native-control-bake-manifest.json').read_text());assert uvhash==manifest['uv_layout_sha256'],'UV chart changed: re-author/rebake selectors rather than silently fitting'
def load_image(path,colorspace):
 im=bpy.data.images.load(str(path),check_existing=False);im.colorspace_settings.name=colorspace;im.pack();return im
images={'art':load_image(ART,'sRGB'),'features':load_image(MAPDIR/'V29_FeatureControls_RGB.exr','Non-Color'),'response':load_image(MAPDIR/'V29_LightReflectControls_RGB.exr','Non-Color')}
newmaterials=[]
def material(old,name,wall=False):
 assert old.use_nodes and not any(n.type=='GROUP' for n in old.node_tree.nodes),'Do not shallow-copy and edit shared groups. A touched group needs an explicit independent clone.'
 # Replaced originals can become zero-user IDs. Retain their unchanged
 # graphs in the saved candidate so the reopen preservation guard can audit
 # them, rather than allowing Blender's orphan omission to discard them.
 old.use_fake_user=True
 mat=old.copy();mat.name=name;n=mat.node_tree.nodes;l=mat.node_tree.links;uv=n.get('UV 맵.001');assert uv and uv.uv_map=='UVMap';pig=n['V27_ACTUAL_UV_PIGMENT'].outputs['Color'];ramp=n['MIA_CommonSkinLightRamp'].outputs['Color'];multiply=n['PigmentTimesControlledLight'];emission=n['방출'];output=next(x for x in n if x.type=='OUTPUT_MATERIAL' and x.is_active_output);assert output.inputs['Surface'].links[0].from_node==emission
 def value(name,v):
  q=n.new('ShaderNodeValue');q.name=name;q.label=name;q.outputs[0].default_value=v;return q.outputs[0]
 def math(op,x,y=None,label=None):
  q=n.new('ShaderNodeMath');q.operation=op
  if label:q.name=label
  for i,s in enumerate([x,y] if y is not None else [x]):
   if hasattr(s,'node'):l.new(s,q.inputs[i])
   else:q.inputs[i].default_value=s
  return q.outputs[0]
 def mix(f,x,y,name):
  q=n.new('ShaderNodeMixRGB');q.blend_type='MIX';q.name=name
  for i,s in enumerate([f,x,y]):
   if hasattr(s,'node'):l.new(s,q.inputs[i])
   elif isinstance(s,(float,int)):q.inputs[i].default_value=s
   else:q.inputs[i].default_value=s
  return q.outputs[0]
 def tex(key,name):
  q=n.new('ShaderNodeTexImage');q.name=name;q.image=images[key];q.interpolation='Linear';q.extension='EXTEND';l.new(uv.outputs['UV'],q.inputs['Vector']);return q.outputs['Color']
 feat=n.new('ShaderNodeSeparateColor');feat.mode='RGB';l.new(tex('features','V29_NATIVE_FeatureControls'),feat.inputs['Color']);resp=n.new('ShaderNodeSeparateColor');resp.mode='RGB';l.new(tex('response','V29_NATIVE_LightReflectControls'),resp.inputs['Color']);art=tex('art','V29_ImageGenB_MaskedArt_sRGB')
 enabled=value('V29_SurfaceEnabled',1.);fatiguegain=value('V29_FatigueGain',.55);foldgain=value('V29_FoldGain',.65);makeupgain=value('V29_MakeupGain',.40);specgain=value('V29_SpecularGain',.08);shadowenabled=value('V29_ShadowEnabled',1.)
 if wall:
  at=n.new('ShaderNodeAttribute');at.attribute_name='V29_CosmeticRootFade';fade=at.outputs['Fac']
 else:fade=value('V29_FaceRootFade',1.)
 blink=[]
 for side in ['R','L']:
  out=value('V29_FoldOpen_'+side,1.);driver=out.driver_add('default_value').driver;driver.type='SCRIPTED'
  for varname,key in [('allclose','Face.M_F00_000_00_Fcl_EYE_Close'),('sideclose','Face.M_F00_000_00_Fcl_EYE_Close_'+side)]:
   var=driver.variables.new();var.name=varname;var.type='SINGLE_PROP';var.targets[0].id_type='KEY';var.targets[0].id=owner.data.shape_keys;var.targets[0].data_path='key_blocks["'+key+'"].value'
  driver.expression='max(0.0,1.0-max(allclose,sideclose))';blink.append(out)
 sepuv=n.new('ShaderNodeSeparateXYZ');l.new(uv.outputs['UV'],sepuv.inputs[0]);right=math('LESS_THAN',sepuv.outputs['X'],.5);openfactor=math('ADD',math('MULTIPLY',right,blink[0]),math('MULTIPLY',math('SUBTRACT',1.,right),blink[1]));foldstrength=math('MULTIPLY',foldgain,openfactor)
 # Only the old flattened fatigue/fold need neutral-carrier cleanup. Makeup
 # is an overlay: retain the original lip seam, nose accents and skin color.
 coverage=math('MAXIMUM',feat.outputs['Red'],feat.outputs['Green'])
 # Remove only the old flattened accents inside native cosmetic selections.
 # Outside coverage0 the original packed pigment path is bit-for-bit intact.
 clean=mix(coverage,pig,(.82,.63,.55,1.),'V29_LocalOldAccentCleanup')
 weights=[math('MULTIPLY',feat.outputs['Red'],fatiguegain),math('MULTIPLY',feat.outputs['Green'],foldstrength),math('MULTIPLY',feat.outputs['Blue'],makeupgain)];paintweight=math('MAXIMUM',math('MAXIMUM',weights[0],weights[1]),weights[2])
 colored=mix(paintweight,clean,art,'V29_IndependentCosmeticArt')
 # Fade the COMPLETE cosmetic result, including old-accent cleanup, once.
 # Deep wall fade0 therefore returns the exact original pigment. At root1
 # the wall and Face run the same complete cosmetic expression at the sameUV.
 rooted=mix(fade,pig,colored,'V29_CompleteCosmeticRootFade');pigment=mix(enabled,pig,rooted,'V29_OriginalVsSurfaceBypass');l.new(pigment,multiply.inputs['Color1'])
 # Actual diffuse light remains the existing BSDF/ShaderToRGB/ramp path.
 shadowamount=math('MULTIPLY',math('MULTIPLY',enabled,shadowenabled),fade);shadow=math('SUBTRACT',1.,math('MULTIPLY',math('SUBTRACT',1.,resp.outputs['Red']),shadowamount));light=mix(shadow,(1,1,1,1),ramp,'V29_ActiveDiffuseShadowControl');l.new(light,multiply.inputs['Color2'])
 specoverride=value('V29_SpecularOverrideFlag',0.);specvalue=value('V29_SpecularOverrideValue',1.);roughoverride=value('V29_RoughnessOverrideFlag',0.);roughvalue=value('V29_RoughnessOverrideValue',.2)
 specweight=mix(specoverride,resp.outputs['Green'],specvalue,'V29_SpecularMaskOrFlatProbe');rough=mix(roughoverride,resp.outputs['Blue'],roughvalue,'V29_RoughnessMapOrFlatProbe')
 glossy=n.new('ShaderNodeBsdfAnisotropic');glossy.name='V29_ACTUAL_SpecularBSDF';glossy.inputs['Color'].default_value=(1,1,1,1);glossy.inputs['Anisotropy'].default_value=0.;l.new(rough,glossy.inputs['Roughness']);torgb=n.new('ShaderNodeShaderToRGB');torgb.name='V29_ActualSceneSpecular';l.new(glossy.outputs[0],torgb.inputs['Shader'])
 weight=math('MULTIPLY',math('MULTIPLY',specgain,enabled),fade);scale=n.new('ShaderNodeMixRGB');scale.name='V29_WeightedActualSpecular';scale.blend_type='MULTIPLY';scale.inputs[0].default_value=1.;l.new(torgb.outputs['Color'],scale.inputs[1]);l.new(math('MULTIPLY',specweight,weight),scale.inputs[2]);add=n.new('ShaderNodeMixRGB');add.name='V29_DiffusePlusRestrainedSpecular';add.blend_type='ADD';add.inputs[0].default_value=1.;l.new(multiply.outputs['Color'],add.inputs[1]);l.new(scale.outputs[0],add.inputs[2]);l.new(add.outputs[0],emission.inputs['Color'])
 assert output.is_active_output and output.inputs['Surface'].links[0].from_node==emission
 mat['V29_role']='Face-only masked art and independently controlled actual-light diffuse/spec/roughness. No shared groups edited.';newmaterials.append(mat.name);return mat
assert owner.data.users==1;old=owner.material_slots[0].material;owner.material_slots[0].material=material(old,'V29_Face_MaskedPigment_ActualLight')
walls=[]
for sign in [-1,1]:
 wall=bpy.data.objects['V28G_InnerLid_'+str(sign)];assert len(wall.data.vertices)==576 and wall.data.users==1
 attr=wall.data.attributes.get('V29_CosmeticRootFade') or wall.data.attributes.new('V29_CosmeticRootFade','FLOAT','POINT')
 for i,item in enumerate(attr.data):
  t=(i//96)/5.;item.value=1.-t*t*(3.-2.*t)
 wall.material_slots[0].material=material(wall.material_slots[0].material,'V29_InnerWall_'+str(sign)+'_RootFade',wall=True);walls.append(wall.name)
assert geometry()==oldgeometry
for name,h in oldgraphs.items():assert digest(graph(bpy.data.materials[name].node_tree))==h,('original shared material/group modified',name)
assert (digest(graph(world.node_tree)) if world and world.use_nodes else None)==worldhash
for name,(cs,h) in oldimages.items():
 im=bpy.data.images[name];assert im.colorspace_settings.name==cs and (hashlib.sha256(im.packed_file.data).hexdigest() if im.packed_file else None)==h
# open_mainfile invalidates every RNA handle. Persist only plain identifiers
# and expected values before reopening, then reacquire the packed image IDs.
new_image_expected={k:{'name':im.name,'size':list(im.size),'colorspace':im.colorspace_settings.name,'packed_sha256':hashlib.sha256(im.packed_file.data).hexdigest()} for k,im in images.items()}
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(O));bpy.ops.wm.open_mainfile(filepath=str(O),use_scripts=False)
reopened_images={}
for role,expected in new_image_expected.items():
 im=bpy.data.images[expected['name']];actual={'name':im.name,'size':list(im.size),'colorspace':im.colorspace_settings.name,'packed_sha256':hashlib.sha256(im.packed_file.data).hexdigest() if im.packed_file else None};assert actual==expected,('packed image changed on reopen',role);reopened_images[role]=actual
reopened_world=bpy.context.scene.world;assert (digest(graph(reopened_world.node_tree)) if reopened_world and reopened_world.use_nodes else None)==worldhash
for name,(cs,h) in oldimages.items():
 im=bpy.data.images[name];assert im.colorspace_settings.name==cs and (hashlib.sha256(im.packed_file.data).hexdigest() if im.packed_file else None)==h,('original image changed on reopen',name)
assert geometry()==oldgeometry
for name,h in oldgraphs.items():assert digest(graph(bpy.data.materials[name].node_tree))==h,('reopened original material/group changed',name)
allowed={'MIA_V27_SharedHeadBody',*walls}
for name,slots in oldslots.items():
 now=[s.material.name if s.material else None for s in bpy.data.objects[name].material_slots]
 if name not in allowed:assert now==slots,('other owner slots changed',name)
 else:assert now[1:]==slots[1:],('non-face slot changed',name)
report={'baseline':str(S),'baseline_sha256':a.sha256,'baseline_sha256_after':sha(S),'candidate':str(O),'candidate_sha256':sha(O),'geometry_all_owners_exact':True,'original_material_and_nested_group_digests_equal':True,'original_image_pixels_colorspaces_equal':True,'body_head_neck_existing_material_graphs_untouched':True,'new_materials':newmaterials,'actual_new_material_graphs':{name:graph(bpy.data.materials[name].node_tree) for name in newmaterials},'only_changed_slots':'SharedHeadBody slot0; both accepted InnerLid slot0. No other owner slots changed.','wall_fade':'StoredPOINT attr row0=1, row5=0 on6x96 accepted topology; new cosmetics/spec fade into wall while root matchesface.','fold_fade':'UVleft/worldXnegative uses max(Close,Close_R); UVright uses max(Close,Close_L); originalgeometry/keys/driversunchanged. Inspect actual .5/1 bilateral/unilateral closure before accepting.','maps':reopened_images,'packed_map_reopen_verification':True,'cpu_native_endpoint_validation':endpoint_validation,'original_geometry_digests':oldgeometry,'original_material_digests':oldgraphs,'status':'UNREVIEWED material-only native. Actual color-only/source/diffuse/spec/roughness/moved-light/blink probes required; hashes are not art acceptance.'}
assert report['baseline_sha256_after']==a.sha256;(O.parent/'surface-candidate-guard.json').write_text(json.dumps(report,indent=2),encoding='utf8');print('V29_MATERIAL_ONLY_CANDIDATE_SAVED',str(O),flush=True)
