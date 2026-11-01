import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).parent/'paint1'
bpy.ops.wm.open_mainfile(filepath=str(P/'Mia_HairStructurePaint_v24.blend'),use_scripts=False)
s=bpy.context.scene
new=[o for o in bpy.data.objects if o.name.startswith('MIA_V24_Gather_')]
old=[bpy.data.objects[n] for n in ['MIA_V20_HalfUp_Fold_Left','MIA_V20_HalfUp_Fold_Right','MIA_V20_HalfUp_Binder']]
views=['front','profile','back','left_oblique','right_oblique'];records={}
for baseline in [True,False]:
 for o in new:o.hide_render=baseline
 for o in old:o.hide_render=not baseline
 for name in views:
  c=bpy.data.objects['V24 '+name];s.camera=c;s.render.filepath=str(P/(('baseline' if baseline else 'candidate')+'_'+name+'.png'));bpy.ops.render.render(write_still=True)
  records[name]={'projection':'ORTHO','ortho_scale':c.data.ortho_scale,'matrix':[list(r) for r in c.matrix_world],'frame':s.frame_current,'active_shape_keys':{o.name:{k.name:k.value for k in o.data.shape_keys.key_blocks if k.value} for o in bpy.data.objects if o.type=='MESH' and o.data.shape_keys and not o.hide_render},'lighting':[{'name':o.name,'position':list(o.location),'energy':o.data.energy,'size':o.data.size} for o in s.objects if o.type=='LIGHT' and not o.hide_render],'color_management':{'view_transform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma},'resolution':[s.render.resolution_x,s.render.resolution_y],'pixel_aspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'lens_shift':[c.data.shift_x,c.data.shift_y]}
(P/'review-cameras.json').write_text(json.dumps(records,indent=2))
# Diagnostic close plates use the exact frozen paint camera, actual saved maps.
for o in s.objects:
 if o.type=='MESH':o.hide_render=o not in new
projection=json.loads((P.parent/'sculpt2/paint-projection.json').read_text())['views'];cameras={}
for name,row in projection.items():
 d=bpy.data.cameras.new('PaintReview '+name);d.type='ORTHO';d.ortho_scale=row['ortho_scale'];c=bpy.data.objects.new(d.name,d);s.collection.objects.link(c);c.matrix_world=Matrix(row['matrix_world']);cameras[name]=c
s.render.resolution_x=s.render.resolution_y=1024
originalmats={o.name:o.data.materials[0] for o in new}
def close(mode):
 for name,c in cameras.items():
  s.camera=c;s.render.filepath=str(P/(mode+'_'+name+'.png'));bpy.ops.render.render(write_still=True)
close('targetclose')
for o in new:
 m=originalmats[o.name].copy();o.data.materials[0]=m;n=m.node_tree.nodes;l=m.node_tree.links;emit=next(n for n in n if n.type=='EMISSION');l.new(n['V24_VisiblePaint_UnseenAshFallback'].outputs[0],emit.inputs['Color'])
close('coloronly')
for o in new:
 m=bpy.data.materials.new(o.name+'_Checker');m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;n.clear();uv=n.new('ShaderNodeUVMap');uv.uv_map='V24_GatherPaintUV';check=n.new('ShaderNodeTexChecker');check.inputs['Scale'].default_value=16;check.inputs['Color1'].default_value=(.04,.13,.25,1);check.inputs['Color2'].default_value=(.75,.75,.75,1);l.new(uv.outputs[0],check.inputs[0]);e=n.new('ShaderNodeEmission');l.new(check.outputs[0],e.inputs[0]);out=n.new('ShaderNodeOutputMaterial');l.new(e.outputs[0],out.inputs['Surface']);o.data.materials[0]=m
close('checker')
for o in new:o.data.materials[0]=originalmats[o.name]
key=bpy.data.objects['V24 Key'];key.location=(-.6,-.8,2);key.rotation_euler=(Vector((0,.135,1.575))-key.location).to_track_quat('-Z','Y').to_euler();close('opposedlight')
print('PAINTED REVIEW COMPLETE')
