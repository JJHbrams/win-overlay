"""Restore chart diagnostic to the cleaner D repair baseline."""
import hashlib
import json
import bpy
import numpy as np
ob = bpy.data.objects['MIA_Review12_H_LiveRepair']; ns = bpy.app.driver_namespace
v = np.array([p.co[:] for p in ob.data.vertices], np.float32)
assert np.array_equal(v, ns['MIA_Live_CapChart_After'])
q = ns['MIA_Live_CapChart_Before']
ob.data.vertices.foreach_set('co', q.ravel()); ob.data.update(); bpy.context.view_layer.update()
print(json.dumps(dict(status='CAP_CHART_DIAGNOSTIC_RESTORED_TO_D', world_sha256=hashlib.sha256(q.tobytes()).hexdigest(),
    reason='Independent actual high/oblique review rejects scalloped V termination; posterior leaf was outside mask', native_saved=False)))
