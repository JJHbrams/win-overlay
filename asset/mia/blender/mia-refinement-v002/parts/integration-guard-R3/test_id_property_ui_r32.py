"""Bounded r3.2 UI hard-max observation/restore/fresh-R2 test; no save/GPU."""
from pathlib import Path
import hashlib,json,sys,time
import bpy
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import scene_fingerprint as h
import scene_fingerprint_r31 as old
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
HELPER_SHA=sha(P/'scene_fingerprint.py');OLD_SHA='e282d98bd8db32cdc9a56d444fce41e4cadd4aed10ae53337972f8dfc70c5e29'
assert sha(P/'scene_fingerprint_r31.py')==OLD_SHA
N=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-refinement-v002/integrated/Mia_v0.0.2_Review_R2.blend')
SHA='eed408b82e9a6160377e92e97fe94ce9619a51393e1ec1d4c928f4a4fd498d82';assert sha(N)==SHA
bpy.ops.wm.open_mainfile(filepath=str(N),use_scripts=False);s=bpy.context.scene;s.frame_set(2);s.frame_set(1);bpy.context.view_layer.update();start=time.time()
assert h.FINGERPRINT_VERSION=='mia.scene-fingerprint.r3.2'
baseline=h.snapshot_scene();repeated=h.snapshot_scene();assert repeated==baseline
ctrl=bpy.data.objects['Mia_FacialControls_v002'];ui=ctrl.id_properties_ui('PresetTotal');original_ui=dict(ui.as_dict());assert original_ui['max']==1.
original_value=ctrl['PresetTotal'];original_drivers=h.driver_signature(ctrl)
before=h.object_fingerprint(ctrl);old_before=old.object_fingerprint(ctrl)
try:
    ui.update(max=16.)
    bpy.context.view_layer.update()
    mutated_ui=dict(ui.as_dict());after=h.object_fingerprint(ctrl);old_after=old.object_fingerprint(ctrl)
    changed=sorted(k for k in set(before)|set(after) if before.get(k)!=after.get(k))
    assert changed==['custom_property_ui'],changed
    assert after['custom_property_ui']['object']['PresetTotal']['max']==16.
    assert old_before==old_after,'Old schema unexpectedly sees hard-max-only edit'
    assert ctrl['PresetTotal']==original_value and h.driver_signature(ctrl)==original_drivers
finally:
    ui.update(**original_ui)
    bpy.context.view_layer.update()
assert dict(ui.as_dict())==original_ui
restored=h.snapshot_scene();assert restored==baseline,'Full-scene restoration mismatch'
bpy.ops.wm.open_mainfile(filepath=str(N),use_scripts=False);bpy.context.scene.frame_set(2);bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
fresh=h.snapshot_scene();assert fresh==baseline,'Fresh R2 schema snapshot differs'
assert sha(N)==SHA and sha(P/'scene_fingerprint.py')==HELPER_SHA and sha(P/'scene_fingerprint_r31.py')==OLD_SHA
report=dict(schema=h.FINGERPRINT_VERSION,helper_sha256=HELPER_SHA,frozen_r31_sha256=OLD_SHA,native=str(N),native_sha256=SHA,
    property_owner=ctrl.name if False else 'Mia_FacialControls_v002',property='PresetTotal',original_ui=original_ui,mutated_ui=mutated_ui,
    ui_metadata_changed_keys=sorted(k for k in set(original_ui)|set(mutated_ui) if original_ui.get(k)!=mutated_ui.get(k)),detected_fields=changed,
    r31_does_not_detect_hardmax_edit=old_before==old_after,r32_detects_hardmax_edit=True,property_value_and_drivers_unchanged=True,
    repeated_full_snapshot_equal=True,exact_full_snapshot_restore=True,fresh_reopen_full_snapshot_equal=True,object_count=len(baseline['objects']),
    full_snapshot_sha256=h.json_digest(baseline),r31_bytes_preserved=True,helper_bytes_unchanged_during_test=True,native_saved=False,gpu_used=False,native_unchanged=True,elapsed_seconds=time.time()-start)
(P/'CPU-id-property-ui-r32-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('R32_ID_PROPERTY_UI_GUARD_DONE',changed,len(baseline['objects']),'owners',round(time.time()-start,2),'seconds',flush=True)
