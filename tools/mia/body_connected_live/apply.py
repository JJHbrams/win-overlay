"""Apply the single design proposal only to the private live cage, with actual evaluation."""
from pathlib import Path
import hashlib,json
import bpy,numpy as np

ROOT=Path('D:/MiaWorkCache/mia-reference-work/win-overlay');CACHE=ROOT/'.mia-cache/body-connected'
ns=bpy.app.driver_namespace;ob=bpy.data.objects['MIA_ConnectedBody_Design'];source=bpy.data.objects['MIA_V27_SharedHeadBody']
if ob.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
proposal=dict(np.load(CACHE/'proposal.npz'))
raw=np.array([v.co[:]for v in ob.data.vertices],np.float32)
assert np.array_equal(raw,ns['MIA_Connected_Baseline_Local']) or np.array_equal(raw,proposal['target_posed_local']),'Expected original baseline or interrupted same proposal'
# World/local float roundtrip must not touch protected controls at all.
raw=ns['MIA_Connected_Baseline_Local'].copy()
ob.data.vertices.foreach_set('co',raw.ravel());ob.data.update();bpy.context.view_layer.update()
target_local=proposal['target_posed_local'].copy();outside=np.ones(len(raw),bool);outside[proposal['selected']]=False
target_local[outside]=raw[outside];ns['MIA_Connected_Target_Local']=target_local

def evaluated(owner):
    dg=bpy.context.evaluated_depsgraph_get();e=owner.evaluated_get(dg);me=e.to_mesh(preserve_all_data_layers=True,depsgraph=dg)
    v=np.array([e.matrix_world@p.co for p in me.vertices],np.float32)
    loops=np.array([p.vertex_index for p in me.loops],np.int32)
    uv={u.name:hashlib.sha256(np.array([p.uv[:]for p in u.data],np.float32).tobytes()).hexdigest()for u in me.uv_layers}
    me.calc_loop_triangles();tri=np.array([t.vertices[:]for t in me.loop_triangles],np.int32)
    e.to_mesh_clear();return v,loops,uv,tri

baseline=evaluated(ob);original=evaluated(source)
assert np.array_equal(baseline[0],original[0]),'Private baseline differs from actual live original geometry'
ns['MIA_Connected_Evaluated_Before']=baseline
ob.data.vertices.foreach_set('co',target_local.ravel());ob.data.update();bpy.context.view_layer.update()
after=evaluated(ob)
assert np.array_equal(baseline[1],after[1])
head=(baseline[0][:,2]>=1.465)
displacement=np.linalg.norm(after[0]-baseline[0],axis=1)
t=baseline[3];a=baseline[0][t];b=after[0][t]
u=a[:,1]-a[:,0];v=a[:,2]-a[:,0];du=b[:,1]-b[:,0];dv=b[:,2]-b[:,0]
cross=np.cross(u,v);newcross=np.cross(du,dv)
area=np.linalg.norm(cross,axis=1);newarea=np.linalg.norm(newcross,axis=1)
valid=area>1e-11;ratio=newarea[valid]/area[valid]
reverse=(np.sum(cross*newcross,axis=1)<0)&valid
changed=displacement.max()>0
rawsource=np.array([p.co[:]for p in source.data.vertices],np.float32)
keys={k.name:hashlib.sha256(np.array([p.co[:]for p in k.data],np.float32).tobytes()).hexdigest()for k in source.data.shape_keys.key_blocks}
assert np.array_equal(rawsource,ns['MIA_Connected_Source_Raw']) and keys==ns['MIA_Connected_Source_Key_SHA']
np.savez_compressed(CACHE/'actual-evaluation.npz',baseline=baseline[0],after=after[0],triangles=t,head=head)
report=dict(operation='ONE broad connected DESIGN proposal applied to private live cage',
    runtime='LIVE_OFFICIAL_MCP',object=ob.name,changed=bool(changed),proposal_sha256=hashlib.sha256((CACHE/'proposal.npz').read_bytes()).hexdigest(),
    evaluated_vertices=len(after[0]),evaluated_head_vertices=int(head.sum()),
    actual_head_world_max_delta_mm=float(displacement[head].max()*1000),actual_head_exact=bool(np.array_equal(baseline[0][head],after[0][head])),
    actual_body_max_delta_mm=float(displacement.max()*1000),all_original_raw_head_controls_exact=bool(np.array_equal(raw[proposal['protected']],target_local[proposal['protected']])),
    original47_unchanged=True,original_raw_unchanged=True,private_evaluated_UV_before=baseline[2],private_evaluated_UV_after=after[2],evaluated_polygon_loops_exact=True,
    UV_evaluated_warning='MIA_BODY_V23_UV evaluation hash alternates before geometry edit; raw private UV preservation requires separate check, no UV migration claim',
    UV_preexisting_live_private_vs_original_equal=baseline[2]==original[2],UV_live_original=original[2],
    postmodifiers=[dict(name=m.name,type=m.type)for m in ob.modifiers],
    triangle_area_ratio_percentiles=np.percentile(ratio,[0,1,5,50,95,99,100]).tolist(),
    triangle_normal_over90deg_count=int(reverse.sum()),normal_warning='Normal angle is a strain diagnostic, not a proof of self intersection',
    ART=False,native_saved=False,production_migration=False)
(CACHE/'live/applied.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(report),flush=True)
