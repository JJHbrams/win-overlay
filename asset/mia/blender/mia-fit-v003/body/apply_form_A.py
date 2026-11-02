"""Add one explicit always-on body base correction; no open/save/material replay."""
from pathlib import Path
import bpy,numpy as np
P=Path(__file__).resolve().parent;OWNER='MIA_V27_SharedHeadBody';KEY='Mia.v003.SupportedBody.FormA'
def apply():
    d=np.load(P/'form-A-delta.npz');ob=bpy.data.objects[OWNER];me=ob.data;keys=me.shape_keys.key_blocks;ids=d['indices'];basis=np.asarray([v.co[:] for v in keys['Basis'].data],np.float32)
    assert len(me.vertices)==4647 and ids.max()<3957
    assert np.array_equal(basis[ids],d['baseline_selected']),'Current body ROI differs; do not overwrite another body correction'
    target=basis.copy();target[ids]+=d['local_delta'];assert np.array_equal(target[3957:],basis[3957:])
    if KEY in keys:
        current=np.asarray([v.co[:] for v in keys[KEY].data],np.float32);assert np.array_equal(current,target)
        return dict(idempotent=True,key=KEY,changed_controls=len(ids))
    active=ob.active_shape_key_index
    key=ob.shape_key_add(name=KEY,from_mix=False);key.value=0.;key.relative_key=keys['Basis'];key.data.foreach_set('co',target.ravel())
    # This is deliberately an always-on base correction, not an accidental
    # default1 expression. Original47/other new eye keys remain untouched.
    key.value=1.;driver=key.driver_add('value').driver;driver.type='SCRIPTED';driver.expression='1.0'
    ob.active_shape_key_index=active;bpy.context.view_layer.update()
    return dict(idempotent=False,key=KEY,value=key.value,driver='constant1 base correction',changed_controls=len(ids),face690_delta_zero=True,opens_or_saves_scene=False,original_keys_not_rewritten=True,material_UV_weights_not_changed=True)
def disable():
    key=bpy.data.objects[OWNER].data.shape_keys.key_blocks.get(KEY)
    if key:key.mute=True;bpy.context.view_layer.update()
