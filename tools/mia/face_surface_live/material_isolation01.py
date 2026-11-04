"""Matched current Main look / pigment / constant emission diagnostics only.

The original shader is never edited. A temporary OBJECT material override and
private camera are removed in finally. This is neither paint nor an ART pass.
"""
from pathlib import Path
import hashlib
import json
import runpy
import sys

import bpy
import numpy as np
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'.mia-cache/face-live/material-isolation01'
assert not OUT.exists(), 'Keep diagnostic evidence immutable'
assert 'MIA_HairReviewState' in bpy.app.driver_namespace
h = runpy.run_path(str(Path(__file__).with_name('lock_look01.py')),
                  init_globals={'MIA_LOCK_LOOK01_LIBRARY_ONLY': True})
sys.path.insert(0, str(ROOT/'asset/mia/blender/mia-fit-v003/body/surface-review12'))
import review_fixture as fixture

scene = bpy.context.scene
remaining = bpy.data.objects['MIA_Hair_CurvedRear03Base_RemainingMain']
raw = bpy.data.objects['MIA_V17_PIXAL_DetailedHair']
assert raw.hide_render and not remaining.hide_render
assert remaining.data != raw.data, 'Never modify the raw shared source data'
parts = list(bpy.app.driver_namespace['MIA_CurvedRear03Base']['objects'])+[raw]
fingerprints = {ob.name:h['fingerprint'](ob) for ob in parts}
old_slot = (remaining.material_slots[0].link, remaining.material_slots[0].material)
original = old_slot[1]
assert original.name == 'MIA_v002_R_SideNape_SourceAshEnvelope'
original_graph = h['shader_signature'](original)
body = bpy.data.objects['MIA_Review12_H_LiveRepair']
body_data = body.data
body_sha = lambda: hashlib.sha256(np.asarray([v.co[:] for v in body.data.vertices], np.float32).tobytes()).hexdigest()
before_body = body_sha()
source_camera = scene.camera
original_render = {key:getattr(scene.render, key) for key in ('resolution_x', 'resolution_y', 'resolution_percentage', 'filepath')}
source = json.loads((ROOT/'.mia-cache/face-live/fringe-resume01/capture-v2.json').read_text())
views = {row['view']:row['fixture'] for row in source['frames'] if row['view'] in ('front', 'oblique')}
assert set(views) == {'front', 'oblique'}
copy = original.copy(); copy.name = 'MIA_TMP_MainColorIsolation01'
camera = source_camera.copy(); camera.data = source_camera.data.copy()
camera_data = camera.data
scene.collection.objects.link(camera)
OUT.mkdir(parents=True)
record = dict(scope='Current matched material-isolation only; not final maps/paint/ART',
              body_sha256=before_body, original_material=original.name,
              pigment_node='V002_SOURCE_ASH_GRADE_OUTPUT', frames=[])
try:
    nodes = copy.node_tree.nodes; links = copy.node_tree.links
    output = [n for n in nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output and n.target in ('ALL', 'EEVEE')]
    assert len(output) == 1
    pigment = nodes['V002_SOURCE_ASH_GRADE_OUTPUT'].outputs['Color']
    emission = nodes.new('ShaderNodeEmission'); emission.inputs['Strength'].default_value = 1
    links.new(emission.outputs[0], output[0].inputs['Surface'])
    scene.camera = camera
    scene.render.resolution_percentage = 100
    for view, saved in views.items():
        camera.data.type = 'ORTHO'; camera.data.ortho_scale = saved['ortho_scale']
        camera.data.clip_start, camera.data.clip_end = saved['clip']
        camera.matrix_world = Matrix(saved['camera_matrix'])
        camera['MIA12_target_world'] = saved['target_world']
        scene.render.resolution_x, scene.render.resolution_y = saved['resolution']
        bpy.context.view_layer.update(); frozen = fixture.record(scene)
        for phase in ('target', 'pigment', 'constant'):
            if phase == 'target':
                remaining.material_slots[0].link = old_slot[0]
                remaining.material_slots[0].material = original
            else:
                remaining.material_slots[0].link = 'OBJECT'
                remaining.material_slots[0].material = copy
                for link in list(emission.inputs['Color'].links): links.remove(link)
                if phase == 'pigment': links.new(pigment, emission.inputs['Color'])
                else: emission.inputs['Color'].default_value = (.15, .13, .12, 1)
            bpy.context.view_layer.update()
            actual = fixture.record(scene); assert actual == frozen
            path = OUT/(view+'-'+phase+'.png'); scene.render.filepath = str(path)
            bpy.ops.render.render(write_still=True)
            record['frames'].append(dict(view=view, phase=phase, path=str(path), sha256=fixture.sha(path), fixture=actual))
finally:
    remaining.material_slots[0].link = old_slot[0]
    remaining.material_slots[0].material = original
    scene.camera = source_camera
    for key, value in original_render.items(): setattr(scene.render, key, value)
    bpy.data.objects.remove(camera, do_unlink=True)
    bpy.data.cameras.remove(camera_data)
    if copy.users == 0: bpy.data.materials.remove(copy)
    bpy.context.view_layer.update()
assert fingerprints == {ob.name:h['fingerprint'](ob) for ob in parts}
assert h['shader_signature'](original) == original_graph
assert body.data == body_data and body_sha() == before_body
record.update(original_slots_graph_geometry_restored=True, body_held=True, native_saved=False, art_accepted=False)
(OUT/'capture.json').write_text(json.dumps(record, indent=2)+'\n', encoding='utf8')
print(json.dumps(dict(actual_frames=len(record['frames']), output=str(OUT), original_slots_graph_geometry_restored=True,
                      body_held=True, native_saved=False, art_accepted=False)))
