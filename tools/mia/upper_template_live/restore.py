"""Restore the exact original D mesh pointer after template03 review."""
from pathlib import Path
import hashlib
import json

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'.mia-cache/body-h/shape/assembly/template03'
KEY = 'MIA_UpperTemplate03'


def digest(mesh):
    values = np.empty((len(mesh.vertices), 3), np.float32)
    mesh.vertices.foreach_get('co', values.ravel())
    return hashlib.sha256(values.tobytes()).hexdigest()


state = bpy.app.driver_namespace[KEY]; body = state['body_object']
assert body.mode == 'OBJECT' and body.data == state['after_mesh']
assert digest(body.data) == state['report']['candidate_sha256'], 'Do not overwrite another edit'
receipt = OUT/'live-restore.json'; assert not receipt.exists(), 'Immutable restore receipt exists'
body.data = state['before_mesh']
for slot, (link, material) in zip(body.material_slots, state['before_material_slots']):
    slot.link = link; slot.material = material
bpy.context.view_layer.update()
sha = digest(body.data)
assert sha == state['report']['before_sha256']
after, gray = state['after_mesh'], state['gray_material']
del bpy.app.driver_namespace[KEY]
if after.users == 0: bpy.data.meshes.remove(after)
if gray.users == 0: bpy.data.materials.remove(gray)
report = dict(status='Exact D69d4 mesh pointer restored', world_sha256=sha,
              original_material_slot_links_restored=True, native_saved=False, art_accepted=False)
receipt.write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
print(json.dumps(report))
