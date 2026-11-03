"""Read-only live normal diagnosis on an unlinked temporary mesh copy."""
from pathlib import Path
import json
import bpy
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
body=bpy.data.objects['MIA_Review12_H_LiveRepair']
assert body.mode=='OBJECT'
original=body.data
before=np.array([n.vector[:] for n in original.corner_normals],np.float32).reshape(-1,3,3)
probe=original.copy();probe.name='MIA_Live_NormalProbe_Temporary_Unlinked'
assert probe.users==0
try:
    probe.normals_split_custom_set(np.zeros((len(probe.loops),3),np.float32).tolist())
    probe.update()
    auto=np.array([n.vector[:] for n in probe.corner_normals],np.float32).reshape(-1,3,3)
    x=before.astype(float);y=auto.astype(float)
    angle=np.degrees(np.arctan2(np.linalg.norm(np.cross(x,y),axis=2),(x*y).sum(2)))
    d=np.load(Path(bpy.app.driver_namespace['MIA_Live_H_Payload'])/'geometry.npz')
    part=d['source_part'];groups={}
    for name,mask in [('body',part!=1),('neck',np.arange(len(part))>=209484),('head',part==1)]:
        if name=='neck':mask&=np.arange(len(part))<221750
        groups[name]=dict(corners=int(mask.sum()*3),max_angle_degrees=float(angle[mask].max()),p95_angle_degrees=float(np.percentile(angle[mask],95)))
    result=dict(scope='Actual live normals versus pure-auto unlinked copy; source mesh unchanged',groups=groups,
                mesh_geometry_changed=False,body_materials_changed=False)
    (ROOT/'.mia-cache/body-h/live/normal-probe.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result))
finally:
    assert body.data==original and probe.users==0
    bpy.data.meshes.remove(probe)
