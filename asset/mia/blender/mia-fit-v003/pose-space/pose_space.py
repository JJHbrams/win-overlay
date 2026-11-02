"""Empirical fixed-pose control-cage map. No scene open/save/render operations.

Run inside Blender. build_mapping(obj) evaluates a private object/mesh copy with a
POINT vector offset immediately before its sole Armature. Post-Armature modifiers
are disabled on that copy. Every temporary datablock is removed in finally.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path

import bpy
import numpy as np


def _coords(vertices):
    a = np.empty(len(vertices) * 3, dtype=np.float64)
    vertices.foreach_get('co', a)
    return a.reshape(-1, 3)


def _matrix(matrix):
    return np.asarray([list(row) for row in matrix], dtype=np.float64)


def _world(local, matrix):
    return local @ matrix[:3, :3].T + matrix[:3, 3]


def _json_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def pose_signature(obj, armature_modifier):
    """Identity guard for the exact evaluated pose, weights, and key state."""
    rig = armature_modifier.object
    state = {
        'frame': bpy.context.scene.frame_current,
        'subframe': bpy.context.scene.frame_subframe,
        'owner': obj.name,
        'matrix_world': _matrix(obj.matrix_world).tolist(),
        'raw_vertex_sha256': hashlib.sha256(_coords(obj.data.vertices).tobytes()).hexdigest(),
        'weights': [[(g.group, g.weight) for g in v.groups] for v in obj.data.vertices],
        'vertex_groups': [g.name for g in obj.vertex_groups],
        'keys': [{'name': k.name, 'value': k.value, 'mute': k.mute,
                  'relative': k.relative_key.name, 'vertex_group': k.vertex_group,
                  'co_sha256': hashlib.sha256(_coords(k.data).tobytes()).hexdigest()}
                 for k in obj.data.shape_keys.key_blocks] if obj.data.shape_keys else [],
        'show_only_shape_key': obj.show_only_shape_key,
        'active_shape_key_index': obj.active_shape_key_index,
        'rig': rig.name,
        'rig_matrix_world': _matrix(rig.matrix_world).tolist(),
        'rig_pose_position': rig.data.pose_position,
        'bones': {b.name: {'matrix_local': _matrix(b.matrix_local).tolist(),
                         'parent': b.parent.name if b.parent else None,
                         'use_deform': b.use_deform, 'envelope_distance': b.envelope_distance,
                         'envelope_weight': b.envelope_weight,
                         'head_radius': b.head_radius, 'tail_radius': b.tail_radius,
                         'matrix': _matrix(rig.pose.bones[b.name].matrix).tolist(),
                         'matrix_basis': _matrix(rig.pose.bones[b.name].matrix_basis).tolist()}
                  for b in rig.data.bones},
        'armature_flags': {k: getattr(armature_modifier, k) for k in (
            'use_deform_preserve_volume', 'use_vertex_groups', 'use_bone_envelopes',
            'use_multi_modifier', 'vertex_group', 'invert_vertex_group', 'show_viewport',
            'show_render', 'show_in_editmode', 'show_on_cage')},
    }
    return _json_hash(state), state


def _smooth_field(local):
    """Independent nonuniform 20..40 mm local field, not a basis probe."""
    lo, hi = local.min(axis=0), local.max(axis=0)
    u = (local - lo) / np.maximum(hi - lo, 1e-12)
    direction = np.column_stack((
        np.sin(2.1 * u[:, 2] + 0.37) + 0.25 * np.cos(2.7 * u[:, 1]),
        np.cos(1.8 * u[:, 0] - 0.31) + 0.3 * np.sin(3.1 * u[:, 2]),
        0.6 + 0.4 * np.sin(2.4 * u[:, 1] + 1.3 * u[:, 0])))
    direction /= np.linalg.norm(direction, axis=1)[:, None]
    phase = 0.5 + 0.5 * np.sin(2.8 * u[:, 2] - 1.7 * u[:, 0] + 0.6 * u[:, 1])
    amplitude = 0.020 + 0.020 * phase
    return direction * amplitude[:, None]


def _stats(errors):
    return {'max_m': float(np.max(errors)), 'rms_m': float(np.sqrt(np.mean(errors**2))),
            'p95_m': float(np.percentile(errors, 95))}


def build_mapping(current_object, *, probe_m=0.01, tolerance_m=2e-5,
                  max_condition=1e6):
    """Return q0/J/inverse and actual field roundtrip proof for current frame.

    Arrays use raw vertex order. J[v,world_axis,local_axis] maps an ADDITIVE
    pre-Armature local offset to world displacement. target_world_to_local_delta
    returns that offset; it is not an absolute coordinate. Mapping excludes all
    post-Armature modifiers. A changed rig/pose/weights/shape-key state needs a
    fresh build. Never apply to evaluated/subdivided vertex indices.

    No original object/mesh/key/rig/modifier is modified. The helper does not open
    or save a scene. It rejects unsupported pre-Armature processing and reports
    FAIL (without a usable inverse) for singular or non-affine responses.
    """
    obj = current_object
    if obj.type != 'MESH' or obj.mode != 'OBJECT':
        raise ValueError('An OBJECT-mode mesh is required')
    if not np.isfinite(probe_m) or probe_m <= 0:
        raise ValueError('probe_m must be positive and finite')
    arms = [(i, m) for i, m in enumerate(obj.modifiers) if m.type == 'ARMATURE' and m.show_viewport]
    if len(arms) != 1:
        raise ValueError('Exactly one enabled Armature modifier is required')
    arm_index, arm = arms[0]
    if arm.object is None or arm.use_multi_modifier:
        raise ValueError('A bound standalone Armature is required; multi_modifier unsupported')
    if any(m.show_viewport for m in list(obj.modifiers)[:arm_index]):
        raise ValueError('Enabled pre-Armature modifiers are outside ARMATURE-only scope')
    if any(m.type == 'ARMATURE' for m in list(obj.modifiers)[arm_index + 1:]):
        raise ValueError('Multiple Armature modifiers are outside the mapping scope')
    bpy.context.view_layer.update()
    signature, pose = pose_signature(obj, arm)
    private_obj = private_mesh = group = None
    private_key_name = None
    n = len(obj.data.vertices)
    uid = uuid.uuid4().hex
    attr_name = '_MIA_POSE_SPACE_OFFSET_' + uid
    original_matrix = _matrix(obj.matrix_world)
    try:
        private_obj = obj.copy()
        private_obj.name = '_MIA_POSE_SPACE_PROBE_' + uid
        private_mesh = obj.data.copy()
        private_mesh.name = '_MIA_POSE_SPACE_MESH_' + uid
        private_obj.data = private_mesh
        if private_mesh.shape_keys:
            if private_mesh.shape_keys == obj.data.shape_keys:
                raise RuntimeError('Mesh.copy unexpectedly shares original shape keys')
            private_key_name = private_mesh.shape_keys.name
        bpy.context.scene.collection.objects.link(private_obj)
        private_obj.hide_render = True
        private_obj.hide_viewport = False
        private_obj.hide_set(False)
        # Object.copy owns an independent modifier stack; never edit obj.modifiers.
        post = []
        for i, modifier in enumerate(private_obj.modifiers):
            if i > arm_index:
                post.append({'name': modifier.name, 'type': modifier.type,
                             'original_viewport': modifier.show_viewport,
                             'original_render': modifier.show_render})
                modifier.show_viewport = False
                modifier.show_render = False
        attribute = private_mesh.attributes.new(attr_name, 'FLOAT_VECTOR', 'POINT')
        group = bpy.data.node_groups.new('_MIA_POSE_SPACE_GN_' + uid, 'GeometryNodeTree')
        group.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
        group.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
        inp = group.nodes.new('NodeGroupInput')
        out = group.nodes.new('NodeGroupOutput')
        offset = group.nodes.new('GeometryNodeInputNamedAttribute')
        offset.data_type = 'FLOAT_VECTOR'
        offset.inputs['Name'].default_value = attr_name
        set_position = group.nodes.new('GeometryNodeSetPosition')
        group.links.new(inp.outputs['Geometry'], set_position.inputs['Geometry'])
        group.links.new(offset.outputs['Attribute'], set_position.inputs['Offset'])
        group.links.new(set_position.outputs['Geometry'], out.inputs['Geometry'])
        gn = private_obj.modifiers.new('_MIA_POSE_SPACE_OFFSET_' + uid, 'NODES')
        gn.node_group = group
        with bpy.context.temp_override(object=private_obj, active_object=private_obj):
            bpy.ops.object.modifier_move_to_index(modifier=gn.name, index=arm_index)

        def evaluate(field):
            attribute.data.foreach_set('vector', np.asarray(field, dtype=np.float32).ravel())
            private_mesh.update()
            private_obj.update_tag(refresh={'DATA'})
            bpy.context.view_layer.update()
            depsgraph = bpy.context.evaluated_depsgraph_get()
            evaluated = private_obj.evaluated_get(depsgraph)
            mesh = evaluated.to_mesh()
            try:
                if len(mesh.vertices) != n:
                    raise RuntimeError('Control-cage vertex count changed')
                local = _coords(mesh.vertices)
                return _world(local, _matrix(evaluated.matrix_world))
            finally:
                evaluated.to_mesh_clear()

        zero = np.zeros((n, 3), dtype=np.float64)
        q0 = evaluate(zero)
        gn.show_viewport = False
        without_offset_node = evaluate(zero)
        gn.show_viewport = True
        zero_node_error = float(np.max(np.linalg.norm(q0 - without_offset_node, axis=1)))
        j = np.empty((n, 3, 3), dtype=np.float64)
        central_midpoint_error = []
        for axis in range(3):
            probe = zero.copy()
            probe[:, axis] = probe_m
            plus = evaluate(probe)
            minus = evaluate(-probe)
            j[:, :, axis] = (plus - minus) / (2 * probe_m)
            central_midpoint_error.append(float(np.max(np.linalg.norm((plus + minus) / 2 - q0, axis=1))))
        singular_values = np.linalg.svd(j, compute_uv=False)
        condition = singular_values[:, 0] / np.maximum(singular_values[:, -1], 1e-300)
        well_conditioned = bool(np.all(np.isfinite(condition)) and np.max(condition) <= max_condition
                                and np.min(singular_values[:, -1]) > 1e-10)
        inverse = np.linalg.inv(j) if well_conditioned else None
        # Independent smooth vector field, evaluated beyond the 10 mm probes.
        field = _smooth_field(_coords(obj.data.vertices))
        q_actual = evaluate(field)
        q_prediction = q0 + np.einsum('nij,nj->ni', j, field)
        forward_error = np.linalg.norm(q_actual - q_prediction, axis=1)
        if inverse is not None:
            recovered_field = np.einsum('nij,nj->ni', inverse, q_actual - q0)
            local_error = np.linalg.norm(recovered_field - field, axis=1)
            q_roundtrip = evaluate(recovered_field)
            roundtrip_error = np.linalg.norm(q_roundtrip - q_actual, axis=1)
        else:
            recovered_field = np.full_like(field, np.nan)
            q_roundtrip = np.full_like(q0, np.nan)
            local_error = roundtrip_error = np.full(n, np.inf)
        passed = bool(well_conditioned and zero_node_error <= tolerance_m and np.max(forward_error) <= tolerance_m
                      and np.max(roundtrip_error) <= tolerance_m and np.max(local_error) <= tolerance_m)
        metadata = {
            'schema_version': 1, 'status': 'PASS' if passed else 'FAIL',
            'scope': 'current shape-key state + sole Armature control cage; pre-Weld/Subsurf/Smooth/outline',
            'semantics': 'q_world = q0_world + J_world_from_local @ additive_pre_armature_local_delta',
            'owner': obj.name, 'vertex_count': n, 'frame': bpy.context.scene.frame_current,
            'shape_key_count': len(obj.data.shape_keys.key_blocks) if obj.data.shape_keys else 0,
            'blender_version': bpy.app.version_string, 'probe_m': float(probe_m),
            'pose_sha256': signature, 'rig': arm.object.name,
            'armature_flags': pose['armature_flags'], 'disabled_post_modifiers_on_copy': post,
            'conditioning': {'min_singular_value': float(singular_values[:, -1].min()),
                             'max_singular_value': float(singular_values[:, 0].max()),
                             'max_condition': float(condition.max()),
                             'p95_condition': float(np.percentile(condition, 95)),
                             'condition_limit': float(max_condition),
                             'determinant_min': float(np.linalg.det(j).min()),
                             'determinant_max': float(np.linalg.det(j).max())},
            'verification': {'tolerance_m': float(tolerance_m),
                             'zero_offset_node_vs_no_node_max_m': zero_node_error,
                             'central_midpoint_max_m_by_axis': central_midpoint_error,
                             'field_definition': 'smooth nonuniform trigonometric direction and amplitude; independent of basis probes',
                             'field_amplitude_min_m': float(np.linalg.norm(field, axis=1).min()),
                             'field_amplitude_max_m': float(np.linalg.norm(field, axis=1).max()),
                             'forward_prediction': _stats(forward_error),
                             'world_to_local_delta': _stats(local_error),
                             'actual_re_evaluated_roundtrip': _stats(roundtrip_error)},
            'limitations': ['Fixed pose/weights/key state only; rebuild when state changes.',
                           'No post-Armature surface inverse, body fit, rig retarget, render, or art acceptance.',
                           'Envelope response may depend on location; finite field test covers this field only.'],
        }
        q0_local = (q0 - original_matrix[:3, 3]) @ np.linalg.inv(original_matrix[:3, :3]).T
        return {'q0_world': q0, 'q0_local': q0_local,
                'J_world_from_local': j, 'local_from_world': inverse,
                'matrix_world': original_matrix, 'control_local': _coords(obj.data.vertices),
                'singular_values': singular_values, 'condition': condition,
                'test_local_field': field, 'test_actual_world': q_actual,
                'test_recovered_local_field': recovered_field, 'test_roundtrip_world': q_roundtrip,
                'metadata': metadata, 'pose_state': pose}
    finally:
        if private_obj is not None:
            bpy.data.objects.remove(private_obj, do_unlink=True)
        if private_mesh is not None and private_mesh.users == 0:
            bpy.data.meshes.remove(private_mesh)
        if private_key_name:
            key = bpy.data.shape_keys.get(private_key_name)
            if key is not None and key.users == 0:
                bpy.data.shape_keys.remove(key)
        if group is not None and group.users == 0:
            bpy.data.node_groups.remove(group)
        bpy.context.view_layer.update()


def target_world_to_local_delta(mapping, target_world):
    """Convert (N,3) world targets into ADDITIVE local cage offsets."""
    if mapping['metadata']['status'] != 'PASS' or mapping['local_from_world'] is None:
        raise ValueError('The empirical map did not pass its roundtrip/conditioning check')
    target = np.asarray(target_world, dtype=np.float64)
    if target.shape != mapping['q0_world'].shape or not np.all(np.isfinite(target)):
        raise ValueError('target_world must be finite (raw_vertex_count, 3)')
    return np.einsum('nij,nj->ni', mapping['local_from_world'], target - mapping['q0_world'])


def save_mapping(mapping, stem):
    """Serialize numeric arrays + JSON metadata. Does not save Blender native."""
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    arrays = {k: v for k, v in mapping.items() if isinstance(v, np.ndarray)}
    np.savez_compressed(str(stem) + '.npz', **arrays)
    payload = dict(mapping['metadata'])
    pose = mapping['pose_state']
    payload['pose_guard_summary'] = {k: pose[k] for k in (
        'frame', 'subframe', 'owner', 'matrix_world', 'rig', 'rig_matrix_world',
        'rig_pose_position', 'show_only_shape_key', 'active_shape_key_index')}
    payload['pose_guard_summary']['active_keys'] = {k['name']: k['value'] for k in pose['keys'] if k['value']}
    payload['npz_sha256'] = hashlib.sha256(Path(str(stem) + '.npz').read_bytes()).hexdigest()
    Path(str(stem) + '.json').write_text(json.dumps(payload, indent=2, sort_keys=True), encoding='utf-8')
