"""CPU-only reproduction and four-state operator scope proof. No native save."""
from pathlib import Path
import sys,json,hashlib
import bpy,numpy as np
O=Path(__file__).resolve().parent;P=O.parent
sys.path.insert(0,str(P));sys.path.insert(0,str(O));sys.path.insert(0,str(P/'inputs'))
import install_posed_target_05, rigged05 as diag, scene_fingerprint as fp
d=json.loads((P/'current-body-audit.json').read_text());native=Path(d['native']);assert diag.digest(native)==d['sha256']
bpy.ops.wm.open_mainfile(filepath=str(native),use_scripts=False)
s=bpy.context.scene;s.frame_set(2);s.frame_set(1);bpy.context.view_layer.update()
original_names={ob.name for ob in bpy.data.objects};cache={};before={name:fp.object_fingerprint(bpy.data.objects[name],cache) for name in original_names};envelope=fp.scene_envelope()
print('DIAGNOSTIC05_ORIGINALS_CAPTURED',len(before),flush=True)
source=bpy.data.objects['MIA_V27_SharedHeadBody'];original47={k.name:diag.coordinates(k.data) for k in source.data.shape_keys.key_blocks}
static=install_posed_target_05.build();frozen=diag.read_surface(static);baseline=diag.read_surface(source)
ctx=diag.build(source);rigged=diag.read_surface(ctx['object']);error=np.linalg.norm(rigged['world']-frozen['world'],axis=1)
print('DIAGNOSTIC05_INVERSE_EVALUATED',float(error.max()*1000),'mm',flush=True)
assert all(np.array_equal(rigged[k],frozen[k]) for k in ['loops','sizes','materials'])
assert error.max() <= 2e-6, ('Actual05 rigged reproduction failed',error.max())
head=baseline['world'][:,2]>=1.465
assert np.array_equal(rigged['world'][head],frozen['world'][head]),('Head reproduction changed',np.linalg.norm(rigged['world'][head]-frozen['world'][head],axis=1).max())
normal_angle=lambda a,b:np.degrees(np.arccos(np.clip(np.sum(a*b,axis=1)/(np.linalg.norm(a,axis=1)*np.linalg.norm(b,axis=1)),-1,1)))
normal=normal_angle(rigged['face_normals'],frozen['face_normals'])
states=[];surfaces={}
for pose in ['current','source-like']:
    for smooth_on in [True,False]:
        row=diag.set_state(ctx,pose,smooth_on);q=diag.read_surface(ctx['object']);name=pose+('-smooth-on' if smooth_on else '-smooth-body-off')
        assert np.array_equal(q['world'][head],frozen['world'][head]), ('Protected head changed',name)
        assert all(np.array_equal(q[k],frozen[k]) for k in ['loops','sizes','materials'])
        for key,array in original47.items():assert np.array_equal(diag.coordinates(ctx['object'].data.shape_keys.key_blocks[key].data),array)
        cache={}
        for name0,signature in before.items():assert fp.object_fingerprint(bpy.data.objects[name0],cache)==signature,('Original mutated',name0)
        row.update(name=name,head_count=int(head.sum()),evaluated_head_bitexact=True,all_original_objects_exact=len(before),original47_private_arrays_exact=True)
        surfaces[name]=q['world'];states.append(row);print('DIAGNOSTIC05_STATE_CPU_PASS',name,flush=True)
for row in states:
    name=row['name'];ref=surfaces[row['pose']+'-smooth-on'];row['smooth_body_delta_max_mm']=float(np.linalg.norm(surfaces[name]-ref,axis=1).max()*1000)
diag.set_state(ctx,'current',True)
restored=diag.read_surface(ctx['object']);restore=np.linalg.norm(restored['world']-rigged['world'],axis=1)
assert np.array_equal(restored['world'],rigged['world']),('Private state restore not exact',restore.max())
cache={}
for name,signature in before.items():assert fp.object_fingerprint(bpy.data.objects[name],cache)==signature,('Original mutated',name)
assert fp.scene_envelope()==envelope
assert diag.digest(native)==d['sha256']
report=dict(status='CPU PASS: rejected05 faithfully reproduced; four diagnostic states prepared, no anatomy approval',native_sha256=d['sha256'],metadata=ctx['metadata'],
    actual05_reproduction=dict(evaluated_vertices=len(error),polygon_topology_exact=True,positions_bitexact=bool(np.array_equal(rigged['world'],frozen['world'])),
    error_mm=dict(max=float(error.max()*1000),p95=float(np.percentile(error,95)*1000),rms=float(np.sqrt(np.mean(error**2))*1000)),
    true_face_normal_difference_degrees=dict(max=float(normal.max()),p95=float(np.percentile(normal,95)))),
    states=states,private_state_restore_bitexact=True,original_objects_exact=len(before),scene_envelope_exact=True,original47_and_accepted_head_exact=True,
    native_unchanged=True,native_saved=False,gpu_used=False)
(O/'cpu-guard.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('REJECTED05_RIG_POSE_SMOOTH_CPU_PASS',json.dumps(report),flush=True)
