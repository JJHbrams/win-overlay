"""Restore the exact D69d4 body after the neck-contour02 visual review."""
from pathlib import Path
import hashlib
import json

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / '.mia-cache/body-h/live/neck-contour02'
SOURCE = ROOT / '.mia-cache/body-h/shape/assembly/live-D/geometry.npz'
BODY_NAME = 'MIA_Review12_H_LiveRepair'
KEY = 'MIA_NeckContour02'
GROUP = 'MIA_NeckContour02_Selected'
BASE_SHA = '69d4d4f0ea907da2474bc74f4b55312971d137f0911bdf9089fc02509a6bf25a'


def digest(values):
    return hashlib.sha256(np.ascontiguousarray(values, dtype=np.float32).tobytes()).hexdigest()


def coordinates(ob):
    values = np.empty((len(ob.data.vertices), 3), np.float32)
    ob.data.vertices.foreach_get('co', values.ravel())
    return values


assert globals().get('MIA_EDIT_PHASE', 'restore') == 'restore'
receipt = OUT / 'neck-contour02-restore.json'
assert not receipt.exists(), 'Immutable restore receipt already exists'
ob = bpy.data.objects[BODY_NAME]
assert ob.mode == 'OBJECT'
state = bpy.app.driver_namespace[KEY]
current = coordinates(ob)
assert digest(current) == digest(state['after']), 'Refuse to restore over an unrelated live edit'
baseline = np.load(SOURCE)['world'].astype(np.float32)
assert digest(baseline) == BASE_SHA and np.array_equal(baseline, state['before'])
ob.data.vertices.foreach_set('co', baseline.ravel())
ob.data.update(); bpy.context.view_layer.update()
assert digest(coordinates(ob)) == BASE_SHA
group = ob.vertex_groups.get(GROUP)
if group is not None:
    ob.vertex_groups.remove(group)
del bpy.app.driver_namespace[KEY]
report = dict(state['report'], phase='restore', actual_live_geometry=True,
              geometry_world_sha256=BASE_SHA, retained_as_working_sculpt=False,
              restored_exact_D69d4=True)
receipt.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
print(json.dumps(report))
