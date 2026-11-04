"""Restore the exact original D Mesh pointer after the one AP-profile trial."""
from pathlib import Path
import importlib.util
import json

spec = importlib.util.spec_from_file_location('mia_ap_profile01_restore', Path(__file__).with_name('ap_profile01.py'))
helpers = importlib.util.module_from_spec(spec); helpers.MIA_AP_PROFILE01_NO_MAIN = True
spec.loader.exec_module(helpers)
ns = helpers.bpy.app.driver_namespace; state = ns[helpers.KEY]; body = state['body_object']
expected = state['after_mesh'] if state['after_mesh'] is not None else state['before_mesh']
assert body.mode == 'OBJECT' and body.data == expected
expected_sha = state['report']['candidate_sha256'] if state['after_mesh'] is not None else helpers.BASE
assert helpers.sha(helpers.xyz(body.data)) == expected_sha, 'Do not overwrite another edit'
receipt = helpers.OUT/'restore.json'; assert not receipt.exists()
helpers.restore_checkpoint(state); del ns[helpers.KEY]
report = dict(status='Exact original D69d4 Mesh pointer restored', world_sha256=helpers.BASE,
              original_custom_normal_storage_UV_topology_groups_restored=True,
              only_owned_overlay_and_trial_mesh_removed=True, context_restored=True,
              native_saved=False, art_accepted=False)
receipt.write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
print(json.dumps(report))
