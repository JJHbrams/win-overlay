"""Two authorized causal diagnostics; B recipes/geometry/actuals untouched."""
from pathlib import Path
import types,json,hashlib,sys
DIAG=Path(__file__).resolve().parent;B=DIAG.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
before={str(f):sha(f) for f in B.rglob('*') if f.is_file() and 'diagnostic' not in f.parts and '__pycache__' not in f.parts}
DIAG_INSTALL=types.ModuleType('sculpt07_B_diagnostic_install');DIAG_INSTALL.__file__=str(B/'install_design.py');DIAG_INSTALL.DIAG=DIAG
code=(B/'install_design.py').read_text(encoding='utf-8').replace("(P/'preservation.json')","(DIAG/'preservation.json')")
exec(compile(code,str(B/'install_design.py'),'exec'),DIAG_INSTALL.__dict__)
recipe=(B/'render_four.py').read_text(encoding='utf-8').split('for fixture in old:')[0]
recipe=recipe.replace('import install_design','install_design=DIAG_INSTALL').replace("(P/'preservation.json')","(DIAG/'preservation.json')")
globals()['__file__']=str(B/'render_four.py');exec(compile(recipe,str(B/'render_four.py'),'exec'),globals())
from mathutils import Vector
target=Vector((0,-.035,1.275));cam.location=target+Vector((0,-2,0));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.40;s.render.resolution_x=s.render.resolution_y=640;bpy.context.view_layer.update()
assert [list(r) for r in cam.matrix_world]==old[0]['camera']['matrix']
# Audit actual evaluated material indices BEFORE hiding the context.
from mathutils.bvhtree import BVHTree
import numpy as np
actors=[];trees=[]
for actor in s.objects:
    if actor.type!='MESH' or actor.hide_render:continue
    ev=actor.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
    if not len(me.vertices):ev.to_mesh_clear();continue
    verts=np.asarray([list(ev.matrix_world@p.co) for p in me.vertices]);lo,hi=verts.min(0),verts.max(0)
    if lo[2]>1.29 or hi[2]<1.13 or lo[0]>.16 or hi[0]<-.16 or lo[1]>.15 or hi[1]<-.25:ev.to_mesh_clear();continue
    materials=list(me.materials);transparent_slots=[]
    for i,mat in enumerate(materials):
        if mat and mat.use_nodes:
            out=mat.node_tree.get_output_node('EEVEE');links=list(out.inputs['Surface'].links) if out else []
            if len(links)==1 and links[0].from_node.bl_idname=='ShaderNodeBsdfTransparent':transparent_slots.append(i)
    counts={};opaque=[];indices=[]
    for triangle in me.loop_triangles:
        mi=me.polygons[triangle.polygon_index].material_index;counts[str(mi)]=counts.get(str(mi),0)+1
        if mi not in transparent_slots:opaque.append(tuple(triangle.vertices));indices.append((triangle.polygon_index,mi))
    actors.append(dict(name=actor.name,evaluated_vertices=len(verts),actual_evaluated_triangle_material_counts=counts,actual_evaluated_materials=[dict(slot=i,name=m.name if m else None,sha256=fp.material_signature(m)['sha256'] if m else None) for i,m in enumerate(materials)],transparent_output_slots=transparent_slots,opaque_triangles=len(opaque)))
    if opaque:trees.append((actor.name,BVHTree.FromPolygons(verts.tolist(),opaque,all_triangles=True),indices))
    ev.to_mesh_clear()
samples=[];owners={}
for z in np.linspace(1.14,1.27,53):
    for x in np.linspace(-.14,.14,57):
        origin=cam.matrix_world.translation+cam.matrix_world.col[0].xyz*float(x)+cam.matrix_world.col[1].xyz*float(z-1.275);direction=-cam.matrix_world.col[2].xyz
        hits=[]
        for name,tree,indices in trees:
            location,normal,index,distance=tree.ray_cast(origin,direction,4.)
            if location is not None:hits.append((distance,name,location,normal,indices[index]))
        if hits:
            distance,name,location,normal,ids=min(hits,key=lambda q:q[0]);owners[name]=owners.get(name,0)+1;samples.append(dict(x=float(x),z=float(z),owner=name,point=list(location),normal=list(normal),polygon=ids[0],actual_material_slot=ids[1]))
        else:owners['MISS']=owners.get('MISS',0)+1
sample_file=DIAG/'actual-first-hit-samples.npz';np.savez_compressed(sample_file,xz=np.array([[r['x'],r['z']] for r in samples]),points=np.array([r['point'] for r in samples]),normals=np.array([r['normal'] for r in samples]),owner=np.array([r['owner'] for r in samples]),polygon=np.array([r['polygon'] for r in samples]),material=np.array([r['actual_material_slot'] for r in samples]))
(DIAG/'actual-context-first-hit-audit.json').write_text(json.dumps(dict(B_mesh_sha256=targetsha,actors=actors,first_hit_owners=owners,sample_count=len(samples),samples_npz=dict(path=sample_file.name,sha256=sha(sample_file)),transparent_triangles_skipped_by_actual_output_ancestry=True,limits='Opaque first-hit sample grid underbust x±.14,Z1.14..1.27 at exact front camera. Full-transparent BSDF slots skipped; no general alpha/transmission solver claimed.'),indent=2)+'\n',encoding='utf-8')
# Render exactly two design-only shots, all other mesh actors hidden.
for actor in s.objects:
    if actor.type=='MESH':actor.hide_render=actor!=design
normalmat=bpy.data.materials.new('Sculpt07_B_ActualGeometryNormalEmission');normalmat.use_nodes=True;nn=normalmat.node_tree.nodes;nn.clear();geo=nn.new('ShaderNodeNewGeometry');vm=nn.new('ShaderNodeVectorMath');vm.operation='MULTIPLY_ADD';vm.inputs[1].default_value=(.5,.5,.5);vm.inputs[2].default_value=(.5,.5,.5);em=nn.new('ShaderNodeEmission');oo=nn.new('ShaderNodeOutputMaterial');normalmat.node_tree.links.new(geo.outputs['Normal'],vm.inputs[0]);normalmat.node_tree.links.new(vm.outputs['Vector'],em.inputs['Color']);normalmat.node_tree.links.new(em.outputs[0],oo.inputs['Surface'])
records=[]
for mode,mat in [('gray',gray),('normal',normalmat)]:
    design.data.materials[0]=mat;bpy.context.view_layer.update();path=DIAG/('design-only-'+mode+'-front.png');assert not path.exists()
    row=dict(mode=mode,path=str(path),B_mesh_sha256=targetsha,camera=old[0]['camera'],actual_mesh_actor_flags=[dict(name=o.name,hide_render=o.hide_render) for o in s.objects if o.type=='MESH'],actual_visible_mesh_actors=[o.name for o in s.objects if o.type=='MESH' and not o.hide_render],material_signature=fp.material_signature(mat),actual_lights=[dict(name=o.name,hide_render=o.hide_render,energy=o.data.energy,matrix=[list(r) for r in o.matrix_world],size=o.data.size,use_shadow=o.data.use_shadow) for o in s.objects if o.type=='LIGHT'],color_management=old[0]['color_management'],native_saved=False,geometry_changed=False)
    assert row['actual_visible_mesh_actors']==[design.name];row['state_sha256']=fp.json_digest(row);(DIAG/('design-only-'+mode+'-pre-render.json')).write_text(json.dumps(row,indent=2)+'\n',encoding='utf-8');s.render.filepath=str(path);bpy.ops.render.render(write_still=True);assert row['material_signature']==fp.material_signature(mat);row['sha256']=sha(path);records.append(row);(DIAG/'render-records.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
assert len(records)==2 and sha(N)==NATIVE_SHA and before=={str(f):sha(f) for f in B.rglob('*') if f.is_file() and 'diagnostic' not in f.parts and '__pycache__' not in f.parts}
print('SCULPT07_B_TWO_CAUSAL_DIAGNOSTICS_DONE B files/native unchanged',flush=True)
