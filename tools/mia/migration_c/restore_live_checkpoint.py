"""Rehydrate only the retained C static-body/hair ownership after native reopen."""
from pathlib import Path
import hashlib
import json
import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'.mia-cache/migration-to-C'
record = json.loads((OUT/'runtime.json').read_text(encoding='utf8'))
native = Path(record['native'])
assert Path(bpy.data.filepath).resolve() == native.resolve()
assert hashlib.sha256(native.read_bytes()).hexdigest() == record['native_sha256']
sha = lambda ob: hashlib.sha256(np.array([v.co[:] for v in ob.data.vertices], np.float32).tobytes()).hexdigest()
for name, expected in record['actor_geometry'].items():
    assert sha(bpy.data.objects[name]) == expected, name
for name, expected in record['visibility'].items():
    ob = bpy.data.objects[name]
    assert [ob.hide_get(),ob.hide_render] == expected, name
assert bpy.context.scene.frame_current == record['frame']
assert np.allclose(np.array(bpy.context.scene.camera.matrix_world),record['camera_matrix'],atol=1e-7)
rear = dict(record['rear'])
for name, collection in [('objects',bpy.data.objects),('meshes',bpy.data.meshes),('groups',bpy.data.node_groups),('materials',bpy.data.materials)]:
    rear[name] = [collection[item] for item in rear[name]]
rear['source_visibility'] = tuple(rear['source_visibility'])
ns = bpy.app.driver_namespace
ns['MIA_CurvedRear03Base'] = rear
ns['MIA_Live_H_Rows'] = dict(np.load(OUT/'row-ownership.npz'))
ns['MIA_Live_H_Payload'] = record['live_payload']
# A borrowed hair review is transient. A new review must capture this C state.
ns.pop('MIA_HairReviewState',None)
for key in ('review_fixture','assemble','live_relax'):
    import sys
    module = sys.modules.get(key)
    if module and str(getattr(module,'__file__','')).startswith('D:'):
        del sys.modules[key]
report = dict(native=str(native),body_sha256=record['body_sha256'],rear_actors=len(rear['objects']),
              exact_actor_geometry=True,exact_visibility=True,camera_frame_preserved=True,
              row_ownership_rehydrated=True,live_payload=ns['MIA_Live_H_Payload'],
              ART=False,scope='C migration reopen/runtime continuity only')
(OUT/'reopen-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(report))
