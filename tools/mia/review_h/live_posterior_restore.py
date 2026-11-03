"""Restore rejected posterior patch and unadopted normal diagnostic to D."""
import hashlib
import json
import bpy
import numpy as np
ob = bpy.data.objects['MIA_Review12_H_LiveRepair']; ns = bpy.app.driver_namespace
v = np.array([p.co[:] for p in ob.data.vertices], np.float32)
assert np.array_equal(v, ns['MIA_Live_Posterior_After'])
q = ns['MIA_Live_Posterior_Before']
ob.data.vertices.foreach_set('co', q.ravel())
ob.data.normals_split_custom_set(ns['MIA_Live_CutShade_BeforeInput'].reshape(-1, 3).tolist())
ob.data.update(); bpy.context.view_layer.update()
assert np.array_equal(q, np.array([p.co[:] for p in ob.data.vertices], np.float32))
print(json.dumps(dict(status='RESTORED_D_COORDINATES_AND_ORIGINAL_NORMAL_INPUT',
    world_sha256=hashlib.sha256(q.tobytes()).hexdigest(),
    reason='Posterior patch actual back still shows an artificial circular depression; normal-only cut probe remains diagnostic',
    native_saved=False)))
