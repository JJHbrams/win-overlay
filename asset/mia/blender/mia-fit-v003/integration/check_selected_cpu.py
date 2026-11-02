"""Actual fresh composition guard; no GPU, no native save or art approval."""
from pathlib import Path
import hashlib,json,sys
import bpy

P=Path(__file__).resolve().parent;B=P.parent.parent
native=B/'mia-refinement-v002/integrated/Mia_v0.0.2_Review_R3b.blend'
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
expected='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'
assert sha(native)==expected
bpy.ops.wm.open_mainfile(filepath=str(native),use_scripts=False)
bpy.context.scene.frame_set(2);bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
sys.path.insert(0,str(P));import compose_selected
fp=compose_selected.module(B/'mia-refinement-v002/scene_fingerprint.py')
before=fp.snapshot_scene();report=compose_selected.apply()
after=fp.snapshot_scene();changed=[]
keys_allowed={'MIA_V27_SharedHeadBody','V28G_InnerLid_1','V30_LowerLashes_1'}
materials_allowed={'MIA_V27_SharedHeadBody','V28G_InnerLid_-1','V28G_InnerLid_1','MIA_V17_PIXAL_DetailedHair'}
for name,old in before['objects'].items():
    new=after['objects'][name]
    allowed=set()
    if name in keys_allowed:allowed.update({'keys','key_state','drivers'})
    if name in materials_allowed:allowed.update({'materials','material_signatures'})
    if name=='MIA_V17_PIXAL_DetailedHair':allowed.add('uv')
    for field,value in old.items():
        if field not in allowed:assert new.get(field)==value,(name,'Undeclared authored-data change',field)
    for field in ['vertices','loop_vertices','polygon_sizes','weight_hash','modifiers','modifier_settings','point_attributes']:
        assert old.get(field)==new.get(field),(name,field)
    for key,value in old.get('keys',{}).items():assert new['keys'][key]==value,(name,key)
    for key,value in old.get('uv',{}).items():assert new['uv'][key]==value,(name,key)
    if set(old.get('keys',{}))!=set(new.get('keys',{})):assert name in keys_allowed
    if old.get('uv')!=new.get('uv'):assert name=='MIA_V17_PIXAL_DetailedHair'
    if old.get('materials')!=new.get('materials'):assert name in materials_allowed
    if old.get('material_signatures'):
        for i,value in enumerate(old['material_signatures']):
            if name in materials_allowed and name!='MIA_V17_PIXAL_DetailedHair' and i==0:continue
            assert new['material_signatures'][i]==value,(name,'Original material graph changed',i)
    if old!=new:changed.append(name)
fp.assert_existing_driver_preservation(before['objects'],after['objects'],{'id':'selected-v003-composition'})
fp.assert_scene_pose_owners_protected(before['objects'],after['objects'],{'id':'selected-v003-composition'})
assert before['scene']==after['scene'],'Selected component changed scene fixture'
assert sha(native)==expected
report.update(original_owners_checked=len(before['objects']),changed_original_owners=changed,
    original_raw_geometry_keys_uv_weights_modifiers_point_fields_exact=True,
    undeclared_original_authored_fields_exact=True,original_material_graphs_held_except_declared_new_copies=True,
    original_driver_pose_camera_light_scene_exact=True,selected_baseline_unchanged=True,
    technical_composition_pass=True,actual_visual_integration_unverified=True)
(P/'selected-components-cpu.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('SELECTED_V003_COMPONENTS_CPU_COMPOSE_PASS',len(before['objects']),changed,flush=True)
