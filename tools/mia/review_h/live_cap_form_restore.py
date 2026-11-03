"""Restore the rejected normal-ray cap edit exactly; keep failed evidence."""
import hashlib
import json
import bpy
import numpy as np

ob = bpy.data.objects['MIA_Review12_H_LiveRepair']
ns = bpy.app.driver_namespace
v = np.array([p.co[:] for p in ob.data.vertices], np.float32)
assert np.array_equal(v, ns['MIA_Live_CapForm_After'])
q = ns['MIA_Live_CapForm_Before']
ob.data.vertices.foreach_set('co', q.ravel()); ob.data.update(); bpy.context.view_layer.update()
assert np.array_equal(np.array([p.co[:] for p in ob.data.vertices], np.float32), q)
print(json.dumps(dict(status='REJECTED_CAP_NORMAL_RAY_RESTORED',
    reason='Actual high/oblique views show local folds/pits from varying vertex-normal displacement',
    world_sha256=hashlib.sha256(q.tobytes()).hexdigest(), native_saved=False)))
