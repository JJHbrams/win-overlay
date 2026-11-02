"""Fresh current-scene body field isolation; no render/native save."""
from pathlib import Path
import json,hashlib,sys
import bpy,numpy as np
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));variant='C' if '--variant-C' in sys.argv else ('B' if '--variant-B' in sys.argv else 'A')
if variant=='C':import apply_form_C as patch
elif variant=='B':import apply_form_B as patch
else:import apply_form_A as patch
OLD=P.parents[1]/'mia-body-underwear-v002';sys.path.insert(0,str(OLD/'integration-guard-R3'));import scene_fingerprint as h
d=json.loads((P/'current-body-audit.json').read_text());native=Path(d['native']);assert hashlib.sha256(native.read_bytes()).hexdigest()==d['sha256']
bpy.ops.wm.open_mainfile(filepath=str(native),use_scripts=False);s=bpy.context.scene;s.frame_set(2);s.frame_set(1);bpy.context.view_layer.update();ob=bpy.data.objects[patch.OWNER]
def coords():return {k.name:np.asarray([v.co[:] for v in k.data],np.float32) for k in ob.data.shape_keys.key_blocks}
def evaluated():
    dg=bpy.context.evaluated_depsgraph_get();ev=ob.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles();p=np.asarray([list(ev.matrix_world@v.co) for v in me.vertices]);tri=np.asarray([t.vertices[:] for t in me.loop_triangles]);mi=np.asarray([me.polygons[t.polygon_index].material_index for t in me.loop_triangles]);ev.to_mesh_clear();return p,tri,mi
before=h.snapshot_scene();keys=coords();p,t,mi=evaluated();faceids=np.unique(t[np.isin(mi,[0,9,10,11])]);raw_before=np.asarray([v.co[:] for v in ob.data.vertices],np.float32)
result=patch.apply();after=h.snapshot_scene();newkeys=coords();q,tt,mii=evaluated()
assert all(np.array_equal(v,newkeys[k]) for k,v in keys.items()),'An original key was rewritten'
assert np.array_equal(raw_before,np.asarray([v.co[:] for v in ob.data.vertices],np.float32))
assert np.array_equal(p[faceids],q[faceids]),'Accepted evaluated face changed'
assert all(before['objects'][n]==after['objects'][n] for n in before['objects'] if n!=ob.name)
assert before['scene']==after['scene']
for field in ['vertices','loop_vertices','polygon_sizes','uv','materials','weight_hash','modifiers','modifier_settings','material_signatures','matrix_world']:
    assert before['objects'][ob.name][field]==after['objects'][ob.name][field],field
assert np.array_equal(t,tt) and np.array_equal(mi,mii)
np.savez_compressed(P/('form-'+variant+'-evaluated.npz'),world=q,triangles=t,triangle_materials=mi)
polys_before=p[t];polys_after=q[t];normal0=np.cross(polys_before[:,1]-polys_before[:,0],polys_before[:,2]-polys_before[:,0]);normal1=np.cross(polys_after[:,1]-polys_after[:,0],polys_after[:,2]-polys_after[:,0]);dots=(normal0*normal1).sum(1);flipped=np.flatnonzero(dots<-1e-15)
assert len(flipped)==0,('New reversed evaluated triangles',flipped[:10])
repeat=patch.apply();assert repeat['idempotent']
report=dict(native=str(native),sha256=d['sha256'],candidate=result,existing_key_count=len(keys),original_all47_coordinates_exact=True,raw_cache_exact=True,face690_all_keys_exact=True,evaluated_head_face_vertices=len(faceids),accepted_evaluated_face_bitexact=True,nonbody_owners_exact=len(before['objects'])-1,all_materials_UV_weights_modifiers_pose_camera_lights_exact=True,body_evaluated_max_move_mm=float(np.linalg.norm(q-p,axis=1).max()*1000),evaluated_reversed_triangles=len(flipped),idempotent=True,native_saved=False,gpu_used=False,native_unchanged=hashlib.sha256(native.read_bytes()).hexdigest()==d['sha256'],status='Technical isolation only; actual8gray/source views required before choosing anatomy')
(P/('form-'+variant+'-fresh-guard.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('V003_BODY_FORM_'+variant+'_GUARD_DONE',json.dumps(report),flush=True)
