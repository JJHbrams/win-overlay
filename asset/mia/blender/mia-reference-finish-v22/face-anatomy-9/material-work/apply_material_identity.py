"""Material-only Mia fatigue/line interpretation; existing UV pigment maps retained.

No raster painting, mesh, UV, key or light edits. Shader-space shifted line is an
explicit secondary fold trial, not new painted source fidelity or a rig pass.
"""
import argparse,sys,json,hashlib
from pathlib import Path
import bpy
import numpy as np

ROOT=Path(__file__).resolve().parent
V22=ROOT.parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def snapshots():
 out={}
 for o in bpy.data.objects:
  if o.type!='MESH':continue
  m=o.data;h=hashlib.sha256()
  for v in m.vertices:h.update(np.asarray(v.co,dtype=np.float32).tobytes())
  for p in m.polygons:h.update(np.asarray(p.vertices,dtype=np.int32).tobytes());h.update(str(p.material_index).encode())
  for uv in m.uv_layers:
   h.update(uv.name.encode())
   for p in uv.data:h.update(np.asarray(p.uv,dtype=np.float32).tobytes())
  if m.shape_keys:
   for k in m.shape_keys.key_blocks:
    h.update(k.name.encode());h.update(str(k.value).encode())
    for p in k.data:h.update(np.asarray(p.co,dtype=np.float32).tobytes())
  h.update(np.asarray(o.matrix_world,dtype=np.float32).tobytes())
  out[o.name]=h.hexdigest()
 return out

def apply_identity(skin,variant='m1'):
 assert variant in ('m1','m2','m3','m4')
 old=skin.data.materials[7];mat=old.copy();mat.name='MIA_FaceAnatomy9_Identity_'+variant
 skin.data.materials[7]=mat;n=mat.node_tree.nodes;l=mat.node_tree.links
 required=['FINISH8_ACTUAL_UV','FINISH8_BasePigment','FINISH8_FatigueMask','FINISH8_FineLineMask','FINISH8_PigmentFatigue','FINISH8_FineLinePigment','PigmentTimesControlledLight']
 assert all(n.get(k) for k in required), 'Requires authored Finish8 map route'
 def math(name,op,a,b):
  q=n.new('ShaderNodeMath');q.name='IDENTITY9_'+name;q.operation=op
  for i,v in enumerate([a,b]):
   if isinstance(v,(float,int)):q.inputs[i].default_value=v
   else:l.new(v,q.inputs[i])
  return q.outputs[0]
 fat=math('FatigueExponent','POWER',n['FINISH8_FatigueMask'].outputs['Color'],.82)
 fat=math('FatigueStrength','MULTIPLY',fat,1.14)
 l.new(fat,n['FINISH8_PigmentFatigue'].inputs[0]);n['FINISH8_PigmentFatigue'].inputs[2].default_value=((.38,.32,.34,1) if variant in ('m2','m3','m4') else (.42,.28,.32,1))
 fine=math('LidLineExponent','POWER',n['FINISH8_FineLineMask'].outputs['Color'],.72)
 fine=math('LidLineStrength','MULTIPLY',fine,.90)
 l.new(fine,n['FINISH8_FineLinePigment'].inputs[0]);n['FINISH8_FineLinePigment'].inputs[2].default_value=(.12,.075,.09,1)
 # A second soft, lateral fold from the existing mask in UV space. It remains
 # deliberately fainter than the anatomical lid rim and excludes nostrils.
 uv=n['FINISH8_ACTUAL_UV'].outputs['UV'];sep=n.new('ShaderNodeSeparateXYZ');sep.name='IDENTITY9_UVComponents';l.new(uv,sep.inputs[0])
 offset=n.new('ShaderNodeVectorMath');offset.name='IDENTITY9_FoldOffset';offset.operation='ADD';l.new(uv,offset.inputs[0]);offset.inputs[1].default_value=(0,.025 if variant=='m2' else .012,0)
 tex=n.new('ShaderNodeTexImage');tex.name='IDENTITY9_SecondaryFoldExistingMask';tex.image=n['FINISH8_FineLineMask'].image;tex.interpolation='Linear';l.new(offset.outputs[0],tex.inputs['Vector'])
 vu=math('FoldVLow','GREATER_THAN',sep.outputs['Y'],.36);vh=math('FoldVHigh','LESS_THAN',sep.outputs['Y'],.47);vscope=math('FoldVScope','MULTIPLY',vu,vh)
 u=math('FoldUOffset','SUBTRACT',sep.outputs['X'],.5);u=math('FoldUAbs','ABSOLUTE',u,0)
 ramp=n.new('ShaderNodeMapRange');ramp.name='IDENTITY9_LateralFoldFade';ramp.interpolation_type='SMOOTHERSTEP';ramp.clamp=True
 l.new(u,ramp.inputs['Value']);ramp.inputs['From Min'].default_value=.115;ramp.inputs['From Max'].default_value=.170
 fold=math('FoldWeight','MULTIPLY',ramp.outputs['Result'],vscope)
 fold=math('FoldLinePower','MULTIPLY',fold,math('FoldMaskExponent','POWER',tex.outputs['Color'],1.10 if variant=='m2' else .78))
 fold=math('FoldStrength','MULTIPLY',fold,.65 if variant=='m2' else .46)
 if variant in ('m3','m4'):
  # Smooth UV curve follows measured existing lower-lid UV samples. This is
  # shader authoring, not a modified bitmap or projected concept photograph.
  # It avoids copying the old mask's visible per-triangle vertical streaks.
  curve=n.new('ShaderNodeFloatCurve');curve.name='IDENTITY9_MeasuredLowerLidUVCurve';curve.mapping.initialize()
  cv=curve.mapping.curves[0]
  for p in list(cv.points)[1:-1]:cv.points.remove(p)
  samples=[(.285,.43701),(.295,.42041),(.305,.41064),(.315,.40527),(.325,.40186),(.335,.39941),(.345,.39893),(.355,.40039),(.365,.40234),(.375,.40527),(.385,.40869),(.395,.41309),(.405,.42139)]
  # Mirror UV x about .5 to use the measured left UV island on both sides.
  mirrored=math('FoldMirrorU','SUBTRACT',.5,u);l.new(mirrored,curve.inputs['Value'])
  cv.points[0].location=(0,.45);cv.points[-1].location=(1,.45)
  for xx,yy in samples:
   p=cv.points.new(xx,yy);p.handle_type='AUTO'
  curve.mapping.update()
  center=math('SmoothFoldOffset','SUBTRACT',curve.outputs[0],.019 if variant=='m4' else .022)
  distance=math('SmoothFoldDistance','SUBTRACT',sep.outputs['Y'],center)
  normalized=math('SmoothFoldWidth','DIVIDE',distance,.00135 if variant=='m4' else .0020)
  sq=math('SmoothFoldSquare','MULTIPLY',normalized,normalized)
  neg=math('SmoothFoldNegative','MULTIPLY',sq,-1.)
  gaussian=math('SmoothFoldGaussian','POWER',2.718281828,neg)
  left_fade=n.new('ShaderNodeMapRange');left_fade.name='IDENTITY9_FoldOuterFade';left_fade.clamp=True;left_fade.interpolation_type='SMOOTHERSTEP'
  l.new(mirrored,left_fade.inputs['Value']);left_fade.inputs['From Min'].default_value=.292;left_fade.inputs['From Max'].default_value=.308 if variant=='m4' else .312
  right_fade=n.new('ShaderNodeMapRange');right_fade.name='IDENTITY9_FoldInnerFade';right_fade.clamp=True;right_fade.interpolation_type='SMOOTHERSTEP'
  l.new(mirrored,right_fade.inputs['Value']);right_fade.inputs['From Min'].default_value=.320 if variant=='m4' else .365;right_fade.inputs['From Max'].default_value=.355 if variant=='m4' else .402;right_fade.inputs['To Min'].default_value=1;right_fade.inputs['To Max'].default_value=0
  scope=math('SmoothFoldEndpoints','MULTIPLY',left_fade.outputs[0],right_fade.outputs[0]);scope=math('SmoothFoldEyeOnly','MULTIPLY',scope,vscope)
  fold=math('SmoothFoldValue','MULTIPLY',scope,gaussian);fold=math('SmoothFoldStrength','MULTIPLY',fold,.34 if variant=='m4' else .68)
 mix=n.new('ShaderNodeMixRGB');mix.name='IDENTITY9_SecondaryFoldPigment';mix.blend_type='MULTIPLY';l.new(fold,mix.inputs[0]);l.new(n['FINISH8_FineLinePigment'].outputs['Color'],mix.inputs[1]);mix.inputs[2].default_value=(.22,.12,.16,1)
 l.new(mix.outputs[0],n['PigmentTimesControlledLight'].inputs[1])
 mat['mia_identity9_limits']='Existing UV maps: stronger brown/mauve tired mass, lid rim; clean procedural UV lower fold for M3, shifted-map fold for M1/M2. No new UV paint, no shape change, no new actual map resolution.'
 return mat

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--source',default=str(V22/'integration-wip-8-review/Mia_ReferenceFinish_v22.blend'));ap.add_argument('--output-dir',default=str(ROOT/'trial-m1'));ap.add_argument('--variant',default='m1')
 a=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
 source=Path(a.source);out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=True);native=out/'Mia_FaceIdentity9_Material.blend';assert not native.exists()
 source_sha=sha(source);bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);before=snapshots();skin=bpy.data.objects['MIA_V14_SculptedSkin'];oldmat=skin.data.materials[7].name
 mat=apply_identity(skin,a.variant);after=snapshots();assert before==after,'Unexpected mesh/key/UV/transform change'
 maps={node.name:{'image':node.image.name,'colorspace':node.image.colorspace_settings.name,'size':list(node.image.size),'packed_sha256':hashlib.sha256(node.image.packed_file.data).hexdigest() if node.image.packed_file else None} for node in mat.node_tree.nodes if node.type=='TEX_IMAGE' and node.image and (node.name.startswith('FINISH8') or node.name.startswith('IDENTITY9'))}
 bpy.ops.wm.save_as_mainfile(filepath=str(native));bpy.ops.wm.open_mainfile(filepath=str(native),use_scripts=False);assert snapshots()==after
 report={'source':{'path':str(source),'sha256':source_sha},'candidate':{'path':str(native),'sha256':sha(native)},'material_before':oldmat,'material_after':'MIA_FaceAnatomy9_Identity_'+a.variant,'maps':maps,'meshes_uv_keys_transforms_exact':True,'source_unchanged':sha(source)==source_sha,'recipe':{'path':str(Path(__file__)),'sha256':sha(__file__)},'limits':['No new UV texture painting or normal/specular maps.','M3 uses a measured UV lower-lid curve for the separate procedural fold. M1/M2 duplicate the existing line mask. Expression and new eye geometry alignment must be reviewed.','Material trial is not ART PASS.']}
 (out/'manifest.json').write_text(json.dumps(report,indent=2));print('MATERIAL_IDENTITY_DONE',str(native))
