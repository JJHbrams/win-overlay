"""Combine frozen independent body/hair and face edits; retain source visibility and archives."""
import argparse
import hashlib
import json
import shutil
import struct
import sys
from pathlib import Path

import bpy
from mathutils import Vector

p = argparse.ArgumentParser()
for field in ('face', 'face-sha', 'body-hair', 'body-hair-sha', 'output-dir'):
    p.add_argument('--' + field, required=True)
p.add_argument('--hair-archive', action='append', default=[])
p.add_argument('--body', help='Optional independently corrected body native; hair still comes from --body-hair')
p.add_argument('--body-sha')
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
face, body_hair, out = Path(a.face).resolve(), Path(a.body_hair).resolve(), Path(a.output_dir).resolve()
assert bool(a.body) == bool(a.body_sha), 'Independent body needs both path and expected hash'
body_file = Path(a.body).resolve() if a.body else body_hair
digest = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
assert digest(face) == a.face_sha.lower()
assert digest(body_hair) == a.body_hair_sha.lower()
sources = {str(face): digest(face), str(body_hair): digest(body_hair)}
if a.body:
    assert digest(body_file) == a.body_sha.lower()
    sources[str(body_file)] = digest(body_file)
out.mkdir(parents=True, exist_ok=True)
native = out / 'Mia_Corrected_v20.blend'
assert not native.exists(), 'Never overwrite a frozen candidate'
shutil.copyfile(__file__, out / 'exact-integration-recipe.py')
BODY, HAIR = 'MIA_V06_BODY_SKIN', 'MIA_V17_PIXAL_HAIR'
baseline = Path(__file__).resolve().parent.parent / 'mia-reference-finish-v17/integrated-v18/Mia_HeadHair_v18.blend'
assert digest(baseline) == '87334607c76f6c0e876807f10ff407e8ce60fc7055265ae3591257893ba7b88d'
sources[str(baseline)] = digest(baseline)

def scope(o):
    m = o.data
    h = hashlib.sha256()
    for v in m.vertices:
        h.update(struct.pack('<3f', *v.co))
        for g in v.groups:
            h.update(struct.pack('<IIf', v.index, g.group, g.weight))
    for f in m.polygons:
        h.update(struct.pack('<I', len(f.vertices)))
        h.update(struct.pack('<' + 'I' * len(f.vertices), *f.vertices))
    for layer in m.uv_layers:
        h.update(layer.name.encode())
        for v in layer.data:
            h.update(struct.pack('<2f', *v.uv))
    if m.shape_keys:
        for key in m.shape_keys.key_blocks:
            h.update(key.name.encode())
            h.update(struct.pack('<f', key.value))
            for v in key.data:
                h.update(struct.pack('<3f', *v.co))
    return {'mesh_uv_keys_weights': h.hexdigest(),
            'matrix': [list(row) for row in o.matrix_world],
            'materials': [s.material.name if s.material else None for s in o.material_slots],
            'hide_render': o.hide_render}

def body_invariants(o):
    """Body transfer may move vertices only; UV, topology and weights must match."""
    h = hashlib.sha256()
    for group in o.vertex_groups:
        h.update(group.name.encode())
    for v in o.data.vertices:
        h.update(struct.pack('<I', v.index))
        for g in v.groups:
            h.update(struct.pack('<If', g.group, g.weight))
    for f in o.data.polygons:
        h.update(struct.pack('<II', len(f.vertices), f.material_index))
        h.update(struct.pack('<' + 'I' * len(f.vertices), *f.vertices))
    for layer in o.data.uv_layers:
        h.update(layer.name.encode())
        for uv in layer.data:
            h.update(struct.pack('<2f', *uv.uv))
    return h.hexdigest()

bpy.ops.wm.open_mainfile(filepath=str(baseline), use_scripts=False)
baseline_body = bpy.data.objects[BODY]
baseline_coords = [tuple(v.co) for v in baseline_body.data.vertices]
lower_ids = {v.index for v in baseline_body.data.vertices if (baseline_body.matrix_world @ v.co).z < 1.46}
baseline_faces = [tuple(f.vertices) for f in baseline_body.data.polygons]
baseline_body_invariants = body_invariants(baseline_body)
bpy.ops.wm.open_mainfile(filepath=str(body_file), use_scripts=False)
body_source = bpy.data.objects[BODY]
assert body_invariants(body_source) == baseline_body_invariants, 'Body topology/UV/weights changed'
body_coords = [tuple(v.co) for v in body_source.data.vertices]
body_faces = [tuple(f.vertices) for f in body_source.data.polygons]
body_matrix = [list(row) for row in body_source.matrix_world]
body_groups = [g.name for g in body_source.vertex_groups]
body_reference_scope = scope(body_source)
assert body_faces == baseline_faces
assert all((Vector(co) - Vector(baseline_coords[i])).length < 1e-7
           for i, co in enumerate(body_coords) if i not in lower_ids), 'Body producer edited protected head cap'
bpy.ops.wm.open_mainfile(filepath=str(body_hair), use_scripts=False)
hair_visibility = {o.name: {'render': o.hide_render, 'viewport': o.hide_viewport}
                   for o in bpy.data.collections[HAIR].all_objects}
hair_scopes = {o.name: scope(o) for o in bpy.data.collections[HAIR].all_objects if o.type == 'MESH'}
archive_visibility = {name: bpy.data.collections[name].hide_render for name in a.hair_archive}

bpy.ops.wm.open_mainfile(filepath=str(face), use_scripts=False)
body = bpy.data.objects[BODY]
assert body_invariants(body) == baseline_body_invariants, 'Face source changed protected body structure'
assert [list(row) for row in body.matrix_world] == body_matrix
assert [tuple(f.vertices) for f in body.data.polygons] == body_faces
assert [g.name for g in body.vertex_groups] == body_groups
assert len(body.data.vertices) == len(body_coords)
assert not body.data.shape_keys, 'Body keys require a deliberate delta transfer, not blind replacement'
old_hair = bpy.data.collections[HAIR]
old_objects = set(old_hair.all_objects)
protected = {o.name: scope(o) for o in bpy.context.scene.objects
             if o.type == 'MESH' and o not in old_objects and o != body}
body_before = [tuple(v.co) for v in body.data.vertices]
assert all((Vector(body_before[i]) - Vector(baseline_coords[i])).length < 1e-7
           for i in lower_ids), 'Face producer edited protected body below neck'
changed = []
for v, co in zip(body.data.vertices, body_coords):
    if v.index in lower_ids:
        if (v.co - Vector(co)).length > 1e-9:
            changed.append(v.index)
        v.co = co
body.data.update()
assert all((v.co - Vector(body_coords[v.index] if v.index in lower_ids else body_before[v.index])).length < 1e-7
           for v in body.data.vertices)

for o in old_objects:
    assert set(o.users_collection) <= {old_hair}, 'Unexpected shared hair owner'
    bpy.data.objects.remove(o, do_unlink=True)
bpy.data.collections.remove(old_hair)
with bpy.data.libraries.load(str(body_hair), link=False) as (available, requested):
    assert HAIR in available.collections
    assert all(name in available.collections for name in a.hair_archive)
    requested.collections = [HAIR] + a.hair_archive
new_hair = requested.collections[0]
for collection in requested.collections:
    bpy.context.scene.collection.children.link(collection)
bpy.context.view_layer.update()
assert new_hair.name == HAIR
for name, hidden in archive_visibility.items():
    assert bpy.data.collections[name].hide_render == hidden
# Do not force all imported objects visible: intentionally hidden replaced knot must stay hidden.
for name, visibility in hair_visibility.items():
    obj = bpy.data.objects[name]
    assert obj.hide_render == visibility['render']
    assert obj.hide_viewport == visibility['viewport']
for name, expected in hair_scopes.items():
    actual = scope(bpy.data.objects[name])
    assert actual['mesh_uv_keys_weights'] == expected['mesh_uv_keys_weights'], name
    matrix_error = max(abs(x-y) for ar, er in zip(actual['matrix'], expected['matrix']) for x,y in zip(ar,er))
    if matrix_error > 1e-7:
        print('HAIR_MATRIX_MISMATCH', name, actual['matrix'], expected['matrix'], flush=True)
    assert matrix_error <= 1e-7, name
assert all(scope(bpy.data.objects[name]) == value for name, value in protected.items())
scene = bpy.context.scene
cam = scene.camera
cam.location = (0, -2, 1.555)
cam.rotation_euler = (Vector((0, 0, 1.555)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.type, cam.data.ortho_scale = 'ORTHO', .48
scene['mia_v20_status'] = 'Corrected work in progress; reference and deformation review remains separate from technical preservation.'
for im in bpy.data.images:
    if im.packed_file:
        im.use_fake_user = True
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(native), relative_remap=False)
assert all(digest(path) == value for path, value in sources.items())
record = {'native': str(native), 'sha256': digest(native), 'source_hashes': sources,
          'recipe_sha256': digest(__file__), 'changed_body_vertices': changed,
          'body_matches_producer': True, 'face_and_other_meshes_preserved': protected,
          'body_geometry_source': str(body_file), 'hair_geometry_source': str(body_hair),
          'body_uv_topology_weights_preserved': True,
          'head_cap_matches_face': True, 'body_source_scope': body_reference_scope,
          'head_cap_vertices_changed_from_baseline': [i for i in range(len(body_coords)) if i not in lower_ids and (Vector(body_before[i])-Vector(baseline_coords[i])).length > 1e-7],
          'hair_archives_retained': archive_visibility,
          'hair_owner_scopes': hair_scopes, 'hair_source_visibility_preserved': hair_visibility,
          'art_acceptance': 'NOT INFERRED; requires actual fresh multiview comparison',
          'sources_unchanged': True}
(out / 'integration-manifest.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print('V20_INTEGRATED', record['sha256'])
