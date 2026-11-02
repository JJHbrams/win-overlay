"""Guarded4-key lash delta, preserving exact current hair/E/brows/materials.

Blender --background --python-exit-code 2 --python replay_closed_delta.py -- INPUT OUTPUT B
"""
import bpy,numpy as np,json,sys,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));from audit_mesh_helpers import snapshot,jhash,graph
args=sys.argv[sys.argv.index('--')+1:];assert len(args)==3;source,output=[Path(p).resolve() for p in args[:2]];tag=args[2];assert tag in ['B'];assert source!=output and not output.exists();meta=json.loads((P/('closed-'+tag+'-delta.json')).read_text());payload=P/meta['payload'];assert hashlib.sha256(payload.read_bytes()).hexdigest()==meta['payload_sha256'];blob=np.load(payload,allow_pickle=False);sha=hashlib.sha256(source.read_bytes()).hexdigest();bo,_,bm,bi=snapshot(source);names=[r['name'] for r in meta['owners']]
def scene_sig():
    sc=bpy.context.scene;rows=[]
    for o in sc.objects:
        d={'name':o.name,'type':o.type,'matrix':[list(r) for r in o.matrix_world],'hide_render':o.hide_render,'hide_viewport':o.hide_viewport,'parent':o.parent.name if o.parent else None,'collections':sorted(c.name for c in o.users_collection)}
        if o.type=='CAMERA':d['camera']={k:getattr(o.data,k) for k in ['type','lens','ortho_scale','clip_start','clip_end','shift_x','shift_y']}
        if o.type=='LIGHT':d['light']={'type':o.data.type,'energy':o.data.energy,'color':list(o.data.color),'size':getattr(o.data,'size',None)}
        if o.type=='ARMATURE':d['pose']=[(b.name,[list(r) for r in b.matrix_basis]) for b in o.pose.bones]
        rows.append(d)
    return jhash({'objects':rows,'camera':sc.camera.name if sc.camera else None,'world':graph(sc.world.node_tree) if sc.world else None,'frame':sc.frame_current,'engine':sc.render.engine,'resolution':[sc.render.resolution_x,sc.render.resolution_y,sc.render.resolution_percentage],'display':[sc.view_settings.view_transform,sc.view_settings.look,sc.view_settings.exposure,sc.view_settings.gamma]})
scene_before=scene_sig()
for r in meta['owners']:
    n=r['name'];expected=r['baseline_record'];assert n in bo;assert all(jhash(bo[n][k])==jhash(expected[k]) for k in expected if k!='materials'),('Uppergeometry/key/UV/weights/drivers changed; re-evaluate instead ofbypassing',n)
for n,r in meta['protected_surface_records'].items():
    assert n in bo and all(jhash(bo[n][k])==jhash(r[k]) for k in r if k!='materials'),('Protectedskin/Eocular/wall/master geometrychanged; re-evaluatecontact',n)
for r in meta['owners']:
    ob=bpy.data.objects[r['name']]
    for key in r['keys']:ob.data.shape_keys.key_blocks[key['name']].data.foreach_set('co',blob[key['payload_key']].ravel())
    ob.data.update()
output.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(output));ao,_,am,ai=snapshot(output)
checks={'all_input_nonupper_mesh_records_exact':all(bo[n]==ao[n] for n in bo if n not in names),'all_upper_input_noncoordinate_fields_exact':all(all(bo[n][k]==ao[n][k] for k in bo[n] if k!='coordinates') for n in names),'exact_selected_closed_delta':all(ao[r['name']]['coordinates']==r['target_coordinates_sha256'] for r in meta['owners']),'all_input_material_graphs_exact':bm==am,'all_input_images_maps_exact':bi==ai,'all_input_scene_camera_lights_world_pose_exact':scene_sig()==scene_before,'input_native_immutable':hashlib.sha256(source.read_bytes()).hexdigest()==sha}
assert all(checks.values()),checks
report={'input':str(source),'input_sha256':sha,'output':str(output),'output_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'delta_native_sha256':meta['candidate_sha256'],'payload_sha256':meta['payload_sha256'],'checks':checks,'scope':meta['scope'],'pending':meta['pending']};output.with_suffix('.closed-'+tag+'-replay.json').write_text(json.dumps(report,indent=2),encoding='utf8');print('CLOSED_DELTA_REPLAY_DONE',json.dumps(report))
