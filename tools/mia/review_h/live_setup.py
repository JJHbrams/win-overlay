"""Install the explicitly unaccepted H component in live Blender for repair.

Run only through official execute_blender_code. No native save or source edit.
"""
from pathlib import Path
import sys
import json
import hashlib
import bpy
import numpy as np

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
COMPONENT = ROOT/'asset/mia/blender/mia-fit-v003/body/surface-review12'
PAYLOAD = ROOT/'.mia-cache/body-h/shape/assembly/winding-fixed'
SOURCE = ROOT/'asset/mia/blender/mia-refinement-v002/integrated/Mia_v0.0.2_Review_R3b.blend'
assert Path(bpy.data.filepath).resolve() == SOURCE.resolve()
assert 'MIA_Review12_H_LiveRepair' not in bpy.data.objects
sys.path.insert(0, str(COMPONENT))
import install_review
import review_fixture as fixture

out = ROOT/'.mia-cache/body-h/live'
body, proof = install_review.apply(
    geometry_path=PAYLOAD/'geometry.npz', atlas_path=PAYLOAD/'atlas/atlas.npz',
    proof_path=out/'live-installed.json', packing_path=out/'live-head-normal-packing.json')
body.name = 'MIA_Review12_H_LiveRepair'
body['MIA_Live_scope'] = 'UNACCEPTED H baseline for localized live repair; no ART promotion'
scene = bpy.context.scene
fixture.setup(scene)
fixture.hair_visibility(scene, False)
for ob in fixture.hair_actors(scene): ob.hide_set(True)
original = scene.objects['MIA_V27_SharedHeadBody']
original.hide_set(True)
for ob in bpy.context.selected_objects: ob.select_set(False)
body.hide_set(False); body.select_set(True); bpy.context.view_layer.objects.active = body
rows = dict(np.load(ROOT/'.mia-cache/body-h/shape/assembly/collar-rows.npz'))
group = body.vertex_groups.new(name='MIA_Live_Neck_Interior')
group.add(list(map(int, rows['neck'].ravel())), 1., 'REPLACE')
coords = np.array([v.co[:] for v in body.data.vertices], np.float32)
bpy.app.driver_namespace['MIA_Live_H_Baseline'] = coords.copy()
bpy.app.driver_namespace['MIA_Live_H_Rows'] = rows
bpy.app.driver_namespace['MIA_Live_H_Payload'] = str(PAYLOAD)
bpy.app.driver_namespace['MIA_Live_H_ActorProof'] = proof
for vertex in body.data.vertices: vertex.select = False
for vi in rows['neck'].ravel(): body.data.vertices[int(vi)].select = True
body.data.materials[12].diffuse_color = (.52, .52, .52, 1)
fixture.aim(scene, 90, target=(0, .005, 1.42), scale=.42, resolution=(800, 800))
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type != 'VIEW_3D': continue
        space = area.spaces.active
        space.clip_start = .1; space.clip_end = 10
        space.shading.type = 'SOLID'; space.shading.light = 'STUDIO'
        space.shading.color_type = 'MATERIAL'
        space.region_3d.view_location = (0, .005, 1.42)
        space.region_3d.view_distance = .42
        space.region_3d.view_rotation = scene.camera.rotation_euler.to_quaternion()
        space.region_3d.view_perspective = 'ORTHO'
body.show_wire = False
record = dict(scope='Actual official MCP live H setup, NOT accepted',
              filepath=bpy.data.filepath, object=body.name, vertices=len(coords),
              geometry_payload_sha256=fixture.sha(PAYLOAD/'geometry.npz'),
              actual_world_sha256=hashlib.sha256(coords.tobytes()).hexdigest(),
              selected_neck_interior_vertices=int(rows['neck'].size),
              source_native_sha256=fixture.sha(SOURCE), source_saved=False,
              fixture=fixture.record(scene))
(out/'setup.json').write_text(json.dumps(record, indent=2)+'\n', encoding='utf8')
print(json.dumps(record))
