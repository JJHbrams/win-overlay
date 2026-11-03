"""Live-only reversible hair diagnostic setup; preserves the frozen body-D mesh."""
from pathlib import Path
import hashlib
import json
import sys
import bpy
import numpy as np

ROOT = Path('D:/MiaWorkCache/mia-reference-work/win-overlay')
sys.path.insert(0, str(ROOT/'asset/mia/blender/mia-fit-v003/body/surface-review12'))
import review_fixture as fixture

body = bpy.data.objects['MIA_Review12_H_LiveRepair']
coords = np.array([v.co[:] for v in body.data.vertices], np.float32)
assert hashlib.sha256(coords.tobytes()).hexdigest() == '69d4d4f0ea907da2474bc74f4b55312971d137f0911bdf9089fc02509a6bf25a'
ns = bpy.app.driver_namespace
assert 'MIA_HairReviewState' not in ns
scene = bpy.context.scene
assert bpy.context.mode == 'OBJECT'
cam = scene.camera
state = dict(body_sha256=hashlib.sha256(coords.tobytes()).hexdigest(),
             camera=cam, camera_matrix=cam.matrix_world.copy(), camera_scale=cam.data.ortho_scale,
             camera_target=list(cam.get('MIA12_target_world', [])),
             resolution=(scene.render.resolution_x, scene.render.resolution_y),
             objects={o.name: (o.hide_get(), o.hide_render, o.select_get()) for o in scene.objects},
             active=bpy.context.view_layer.objects.active,
             viewport=[])
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type != 'VIEW_3D': continue
        s = area.spaces.active
        state['viewport'].append((s, s.shading.type, s.shading.color_type, s.overlay.show_overlays,
                                  s.region_3d.view_location.copy(), s.region_3d.view_rotation.copy(),
                                  s.region_3d.view_distance, s.region_3d.view_perspective))
fixture.hair_visibility(scene, True)
active_hair = []
for ob in fixture.hair_actors(scene):
    if not ob.hide_render:
        ob.hide_set(False)
        if ob.visible_get(): active_hair.append(ob.name)
for ob in bpy.context.selected_objects: ob.select_set(False)
bpy.context.view_layer.update()
ns['MIA_HairReviewState'] = state
out = ROOT/'.mia-cache/face-live/live'
out.mkdir(parents=True, exist_ok=True)
report = dict(scope='ACTUAL live hair diagnostic, no sculpture edit', active_hair=active_hair,
              body_sha256=state['body_sha256'], filepath=bpy.data.filepath,
              native_saved=False, geometry_modified=False, ART=False)
(out/'entry.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
print(json.dumps(report))
