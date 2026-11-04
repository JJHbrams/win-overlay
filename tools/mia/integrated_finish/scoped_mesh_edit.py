"""Explicit-ID scope gate and one reversible raw-mesh edit, not a sculpt solver.

Only fixed triangle topology and float32 coordinates are supported. Unsupported
modifiers, shape keys or shared mesh owners are rejected before mutation. This
is a cooperative production guard; arbitrary Python/raw MCP can bypass it. It
does not establish art likeness, anatomical correctness or application security.
"""
from pathlib import Path
import hashlib
import json
import runpy
import numpy as np

KEY = 'MIA_ScopedMeshEdit_PENDING'
LAST = 'MIA_ScopedMeshEdit_LAST_REVIEW'


class ScopeError(ValueError):
    pass


def _sha(a): return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def _coordinates(a, label):
    if not isinstance(a, np.ndarray) or a.dtype != np.float32 or a.ndim != 2 or a.shape[1] != 3:
        raise ScopeError(label+' must be a float32[N,3] array; topology-bearing candidates are unsupported')
    if not np.isfinite(a).all(): raise ScopeError(label+' has nonfinite coordinates')
    return a


def _faces(a, count):
    a = np.asarray(a)
    if a.ndim != 2 or a.shape[1] != 3 or a.dtype.kind not in 'iu':
        raise ScopeError('Only an explicit fixed integer triangle[M,3] topology is supported')
    if a.size and (a.min() < 0 or a.max() >= count): raise ScopeError('Triangle index outside vertex range')
    if len(a) and ((a[:, 0] == a[:, 1]) | (a[:, 1] == a[:, 2]) | (a[:, 0] == a[:, 2])).any():
        raise ScopeError('Degenerate index topology is unsupported')
    return a.astype(np.int32, copy=False)


def _ids(a, count, label):
    a = np.asarray(a)
    if a.ndim != 1 or (a.size and a.dtype.kind not in 'iu'):
        raise ScopeError(label+' must be an explicit one-dimensional integer ID array')
    if a.size and (a.min() < 0 or a.max() >= count): raise ScopeError(label+' has out-of-range IDs')
    if len(np.unique(a)) != len(a): raise ScopeError(label+' contains duplicate IDs')
    return a.astype(np.int32, copy=False)


def topology_sha256(faces, vertex_count):
    return _sha(_faces(faces, vertex_count))


def validate_delta(before, candidate, faces, editable_ids, transition_ids, protected_regions,
                   *, expected_before_sha256=None, expected_topology_sha256=None):
    before = _coordinates(before, 'before'); candidate = _coordinates(candidate, 'candidate')
    if before.shape != candidate.shape: raise ScopeError('Vertex count/order changes are unsupported')
    f = _faces(faces, len(before)); topo = _sha(f); base = _sha(before)
    if expected_before_sha256 is not None and base != expected_before_sha256: raise ScopeError('Stale baseline coordinate SHA')
    if expected_topology_sha256 is not None and topo != expected_topology_sha256: raise ScopeError('Stale/changed topology SHA')
    editable = _ids(editable_ids, len(before), 'editable_ids')
    transition = _ids(transition_ids, len(before), 'transition_ids')
    if np.intersect1d(editable, transition).size: raise ScopeError('Editable and transition IDs overlap')
    if not isinstance(protected_regions, dict) or not protected_regions:
        raise ScopeError('Named anatomical protected regions are required; a bounding box is insufficient')
    allowed = np.zeros(len(before), bool); allowed[editable] = True; allowed[transition] = True
    regions = {}
    for name, values in protected_regions.items():
        if not isinstance(name, str) or not name.strip(): raise ScopeError('Protected region needs a readable anatomical name')
        ids = _ids(values, len(before), 'protected region '+name)
        if not len(ids): raise ScopeError('Protected region '+name+' is empty')
        if allowed[ids].any(): raise ScopeError('Edit/fixed overlap in protected region '+name)
        regions[name] = dict(count=len(ids), ids_sha256=_sha(ids), coordinates_sha256=_sha(before[ids]))
    # Signed-zero and every float32 bit are held outside the declared ID union.
    changed = (before.view(np.uint32) != candidate.view(np.uint32)).any(axis=1)
    illegal = np.flatnonzero(changed & ~allowed)
    if len(illegal): raise ScopeError('Displacement outside explicit edit/transition IDs: '+str(illegal[:16].tolist()))
    return dict(status='SCOPE_VALID_ONLY', before_sha256=base, candidate_sha256=_sha(candidate),
        topology_sha256=topo, vertices=len(before), triangles=len(f),
        editable_count=len(editable), transition_count=len(transition), changed_vertices=int(changed.sum()),
        editable_ids_sha256=_sha(editable), transition_ids_sha256=_sha(transition),
        protected_regions=regions, exact_outside_union=True, ART=False)


def _tools(root):
    folder = Path(root)/'tools/mia'
    return (runpy.run_path(str(folder/'face_surface_live/v29_pigment_current.py')),
            runpy.run_path(str(folder/'integrated_finish/arm_chain01_live.py')))


def _mesh_arrays(mesh):
    if any(len(p.vertices) != 3 for p in mesh.polygons): raise ScopeError('Nontriangle topology is unsupported')
    q = np.empty((len(mesh.vertices), 3), np.float32); mesh.vertices.foreach_get('co', q.ravel())
    f = np.empty((len(mesh.polygons), 3), np.int32); mesh.loops.foreach_get('vertex_index', f.ravel())
    return q, f


def _declaration(value):
    if not isinstance(value, dict) or any(not isinstance(value.get(k), str) or not value[k].strip()
                                        for k in ('editable', 'transition', 'basis')):
        raise ScopeError('Anatomical declaration requires readable editable, transition and basis text')
    return dict(value)


def _verify_state(state, candidate):
    import bpy
    guard, live = _tools(state['root']); ob = bpy.data.objects[state['object_name']]
    mesh = state['owned'] if candidate else state['original']
    if ob.data != mesh: raise ScopeError('Actual mesh pointer changed')
    q, f = _mesh_arrays(mesh)
    expected = state['proof']['candidate_sha256' if candidate else 'before_sha256']
    if _sha(q) != expected or _sha(f) != state['proof']['topology_sha256']: raise ScopeError('Actual geometry changed')
    if live['_without_position'](guard['_mesh_payload'](mesh)) != live['_without_position'](state['payload']):
        raise ScopeError('Non-position payload changed')
    if live['_groups'](ob) != state['groups'] or live['_uv_flags'](mesh) != state['uv_flags']:
        raise ScopeError('Diagnostic groups or UV flags changed')
    context = live['_context'](state['root'], guard)
    expected_context = json.loads(json.dumps(state['context']))
    expected_context['objects'][ob.name]['data'] = int(mesh.as_pointer())
    if guard['canonical'](context) != guard['canonical'](expected_context): raise ScopeError('Other actor/pose/modifier/context changed')
    if guard['materials_signature']() != state['materials']: raise ScopeError('Material graphs changed')
    if guard['_mesh_payload'](state['original']) != state['payload']: raise ScopeError('Retained original payload changed')
    return ob, guard, live


def apply(root, object_name, candidate, faces, editable_ids, transition_ids, protected_regions,
          expected_before_sha256, expected_topology_sha256, anatomical_declaration):
    import bpy
    if KEY in bpy.app.driver_namespace: raise ScopeError('One edit is pending: record_keep or restore before another edit')
    root = str(Path(root).resolve()); declaration = _declaration(anatomical_declaration)
    if bpy.context.mode != 'OBJECT': raise ScopeError('Object mode is required')
    ob = bpy.data.objects.get(object_name)
    if ob is None or ob.type != 'MESH': raise ScopeError('Named actual mesh object not found')
    original = ob.data
    owners = [o.name for o in bpy.data.objects if o.type == 'MESH' and o.data == original]
    if owners != [ob.name] or original.users != 1: raise ScopeError('Shared mesh owners require a separate explicit operation')
    if original.shape_keys is not None or len(ob.modifiers):
        raise ScopeError('Shape-key/modifier transport is unsupported; no automatic deletion or rebinding')
    before, actual_faces = _mesh_arrays(original)
    if not np.array_equal(_faces(faces, len(before)), actual_faces): raise ScopeError('Proposed topology differs from actual named mesh')
    proof = validate_delta(before, candidate, actual_faces, editable_ids, transition_ids, protected_regions,
        expected_before_sha256=expected_before_sha256, expected_topology_sha256=expected_topology_sha256)
    guard, live = _tools(root)
    state = dict(root=root, object_name=ob.name, original=original, owned=None, proof=proof,
        anatomical_declaration=declaration, payload=guard['_mesh_payload'](original),
        context=live['_context'](root, guard), materials=guard['materials_signature'](),
        groups=live['_groups'](ob), uv_flags=live['_uv_flags'](original))
    # Everything above is read-only. The first and only editable copy is here.
    bpy.app.driver_namespace[KEY] = state
    try:
        mesh = original.copy(); state['owned'] = mesh; mesh.name = ob.name+'_SCOPED_PENDING'
        ob.data = mesh; mesh.vertices.foreach_set('co', candidate.ravel()); mesh.update()
        bpy.context.view_layer.update(); _verify_state(state, True)
        return dict(proof, status='APPLIED_PENDING_REVIEW', pending_key=KEY,
                    original_pointer=int(original.as_pointer()), native_saved=False,
                    anatomical_declaration=declaration, limitation='Scope only, not likeness/anatomy/collision acceptance')
    except BaseException:
        ob.data = original; state['restore_pending'] = True; bpy.context.view_layer.update()
        _verify_state(state, False)
        if state['owned'] is not None:
            if state['owned'].users: raise ScopeError('Owned copy unexpectedly shared during rollback')
            bpy.data.meshes.remove(state['owned'], do_unlink=False); state['owned'] = None
        bpy.app.driver_namespace.pop(KEY, None)
        raise


def restore():
    import bpy
    state = bpy.app.driver_namespace[KEY]
    if bpy.context.mode != 'OBJECT': raise ScopeError('Object mode is required')
    if not state.get('restore_pending'): _verify_state(state, True)
    ob = bpy.data.objects[state['object_name']]
    if ob.data not in (state['original'], state['owned']):
        raise ScopeError('Interrupted restore cannot overwrite an unrelated later mesh binding')
    ob.data = state['original']; state['restore_pending'] = True
    bpy.context.view_layer.update(); _verify_state(state, False)
    if state['owned'] is not None:
        if state['owned'].users: raise ScopeError('Owned copy unexpectedly shared during restore')
        bpy.data.meshes.remove(state['owned'], do_unlink=False); state['owned'] = None
    bpy.app.driver_namespace.pop(KEY, None)
    return dict(status='RESTORED_EXACT_ORIGINAL_POINTER', before_sha256=state['proof']['before_sha256'], native_saved=False, ART=False)


def record_keep(review):
    """Root records a WIP decision; this is not automatic art approval."""
    import bpy
    if not isinstance(review, dict) or review.get('decision') != 'keep_wip' or not review.get('evidence') or not review.get('reviewer'):
        raise ScopeError('Explicit root keep_wip decision, reviewer and evidence are required')
    state = bpy.app.driver_namespace[KEY]; _verify_state(state, True)
    record = dict(status='ROOT_RECORDED_KEEP_WIP', proof=state['proof'], review=dict(review),
                  original_mesh_name=state['original'].name, original_pointer=int(state['original'].as_pointer()),
                  native_saved=False, ART=False)
    bpy.app.driver_namespace[LAST] = record
    del bpy.app.driver_namespace[KEY]
    return record
