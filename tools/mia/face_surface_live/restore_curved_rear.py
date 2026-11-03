"""Exact owned actor rollback for the source-guided curve probe."""
import hashlib
import json
import bpy
import numpy as np
prefix=globals().get('MIA_CURVED_REAR_KEY','MIA_CurvedRear02');state=bpy.app.driver_namespace[prefix];source=bpy.data.objects['MIA_V17_PIXAL_DetailedHair']
assert hashlib.sha256(np.array([v.co[:] for v in source.data.vertices],np.float32).tobytes()).hexdigest()==state['source_raw_sha256']
for ob in state['objects']:bpy.data.objects.remove(ob,do_unlink=True)
for me in state['meshes']:
    if me.users==0:bpy.data.meshes.remove(me)
for group in state['groups']:
    if group.users==0:bpy.data.node_groups.remove(group)
for mat in state['materials']:
    if mat.users==0:bpy.data.materials.remove(mat)
source.hide_set(state['source_visibility'][0]);source.hide_render=state['source_visibility'][1]
bpy.context.view_layer.update();del bpy.app.driver_namespace[prefix]
print(json.dumps(dict(owned_probe_actors_removed=True,source_original_raw_exact=True,native_saved=False)))
