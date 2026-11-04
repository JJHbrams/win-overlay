"""Exact guarded geometry-only rollback of the six-lock emergence trial."""
from pathlib import Path
import json
import runpy

import bpy

library = runpy.run_path(str(Path(__file__).with_name('rear_root01.py')),
                       init_globals={'MIA_REAR_ROOT01_LIBRARY_ONLY': True})
KEY, OUT = library['KEY'], library['OUT']
assert bpy.context.mode == 'OBJECT'
state = bpy.app.driver_namespace[KEY]
assert not (OUT/'restore.json').exists(), 'Immutable restoration receipt exists'
h = library['helper'](); fingerprint = h['fingerprint']
actors = [bpy.data.objects[name] for name in state['actor_names']]
assert state['after_fingerprints'] == {ob.name:fingerprint(ob) for ob in actors}, 'Unexpected later hair edit'
assert state['before_slots'] == {ob.name:h['slots'](ob) for ob in actors}
assert h['shader_signature'](state['look']) == state['look_signature']
assert library['file_sha'](OUT/'delta.npz') == state['report']['delta_sha256']
body = bpy.data.objects['MIA_Review12_H_LiveRepair']
body_data, body_before = body.data, fingerprint(body)
for name, rec in state['records'].items():
    ob = bpy.data.objects[name]
    ob.data.vertices.foreach_set('co', rec['before'].ravel()); ob.data.update()
bpy.context.view_layer.update()
assert state['before_fingerprints'] == {ob.name:fingerprint(ob) for ob in actors}, 'Exact restoration differs'
assert body.data == body_data and fingerprint(body) == body_before
assert state['before_slots'] == {ob.name:h['slots'](ob) for ob in actors}
assert h['shader_signature'](state['look']) == state['look_signature']
del bpy.app.driver_namespace[KEY]
report = dict(status='EXACT_SIX_REAR_ROOT_GEOMETRY_RESTORED', actor_geometry_UV_normals_exact=True,
              materials_and_other_actors_held=True, body_unchanged=True,
              body_sha256=body_before['coordinates'], native_saved=False, ART=False)
with (OUT/'restore.json').open('x', encoding='utf8') as stream:
    stream.write(json.dumps(report, indent=2)+'\n')
print(json.dumps(report))
