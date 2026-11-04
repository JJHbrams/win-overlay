"""Actual matched close rear views; temporary camera, no native/model mutation.

Run through official live MCP inside the existing borrowed hair review.
MIA_ROOT_REVIEW_PHASE is before or after; each immutable packet is written once.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
phase = globals().get('MIA_ROOT_REVIEW_PHASE', 'before')
assert phase in ('before', 'after')
out = ROOT/'.mia-cache/face-live/rear-root01'/phase
assert not out.exists(), 'Do not overwrite actual review evidence'
assert 'MIA_HairReviewState' in bpy.app.driver_namespace
parts = bpy.app.driver_namespace['MIA_CurvedRear03Base']['objects']
assert len(parts) == 19 and all(not ob.hide_render for ob in parts)
assert bpy.data.objects['MIA_V17_PIXAL_DetailedHair'].hide_render
sys.path.insert(0, str(ROOT/'asset/mia/blender/mia-fit-v003/body/surface-review12'))
import review_fixture as fixture
spec = importlib.util.spec_from_file_location('root_capture_capacity', ROOT/'asset/mia/blender/mia-fit-v003/integration/workspace-storage-20261103/storage_guard.py')
guard = importlib.util.module_from_spec(spec); spec.loader.exec_module(guard)
assert not guard.inspect(16*1024**2)['violations']

def mesh_sha(ob):
    a = np.empty((len(ob.data.vertices), 3), np.float32)
    ob.data.vertices.foreach_get('co', a.ravel())
    return hashlib.sha256(a.tobytes()).hexdigest()

scene = bpy.context.scene
original_camera = scene.camera
camera = original_camera.copy(); camera.data = original_camera.data.copy()
camera_data = camera.data
scene.collection.objects.link(camera)
render_names = ('resolution_x', 'resolution_y', 'resolution_percentage', 'pixel_aspect_x', 'pixel_aspect_y', 'filepath')
render_before = {name: getattr(scene.render, name) for name in render_names}
format_before = scene.render.image_settings.file_format
body = bpy.data.objects['MIA_Review12_H_LiveRepair']
body_sha = mesh_sha(body)
actors = {ob.name: dict(mesh=mesh_sha(ob), matrix=[list(row) for row in ob.matrix_world],
                       materials=[slot.material.name if slot.material else None for slot in ob.material_slots])
          for ob in parts}
native = dict(path=bpy.data.filepath, sha256=fixture.sha(Path(bpy.data.filepath)))
record = dict(phase=phase, native=native, body_sha256=body_sha, actors=actors,
              source='asset/mia/references/mia-clean-master-v22.png',
              limit='Diagnostic rear angles, not recovered drawing cameras or final M2 ART approval', frames=[])
out.mkdir(parents=True)
try:
    scene.camera = camera
    camera.data.type = 'ORTHO'; camera.data.clip_start = .1; camera.data.clip_end = 10
    scene.render.pixel_aspect_x = scene.render.pixel_aspect_y = 1
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    jobs = [('back', 180, 0), ('rear_left', 150, 0), ('rear_right', 210, 0),
            ('rear_high', 150, 25), ('rear_low', 210, -20)]
    for name, yaw, pitch in jobs:
        fixture.aim(scene, yaw, pitch, (0, 0, 1.365), .78, (800, 800))
        path = out/(name+'.png'); scene.render.filepath = str(path)
        actual = fixture.record(scene)
        bpy.ops.render.render(write_still=True)
        record['frames'].append(dict(name=name, path=str(path), sha256=fixture.sha(path), fixture=actual))
        (out/'capture.json').write_text(json.dumps(record, indent=2)+'\n', encoding='utf8')
finally:
    scene.camera = original_camera
    for name, value in render_before.items(): setattr(scene.render, name, value)
    scene.render.image_settings.file_format = format_before
    bpy.data.objects.remove(camera, do_unlink=True)
    bpy.data.cameras.remove(camera_data)
    bpy.context.view_layer.update()
assert mesh_sha(body) == body_sha
assert all(mesh_sha(ob) == actors[ob.name]['mesh'] for ob in parts)
assert fixture.sha(Path(bpy.data.filepath)) == native['sha256']
print(json.dumps(dict(phase=phase, actual_frames=len(record['frames']), output=str(out),
                      body_held=True, native_saved=False, art_accepted=False)))
