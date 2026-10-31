"""Integrate frozen producer ownership without replacing unrelated geometry or materials.

Run with Blender --background --python this_file -- --config frozen-inputs.json.
The manifest validates evidence integrity; actual source-art review remains separate.
"""
import argparse
import hashlib
import json
import os
import copy
import runpy
import shutil
import struct
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
BODY = 'MIA_V06_BODY_SKIN'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def mesh_scope(obj):
    h = hashlib.sha256()
    for v in obj.data.vertices:
        h.update(struct.pack('<3f', *v.co))
        for g in v.groups:
            h.update(struct.pack('<IIf', v.index, g.group, g.weight))
    for p in obj.data.polygons:
        h.update(struct.pack('<II', len(p.vertices), p.material_index))
        h.update(struct.pack('<' + 'I' * len(p.vertices), *p.vertices))
    for uv in obj.data.uv_layers:
        h.update(uv.name.encode())
        for x in uv.data:
            h.update(struct.pack('<2f', *x.uv))
    if obj.data.shape_keys:
        for key in obj.data.shape_keys.key_blocks:
            h.update(key.name.encode())
            h.update(struct.pack('<f', key.value))
            for x in key.data:
                h.update(struct.pack('<3f', *x.co))
    return {'geometry_uv_weights_keys': h.hexdigest(),
            'matrix': [list(r) for r in obj.matrix_world],
            'parent': obj.parent.name if obj.parent else None,
            'groups': [g.name for g in obj.vertex_groups],
            'hide_render': obj.hide_render,
            'hide_viewport': obj.hide_viewport}


def cap_data_scope(obj, source_cap_ids, old_to_new=None):
    """Protect face-owned cap weights, UV loops and topology during body remapping."""
    mapping = old_to_new or {i: i for i in range(len(obj.data.vertices))}
    inverse = {new: old for old, new in mapping.items()}
    cap = {mapping[i] for i in source_cap_ids}
    polygons = []
    for poly in obj.data.polygons:
        if not cap.intersection(poly.vertices):
            continue
        assert all(i in inverse for i in poly.vertices), 'New body topology reached headcap'
        polygons.append((tuple(inverse[i] for i in poly.vertices), poly.material_index,
                         tuple(tuple(tuple(layer.data[i].uv) for i in poly.loop_indices)
                               for layer in obj.data.uv_layers)))
    return {'uv_layers': [uv.name for uv in obj.data.uv_layers],
            'weights': {i: [(g.group, g.weight) for g in obj.data.vertices[mapping[i]].groups]
                        for i in sorted(source_cap_ids)},
            'polygons': sorted(polygons)}


def main(config_path):
    config = json.loads(config_path.read_text(encoding='utf-8'))
    # Portable inputs are relative to their config, never to Blender's cwd.
    for part in ('baseline', 'face', 'body', 'hair'):
        for key in ('path', 'review_package', 'provenance'):
            if key in config[part]:
                p = Path(config[part][key])
                config[part][key] = str((p if p.is_absolute() else config_path.parent/p).resolve())
    output_path = Path(config['output_dir'])
    config['output_dir'] = str((output_path if output_path.is_absolute() else config_path.parent/output_path).resolve())
    source_rows = [config[k] for k in ('baseline', 'face', 'body', 'hair')]
    for row in source_rows:
        assert sha(row['path']) == row['sha256'], row['path']
    out = Path(config['output_dir']).resolve()
    out.mkdir(parents=True, exist_ok=True)
    native = out / 'Mia_ReferenceFinish_v22.blend'
    assert not native.exists(), 'Frozen output must not be overwritten'
    validate = runpy.run_path(str(HERE / 'validate_reference_review.py'))['validate']
    validations = {}
    for part in ('face', 'body', 'hair'):
        package = Path(config[part]['review_package']).resolve()
        result = validate(package)
        assert result['evidence_valid'], (part, result)
        assert json.loads(package.read_text(encoding='utf-8'))['candidate_native']['sha256'] == config[part]['sha256']
        validations[part] = result

    bpy.ops.wm.open_mainfile(filepath=config['baseline']['path'], use_scripts=False)
    base_body = bpy.data.objects[BODY]
    base_coords = [v.co.copy() for v in base_body.data.vertices]
    base_world = base_body.matrix_world.copy()
    cap_ids = {i for i, co in enumerate(base_coords) if (base_world @ co).z >= 1.46}
    baseline_cap_data = cap_data_scope(base_body, cap_ids)
    source_count = len(base_coords)

    bpy.ops.wm.open_mainfile(filepath=config['hair']['path'], use_scripts=False)
    hair_owners = config['hair']['material_owners']
    hair_scopes = {name: mesh_scope(bpy.data.objects[name]) for name in hair_owners}
    hair_slots = {name: [s.material.name if s.material else None for s in bpy.data.objects[name].material_slots]
                  for name in hair_owners}
    assert all(all(x is not None for x in slots) for slots in hair_slots.values())

    bpy.ops.wm.open_mainfile(filepath=config['face']['path'], use_scripts=False)
    target = bpy.data.objects[BODY]
    assert len(target.data.vertices) == source_count and not target.data.shape_keys
    face_body = [v.co.copy() for v in target.data.vertices]
    assert cap_data_scope(target, cap_ids) == baseline_cap_data, 'Face cap UV/weights/topology changed without declared transfer'
    assert all((face_body[i] - base_coords[i]).length < 1e-7 for i in range(source_count) if i not in cap_ids), 'Face edits crossed below head ownership'
    protected = {o.name: mesh_scope(o) for o in bpy.context.scene.objects if o.type == 'MESH' and o != target}
    body_materials = [s.material for s in target.material_slots]
    body_matrix = target.matrix_world.copy()
    body_parent = target.parent
    body_modifiers = [(m.name, m.type) for m in target.modifiers]
    face_body_archive = target.data
    face_body_archive.use_fake_user = True

    provenance = json.loads(Path(config['body']['provenance']).read_text(encoding='utf-8'))
    assert provenance['native_sha256'] == config['body']['sha256']
    mapping = {int(k): int(v) for k, v in provenance['source_to_new_preserved_vertices'].items()}
    assert cap_ids <= set(mapping), 'Body patch removed protected headcap IDs'
    with bpy.data.libraries.load(config['body']['path'], link=False) as (available, requested):
        assert BODY in available.objects
        requested.objects = [BODY]
    donor = requested.objects[0]
    # Library-loaded, unlinked objects have no evaluated world transform yet.
    # Link only for evaluation; the target object/rig itself is never replaced.
    temporary = bpy.data.collections.new('MIA_V22_TEMP_BODY_TRANSFER')
    bpy.context.scene.collection.children.link(temporary)
    temporary.objects.link(donor)
    bpy.context.view_layer.update()
    assert [g.name for g in donor.vertex_groups] == [g.name for g in target.vertex_groups], 'Weight group indices must match'
    assert not donor.data.shape_keys, 'Body shape keys need explicit remapping'
    assert max(abs(a-b) for ar, br in zip(donor.matrix_world, body_matrix) for a,b in zip(ar,br)) < 1e-7, ([list(r) for r in donor.matrix_world], [list(r) for r in body_matrix])
    body_data = donor.data
    # Coordinates on the independent body cap must still match the immutable source.
    assert all((body_data.vertices[mapping[i]].co-base_coords[i]).length < 1e-7 for i in cap_ids)
    assert cap_data_scope(donor, cap_ids, mapping) == baseline_cap_data, 'Donor changed face-owned cap data'
    polygon_material_indices = [p.material_index for p in body_data.polygons]
    assert all(i < len(body_materials) for i in polygon_material_indices), 'Body material slots cannot represent donor polygon indices'
    body_data.materials.clear()
    for mat in body_materials:
        body_data.materials.append(mat)
    for poly, index in zip(body_data.polygons, polygon_material_indices):
        poly.material_index = index
    target.data = body_data
    for old_id in cap_ids:
        body_data.vertices[mapping[old_id]].co = face_body[old_id]
    body_data.update()
    bpy.data.objects.remove(donor, do_unlink=True)
    bpy.data.collections.remove(temporary)
    assert target.parent == body_parent and target.matrix_world == body_matrix
    assert [(m.name, m.type) for m in target.modifiers] == body_modifiers
    assert all((body_data.vertices[mapping[i]].co-face_body[i]).length < 1e-7 for i in cap_ids)
    assert cap_data_scope(target, cap_ids, mapping) == baseline_cap_data, 'Final headcap data changed during material replay'

    material_names = sorted({m for slots in hair_slots.values() for m in slots})
    with bpy.data.libraries.load(config['hair']['path'], link=False) as (available, requested):
        assert set(material_names) <= set(available.materials)
        # Blender replaces entries in the requested list with loaded datablocks.
        requested.materials = list(material_names)
    loaded_materials = dict(zip(material_names, requested.materials))
    for name, slots in hair_slots.items():
        owner = bpy.data.objects[name]
        assert mesh_scope(owner) == hair_scopes[name], ('Hair geometry/UV mismatch', name)
        assert len(owner.material_slots) == len(slots)
        for slot, original_name in zip(owner.material_slots, slots):
            slot.material = loaded_materials[original_name]
    assert all(mesh_scope(bpy.data.objects[name]) == expected for name, expected in protected.items())

    setup = runpy.run_path(str(HERE/'configure_review_scene.py'))['setup']()
    ink = None
    if config.get('skin_contour_render', False):
        ink = runpy.run_path(str(HERE/'production_ink.py'))['configure_skin_ink']()
    scene = bpy.context.scene
    scene['mia_v22_status'] = 'Integrated work in progress. Source-paired art and deformation acceptance remain separate.'
    for img in bpy.data.images:
        if img.packed_file:
            img.use_fake_user = True
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(native), relative_remap=False)
    for row in source_rows:
        assert sha(row['path']) == row['sha256'], 'Source mutated'
    shutil.copyfile(__file__, out/'exact-integration-recipe.py')
    shutil.copyfile(config_path, out/'original-inputs.json')
    replay = copy.deepcopy(config)
    for part in ('baseline', 'face', 'body', 'hair'):
        for key in ('path', 'review_package', 'provenance'):
            if key in replay[part]:
                replay[part][key] = Path(os.path.relpath(replay[part][key], out)).as_posix()
    replay['output_dir'] = '../replayed-integration'
    (out/'frozen-inputs.json').write_text(json.dumps(replay, indent=2), encoding='utf-8')
    for name in ('configure_review_scene.py', 'validate_reference_review.py', 'production_ink.py'):
        shutil.copyfile(HERE/name, out/name)
    result = {'native': str(native), 'sha256': sha(native), 'inputs': config,
              'reference_validations': validations,
              'face_other_geometry_preserved': protected,
              'hair_material_slots_replayed': hair_slots,
              'headcap_old_ids': sorted(cap_ids),
              'headcap_changed_from_baseline': [i for i in sorted(cap_ids) if (face_body[i]-base_coords[i]).length > 1e-7],
              'headcap_weights_uv_topology_material_indices_preserved': True,
              'body_retained_vertex_mapping': mapping,
              'body_vertices': len(body_data.vertices),
              'body_materials_from_face': [m.name if m else None for m in body_materials],
              'body_parent_modifiers_transform_preserved': True,
              'original_face_body_mesh_archived': face_body_archive.name,
              'review_setup': setup,
              'skin_contour_render': ink,
              'art_acceptance': 'NOT_EVALUATED; require fresh integrated source-paired renders and independent review'}
    (out/'integration-manifest.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('REFERENCE_FINISH_INTEGRATED', result['sha256'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    main(Path(args.config).resolve())
