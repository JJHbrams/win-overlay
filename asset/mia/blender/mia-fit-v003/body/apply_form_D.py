"""Standalone current-scene body field + declared56-bone paired rest delta.
Original keys/weights/UV stay untouched. No scene open/save or old scene replay.
"""
from pathlib import Path
import json
import bpy,numpy as np
from mathutils import Vector
P=Path(__file__).resolve().parent;OWNER='MIA_V27_SharedHeadBody';KEY='Mia.v003.SupportedBody.FormD'
def apply():
    d=np.load(P/'form-D-delta.npz');r=json.loads((P/'form-D-rest-delta.json').read_text());ob=bpy.data.objects[OWNER];rig=bpy.data.objects[r['owner']];me=ob.data;keys=me.shape_keys.key_blocks;ids=d['indices'];basis=np.asarray([v.co[:] for v in keys['Basis'].data],np.float32)
    assert len(me.vertices)==4647 and ids.max()<3957;assert np.array_equal(basis[ids],d['baseline_selected']),'Current body ROI differs';assert np.array_equal(np.asarray(rig.matrix_world),np.asarray(r['baseline_matrix_world']))
    assert not any(k.name.startswith('Mia.v003.SupportedBody.') and k.name!=KEY and k.value and not k.mute for k in keys),'Do not stack rejected body variants'
    target=basis.copy();target[ids]+=d['local_delta'];assert np.array_equal(target[3957:],basis[3957:])
    state='target' if KEY in keys else 'baseline'
    for item in r['bones']:
        b=rig.data.bones[item['name']];assert np.allclose(b.head_local,item[state+'_head'],rtol=0,atol=2e-7) and np.allclose(b.tail_local,item[state+'_tail'],rtol=0,atol=2e-7),('Unexpected rest bone',item['name'])
    if KEY in keys:
        assert np.array_equal(np.asarray([v.co[:] for v in keys[KEY].data],np.float32),target);return dict(idempotent=True,key=KEY,rest_bones=len(r['bones']))
    assert bpy.context.mode=='OBJECT';oldactive=bpy.context.view_layer.objects.active;selected=list(bpy.context.selected_objects);hidden=rig.hide_get();rig.hide_set(False)
    for x in selected:x.select_set(False)
    rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
    for item in r['bones']:
        b=rig.data.edit_bones[item['name']];b.head=Vector(item['target_head']);b.tail=Vector(item['target_tail'])
    bpy.ops.object.mode_set(mode='OBJECT');rig.select_set(False);rig.hide_set(hidden)
    for x in selected:x.select_set(True)
    bpy.context.view_layer.objects.active=oldactive
    active=ob.active_shape_key_index;k=ob.shape_key_add(name=KEY,from_mix=False);k.value=0.;k.relative_key=keys['Basis'];k.data.foreach_set('co',target.ravel());k.value=1.;dr=k.driver_add('value').driver;dr.type='SCRIPTED';dr.expression='1.0';ob.active_shape_key_index=active;bpy.context.view_layer.update()
    return dict(idempotent=False,key=KEY,value=k.value,driver='1.0 intentional neutral base correction',changed_controls=len(ids),paired_rest_bones=len(r['bones']),Face690_delta_zero=True,original_keys_weights_UV_unchanged=True,scene_open_save=False)
