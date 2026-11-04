"""Preserve the two known static selection groups across a mesh-pointer trial.

These are diagnostic selections, not deformation/rig weights. The existing
object group collection is never created, cleared, reordered or removed.
"""
import hashlib
import numpy as np

KNOWN = {'MIA_Live_Neck_Interior', 'MIA_Live_UpperFair'}
ENTRY = np.dtype([('vertex', '<i4'), ('group', '<i4'), ('weight', '<f4')])


def metadata(body):
    return dict(groups=[dict(index=int(g.index), name=g.name, lock_weight=bool(g.lock_weight))
                        for g in body.vertex_groups], active_index=int(body.vertex_groups.active_index))


def require_known(body):
    result = metadata(body)
    names = {g['name'] for g in result['groups']}
    assert names in (set(), KNOWN) and len(result['groups']) in (0, 2), 'Unknown static body vertex group'
    assert [g['index'] for g in result['groups']] == list(range(len(result['groups'])))
    return result


def entries(mesh):
    values = np.fromiter(((int(v.index), int(g.group), float(g.weight))
                          for v in mesh.vertices for g in v.groups), dtype=ENTRY)
    if len(values):
        values.sort(order=['vertex', 'group'])
        assert np.isfinite(values['weight']).all()
        assert ((values['weight'] >= 0)&(values['weight'] <= 1)).all()
        duplicate = (values['vertex'][1:] == values['vertex'][:-1])&(values['group'][1:] == values['group'][:-1])
        assert not duplicate.any(), 'Duplicate deform-group entry'
    return values


def digest(values):
    return hashlib.sha256(np.ascontiguousarray(values, dtype=ENTRY).tobytes()).hexdigest()


def remap_retained(old_values, baseline_vertex, old_count):
    """Copy only exact old point owners. New/cut/template points stay unweighted."""
    mapping = np.asarray(baseline_vertex, np.int32)
    assert ((mapping >= -1)&(mapping < old_count)).all()
    new_ids = np.flatnonzero(mapping >= 0)
    assert len(np.unique(mapping[new_ids])) == len(new_ids), 'Repeated baseline point ownership'
    inverse = np.full(old_count, -1, np.int32); inverse[mapping[new_ids]] = new_ids
    if not len(old_values): return np.empty(0, dtype=ENTRY)
    assert ((old_values['vertex'] >= 0)&(old_values['vertex'] < old_count)).all()
    target = inverse[old_values['vertex']]
    keep = target >= 0
    result = old_values[keep].copy(); result['vertex'] = target[keep]
    result.sort(order=['vertex', 'group'])
    return result


def assign_to_fresh_mesh(body, expected, original_metadata):
    """Existing handles write only the now-current fresh mesh, in weight batches."""
    assert metadata(body) == original_metadata, 'Group metadata changed before transfer'
    assert not len(entries(body.data)), 'New mesh unexpectedly has deform weights; do not clear them'
    batches = 0
    for group_id in np.unique(expected['group']):
        selected = expected[expected['group'] == group_id]
        for weight in np.unique(selected['weight']):
            ids = selected['vertex'][selected['weight'] == weight]
            body.vertex_groups[int(group_id)].add(ids.tolist(), float(weight), 'REPLACE')
            batches += 1
    if original_metadata['groups']:
        body.vertex_groups.active_index = original_metadata['active_index']
    assert metadata(body) == original_metadata, 'Group names/order/locks/active changed'
    actual = entries(body.data)
    assert np.array_equal(actual, expected), 'Retained diagnostic weights differ after readback'
    return dict(entries=len(actual), unique_weight_batches=batches, sha256=digest(actual),
                new_points_unweighted=True, meaning='Selection diagnostics only; not a rig/deformation transfer')
