import bpy,numpy as np,math,json,hashlib
from pathlib import Path
from mathutils import Vector
O=Path(__file__).resolve().parent;S=O.parents[1]/'Mia_HairLookdev_v22.blend';bpy.ops.wm.open_mainfile(filepath=str(S));s=bpy.context.scene
names=['Front','Profile','Back','LeftOblique','RightOblique'];hair=bpy.data.objects['MIA_V17_PIXAL_DetailedHair'];mesh=hair.data;mesh.calc_loop_triangles();uv=mesh.uv_layers['MIA_V17_PAINT_UV']
np.savez_compressed(O/'projection-geometry.npz',coords=np.array([hair.matrix_world@v.co for v in mesh.vertices]),normals=np.array([hair.matrix_world.to_3x3()@v.normal for v in mesh.vertices]),triangles=np.array([t.vertices[:] for t in mesh.loop_triangles]),tri_uv=np.array([[uv.data[l].uv[:] for l in t.loops] for t in mesh.loop_triangles]))
cameras={}
for v in names:
 c=bpy.data.objects['MIA_REVIEW_Head_'+v];cameras[v]={'matrix':list(map(list,c.matrix_world)),'inverse':list(map(list,c.matrix_world.inverted())),'scale':c.data.ortho_scale}
(O/'projection-cameras.json').write_text(json.dumps(cameras,indent=2))
# Actual scene render depth and exact technical diffuse-light multiplier.
def material_depth(target):
 m=bpy.data.materials.new('PAINT_CAPTURE_'+str(target));m.use_nodes=True;n=m.node_tree.nodes;n.clear();l=m.node_tree.links;o=n.new('ShaderNodeOutputMaterial');em=n.new('ShaderNodeEmission');g=n.new('ShaderNodeNewGeometry');tr=n.new('ShaderNodeVectorTransform');tr.vector_type='POINT';tr.convert_from='WORLD';tr.convert_to='CAMERA';l.new(g.outputs['Position'],tr.inputs[0]);sep=n.new('ShaderNodeSeparateXYZ');l.new(tr.outputs[0],sep.inputs[0]);neg=n.new('ShaderNodeMath');neg.operation='MULTIPLY';neg.inputs[1].default_value=-1;l.new(sep.outputs['Z'],neg.inputs[0]);combine=n.new('ShaderNodeCombineXYZ');camdepth=n.new('ShaderNodeCameraData');l.new(camdepth.outputs['View Z Depth'],combine.inputs[0]);combine.inputs[1].default_value=float(target);l.new(combine.outputs[0],em.inputs[0]);l.new(em.outputs[0],o.inputs[0]);return m
original={o.name:list(o.data.materials) for o in s.objects if o.type=='MESH'}
targets={'MIA_V17_PIXAL_DetailedHair','MIA_V20_Crown_PixalDonorLock'};dm0=material_depth(0);dm1=material_depth(1)
for mode in ['depth','light']:
 for o in s.objects:
  if o.type!='MESH':continue
  for j,m in enumerate(original[o.name]):
   if mode=='depth':o.data.materials[j]=dm1 if o.name in targets else dm0
   else:o.data.materials[j]=m
 if mode=='light':
  seen=set()
  for o in s.objects:
   if o.type!='MESH' or o.name not in targets:continue
   for mat in o.data.materials:
    if mat.name in seen:continue
    seen.add(mat.name);n=mat.node_tree.nodes;l=mat.node_tree.links;em=next(nn for nn in n if nn.type=='EMISSION');light=n.get('V22_SOFT_TOON_LIGHT')
    if light:l.new(light.outputs[0],em.inputs['Color'])
 for view in names:
  s.camera=bpy.data.objects['MIA_REVIEW_Head_'+view];s.render.image_settings.file_format='OPEN_EXR';s.render.image_settings.color_depth='32';path=O/(mode+'_'+view+'.exr');s.render.filepath=str(path);bpy.ops.render.render(write_still=True);im=bpy.data.images.load(str(path),check_existing=False);a=np.array(im.pixels[:],np.float32).reshape(1000,1000,4);np.save(O/(mode+'_'+view+'.npy'),a);bpy.data.images.remove(im)
print('PROJECTION_CAPTURE_DONE')
