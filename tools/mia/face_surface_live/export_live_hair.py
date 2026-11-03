"""Freeze the actual scoped live WIP, without another native or any promotion."""
from pathlib import Path
import hashlib
import json
import bpy
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'.mia-cache/face-live/curved-rear03/actual-emergence'
assert not OUT.exists()
state=bpy.app.driver_namespace['MIA_CurvedRear03Base']
payload={};records=[]
for ob in state['objects']:
    if ob.name.endswith('_RemainingMain'):continue
    q=np.array([v.co[:] for v in ob.data.vertices],np.float32)
    f=np.array([p.vertices[:] for p in ob.data.polygons],np.int32)
    uv=np.array([u.uv[:] for u in ob.data.uv_layers['LockParamUV'].data],np.float32)
    payload[ob.name+'_world']=q;payload[ob.name+'_triangles']=f;payload[ob.name+'_UV']=uv
    records.append(dict(name=ob.name,vertices=len(q),triangles=len(f),
                        world_sha256=hashlib.sha256(q.tobytes()).hexdigest(),
                        topology_sha256=hashlib.sha256(f.tobytes()).hexdigest()))
source=bpy.data.objects['MIA_V17_PIXAL_DetailedHair']
source_native_sha=hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()
assert source_native_sha=='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'
raw_sha=hashlib.sha256(np.array([v.co[:] for v in source.data.vertices],np.float32).tobytes()).hexdigest()
assert raw_sha==state['source_raw_sha256']
body=bpy.data.objects['MIA_Review12_H_LiveRepair']
body_sha=hashlib.sha256(np.array([v.co[:] for v in body.data.vertices],np.float32).tobytes()).hexdigest()
assert body_sha==bpy.app.driver_namespace['MIA_HairReviewState']['body_sha256']
OUT.mkdir(parents=True);np.savez_compressed(OUT/'geometry.npz',**payload)
report=dict(scope='ACTUAL LIVE WIP readback; not selected, ART accepted or final rig',actors=records,
            geometry_sha256=hashlib.sha256((OUT/'geometry.npz').read_bytes()).hexdigest(),
            current_original_Main_raw_sha256=raw_sha,body_sha256=body_sha,
            underlying_base_retained=True,only_traced_U_family_omitted_on_derived_Main=True,
            source_native_saved=False,source_native_unchanged=True,source_native_sha256=source_native_sha,ART=False,
            actual_views=['.mia-cache/face-live/live/emergence-back-after-0.png',
                          '.mia-cache/face-live/live/emergence-oblique-after-0.png'])
(OUT/'capture.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(actors=len(records),bytes=(OUT/'geometry.npz').stat().st_size,
                      path=str(OUT),geometry_sha256=report['geometry_sha256'],body_sha256=body_sha,ART=False)))
