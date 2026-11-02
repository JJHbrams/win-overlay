"""CPU preparation / four authorized-when-granted lateral visibility renders."""
from pathlib import Path
import types,json,hashlib,sys,math
DIAG=Path(__file__).resolve().parent;D=DIAG.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
before={str(f):sha(f) for f in D.rglob('*') if f.is_file() and 'axilla-review' not in f.parts and '__pycache__' not in f.parts}
DIAG_INSTALL=types.ModuleType('sculpt07_D_axilla_install');DIAG_INSTALL.__file__=str(D/'install_design.py');DIAG_INSTALL.DIAG=DIAG
code=(D/'install_design.py').read_text(encoding='utf-8').replace("(P/'preservation.json')","(DIAG/'preservation.json')");exec(compile(code,str(D/'install_design.py'),'exec'),DIAG_INSTALL.__dict__)
recipe=(D/'render_core_six.py').read_text(encoding='utf-8').split('for fixture in old:')[0].replace('import install_design','install_design=DIAG_INSTALL').replace("(P/'preservation.json')","(DIAG/'preservation.json')")
globals()['__file__']=str(D/'render_core_six.py');exec(compile(recipe,str(D/'render_core_six.py'),'exec'),globals())
from mathutils import Vector
DO_RENDER='--render' in sys.argv
for actor in s.objects:
    if actor.type=='MESH':actor.hide_render=actor!=design
target=Vector((.150,-.005,1.315));yaw,pitch=90.,-5.;angle,elev=math.radians(yaw),math.radians(pitch);dist=1.2;cam.location=target+Vector((dist*math.sin(angle)*math.cos(elev),-dist*math.cos(angle)*math.cos(elev),dist*math.sin(elev)));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.220;s.render.resolution_x=s.render.resolution_y=640;bpy.context.view_layer.update()
normalmat=bpy.data.materials.new('Sculpt07_D_ActualGeometryNormalEmission');normalmat.use_nodes=True;nn=normalmat.node_tree.nodes;nn.clear();geo=nn.new('ShaderNodeNewGeometry');vm=nn.new('ShaderNodeVectorMath');vm.operation='MULTIPLY_ADD';vm.inputs[1].default_value=(.5,.5,.5);vm.inputs[2].default_value=(.5,.5,.5);em=nn.new('ShaderNodeEmission');oo=nn.new('ShaderNodeOutputMaterial');normalmat.node_tree.links.new(geo.outputs['Normal'],vm.inputs[0]);normalmat.node_tree.links.new(vm.outputs['Vector'],em.inputs['Color']);normalmat.node_tree.links.new(em.outputs[0],oo.inputs['Surface'])
vertices=install_design.coords(design.data.vertices);tri=np.array([p.vertices[:] for p in design.data.polygons],np.int32);centers=vertices[tri].mean(1);mask=(centers[:,0]>.174)&(centers[:,2]>1.245)&(centers[:,2]<1.395)&(abs(centers[:,1])<.09);assert mask.any();mask_ids=np.flatnonzero(mask).astype(np.int32);np.savez_compressed(DIAG/'diagnostic-outer-arm-material-mask.npz',polygon_indices=mask_ids)
design.data.materials.append(transparent);vertexhash=fp.digest(design.data.vertices,'co',3);topologyhash=hashlib.sha256(tri.tobytes()).hexdigest();records=[]
for phase in ['intact','cutaway']:
    for poly in design.data.polygons:poly.material_index=int(phase=='cutaway' and mask[poly.index])
    for mode,mat in [('gray',gray),('normal',normalmat)]:
        design.data.materials[0]=mat;bpy.context.view_layer.update();path=DIAG/('axilla-'+phase+'-'+mode+'.png')
        row=dict(phase=phase,mode=mode,path=str(path),geometry_changed=False,vertex_array_sha256=vertexhash,topology_sha256=topologyhash,D_mesh_sha256=targetsha,camera=dict(projection=cam.data.type,matrix=[list(r) for r in cam.matrix_world],ortho_scale=cam.data.ortho_scale,clip_start=cam.data.clip_start,clip_end=cam.data.clip_end,resolution=[640,640],pixel_aspect=[1,1],frame=s.frame_current,yaw=yaw,pitch=pitch,target=list(target)),single_actual_actor=design.name,actual_visible_mesh_actors=[o.name for o in s.objects if o.type=='MESH' and not o.hide_render],material_signature=fp.material_signature(mat),transparent_signature=fp.material_signature(transparent),actual_polygon_material_counts=dict(opaque=sum(p.material_index==0 for p in design.data.polygons),transparent=sum(p.material_index==1 for p in design.data.polygons)),cutaway_definition='DIAGNOSTIC material-only OUTER right arm polygon-centroid window X>.174,Z1.245..1.395,|Y|<.09. All vertices/faces retained. No geometry hole or final anatomical cut.',mask_file_sha256=sha(DIAG/'diagnostic-outer-arm-material-mask.npz'),actual_lights=[dict(name=o.name,hidden=o.hide_render,energy=o.data.energy,matrix=[list(r) for r in o.matrix_world],size=o.data.size,use_shadow=o.data.use_shadow) for o in s.objects if o.type=='LIGHT'],world=dict(color=list(bg.inputs['Color'].default_value),strength=bg.inputs['Strength'].default_value),color_management=old[0]['color_management'],status='INTACT/DIAGNOSTIC CUTAWAY inspection only; no source/anatomy/air-corridor PASS',native_saved=False,head_scale_changed=False)
        assert row['actual_visible_mesh_actors']==[design.name] and fp.digest(design.data.vertices,'co',3)==vertexhash;row['actual_renderer_state_sha256']=fp.json_digest(row)
        if DO_RENDER:
            assert not path.exists();(DIAG/('axilla-'+phase+'-'+mode+'-pre-render.json')).write_text(json.dumps(row,indent=2)+'\n',encoding='utf-8');s.render.filepath=str(path);bpy.ops.render.render(write_still=True);row['sha256']=sha(path);assert row['material_signature']==fp.material_signature(mat)
        records.append(row)
        if DO_RENDER:(DIAG/'render-records.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
assert len(records)==4 and fp.digest(design.data.vertices,'co',3)==vertexhash and topologyhash==hashlib.sha256(np.array([p.vertices[:] for p in design.data.polygons],np.int32).tobytes()).hexdigest()
assert before=={str(f):sha(f) for f in D.rglob('*') if f.is_file() and 'axilla-review' not in f.parts and '__pycache__' not in f.parts} and sha(N)==NATIVE_SHA
if not DO_RENDER:(DIAG/'cpu-preparation.json').write_text(json.dumps(dict(planned_actuals=4,masked_polygons=len(mask_ids),camera=records[0]['camera'],single_actor=True,geometry_changed=False,prior_D_files_unchanged=True,plans=[dict(phase=r['phase'],mode=r['mode'],state_sha256=r['actual_renderer_state_sha256']) for r in records]),indent=2)+'\n',encoding='utf-8')
print('D_AXILLA_ACTUAL4_DONE' if DO_RENDER else 'D_AXILLA_CPU4_PREPARED',flush=True)
