import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
P=Path(__file__).parent/'sculpt2'
bpy.ops.wm.open_mainfile(filepath=str(P/'Mia_HairStructure_v24.blend'),use_scripts=False)
s=bpy.context.scene
for o in s.objects:
 if o.type=='MESH':o.hide_render=not o.name.startswith('MIA_V24_Gather_')
 if o.type=='LIGHT' and o.name.startswith('V24 '):o.data.energy*=.24
m=bpy.data.materials.new('V24 paintplate clay');m.use_nodes=True
bsdf=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bsdf.inputs['Base Color'].default_value=(.32,.29,.28,1);bsdf.inputs['Roughness'].default_value=.9
for o in s.objects:
 if o.name.startswith('MIA_V24_Gather_'):o.data.materials[0]=m
s.render.resolution_x=s.render.resolution_y=1024;s.render.film_transparent=True
rows={}
for name,pos in [('back',(0,2,1.575)),('profile',(2,.135,1.575))]:
 d=bpy.data.cameras.new('V24 Paint '+name);d.type='ORTHO';d.ortho_scale=.115
 c=bpy.data.objects.new(d.name,d);s.collection.objects.link(c);c.location=pos;c.rotation_euler=(Vector((0,.135,1.575))-c.location).to_track_quat('-Z','Y').to_euler();s.camera=c
 bpy.context.view_layer.update()
 s.render.filepath=str(P/('paintplate_'+name+'.png'));bpy.ops.render.render(write_still=True)
 rows[name]={'image':str(P/('paintplate_'+name+'.png')),'projection':'ORTHO','ortho_scale':d.ortho_scale,'resolution':[1024,1024],'matrix_world':[list(r) for r in c.matrix_world],'formula':'camera_local = inverse(matrix_world) @ world_vertex; u = .5 + local.x/ortho_scale; v=.5+local.y/ortho_scale; texture origin lower-left','target': [0,.135,1.575]}
(P/'paint-projection.json').write_text(json.dumps({'source_native_sha256':hashlib.sha256((P/'Mia_HairStructure_v24.blend').read_bytes()).hexdigest(),'owners':[o.name for o in s.objects if o.name.startswith('MIA_V24_Gather_')],'views':rows,'instruction':'Keep every geometric silhouette/occlusion/crease position fixed. Paint pigment/hand-drawn source strands only, no new shape. No generated plate is model evidence.'},indent=2))
