"""One supported-body base addition on CURRENT compatible body; no scene replay."""
from pathlib import Path
import bpy,numpy as np
P=Path(__file__).resolve().parent;OWNER='MIA_V27_SharedHeadBody';KEY='Mia.v003.SupportedBody.FormB'
def apply():
    d=np.load(P/'form-B-delta.npz');ob=bpy.data.objects[OWNER];me=ob.data;keys=me.shape_keys.key_blocks;ids=d['indices'];basis=np.asarray([v.co[:] for v in keys['Basis'].data],np.float32)
    assert len(me.vertices)==4647 and ids.max()<3957
    assert not any(k.name.startswith('Mia.v003.SupportedBody.') and k.name!=KEY and k.value and not k.mute for k in keys),'Do not stack unselected body trials'
    assert np.array_equal(basis[ids],d['baseline_selected']),'Current body ROI differs'
    target=basis.copy();target[ids]+=d['local_delta'];assert np.array_equal(target[3957:],basis[3957:])
    if KEY in keys:
        assert np.array_equal(np.asarray([v.co[:] for v in keys[KEY].data],np.float32),target)
        return dict(idempotent=True,key=KEY,changed_controls=len(ids))
    active=ob.active_shape_key_index;key=ob.shape_key_add(name=KEY,from_mix=False);key.value=0.;key.relative_key=keys['Basis'];key.data.foreach_set('co',target.ravel());key.value=1.
    driver=key.driver_add('value').driver;driver.type='SCRIPTED';driver.expression='1.0';ob.active_shape_key_index=active;bpy.context.view_layer.update()
    return dict(idempotent=False,key=KEY,value=key.value,driver='constant1 base correction',changed_controls=len(ids),face690_delta_zero=True,pole_hard_anchors=True,original_keys_not_rewritten=True,material_UV_weights_not_changed=True,opens_or_saves_scene=False)
