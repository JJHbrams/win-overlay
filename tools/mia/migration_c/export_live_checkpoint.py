"""Save the current unaccepted static Mia study once for the D-to-C handoff."""
from pathlib import Path
import hashlib
import json
import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'.mia-cache/migration-to-C'
NATIVE = OUT/'Mia_Current_STATIC_WIP.blend'
assert not NATIVE.exists()
ns = bpy.app.driver_namespace
body = bpy.data.objects['MIA_Review12_H_LiveRepair']
sha = lambda ob: hashlib.sha256(np.array([v.co[:] for v in ob.data.vertices], np.float32).tobytes()).hexdigest()
assert sha(body) == '69d4d4f0ea907da2474bc74f4b55312971d137f0911bdf9089fc02509a6bf25a'
external = [im.name for im in bpy.data.images if im.source in {'FILE','TILED','MOVIE','SEQUENCE'} and not im.packed_file and not len(im.packed_files)]
assert not external and not len(bpy.data.libraries) and not len(bpy.data.cache_files), external
rear = ns['MIA_CurvedRear03Base']
assert rear['provisional_keep'] and len(rear['objects']) == 19
runtime = {}
for name in ('objects','meshes','groups','materials'):
    runtime[name] = [item.name for item in rear[name]]
for name in ('source_visibility','source_raw_sha256','source_fixture_flag_before_keep','provisional_keep'):
    runtime[name] = rear[name]
np.savez_compressed(OUT/'row-ownership.npz', **ns['MIA_Live_H_Rows'])
payload = Path(ns['MIA_Live_H_Payload'])
old_root = Path('D:/MiaWorkCache/mia-reference-work/win-overlay')
payload = ROOT/payload.relative_to(old_root)
assert payload.is_dir()
scene = bpy.context.scene
record = dict(status='STATIC WIP migration only; source anatomy/hair ART remains unfinished',
              canonical_root=str(ROOT), body_sha256=sha(body), rear=runtime,
              actor_geometry={o.name:sha(o) for o in [body,*rear['objects'],bpy.data.objects['MIA_V17_PIXAL_DetailedHair']]},
              visibility={o.name:[o.hide_get(),o.hide_render] for o in scene.objects},
              camera_name=scene.camera.name, camera_matrix=[list(row) for row in scene.camera.matrix_world],
              frame=scene.frame_current, live_payload=str(payload), external_images=external,
              all_images=len(bpy.data.images), native=str(NATIVE), art_approved=False)
scene['MIA_canonical_worktree'] = str(ROOT)
scene['MIA_runtime_manifest'] = str(OUT/'runtime.json')
scene.render.filepath = str(OUT/'render')
(OUT/'runtime.json').write_text(json.dumps(record, indent=2)+'\n', encoding='utf8')
bpy.ops.wm.save_as_mainfile(filepath=str(NATIVE), compress=True, check_existing=False, relative_remap=False)
assert NATIVE.is_file() and sha(body) == record['body_sha256']
record['native_sha256'] = hashlib.sha256(NATIVE.read_bytes()).hexdigest()
record['native_bytes'] = NATIVE.stat().st_size
(OUT/'runtime.json').write_text(json.dumps(record, indent=2)+'\n', encoding='utf8')
print(json.dumps(dict(saved=str(NATIVE),bytes=record['native_bytes'],sha256=record['native_sha256'],body_sha256=record['body_sha256'],rear_actors=len(rear['objects']),external_images=external,ART=False)))
