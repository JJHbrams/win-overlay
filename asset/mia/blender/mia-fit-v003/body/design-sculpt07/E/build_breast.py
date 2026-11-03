"""Factory Blender native C++ meshing; never opens or saves selected native."""
from pathlib import Path
import json,hashlib,sys,time
import bpy,numpy as np
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import field
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=json.loads((P/'parameters.json').read_text());source=p['source_consumed_before_geometry'];assert len(source['section_support_bands'])==4
f,reg=field.make(p);spec=p['mesher'];density=field.ma(.5-f/spec['density_scale_m'],0.)
bpy.ops.wm.read_factory_settings(use_empty=True)
me=bpy.data.meshes.new('Sculpt07_Empty');ob=bpy.data.objects.new('Sculpt07_E_NEW_IMPLICIT_DESIGN',me);bpy.context.scene.collection.objects.link(ob)
ng=bpy.data.node_groups.new('Sculpt07_PositiveAnatomy','GeometryNodeTree');ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
out=ng.nodes.new('NodeGroupOutput');den=field.nodes(ng,density);vol=ng.nodes.new('GeometryNodeVolumeCube');vol.inputs['Background'].default_value=0.;vol.inputs['Min'].default_value=spec['bounds_min'];vol.inputs['Max'].default_value=spec['bounds_max']
extent=np.array(spec['bounds_max'])-spec['bounds_min'];res=np.ceil(extent/spec['voxel_m']).astype(int)+1
for axis,n in zip('XYZ',res):vol.inputs['Resolution '+axis].default_value=int(n)
ng.links.new(den,vol.inputs['Density']);vm=ng.nodes.new('GeometryNodeVolumeToMesh');vm.inputs['Threshold'].default_value=.5;vm.inputs['Adaptivity'].default_value=0.;ng.links.new(vol.outputs['Volume'],vm.inputs['Volume']);ng.links.new(vm.outputs['Mesh'],out.inputs['Geometry'])
mod=ob.modifiers.new('Sculpt07_NativeImplicitMesher','NODES');mod.node_group=ng
t0=time.time();bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();ev=ob.evaluated_get(dg);mesh=ev.to_mesh();mesh.calc_loop_triangles()
world=np.empty(len(mesh.vertices)*3,np.float32);mesh.vertices.foreach_get('co',world);world=world.reshape(-1,3)
tri=np.array([t.vertices[:] for t in mesh.loop_triangles],np.int32)
assert len(world)>1000 and np.isfinite(world).all();np.savez_compressed(P/'breast-step.npz',world=world,triangles=tri)
# Independent Position-field probes through Geometry Nodes StoreNamedAttribute.
probes=np.array([[0,-.01,1.25],[-.066,-.155,1.257],[.066,-.155,1.257],[.14,-.03,1.31],[.18,0,1.30],[.27,0,1.12],[0,-.19,1.25],[.30,.10,1.4]],np.float32)
pm=bpy.data.meshes.new('FieldProbePoints');pm.from_pydata(probes.tolist(),[],[]);po=bpy.data.objects.new('FieldProbePoints',pm);bpy.context.scene.collection.objects.link(po)
pg=bpy.data.node_groups.new('Sculpt07_ProbeField','GeometryNodeTree');pg.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');pg.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');pin=pg.nodes.new('NodeGroupInput');pout=pg.nodes.new('NodeGroupOutput');store=pg.nodes.new('GeometryNodeStoreNamedAttribute');store.data_type='FLOAT';store.domain='POINT';store.inputs['Name'].default_value='actual_field';pg.links.new(pin.outputs[0],store.inputs['Geometry']);pg.links.new(field.nodes(pg,f),store.inputs['Value']);pg.links.new(store.outputs[0],pout.inputs[0]);po.modifiers.new('Probe','NODES').node_group=pg
bpy.context.view_layer.update();pe=po.evaluated_get(bpy.context.evaluated_depsgraph_get());px=pe.to_mesh();actual=np.array([v.value for v in px.attributes['actual_field'].data]);expected=field.evaluate(f,probes);error=float(abs(actual-expected).max());assert error<2e-6
surface=field.evaluate(f,world[::max(1,len(world)//2000)])
report=dict(parameters_sha256=sha(P/'parameters.json'),mesh_sha256=sha(P/'breast-step.npz'),native_opened=False,native_saved=False,gpu_used=False,vertices=len(world),triangles=len(tri),node_count=len(ng.nodes),resolution=res.tolist(),grid_points=int(np.prod(res)),actual_grid_step_m=(extent/(res-1)).tolist(),build_seconds=time.time()-t0,
 field_probe_max_error_m=error,probes=[dict(point=q.tolist(),cpu_field=float(a),native_node_field=float(b)) for q,a,b in zip(probes,expected,actual)],surface_field_abs_max_mm=float(abs(surface).max()*1000),surface_field_abs_p95_mm=float(np.percentile(abs(surface),95)*1000),field_is_exact_sdf=False,
 status='DESIGN SCULPT first merged volume; actual4 visual review required. No anatomy or source ART pass.')
(P/'breast-build-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('SCULPT07_E_NATIVE_MESH_DONE',json.dumps(report),flush=True)
