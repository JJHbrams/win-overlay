"""Delete only the confirmed raw facial fragments retained in canonical hair.

This is independent of unaccepted B-series hairstyle candidates.  Run in
background Blender, or import apply_face_fragment_cleanup in an open target.
No scene, rig, material, image, other hair actor, or non-hair mesh is changed.
"""
import argparse
import collections
import hashlib
import json
import sys
from pathlib import Path

import bmesh
import bpy
import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from replay_hair import (  # Read-only hashing utilities; no hair replay invoked.
    _digest, _plain, _rna, group_state, mesh_signature, nonhair_snapshot,
    sha, uv_state, verify_preserved,
)

OWNER = 'MIA_V17_PIXAL_DetailedHair'
RAW_ATTRIBUTE = 'MIA_SOURCE_POLYGON'
CANONICAL_MESH_SHA256 = 'ecdc591c3dec433fba1b55a0f131537460446a1c351001fcf2fdd3af1c3a277e'
PLAN_SHA256 = '760e07534689b7a2cd4b7c5493ca711166715f6803d85e81982a303d3cebf952'
# Filled from the exact canonical C -> BMesh FACES_ONLY CPU verification.
CLEANED_MESH_SHA256 = '4f88b566527bc319957a84415397a87281c67644d5ac94e01bba20ff667c17bd'
PROTECTED_LOCK_IDS = (82525, 93291)


def _attribute_values(attr):
    """Exact native storage, independent of transient polygon/loop indices."""
    mapping = {
        'FLOAT': ('value', np.float32, 1),
        'INT': ('value', np.int32, 1),
        'BOOLEAN': ('value', np.bool_, 1),
        'FLOAT_VECTOR': ('vector', np.float32, 3),
        'FLOAT2': ('vector', np.float32, 2),
        'INT32_2D': ('value', np.int32, 2),
        'FLOAT_COLOR': ('color', np.float32, 4),
        'BYTE_COLOR': ('color', np.float32, 4),
        'QUATERNION': ('value', np.float32, 4),
        'FLOAT4X4': ('value', np.float32, 16),
    }
    if attr.data_type not in mapping:
        raise RuntimeError('Unsupported attribute type; refusing lossy cleanup: '
                           + attr.name + '/' + attr.data_type)
    field, dtype, width = mapping[attr.data_type]
    values = np.empty(len(attr.data) * width, dtype=dtype)
    attr.data.foreach_get(field, values)
    return values.reshape(len(attr.data), width)


def _mesh_content(mesh):
    """Surviving per-raw-ID face/corner payload plus all point/edge payload."""
    attr = mesh.attributes.get(RAW_ATTRIBUTE)
    if attr is None or attr.domain != 'FACE' or attr.data_type != 'INT':
        raise RuntimeError('A FACE/INT MIA_SOURCE_POLYGON attribute is required')
    raw = np.empty(len(mesh.polygons), dtype=np.int32)
    attr.data.foreach_get('value', raw)
    duplicate_ids = [int(k) for k, n in collections.Counter(map(int, raw)).items() if n > 1]
    if duplicate_ids:
        raise RuntimeError('Raw source face IDs are not unique: ' + str(duplicate_ids[:20]))
    attributes = {}
    # These derived topology arrays are checked using actual faces and edges.
    derived = {'position', '.edge_verts', '.corner_vert', '.corner_edge'}
    invariant = hashlib.sha256()
    invariant.update(np.asarray([v.co[:] for v in mesh.vertices], dtype='<f4').tobytes())
    invariant.update(np.asarray([e.vertices[:] for e in mesh.edges], dtype='<i4').tobytes())
    invariant.update(np.asarray([(e.use_seam, e.use_edge_sharp) for e in mesh.edges], dtype=np.bool_).tobytes())
    face_attrs = {}
    corner_attrs = {}
    for a in mesh.attributes:
        if a.name in derived:
            continue
        metadata = (a.domain, a.data_type)
        values = _attribute_values(a)
        attributes[a.name] = metadata
        if a.domain in {'POINT', 'EDGE'}:
            invariant.update(a.name.encode())
            invariant.update(str(metadata).encode())
            invariant.update(values.tobytes())
        elif a.domain == 'FACE':
            face_attrs[a.name] = values
        elif a.domain == 'CORNER':
            corner_attrs[a.name] = values
        else:
            raise RuntimeError('Unsupported attribute domain: ' + a.name + '/' + a.domain)
    faces = {}
    for f, rid in zip(mesh.polygons, raw):
        h = hashlib.sha256()
        h.update(np.asarray(f.vertices[:], dtype='<i4').tobytes())
        h.update(np.asarray([f.material_index, f.use_smooth], dtype='<i4').tobytes())
        for name, values in face_attrs.items():
            h.update(name.encode())
            h.update(values[f.index].tobytes())
        for name, values in corner_attrs.items():
            h.update(name.encode())
            h.update(values[f.loop_start:f.loop_start + f.loop_total].tobytes())
        # Explicit UV read checks both active/render UV maps, not just attributes.
        for u in mesh.uv_layers:
            h.update(u.name.encode())
            h.update(np.asarray([u.data[i].uv[:] for i in f.loop_indices], dtype='<f4').tobytes())
        faces[int(rid)] = h.hexdigest()
    return {
        'vertex_count': len(mesh.vertices), 'edge_count': len(mesh.edges),
        'polygon_count': len(mesh.polygons), 'loop_count': len(mesh.loops),
        'point_edge_sha256': invariant.hexdigest(), 'attributes': attributes,
        'faces': faces, 'has_custom_normals': mesh.has_custom_normals,
    }


def _target_metadata(ob):
    return {
        'name': ob.name, 'data_name': ob.data.name,
        'matrix': _plain(ob.matrix_world), 'parent': ob.parent.name if ob.parent else None,
        'parent_type': ob.parent_type, 'parent_bone': ob.parent_bone,
        'hide_render': ob.hide_render, 'hide_viewport': ob.hide_viewport,
        'hide_set': ob.hide_get(), 'collections': sorted(c.name for c in ob.users_collection),
        'modifiers': [_rna(m) for m in ob.modifiers],
        'constraints': [_rna(c) for c in ob.constraints],
        'materials': [m.name if m else None for m in ob.data.materials],
        'vertex_groups_sha256': _digest(group_state(ob)), 'uv_state': uv_state(ob),
        'custom_properties': _plain(dict(ob.items())),
        'mesh_properties': _rna(ob.data, {'vertices', 'edges', 'loops', 'polygons',
                                        'loop_triangles', 'loop_triangle_polygons',
                                        'attributes', 'color_attributes', 'uv_layers',
                                        'corner_normals', 'vertex_normals', 'polygon_normals',
                                        'total_vert_sel', 'total_edge_sel', 'total_face_sel'}),
    }


def _protected_snapshot():
    # An empty exclusion includes the target hair's materials too. Only its mesh
    # object hash is then removed; every old graph/image/other actor stays guarded.
    state = nonhair_snapshot(set())
    state['objects'].pop(OWNER, None)
    return state


def _shape_key_inventory():
    return {
        o.name: [k.name for k in o.data.shape_keys.key_blocks]
        for o in bpy.context.scene.objects
        if o.type == 'MESH' and o.data.shape_keys
    }


def _write_report(path, report):
    if path:
        Path(path).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')


def apply_face_fragment_cleanup(plan_path=None, report_path=None):
    """Apply only exact source IDs in memory; caller owns opening and saving."""
    plan_path = Path(plan_path) if plan_path else HERE / 'source-face-exclusion-plan.json'
    if sha(plan_path) != PLAN_SHA256:
        raise RuntimeError('The confirmed source-ID plan changed; re-review it before cleanup')
    plan = json.loads(plan_path.read_text(encoding='utf-8'))
    ids = list(map(int, plan['excluded_raw_source_ids']))
    exclude = set(ids)
    if len(ids) != 1216 or len(exclude) != 1216:
        raise RuntimeError('Expected exactly 1,216 unique confirmed raw IDs')
    if exclude.intersection(PROTECTED_LOCK_IDS):
        raise RuntimeError('The exclusion plan contains a protected real hair lock')
    ob = bpy.data.objects.get(OWNER)
    if ob is None or ob.type != 'MESH':
        raise RuntimeError('Canonical main-hair owner is required: ' + OWNER)
    if ob.mode != 'OBJECT' or ob.data.users != 1:
        raise RuntimeError('Cleanup requires object mode and a single-owner hair mesh')
    if ob.data.shape_keys:
        raise RuntimeError('Canonical hair has no shape keys; refusing an altered owner')
    before_mesh = _mesh_content(ob.data)
    before_sig = mesh_signature(ob)
    before_ids = set(before_mesh['faces'])
    matches = before_ids & exclude
    missing = exclude - before_ids
    locks = {str(rid): rid in before_ids for rid in PROTECTED_LOCK_IDS}
    base_report = {
        'technical_cleanup_only': True, 'art_acceptance': False, 'owner': OWNER,
        'plan': str(plan_path), 'plan_sha256': PLAN_SHA256,
        'plan_raw_id_count': len(exclude), 'matched_raw_ids_count': len(matches),
        'missing_plan_raw_ids': sorted(missing), 'matched_plan_raw_ids': sorted(matches),
        'known_real_hair_raw_ids_present_before': locks,
        'input_mesh_sha256': before_sig,
        'unaccepted_shape_or_material_imported': False,
        'rig_or_pose_modified': False,
        'method': 'Exact confirmed MIA_SOURCE_POLYGON membership; BMesh FACES_ONLY. No component growth, geometry mask, or B-series model import.',
    }
    if not all(locks.values()):
        _write_report(report_path, {**base_report, 'status': 'guard_failed'})
        raise RuntimeError('A protected true-hair raw ID is missing')
    if not matches and CLEANED_MESH_SHA256 and before_sig == CLEANED_MESH_SHA256:
        result = {**base_report, 'status': 'already_applied', 'removed_faces': 0,
                  'missing_plan_ids_explained_by_exact_cleaned_hash': True,
                  'output_mesh_sha256': before_sig, 'all_other_state_exact': True}
        _write_report(report_path, result)
        return result
    if missing or before_sig != CANONICAL_MESH_SHA256:
        _write_report(report_path, {**base_report, 'status': 'guard_failed'})
        raise RuntimeError('Canonical geometry/all-plan-IDs guard failed before mutation; '
                           f'matched={len(matches)}, missing={len(missing)}, mesh={before_sig}')
    if before_mesh['has_custom_normals']:
        raise RuntimeError('Unexpected custom normals; a lossless corner-normal strategy is required')
    protected = _protected_snapshot()
    metadata = _target_metadata(ob)
    key_inventory = _shape_key_inventory()
    bm = bmesh.new()
    temporary = None
    try:
        bm.from_mesh(ob.data)
        raw_layer = bm.faces.layers.int.get(RAW_ATTRIBUTE)
        if raw_layer is None:
            raise RuntimeError('BMesh did not retain the raw polygon ID layer')
        doomed = [f for f in bm.faces if int(f[raw_layer]) in exclude]
        if len(doomed) != len(exclude):
            raise RuntimeError('BMesh source-ID count mismatch')
        bmesh.ops.delete(bm, geom=doomed, context='FACES_ONLY')
        temporary = ob.data.copy()
        bm.to_mesh(temporary)
        temporary.update()
        candidate = _mesh_content(temporary)
        expected_faces = {k: v for k, v in before_mesh['faces'].items() if k not in exclude}
        if candidate['faces'] != expected_faces:
            bad = [k for k, v in expected_faces.items() if candidate['faces'].get(k) != v]
            raise RuntimeError('A surviving face winding/material/UV/attribute changed: ' + str(bad[:20]))
        for field in ['vertex_count', 'edge_count', 'point_edge_sha256', 'attributes', 'has_custom_normals']:
            if candidate[field] != before_mesh[field]:
                raise RuntimeError('Unintended point/edge/attribute change: ' + field)
        # Commit the already verified BMesh into the existing mesh ID. Keep its
        # name, object association, material slots, groups and every vertex.
        bm.to_mesh(ob.data)
        ob.data.update()
    finally:
        bm.free()
        if temporary is not None:
            bpy.data.meshes.remove(temporary)
    after_mesh = _mesh_content(ob.data)
    if after_mesh != candidate:
        raise RuntimeError('Committed hair differs from the verified temporary result')
    after_sig = mesh_signature(ob)
    if CLEANED_MESH_SHA256 and after_sig != CLEANED_MESH_SHA256:
        raise RuntimeError('Unexpected cleaned mesh fingerprint')
    if _target_metadata(ob) != metadata:
        changes = [k for k, v in metadata.items() if _target_metadata(ob).get(k) != v]
        raise RuntimeError('Target owner metadata changed: ' + str(changes))
    after = _protected_snapshot()
    delta = verify_preserved(protected, after)
    if delta or _shape_key_inventory() != key_inventory:
        raise RuntimeError('Protected scene/model state changed: ' + json.dumps(delta))
    result = {
        **base_report, 'status': 'applied', 'removed_faces': len(matches),
        'output_mesh_sha256': after_sig,
        'before_counts': {k: before_mesh[k] for k in ['vertex_count', 'edge_count', 'polygon_count', 'loop_count']},
        'after_counts': {k: after_mesh[k] for k in ['vertex_count', 'edge_count', 'polygon_count', 'loop_count']},
        'surviving_face_payloads_exact': True, 'all_vertices_edges_groups_exact': True,
        'remaining_uv_face_corner_attributes_exact': True, 'all_other_state_exact': True,
        'target_metadata_material_slots_active_uv_exact': True,
        'known_real_hair_raw_ids_retained': {str(rid): rid in after_mesh['faces'] for rid in PROTECTED_LOCK_IDS},
        'protected_counts': {k: len(protected[k]) for k in ['objects', 'materials', 'images']},
        'shape_key_inventory': key_inventory,
        'protected_before': protected,
        'limits': 'Only confirmed old facial fragments are removed. Hair shape/source likeness, residual fragments, clipping, texture appearance and animation remain independently unverified; no ART PASS.',
    }
    _write_report(report_path, result)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--target', required=True)
    ap.add_argument('--plan')
    ap.add_argument('--report', required=True)
    ap.add_argument('--output')
    ap.add_argument('--expected-preservation-report')
    args = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
    target = Path(args.target)
    target_sha = sha(target)
    if args.output and Path(args.output).exists():
        raise RuntimeError('Refusing to overwrite an existing output native')
    bpy.ops.wm.open_mainfile(filepath=str(target), use_scripts=False)
    if args.expected_preservation_report:
        expected = json.loads(Path(args.expected_preservation_report).read_text(encoding='utf-8'))
        delta = verify_preserved(expected['protected_before'], _protected_snapshot())
        if delta:
            raise RuntimeError('Fresh reopen changed the original protected state: ' + json.dumps(delta))
    result = apply_face_fragment_cleanup(args.plan, args.report)
    if args.expected_preservation_report:
        result['fresh_reopen_original_protected_state_exact'] = True
    if args.output:
        bpy.ops.wm.save_as_mainfile(filepath=str(Path(args.output)), relative_remap=False)
        result['diagnostic_output_native'] = str(Path(args.output))
        result['diagnostic_output_sha256'] = sha(args.output)
    if sha(target) != target_sha:
        raise RuntimeError('Input target native changed on disk')
    result['input_native_unchanged_on_disk'] = True
    _write_report(args.report, result)
    print('FACE_FRAGMENT_CLEANUP', result['status'], result['removed_faces'], result['output_mesh_sha256'])


if __name__ == '__main__':
    main()
