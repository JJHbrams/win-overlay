"""Attach real pigment and linear mask maps to a separate owned face material."""
import bpy,json,hashlib,ast
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'look-d';MAP=OUT/'maps';SOURCE=ROOT/'shape-b/Mia_FaceFinish8_NasalBuccalB.blend'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();ah=lambda p:hashlib.sha256(np.asarray(p).tobytes()).hexdigest()
t=ast.parse((ROOT.parent/'finish-6/dependencies/legacy_snapshot_apply_interp.py').read_text());exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='snapshots'],type_ignores=[]),'guards','exec'))
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));before=snapshots();skin=bpy.data.objects['MIA_V14_SculptedSkin'];old=skin.data.materials[7];mat=old.copy();mat.name='MIA_Finish8_AuthoredFacePigment';skin.data.materials[7]=mat
nodes=mat.node_tree.nodes;links=mat.node_tree.links;uv=nodes.new('ShaderNodeUVMap');uv.name='FINISH8_ACTUAL_UV';uv.uv_map='UVMap'
artifacts={}
def image(name,array,scalar=False):
 im=bpy.data.images.new('MIA_Finish8_'+name,width=2048,height=2048,alpha=True,float_buffer=True);im.colorspace_settings.name='Non-Color'
 if scalar:rgba=np.concatenate([np.repeat(array[:,:,None],3,axis=2),np.ones((2048,2048,1),np.float32)],axis=2)
 else:rgba=array
 im.pixels.foreach_set(np.ascontiguousarray(rgba,dtype=np.float32).ravel());im.file_format='OPEN_EXR';im.filepath_raw=str(MAP/(name+'_LINEAR_2048.exr'));im.save();im.pack()
 tex=nodes.new('ShaderNodeTexImage');tex.name='FINISH8_'+name;tex.image=im;tex.interpolation='Linear';links.new(uv.outputs['UV'],tex.inputs['Vector']);artifacts[name]={'path':im.filepath_raw,'sha256':sha(im.filepath_raw),'size':list(im.size),'colorspace':im.colorspace_settings.name,'node':tex.name};return tex
base=image('BasePigment',np.load(MAP/'BasePigment_LINEAR.npy'))
fat=image('FatigueMask',np.load(MAP/'FatigueMask_LINEAR.npy'),True);ink=image('FineLineMask',np.load(MAP/'FineLineMask_LINEAR.npy'),True)
def tinted(src,mask,color,name):
 m=nodes.new('ShaderNodeMixRGB');m.name=name;m.blend_type='MULTIPLY';links.new(mask.outputs['Color'],m.inputs[0]);links.new(src.outputs['Color'],m.inputs[1]);m.inputs[2].default_value=(*color,1);return m
fatmix=tinted(base,fat,(.48,.35,.39),'FINISH8_PigmentFatigue');linemix=tinted(fatmix,ink,(.13,.09,.10),'FINISH8_FineLinePigment')
light=nodes['PigmentTimesControlledLight'];links.new(linemix.outputs['Color'],light.inputs[1])
# Archived upstream nodes are left inert for provenance; connected routes above
# now consume the actual new maps. Actual scene light -> ramp is retained.
after=snapshots()
for n in before:
 for field in before[n]:
  if n==skin.name and field=='materials':continue
  assert before[n][field]==after[n][field],(n,field)
native=OUT/'Mia_FaceFinish8_AuthoredLookD.blend';assert not native.exists();bpy.ops.wm.save_as_mainfile(filepath=str(native));bpy.ops.wm.open_mainfile(filepath=str(native));assert snapshots()==after
report={'status':'WORKING LOOK / ART UNAPPROVED','geometry_source':{'path':str(SOURCE),'sha256':sha(SOURCE)},'native':{'path':str(native),'sha256':sha(native)},'maps':artifacts,'material':mat.name if False else 'MIA_Finish8_AuthoredFacePigment','consumed_route':'UVMap -> BasePigment RGB -> FatigueMask multiply brown-mauve -> FineLineMask multiply deep warm ink -> PigmentTimesControlledLight; white Diffuse -> ShaderToRGB -> inherited scene light ramp -> same multiply -> Emission -> Output','geometry_keys_uv_all_exact_from_shape_b':True,'limits':['Stylized scene-light-driven pigment shader; not a PBR reflectance claim.','No unused normal/roughness map added just to claim completeness.','Source4/checker/color-only/light-direction/blink review pending.'],'recipe':{'path':str(Path(__file__)),'sha256':sha(__file__)}}
(OUT/'manifest.json').write_text(json.dumps(report,indent=2));print('LOOK_D_DONE')
