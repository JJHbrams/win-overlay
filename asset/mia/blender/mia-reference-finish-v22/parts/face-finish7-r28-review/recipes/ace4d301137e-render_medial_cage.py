"""Actual control-cage faces/edges; read-only same-view before/after evidence."""
import ast,sys,json
from pathlib import Path
src=Path(__file__).resolve().parent.parent/'render_source_motion.py';tree=ast.parse(src.read_text());nodes=[]
for n in tree.body:
 if isinstance(n,ast.For):break
 nodes.append(n)
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(src),'exec'))
s=load(False,True);skin=bpy.data.objects['MIA_V14_SculptedSkin']
for key in skin.data.shape_keys.key_blocks:key.value=0.
sub=next(m for m in skin.modifiers if m.type=='SUBSURF');sub.show_viewport=False;bpy.context.view_layer.update();mesh=bpy.data.meshes.new_from_object(skin.evaluated_get(bpy.context.evaluated_depsgraph_get()));sub.show_viewport=True;skin.hide_render=True
cage=bpy.data.objects.new('ACTUAL_UNSUBDIVIDED_MEDIAL_CAGE',mesh);s.collection.objects.link(cage);cage.matrix_world=skin.matrix_world.copy();cage.data.materials.clear();cage.data.materials.append(constant('CAGE_GREY',(.18,.18,.18),True))
for p in cage.data.polygons:p.material_index=0;p.use_smooth=False
wire=bpy.data.objects.new('ACTUAL_CAGE_EDGES',mesh.copy());s.collection.objects.link(wire);wire.matrix_world=cage.matrix_world.copy();wire.data.materials.clear();wire.data.materials.append(constant('CAGE_EDGE_INK',(.008,.012,.02)));wf=wire.modifiers.new('Real cage edges','WIREFRAME');wf.thickness=.00010;wf.offset=1.;wf.use_replace=True
edited={307,310,309,319,322,323,324,253,252,258,295,294,254,292,296,301,137,138,136,515,516,154,153,60,59,147,146,144,148,31,141,139}
curve=bpy.data.curves.new('EDITED_MEDIAL_NEIGHBOR_EDGES','CURVE');curve.dimensions='3D';curve.bevel_depth=.000075;curve.bevel_resolution=0
for edge in mesh.edges:
 i,j=edge.vertices
 if i not in edited and j not in edited:continue
 spline=curve.splines.new('POLY');spline.points.add(1)
 for point,index in zip(spline.points,[i,j]):q=mesh.vertices[index].co;point.co=(*q,1.)
highlight=bpy.data.objects.new('MEDIAL_EDIT_REGION_EDGES',curve);s.collection.objects.link(highlight);highlight.matrix_world=cage.matrix_world.copy();curve.materials.append(constant('EDIT_REGION_ORANGE',(.7,.18,.025)))
view={'id':'actual_medial_cage','yaw':30,'elevation':-10,'roll':0};r.camera(s,view);s.camera.location.z-=.025;s.camera.data.ortho_scale=.16;bpy.context.view_layer.update();s.render.filepath=str(OUT/'actual_medial_cage_yaw+30_elev-10.png');bpy.ops.render.render(write_still=True);camera=r.record(s,view,'Actual unsubdivided cage; flat grey faces, black actual edges, orange edit-neighborhood edges');camera['ortho_scale']=float(s.camera.data.ortho_scale);camera['target_z']=1.525
assert r.sha(SOURCE)==source_sha
(OUT/'render-records.json').write_text(json.dumps({'source':r.artifact(SOURCE),'recipe':r.artifact(__file__),'records':[{'label':'actual_medial_cage_yaw+30_elev-10','render':r.artifact(s.render.filepath),'camera':camera}],'limits':'Actual cage diagnostic only. Subdivision disabled on temporary copy; not an art or final smooth-surface view. Native never saved.'},indent=2));print('ACTUAL_MEDIAL_CAGE_DONE')
