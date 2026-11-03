"""Restore the rejected noisy one-step neck-secant proposal exactly."""
import hashlib
import json
import bpy
import numpy as np
ob = bpy.data.objects['MIA_Review12_H_LiveRepair']; ns = bpy.app.driver_namespace
v = np.array([p.co[:] for p in ob.data.vertices], np.float32)
assert np.array_equal(v, ns['MIA_Live_CutTangent_After'])
q = ns['MIA_Live_CutTangent_Before']
ob.data.vertices.foreach_set('co', q.ravel()); ob.data.update(); bpy.context.view_layer.update()
print(json.dumps(dict(status='NOISY_TOP_NECK_SECANT_RESTORED', world_sha256=hashlib.sha256(q.tobytes()).hexdigest(),
    reason='Actual oblique/profile exposed small angular rails from the one-millimetre source secant; no adoption', native_saved=False)))
