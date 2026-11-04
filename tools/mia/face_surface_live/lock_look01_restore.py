"""Restore only the owned lock-look01 material assignment, refusing later edits."""
from pathlib import Path
import importlib.util
import json

import bpy

path = Path(__file__).with_name('lock_look01.py')
spec = importlib.util.spec_from_file_location('mia_lock_look01_readback', path)
helper = importlib.util.module_from_spec(spec); helper.MIA_LOCK_LOOK01_LIBRARY_ONLY = True
spec.loader.exec_module(helper)

assert globals().get('MIA_EDIT_PHASE', 'restore') == 'restore'
receipt = helper.OUT/'restore.json'; assert not receipt.exists()
namespace = bpy.app.driver_namespace; state = namespace[helper.KEY]
material = state['material']
assert helper.array_sha(helper.coordinates(bpy.data.objects['MIA_Review12_H_LiveRepair'])) == state['body_sha256']
assert helper.file_sha(state['native']) == state['native_sha256']
assert state['fingerprints'] == {name: helper.fingerprint(bpy.data.objects[name]) for name in state['fingerprints']}, 'Geometry/UV changed after look installation'
for name, previous in state['previous'].items():
    slot = bpy.data.objects[name].material_slots[0]
    assert slot.link == previous['link'] and slot.material == material, 'Refuse to replace an unrelated material edit: '+name
for name, expected in state['before_slots'].items():
    if name not in state['previous']: assert helper.slots(bpy.data.objects[name]) == expected
rear = namespace['MIA_CurvedRear03Base']
assert [ob.name for ob in rear['objects']] == state['actor_names']
assert sum(item == material for item in rear['materials']) == 1

for name, previous in state['previous'].items():
    bpy.data.objects[name].material_slots[0].material = previous['material']
bpy.context.view_layer.update()
assert state['before_slots'] == {name: helper.slots(bpy.data.objects[name]) for name in state['before_slots']}
assert state['fingerprints'] == {name: helper.fingerprint(bpy.data.objects[name]) for name in state['fingerprints']}
assert material.users == 0, 'Owned material still has an undeclared user; do not remove it'
rear['materials'].remove(material); bpy.data.materials.remove(material)
del namespace[helper.KEY]
report = dict(status='RESTORED_ORIGINAL_18_LOCK_MATERIALS', actors=len(state['previous']),
              geometry_UV_normals_and_transforms_unchanged=True, original_material_links_exact=True,
              body_sha256=state['body_sha256'], native_saved=False, ART=False)
receipt.write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
print(json.dumps(report))
