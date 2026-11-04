"""Render the actual live body in an isolated gray review scene, then remove it.

Reuses the current review fixture. Object material overrides leave the working
mesh/materials and visible user's scene unchanged; this never saves a native.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import re
import sys

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'asset/mia/blender/mia-fit-v003/body/surface-review12'))
import review_fixture as fixture

phase = globals().get('MIA_EDIT_PHASE', 'select')
label = {'select': 'before', 'apply': 'after'}[phase]
trial = globals().get('MIA_BODY_REVIEW_ID', 'neck-contour02')
state_key = globals().get('MIA_BODY_REVIEW_KEY', 'MIA_NeckContour02')
assert re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', trial)
out = ROOT/'.mia-cache/body-h/live'/trial/(label+'-v2')
assert not out.exists(), 'Do not overwrite a frozen review'
spec = importlib.util.spec_from_file_location('contour_capacity', ROOT/'asset/mia/blender/mia-fit-v003/integration/workspace-storage-20261103/storage_guard.py')
guard = importlib.util.module_from_spec(spec); spec.loader.exec_module(guard)
assert not guard.inspect(64*1024**2)['violations']
source = bpy.context.scene
body = bpy.data.objects['MIA_Review12_H_LiveRepair']
assert body.mode == 'OBJECT'
digest = lambda a: hashlib.sha256(np.asarray(a, np.float32).tobytes()).hexdigest()
coords = np.array([v.co[:] for v in body.data.vertices], np.float32)
expected = ('69d4d4f0ea907da2474bc74f4b55312971d137f0911bdf9089fc02509a6bf25a'
            if label == 'before' else bpy.app.driver_namespace[state_key]['report']['candidate_sha256'])
active_digest = digest(coords)
review_coords = coords
if label == 'before' and active_digest != expected:
    state = bpy.app.driver_namespace[state_key]
    assert active_digest == state['report']['candidate_sha256']
    review_coords = (state['before'] if 'before' in state else
                     np.array([v.co[:] for v in state['before_mesh'].vertices], np.float32))
assert digest(review_coords) == expected
original_slots = [(slot.link, slot.material.name if slot.material else None) for slot in body.material_slots]
scene = bpy.data.scenes.new('MIA_Contour02_TemporaryReview')
created = []
gray = bpy.data.materials.new('MIA_Contour02_Gray'); gray.use_nodes = True
bsdf = next(n for n in gray.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
bsdf.inputs['Base Color'].default_value = (.23, .23, .23, 1)
bsdf.inputs['Roughness'].default_value = .85
bsdf.inputs['Metallic'].default_value = 0
camera_data = None
private_mesh = None
window = bpy.context.window
assert window is not None and window.scene == source
try:
    actor = body.copy(); created.append(actor); scene.collection.objects.link(actor)
    if label == 'before' and active_digest != expected:
        state = bpy.app.driver_namespace[state_key]
        private_mesh = state.get('before_mesh', body.data).copy(); actor.data = private_mesh
        private_mesh.vertices.foreach_set('co', review_coords.ravel()); private_mesh.update()
        assert digest(np.array([v.co[:] for v in private_mesh.vertices], np.float32)) == expected
    actor.hide_render = False; actor.hide_viewport = False
    for slot in actor.material_slots:
        slot.link = 'OBJECT'; slot.material = gray
    camera = source.camera.copy(); camera_data = source.camera.data.copy(); camera.data = camera_data
    created.append(camera); scene.collection.objects.link(camera); scene.camera = camera
    camera.data.type = 'ORTHO'; camera.data.clip_start = .1; camera.data.clip_end = 10
    for name in ['MIA12_Review_Key', 'MIA12_Review_Fill', 'MIA12_Review_Rim']:
        lamp = bpy.data.objects[name].copy(); created.append(lamp); scene.collection.objects.link(lamp)
        lamp.hide_render = False
    scene.world = source.world
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_percentage = 100
    scene.render.pixel_aspect_x = scene.render.pixel_aspect_y = 1
    scene.render.image_settings.file_format = 'PNG'; scene.render.film_transparent = False
    for name in ['view_transform', 'look', 'exposure', 'gamma']:
        setattr(scene.view_settings, name, getattr(source.view_settings, name))
    scene.frame_set(source.frame_current)
    # A private scene's camera matrix is not refreshed by updating a different
    # window's dependency graph. Activate it for fixture.aim/record/render, then
    # restore the user's scene before removing this temporary scene.
    window.scene = scene; bpy.context.view_layer.update()
    jobs = [('front', 0, 0), ('profile', 90, 0), ('back', 180, 0),
            ('oblique', 30, 0), ('opposite', -30, 0), ('high', 40, 25), ('low', -40, -25)]
    record = dict(scope='Actual live geometry; isolated gray object-material override; no native or ART promotion',
                  phase=label, world_sha256=expected, active_live_sha256=active_digest, native=bpy.data.filepath,
                  baseline_replay='Exact preserved actual pre-edit coordinates on temporary mesh copy' if private_mesh else None,
                  original_pose=fixture.pose(source), original_slots=original_slots,
                  source_reference='asset/mia/references/body-foundation/v06/mia-body-visibility-guide-v06.png',
                  source_camera_limit='Nominal source-view estimates; opposite/high/low diagnose continuity, not calibrated drawing cameras',
                  hair=False, frames=[])
    out.mkdir(parents=True)
    for name, yaw, pitch in jobs:
        target, scale, resolution = (fixture.FULL_TARGET, fixture.FULL_SCALE, fixture.FULL_RES)
        if name in ['high', 'low']:
            target, scale, resolution = ((0, -.015, 1.385), .46, (800, 800))
        fixture.aim(scene, yaw, pitch, target, scale, resolution)
        path = out/(name+'.png'); scene.render.filepath = str(path)
        actual = fixture.record(scene)
        assert digest(np.array([v.co[:] for v in body.data.vertices], np.float32)) == active_digest
        bpy.ops.render.render(write_still=True, scene=scene.name)
        record['frames'].append(dict(name=name, yaw=yaw, pitch=pitch, path=str(path), sha256=fixture.sha(path), fixture=actual))
        (out/'capture.json').write_text(json.dumps(record, indent=2)+'\n', encoding='utf8')
    assert original_slots == [(slot.link, slot.material.name if slot.material else None) for slot in body.material_slots]
finally:
    window.scene = source
    for actor in created:
        bpy.data.objects.remove(actor, do_unlink=True)
    bpy.data.scenes.remove(scene)
    if private_mesh: bpy.data.meshes.remove(private_mesh)
    if camera_data: bpy.data.cameras.remove(camera_data)
    bpy.data.materials.remove(gray)
assert digest(np.array([v.co[:] for v in body.data.vertices], np.float32)) == active_digest
print(json.dumps(dict(actual=label, frames=len(record['frames']), world_sha256=expected,
                      output=str(out), original_scene_and_slots_held=True, native_saved=False)))
