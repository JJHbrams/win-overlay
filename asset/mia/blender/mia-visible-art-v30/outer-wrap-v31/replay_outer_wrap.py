"""Apply guarded coordinate-only outer-wrap delta to integrated M+FaceA+hair.

Blender --background --python replay_outer_wrap.py -- INPUT OUTPUT E
E is preferred: same coordinates as D, plus unilateral-aware wall drivers.
No complete standalone scene is loaded over the integrated target.
"""
import bpy,numpy as np,json,sys,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
from audit_mesh_helpers import snapshot,graph,jhash
args=sys.argv[sys.argv.index('--')+1:];assert len(args)==3
source,output=[Path(s).resolve() for s in args[:2]];tag=args[2];assert tag in ['C','D','E']
assert source!=output and not output.exists()
meta=json.loads((P/('outer-wrap-'+tag+'-portable.json')).read_text());payload=P/meta['payload'];assert hashlib.sha256(payload.read_bytes()).hexdigest()==meta['payload_sha256']
blob=np.load(payload,allow_pickle=False);sha=hashlib.sha256(source.read_bytes()).hexdigest();bo,_,bm,bi=snapshot(source)
def scene_signature():
    sc=bpy.context.scene
    rows=[]
    for ob in sc.objects:
        row={'name':ob.name,'type':ob.type,'matrix':[list(r) for r in ob.matrix_world],'hide_render':ob.hide_render,'hide_viewport':ob.hide_viewport,'parent':ob.parent.name if ob.parent else None,'collections':sorted(c.name for c in ob.users_collection)}
        if ob.type=='CAMERA':row['camera']={k:getattr(ob.data,k) for k in ['type','lens','ortho_scale','shift_x','shift_y','clip_start','clip_end']}
        if ob.type=='LIGHT':row['light']={'type':ob.data.type,'energy':ob.data.energy,'color':list(ob.data.color),'size':getattr(ob.data,'size',None)}
        rows.append(row)
    return jhash({'objects':rows,'world':graph(sc.world.node_tree) if sc.world and sc.world.use_nodes else sc.world.name if sc.world else None,'active_camera':sc.camera.name if sc.camera else None,'frame':sc.frame_current,'render_engine':sc.render.engine,'resolution':[sc.render.resolution_x,sc.render.resolution_y,sc.render.resolution_percentage],'display':[sc.view_settings.view_transform,sc.view_settings.look,sc.view_settings.exposure,sc.view_settings.gamma]})
scene_before=scene_signature();names=[o['name'] for o in meta['owners']]
for row in meta['owners']:
    n=row['name'];base=row['baseline_record'];assert n in bo,n
    # Snapshot uses tuples inside driver records; JSON metadata has lists.
    # Canonical serialization compares exact values without tuple/list artifacts.
    assert all(jhash(bo[n][k])==jhash(base[k]) for k in base if k!='materials'),('Input M geometry/topology/key/weight/driver/modifier/transform changed; re-evaluate contact rather than bypass guard',n)
for row in meta['owners']:
    n=row['name'];ob=bpy.data.objects[n];prefix=row['prefix'];ob.data.vertices.foreach_set('co',blob[prefix+'_raw'].ravel())
    for added in row.get('added_shape_keys',[]):
        assert added['name'] not in ob.data.shape_keys.key_blocks
        sk=ob.shape_key_add(name=added['name'],from_mix=False);sk.slider_min=0;sk.slider_max=1
        spec=added['driver'];dr=sk.driver_add('value').driver;dr.type=spec['type'];dr.expression=spec['expression']
        for vn,vt,targets in spec['variables']:
            var=dr.variables.new();var.name=vn;var.type=vt
            for t,(_,dp) in zip(var.targets,targets):t.id_type='KEY';t.id=bpy.data.objects['MIA_V27_Foundation_Face'].data.shape_keys;t.data_path=dp
    for key,q in zip(ob.data.shape_keys.key_blocks,blob[prefix+'_keys']):key.data.foreach_set('co',q.ravel())
    ob.data.update()
output.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(output));ao,_,am,ai=snapshot(output)
checks={'all_input_nonowned_mesh_records_exact':all(bo[n]==ao[n] for n in bo if n not in names),'all_owned_input_noncoordinate_nonextended_fields_exact':all(all(bo[n][k]==ao[n][k] for k in bo[n] if k not in (['coordinates','key_names','drivers'] if tag in ['D','E'] and 'InnerLid_' in n else ['coordinates'])) for n in names),'all_delta_coordinates_exact':all(ao[r['name']]['coordinates']==r['target_coordinate_sha256'] for r in meta['owners']),'all_target_key_names_drivers_exact':all(jhash(ao[r['name']]['key_names'])==jhash(r.get('target_record',r['baseline_record'])['key_names']) and jhash(ao[r['name']]['drivers'])==jhash(r.get('target_record',r['baseline_record'])['drivers']) for r in meta['owners']),'all_input_material_graphs_exact':bm==am,'all_input_images_packing_colorspace_exact':bi==ai,'all_input_scene_object_camera_light_world_settings_exact':scene_signature()==scene_before,'input_native_unchanged':hashlib.sha256(source.read_bytes()).hexdigest()==sha}
assert all(checks.values()),checks
record={'input':str(source),'input_sha256':sha,'output':str(output),'output_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'delta_native_sha256':meta['target_native_sha256'],'payload_sha256':meta['payload_sha256'],'owners':names,'checks':checks,'scope':meta['scope'],'pending':meta['pending']}
output.with_suffix('.outer-wrap-'+tag+'-replay.json').write_text(json.dumps(record,indent=2),encoding='utf8');print('OUTER_WRAP_REPLAY_DONE',json.dumps(record))
