"""Undo only this bundle's explicit Main key; original coordinates remain untouched."""
import bpy
import numpy as np
import json
ob=bpy.data.objects['MIA_V17_PIXAL_DetailedHair']
state=bpy.app.driver_namespace['MIA_HairForelockBend01']
if bpy.context.mode!='OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
assert np.array_equal(np.array([v.co[:] for v in ob.data.vertices],np.float32),state['before'])
key=ob.data.shape_keys.key_blocks.get('Mia.Live.ForelockBend01') if ob.data.shape_keys else None
if key is not None: ob.shape_key_remove(key)
if state['created_basis'] and ob.data.shape_keys:
    assert len(ob.data.shape_keys.key_blocks)==1
    ob.shape_key_remove(ob.data.shape_keys.key_blocks[0])
for v,s in zip(ob.data.vertices,state['vertex_selection']): v.select=bool(s)
bpy.context.view_layer.update()
print(json.dumps(dict(only_own_key_removed=True, original_Main_raw_exact=True,
                     keys_restored_to_none=ob.data.shape_keys is None,native_saved=False)))
