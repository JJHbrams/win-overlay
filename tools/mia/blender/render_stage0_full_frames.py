"""Complete full-frame source evidence without resampling source mesh data."""
import importlib.util
import json
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

out = Path(sys.argv[sys.argv.index('--') + 1]).resolve()
helper_path = Path(__file__).with_name('build_mia_stage0_comparison.py')
spec = importlib.util.spec_from_file_location('stage0_helper', helper_path)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
scene = bpy.context.scene
cam = bpy.data.objects['STAGE0_CAMERA']
clay = bpy.data.materials['STAGE0_NEUTRAL_CLAY']
manifest_path = out / 'source-inventory.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
for record in manifest['records']:
    if helper.sha(record['path']) != record['sha256_before']:
        raise RuntimeError('Source hash mismatch: ' + record['id'])
for c in bpy.data.collections:
    if c.name.startswith('CANDIDATE_'):
        c.hide_render = c.hide_viewport = True

for name in ('previous0240', 'latest0416', 'pixal_full'):
    c = bpy.data.collections['CANDIDATE_' + name.upper()]
    c.hide_render = c.hide_viewport = False
    root = bpy.data.objects['PREVIEW_ROOT_' + name]
    original_matrix = root.matrix_world.copy()
    bpy.context.view_layer.update()
    visible_meshes = [o for o in c.all_objects
                      if o.type == 'MESH' and not o.hide_render and not o.hide_viewport]
    lo, hi = helper.bounds(visible_meshes)
    factor = 1.7 / (hi.z - lo.z)
    offset = Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z)) * factor
    root.matrix_world = Matrix.Translation(offset) @ Matrix.Scale(factor, 4) @ original_matrix
    bpy.context.view_layer.update()
    record = next(r for r in manifest['records'] if r['id'] == name)
    record['fullbody_common_frame'] = {
        'visible_height': 1.7, 'sole_z': 0.0, 'ortho_scale': 1.95,
        'root_matrix': [list(row) for row in root.matrix_world],
        'purpose': 'uniform full-silhouette comparison; source poses and shaders remain different',
    }
    files = []
    for view in (('front', 0), ('side', 90), ('back', 180)):
        for clay_pass in (False, True):
            files.append(helper.render(scene, cam, out, name + '_full',
                                       Vector((0, 0, .85)), 1.95, clay, clay_pass, view))
    record['fullbody_common_evidence'] = files
    root.matrix_world = original_matrix
    c.hide_render = c.hide_viewport = True

manifest['render_camera_manifest'].extend(helper.CAMERA_LOG)
manifest['render_camera_manifest']=list({row['file']:row for row in manifest['render_camera_manifest']}.values())
manifest['status'] = 'EVIDENCE_READY; qualitative review uses explicitly approximate head proxies, not metric landmark alignment'
manifest['limitations'] = [
    'Generated illustrated input is not a calibrated orthographic turnaround.',
    'Head normalization uses recorded region/bounds proxies; differences in face proportions are qualitative.',
    'Actual-color passes preserve source shader differences; use clay alongside them.',
]
for record in manifest['records']:
    record['sha256_after'] = helper.sha(record['path'])
    if record['sha256_after'] != record['sha256_before']:
        raise RuntimeError('Source changed during supplemental rendering')
manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
preview = bpy.data.collections['CANDIDATE_PIXAL_SINGLE']
preview.hide_render = preview.hide_viewport = False
scene.view_layers[0].material_override = None
helper.aim(cam, Vector((0, 0, 1.58)), 0, .55)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.region_3d.view_location = Vector((0, 0, 1.58))
            area.spaces.active.region_3d.view_distance = 1.1
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(out / 'mia-stage0-native-comparison-reviewed.blend'))
