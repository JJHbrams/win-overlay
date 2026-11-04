"""Preserve the two known static selection groups across a mesh-pointer trial.

These are diagnostic selections, not deformation/rig weights. Blender stores
group definitions/active index on Mesh despite its Object.vertex_groups API.
Original definitions are never altered; the fresh mesh receives exact copies.
Measured in the isolated live Blender 5.2 probe: swapping A -> fresh B exposes
zero groups/active -1, while swapping B -> A recovers A's two groups/active 1.
Candidate definitions are NEW mesh-owned records, not original Object handles.
Official source (main inspected, not claimed as the installed build revision):
https://github.com/blender/blender/blob/main/source/blender/blenkernel/intern/deform.cc
BKE_id_defgroup_list_get and object_defgroup_active_index_get_p read Mesh fields.
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


def metadata_for_mesh(bpy_module, mesh):
    """Read mesh-owned definitions without switching the scene actor's data."""
    holder = bpy_module.data.objects.new('MIA_UpperTemplate03_GroupMetadata', mesh)
    try:
        return metadata(holder)
    finally:
        bpy_module.data.objects.remove(holder, do_unlink=True)


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
    """Candidate group handles write only its fresh mesh, in weight batches."""
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


def prepare_fresh_mesh(bpy_module, mesh, expected, original_metadata):
    """Populate the candidate before the scene actor's pointer is changed.

    A temporary unlinked Object provides Blender's group RNA facade. Definitions
    survive removal of that holder because they belong to this candidate Mesh.
    Never clear a group collection or borrow original-mesh group handles here.
    """
    holder = bpy_module.data.objects.new('MIA_UpperTemplate03_GroupTransfer', mesh)
    try:
        assert not len(holder.vertex_groups), 'Candidate already has group definitions'
        assert not len(entries(mesh)), 'Candidate already has deform weights'
        for rec in original_metadata['groups']:
            group = holder.vertex_groups.new(name=rec['name'])
            assert int(group.index) == rec['index'] and group.name == rec['name']
            group.lock_weight = rec['lock_weight']
        if original_metadata['groups']:
            holder.vertex_groups.active_index = original_metadata['active_index']
        assert metadata(holder) == original_metadata, 'Candidate group definitions differ'
        return assign_to_fresh_mesh(holder, expected, original_metadata)
    finally:
        bpy_module.data.objects.remove(holder, do_unlink=True)
