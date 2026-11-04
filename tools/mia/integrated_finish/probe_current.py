"""Read-only live inventory and one small current geometry packet."""
from pathlib import Path
import hashlib,json,runpy
import bpy
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'.mia-cache/body-h/live/integrated01'
OUT.mkdir(parents=True,exist_ok=True)
assert not (OUT/'probe.json').exists()
body=bpy.data.objects['MIA_Review12_H_LiveRepair']
co=np.empty((len(body.data.vertices),3),np.float32);body.data.vertices.foreach_get('co',co.ravel())
faces=np.asarray([p.vertices[:] for p in body.data.polygons],np.int32)
assert faces.shape[1]==3
payload=dict(co=co,faces=faces)
attrs=[]
for a in body.data.attributes:
    attrs.append(dict(name=a.name,domain=a.domain,data_type=a.data_type,length=len(a.data)))
    if a.data_type=='INT' and a.domain=='FACE':
        values=np.empty(len(a.data),np.int32);a.data.foreach_get('value',values)
        payload[a.name]=values
report=dict(filepath=bpy.data.filepath,native_sha256=hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),
 body_sha256=hashlib.sha256(co.tobytes()).hexdigest(),body_vertices=len(co),body_faces=len(faces),
 attributes=attrs,modifiers=[dict(name=m.name,type=m.type) for m in body.modifiers],
 keys=len(body.data.shape_keys.key_blocks) if body.data.shape_keys else 0,
 body_matrix=[list(r) for r in body.matrix_world],
 namespaces=[k for k in bpy.app.driver_namespace if k.startswith('MIA_')],
 hair=[dict(name=o.name,vertices=len(o.data.vertices),hidden=o.hide_get(),hide_render=o.hide_render)
       for o in bpy.data.objects if o.name.startswith('MIA_Hair_CurvedRear03Base_')],
 source='Current actual live state; no mutation/approval',ART=False)
np.savez_compressed(OUT/'current-geometry.npz',**payload)
(OUT/'probe.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k not in ('namespaces','attributes','hair')}))
