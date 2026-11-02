"""Preferred final support: two reversible modifiers, no keys or arrays edited."""
from pathlib import Path
import hashlib,json
import bpy,numpy as np
P=Path(__file__).resolve().parent
NAME='Mia.R3.BrowFinalDepthSupport'
OWNERS=['V31_SourceBrow_-1','V31_SourceBrow_1']
def apply():
    target=bpy.data.objects['MIA_V27_SharedHeadBody'];created=[]
    metadata=json.loads((P/'brow-support-metadata.json').read_text())
    for record in metadata['original42_owners']:
        ob=bpy.data.objects[record['name']]
        hh=lambda x,t:hashlib.sha256(np.asarray(x,dtype=t).tobytes()).hexdigest()
        assert hh([[v.co[:] for v in ob.data.shape_keys.key_blocks[n].data] for n in record['key_names']],np.float32)==record['keys_sha256'],'Original42 brow arrays differ'
        assert hh([v.co[:] for v in ob.data.vertices],np.float32)==record['raw_sha256'],'Original brow cache differs'
        assert hh([f.vertices[:] for f in ob.data.polygons],np.int32)==record['faces_sha256'],'Original brow topology differs'
        assert hh([d.uv[:] for d in ob.data.uv_layers['BrowParamUV'].data],np.float32)==record['uv_sha256'],'Original brow UV differs'
        assert not any(k.name.startswith('Mia.R3.BrowAngry.Contact.') for k in ob.data.shape_keys.key_blocks),'Unselected7-field rollback must not be installed with final support'
        assert len([m for m in ob.modifiers if m.type=='ARMATURE'])==1
    for name in OWNERS:
        ob=bpy.data.objects[name]
        assert len(ob.data.vertices)==195 and len(ob.data.polygons)==128
        original=ob.modifiers.get(NAME)
        if original:
            assert ob.modifiers[-1]==original and original.type=='SHRINKWRAP' and original.target==target
            assert original.wrap_method=='PROJECT' and original.wrap_mode=='OUTSIDE'
            assert original.use_project_y and not original.use_project_x and not original.use_project_z
            assert original.use_positive_direction and original.use_negative_direction
            assert abs(original.offset-.0001)<1e-10 and abs(original.project_limit-.002)<1e-10
            continue
        m=ob.modifiers.new(NAME,'SHRINKWRAP');m.target=target
        m.wrap_method='PROJECT';m.wrap_mode='OUTSIDE';m.use_project_x=False;m.use_project_y=True;m.use_project_z=False
        m.use_positive_direction=True;m.use_negative_direction=True;m.cull_face='OFF';m.use_invert_cull=False
        m.project_limit=.002;m.offset=.0001;m.subsurf_levels=0
        created.append(name)
    bpy.context.view_layer.update()
    return dict(created=created,idempotent_noop=not created,scope='Only final two bounded support modifiers after existing artistic morph/HeadFollow; original arrays42/UV/weights/materials preserved',offset_mm=.1,project_limit_mm=2.,head_angle_limit='Projection miss/contact tests bound acceptance; not all head angles',opens_or_saves_scene=False)

def remove():
    for name in OWNERS:
        ob=bpy.data.objects[name]
        if ob.modifiers.get(NAME):ob.modifiers.remove(ob.modifiers[NAME])
    bpy.context.view_layer.update()
