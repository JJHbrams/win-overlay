"""Root4 token only: D/E fixed observed-front coverage at front/F2 fixtures."""
from pathlib import Path
import sys,json,hashlib,types
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent;E=OUT.parent;D=E.parent/'D';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
frozen=json.loads((E/'manifest.json').read_text());assert all(sha(E/k)==v for k,v in frozen['files'].items())
INSTALL=types.ModuleType('bra_private_install');INSTALL.__file__=str(E/'install_design.py');INSTALL.OUT=OUT
code=(E/'install_design.py').read_text(encoding='utf-8').replace("(P/'preservation.json')","(OUT/'preservation.json')");exec(compile(code,str(E/'install_design.py'),'exec'),INSTALL.__dict__)
recipe=(E/'render_core_six.py').read_text(encoding='utf-8').split('for fixture in old:')[0].replace('import install_design','install_design=INSTALL').replace("(P/'preservation.json')","(OUT/'preservation.json')")
globals()['__file__']=str(E/'render_core_six.py');exec(compile(recipe,str(E/'render_core_six.py'),'exec'),globals())
dd=np.load(D/'sculpt07-D.npz');me=bpy.data.meshes.new('HeldD_BraDiagnostic_Mesh');me.from_pydata(dd['world'].tolist(),[],dd['triangles'].tolist());me.update();held=bpy.data.objects.new('Held_D_PartialBraDiagnostic_ONLY',me);s.collection.objects.link(held)
for poly in me.polygons:poly.use_smooth=True
coverage=json.loads((OUT/'coverage-report.json').read_text());assert coverage['fixed_3D_attribute_reused_for_all_views'];coverage_records={q['state']:q for q in coverage['records']}
for state,ob in [('D',held),('E',design)]:
    record=coverage_records[state];meshpath=D/'sculpt07-D.npz' if state=='D' else E/'sculpt07-E.npz';assert sha(meshpath)==record['mesh_sha256'];payload=np.load(record['coverage_path']);assert sha(record['coverage_path'])==record['coverage_sha256'];values=payload['coverage'];assert len(values)==len(ob.data.vertices)
    attr=ob.data.attributes.new('SourceFrontCentralBraCoverage','FLOAT','POINT');attr.data.foreach_set('value',values)
    actual=np.empty(len(values),np.float32);attr.data.foreach_get('value',actual);assert np.array_equal(actual,values)
cloth=bpy.data.materials.new('PartialObservedFrontBra_DIAGNOSTIC_NoUV');cloth.use_nodes=True;nn=cloth.node_tree.nodes;nn.clear();attribute=nn.new('ShaderNodeAttribute');attribute.attribute_name='SourceFrontCentralBraCoverage';mix=nn.new('ShaderNodeMixRGB');mix.blend_type='MIX';mix.inputs[1].default_value=(.23,.23,.23,1);mix.inputs[2].default_value=(.018,.018,.024,1);surface=nn.new('ShaderNodeBsdfPrincipled');surface.inputs['Roughness'].default_value=.85;oo=nn.new('ShaderNodeOutputMaterial');cloth.node_tree.links.new(attribute.outputs['Fac'],mix.inputs[0]);cloth.node_tree.links.new(mix.outputs[0],surface.inputs['Base Color']);cloth.node_tree.links.new(surface.outputs[0],oo.inputs['Surface']);held.data.materials.append(cloth);design.data.materials[0]=cloth
fixtures=[q for q in json.loads((D/'actual-six-D/render-records.json').read_text()) if q['view'] in ['front','F2lowoblique']];assert len(fixtures)==2
rows=[];dry='--cpu-only' in sys.argv
for fixture in fixtures:
    for state,ob in [('D',held),('E',design)]:
        q=fixture['camera'];yaw,pitch=q['yaw'],q['pitch'];target=Vector((0,-.035,1.275));dist=2;angle=math.radians(yaw);elev=math.radians(pitch)
        cam.location=target+Vector((dist*math.sin(angle)*math.cos(elev),-dist*math.cos(angle)*math.cos(elev),dist*math.sin(elev)));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.40;s.render.resolution_x=s.render.resolution_y=640
        if fixture['view']=='F2lowoblique':
            source=json.loads((CAN/'blender/mia-fit-v003/body/source-binding/constraints.json').read_text());mpp=source['display_metric']['metres_per_pixel'];center=source['cameras']['F2']['body_axis_pixel_x']-887;right=Vector((math.cos(angle),math.sin(angle),0));up=Vector((-math.sin(angle)*math.sin(elev),math.cos(angle)*math.sin(elev),math.cos(elev)));target=Vector((0,-.018,0))-right*((center-443.5)*mpp);crown=1.692881464958191;target.z=(crown*math.cos(elev)-(443.5-11)*mpp-up.x*target.x-up.y*target.y)/up.z;dist=2.5;cam.location=target+Vector((dist*math.sin(angle)*math.cos(elev),-dist*math.cos(angle)*math.cos(elev),dist*math.sin(elev)));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=mpp*887;s.render.resolution_x=s.render.resolution_y=887
        design.hide_render=state!='E';held.hide_render=state!='D';context.hide_render=False;bpy.context.view_layer.update()
        camera=dict(projection=cam.data.type,matrix=[list(r) for r in cam.matrix_world],ortho_scale=cam.data.ortho_scale,clip_start=cam.data.clip_start,clip_end=cam.data.clip_end,resolution=[s.render.resolution_x,s.render.resolution_y],pixel_aspect=[1,1],frame=s.frame_current,yaw=q['yaw'],pitch=q['pitch']);assert camera==q
        assert install_design.fingerprint(original)==original_fingerprint and pose=={b.name:[list(r) for r in b.matrix_basis] for b in rig.pose.bones} and keys=={k.name:k.value for k in master.data.shape_keys.key_blocks}
        actual=install_design.coords(ob.data.vertices);target=np.load(D/'sculpt07-D.npz' if state=='D' else E/'sculpt07-E.npz')['world'];assert np.array_equal(actual,target)
        path=OUT/(state+'-bra-'+fixture['view']+'.png');row=dict(state=state,view=fixture['view'],path=str(path),camera=camera,mesh_sha256=coverage_records[state]['mesh_sha256'],coverage_sha256=coverage_records[state]['coverage_sha256'],coverage_report_sha256=sha(OUT/'coverage-report.json'),actual_material_signature=fp.material_signature(cloth),actual_transparency_signature=fp.material_signature(transparent),actual_visible_meshes=[o.name for o in s.objects if o.type=='MESH' and not o.hide_render],actual_lights=[dict(name=o.name,hidden=o.hide_render,energy=o.data.energy,size=o.data.size,use_shadow=o.data.use_shadow,matrix=[list(r) for r in o.matrix_world]) for o in s.objects if o.type=='LIGHT'],actual_pose_sha256=fp.json_digest(pose),actual_keys_sha256=fp.json_digest(keys),world=dict(color=list(bg.inputs['Color'].default_value),strength=bg.inputs['Strength'].default_value),color_management=fixture['color_management'],geometry_bitexact=True,native_saved=False,head_scale_changed=False,limits=coverage['limits'])
        row['actual_renderer_state_sha256']=fp.json_digest(row)
        if not dry:
            assert not path.exists();(OUT/(path.stem+'-pre-render.json')).write_text(json.dumps(row,indent=2)+'\n',encoding='utf-8');s.render.filepath=str(path);bpy.ops.render.render(write_still=True);row['sha256']=sha(path)
        rows.append(row)
        if not dry:(OUT/'render-records.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
assert len(rows)==4 and all(sha(E/k)==v for k,v in frozen['files'].items()) and sha(N)==NATIVE_SHA
if dry:(OUT/'render-preparation.json').write_text(json.dumps(dict(status='CPU exact4 fixtures/material/attribute/context checks ready; no GPU render',frames=4,geometry_bitexact=True,first15_manifest_files_exact=True,native_sha256=NATIVE_SHA),indent=2)+'\n',encoding='utf-8')
print('BRA_FIXED_COVERAGE_CPU_RENDER_READY' if dry else 'BRA_ACTUAL4_DONE ALL_FIRST15_INPUTS_HELD',flush=True)
