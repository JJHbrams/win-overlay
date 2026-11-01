import bpy,json
from pathlib import Path
P=Path(__file__).parent
bpy.ops.wm.open_mainfile(filepath=str(P/'Mia_HairStructure_v24.blend'),use_scripts=False)
source='C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/references/mia-clean-master-v22.png'
im=bpy.data.images.load(source,check_existing=True);im.name='MIA_V24_OriginalMaster_BunProjection';im.pack()
mat=bpy.data.materials['MIA_V20_AuthoredFold_AshStrata_V22_LightToon'].copy();mat.name='MIA_V24_SourceBunProjection_Probe'
n=mat.node_tree.nodes;l=mat.node_tree.links
uv=n.new('ShaderNodeUVMap');uv.uv_map='V24_SourceBackUV'
tex=n.new('ShaderNodeTexImage');tex.image=im;tex.interpolation='Linear';l.new(uv.outputs['UV'],tex.inputs['Vector'])
uvside=n.new('ShaderNodeUVMap');uvside.uv_map='V24_SourceSideUV'
texside=n.new('ShaderNodeTexImage');texside.image=im;texside.interpolation='Linear';l.new(uvside.outputs['UV'],texside.inputs['Vector'])
geo=n.new('ShaderNodeNewGeometry');sep=n.new('ShaderNodeSeparateXYZ');l.new(geo.outputs['Normal'],sep.inputs[0]);ab=n.new('ShaderNodeMath');ab.operation='ABSOLUTE';l.new(sep.outputs['X'],ab.inputs[0]);power=n.new('ShaderNodeMath');power.operation='POWER';power.inputs[1].default_value=2;l.new(ab.outputs[0],power.inputs[0]);mix=n.new('ShaderNodeMixRGB');l.new(power.outputs[0],mix.inputs[0]);l.new(tex.outputs[0],mix.inputs[1]);l.new(texside.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],n['V22_GRAZING_EDGE_INK'].inputs[1])
for o in bpy.data.objects:
 if o.name.startswith('MIA_V24_Gather_'):
  u=o.data.uv_layers.new(name='V24_SourceBackUV');s=o.data.uv_layers.new(name='V24_SourceSideUV')
  for f in o.data.polygons:
   for li,vi in zip(f.loop_indices,f.vertices):
    x,y,z=o.data.vertices[vi].co
    u.data[li].uv=((838-x/.002)/1536,1-(88-(z-1.574)/.002)/1024)
    s.data[li].uv=((633+(y-.130)/.00155)/1536,1-(82-(z-1.574)/.00155)/1024)
  o.data.materials[0]=mat
scene=bpy.context.scene
for name in ['back','profile','rear_oblique']:
 scene.camera=bpy.data.objects['V24 '+name];scene.render.filepath=str(P/('sourcepaint_'+name+'.png'));bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'Mia_HairStructure_v24_SourcePaintProbe.blend'))
