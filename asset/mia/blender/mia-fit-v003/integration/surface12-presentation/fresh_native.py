"""Independent read-only Blender inspection of the delivered two-state native.

Usage after Blender's --: native geometry atlas bake-report output-json
No saves, rendering, settings installation or source modification.
"""
from pathlib import Path
import hashlib
import json
import sys

import bpy
import numpy as np

args = sys.argv[sys.argv.index('--') + 1:]
native, geometry, atlas, bake_path, output = map(Path, args)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
ah = lambda a: hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
before = sha(native)
assert Path(bpy.data.filepath).resolve() == native.resolve()
g, uv = np.load(geometry), np.load(atlas)
source_uv_names = json.loads((geometry.parent / 'donor.json').read_text(encoding='utf-8'))['uv_layers']
bake = json.loads(bake_path.read_text(encoding='utf-8'))
expected_images = {Path(f['path']).name: f for f in bake['files']}
objects, states = {}, {}
for name, mode in [('SkinOnly', 0.), ('Underwear', 1.)]:
    scene = bpy.data.scenes[name]
    visible = [o for o in scene.objects if o.get('MIA12_static_review_body') and not o.hide_render]
    assert len(visible) == 1, (name, [o.name for o in visible])
    body = objects[name] = visible[0]
    assert np.array_equal(np.asarray(body.matrix_world), np.eye(4))
    assert not body.modifiers and not body.data.shape_keys
    actual = np.asarray([v.co[:] for v in body.data.vertices], np.float32)
    triangles = np.asarray([f.vertices[:] for f in body.data.polygons], np.int32)
    assert np.array_equal(actual, g['world']) and np.array_equal(triangles, g['triangles'])
    actual_uv = np.asarray([q.uv[:] for q in body.data.uv_layers['MIA_Review12UV'].data], np.float32).reshape(-1, 3, 2)
    assert np.array_equal(actual_uv, uv['loop_uv'])
    assert body.data.uv_layers.active.name == 'UVMap'
    assert [u.name for u in body.data.uv_layers if u.active_render] == ['UVMap']
    head = g['source_part'] == 1
    assert [u.name for u in list(body.data.uv_layers)[:3]] == source_uv_names
    assignments = np.asarray([f.material_index for f in body.data.polygons])
    assert (assignments[~head] == 12).all()
    assert np.array_equal(assignments[head], g['triangle_materials'][head])
    for index, uvname in enumerate(source_uv_names):
        layer = body.data.uv_layers[uvname]
        old = np.asarray([q.uv[:] for q in layer.data], np.float32).reshape(-1, 3, 2)
        assert np.array_equal(old[head], g['old_loop_uv'][head, :, index, :])
    slot = body.material_slots[12]
    assert slot.link == 'OBJECT'
    mat = slot.material
    roles = {n.get('mia12_role'): n for n in mat.node_tree.nodes}
    assert roles['UnderwearMode'].outputs[0].default_value == mode
    assert roles['ClavicleStrength'].outputs[0].default_value > 0
    assert roles['ColorOnly'].outputs[0].default_value == 0
    assert roles['BodyUV'].uv_map == 'MIA_Review12UV'
    outlets = [n for n in mat.node_tree.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output]
    assert len(outlets) == 1
    visited, todo = set(), outlets[:]
    while todo:
        node = todo.pop()
        if node in visited:
            continue
        visited.add(node)
        todo.extend(link.from_node for socket in node.inputs for link in socket.links)
    images = []
    for node in visited:
        if node.type != 'TEX_IMAGE':
            continue
        image = node.image
        filename = Path(image.filepath).name
        expected = expected_images[filename]
        assert image.packed_file is not None
        packed_sha = hashlib.sha256(bytes(image.packed_file.data)).hexdigest()
        assert packed_sha == expected['sha256']
        assert image.colorspace_settings.name == expected['color_space']
        assert node.inputs['Vector'].links[0].from_node == roles['BodyUV']
        images.append(dict(role=node.get('mia12_role'), filename=filename, packed_sha256=packed_sha,
                           color_space=image.colorspace_settings.name, size=list(image.size)))
    assert len(images) == 5
    assert scene.objects['MIA_V27_SharedHeadBody'].hide_render
    states[name] = dict(body_object=body.name, shared_mesh=body.data.name, world_sha256=ah(actual),
                       triangles_sha256=ah(triangles), review_uv_sha256=ah(actual_uv),
                       body_only_review_uv_sha256=ah(actual_uv[~head]),
                       old_head_UV_layers=[u.name for u in list(body.data.uv_layers)[:3]],
                       body_material=mat.name, variant_mode=mode, packed_images=images,
                       frame=scene.frame_current, render_engine=scene.render.engine)
assert objects['SkinOnly'].data is objects['Underwear'].data
assert objects['SkinOnly'].material_slots[12].material is not objects['Underwear'].material_slots[12].material
assert sha(native) == before
report = dict(status='PASS read-only fresh saved-native geometry/UV/two-state/packed-output-route checks',
              native=str(native), sha256=before, geometry_sha256=sha(geometry), atlas_sha256=sha(atlas),
              states=states, shared_geometry=True, file_unchanged=True, GPU_used=False,
              art_acceptance='NOT_EVALUATED; actual orbit/source/material comparisons remain separate.')
output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ROOT_REVIEW12_FRESH_NATIVE_PASS', before, flush=True)
