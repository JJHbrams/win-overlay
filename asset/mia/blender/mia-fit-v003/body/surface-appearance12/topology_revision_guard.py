"""Topology-changing E receipt primitives; no producer/native mutation.

Unlike receive_revision.py, this module never assumes stable vertex/triangle
IDs or stable body UVs. Its physical replacement rules must come from the
authorized E section/branch metadata, not a post-hoc nearest-position fit.
"""
import numpy as np
from surface_api import array_sha


def physical_replacement_mask(previous, sections, protected_core_ids):
    world, triangles = previous['world'], previous['triangles']
    allowed = np.zeros(len(world), bool)
    reports = []
    for section in sections:
        axis = np.asarray(section['axis_world'], float)
        origin = np.asarray(section['origin_world'], float)
        if axis.shape != (3,) or origin.shape != (3,) or abs(np.linalg.norm(axis)-1) > 1e-6:
            raise ValueError('Replacement section needs a normalized world axis/origin')
        lower, upper = float(section['min_m']), float(section['max_m'])
        if not lower < upper:
            raise ValueError('Replacement section bounds are invalid')
        ids = section['allowed_old_face_regions']
        if not ids or any(int(x) in [3, 12] for x in ids):
            raise ValueError('Neck regions cannot be authorized replacement branches')
        branch = np.zeros(len(world), bool)
        branch[np.unique(triangles[np.isin(previous['face_region'], ids)])] = True
        denied = section.get('deny_old_face_regions', [])
        if denied:
            branch[np.unique(triangles[np.isin(previous['face_region'], denied)])] = False
        coordinate = (world.astype(float)-origin) @ axis
        tolerance = float(section.get('numeric_tolerance_m', 1e-6))
        if tolerance < 0 or tolerance > 1e-5:
            raise ValueError('Unexpected physical section numeric tolerance')
        selected = branch & (coordinate >= lower-tolerance) & (coordinate <= upper+tolerance)
        allowed |= selected
        reports.append(dict(name=section['name'], branch_vertex_count=int(branch.sum()),
                            inside_physical_section=int(selected.sum()),
                            numeric_tolerance_m=tolerance, section=dict(section)))
    # Vertices absent from body-only triangles include the retained head. Every
    # one is mandatory, including any unused source vertex; no sample subset.
    body_used = np.zeros(len(world), bool)
    body_used[np.unique(triangles)] = True
    protected = ~body_used
    neck_ids = np.unique(triangles[np.isin(previous['face_region'], [3, 12])])
    protected[neck_ids] = True
    core_ids = np.asarray(protected_core_ids, np.int64)
    if core_ids.ndim != 1 or (len(core_ids) and (core_ids.min()<0 or core_ids.max()>=len(world))):
        raise ValueError('Explicit protected core IDs are invalid')
    protected[core_ids] = True
    allowed[protected] = False
    return allowed, dict(sections=reports, mandatory_head_or_nonbody_vertices=int((~body_used).sum()),
                         mandatory_neck_region_vertices=len(neck_ids), explicit_protected_core_vertices=len(np.unique(core_ids)),
                         mandatory_protected_vertices=int(protected.sum()))


def certify_artificial_forearm_points(previous, target, evidence):
    """E-only representation exception for 200 obsolete source-face cut points.

    Caller supplies provenance arrays from the actual fingerprinted joined
    meshes, sliced into each body export's triangle order. Triangle IDs here
    are target BODY triangle IDs, not unrestricted nearest-face queries.
    """
    old_ids = np.asarray(evidence['interpolated_old_vertex_id'], np.int64)
    new_tri = np.asarray(evidence['interpolated_new_triangle_id'], np.int64)
    bary = np.asarray(evidence['interpolated_new_barycentric'], float)
    source_face = np.asarray(evidence['interpolated_source_face'], np.int64)
    old_source_vertex = np.asarray(evidence['old_source_vertex'], np.int64)
    old_source_face = np.asarray(evidence['old_source_face'], np.int64)
    new_source_face = np.asarray(evidence['new_source_face'], np.int64)
    old_bary = np.asarray(evidence['old_source_corner_bary'], float)
    new_bary = np.asarray(evidence['new_source_corner_bary'], float)
    count = len(old_ids)
    if count != 200 or len(np.unique(old_ids)) != count:
        raise ValueError('Only the explicit 200 obsolete D3 forearm points may use E representation proof')
    if new_tri.shape != (count,) or source_face.shape != (count,) or bary.shape != (count, 3):
        raise ValueError('Artificial source-face proof arrays have inconsistent shapes')
    if old_ids.min()<0 or old_ids.max()>=len(previous['world']) or new_tri.min()<0 or new_tri.max()>=len(target['triangles']):
        raise ValueError('Artificial source-face proof IDs out of range')
    if not np.isfinite(bary).all() or np.any(bary < -1e-7) or np.any(bary > 1+1e-7) or np.any(abs(bary.sum(1)-1)>1e-7):
        raise ValueError('Target triangle barycentrics are not inside the actual triangle')
    if old_source_vertex.shape != (len(previous['world']),) or np.any(old_source_vertex[old_ids] != -1):
        raise ValueError('Original source vertices cannot use the artificial-point exception')
    if old_source_face.shape != (len(previous['triangles']),) or new_source_face.shape != (len(target['triangles']),):
        raise ValueError('Source-face arrays must be sliced into each actual body-triangle order')
    arm_vertices = np.zeros(len(previous['world']), bool)
    arm_vertices[np.unique(previous['triangles'][np.isin(previous['face_region'], [6, 7])])] = True
    if not arm_vertices[old_ids].all() or np.any(abs(previous['world'][old_ids, 2]-1.035)>5e-7):
        raise ValueError('Artificial-point exception is limited to the old forearm global-waist split')
    if old_bary.shape != (len(previous['triangles']), 3, 3) or new_bary.shape != (len(target['triangles']), 3, 3):
        raise ValueError('Actual per-corner source barycentric arrays are required')
    if np.any(source_face < 0) or not np.array_equal(new_source_face[new_tri], source_face):
        raise ValueError('Target representations must stay on the SAME original source_face')
    points = np.einsum('ij,ijk->ik', bary, target['world'][target['triangles'][new_tri]].astype(float))
    physical = np.linalg.norm(points-previous['world'][old_ids].astype(float), axis=1)
    if np.any(physical > 1e-6):
        raise ValueError('Source-face representation changes physical geometry beyond float32 rounding')
    source_residual, normal_angle = [], []
    for i, vertex in enumerate(old_ids):
        candidates = np.flatnonzero(np.any(previous['triangles']==vertex, axis=1) & (old_source_face==source_face[i]))
        if not len(candidates):
            raise ValueError('Old cut point has no actual incident triangle with the declared source_face')
        old_tri_world = previous['world'][previous['triangles'][candidates]].astype(float)
        normals = np.cross(old_tri_world[:, 1]-old_tri_world[:, 0], old_tri_world[:, 2]-old_tri_world[:, 0])
        areas2 = np.linalg.norm(normals, axis=1)
        choice = int(np.argmax(areas2))
        if areas2[choice] <= 1e-16:
            raise ValueError('Old source-face fragment has no geometric normal')
        old_normal = normals[choice]/areas2[choice]
        tri = target['world'][target['triangles'][new_tri[i]]].astype(float)
        new_normal = np.cross(tri[1]-tri[0], tri[2]-tri[0])
        new_normal /= max(float(np.linalg.norm(new_normal)), 1e-30)
        angle = float(np.degrees(np.arccos(np.clip(old_normal@new_normal, -1, 1))))
        normal_angle.append(angle)
        corner_values = []
        for index in candidates:
            corners = np.flatnonzero(previous['triangles'][index]==vertex)
            corner_values.extend(old_bary[index, corners])
        reproduced = bary[i] @ new_bary[new_tri[i]]
        residual = float(np.max(np.linalg.norm(np.asarray(corner_values)-reproduced, axis=1)))
        source_residual.append(residual)
    if max(source_residual) > 1e-6 or max(normal_angle) > .05:
        raise ValueError('Source barycentric/physical-normal evidence does not preserve the represented surface: '+repr(dict(
            source_bary_max=max(source_residual), normal_max_deg=max(normal_angle))))
    return dict(status='PASS source-face representation only, no geometry-movement exemption',
                old_vertex_ids=old_ids.tolist(), count=count,
                max_physical_rounding_residual_m=float(physical.max()),
                max_source_barycentric_residual=max(source_residual),
                max_geometric_normal_angle_deg=max(normal_angle),
                source_face_exact=True, original_source_vertex_exception=False,
                physical_tolerance_m=1e-6, source_barycentric_tolerance=1e-6,
                geometric_normal_tolerance_deg=.05,
                normal_method='Largest-area actual old incident fragment of same source_face vs actual target triangle; CUSTOM shading normals excluded.')


def certify_retained_correspondence(previous, target, correspondence, sections, protected_core_ids, *, representation=None):
    old_ids = np.asarray(correspondence['old_vertex_id'], np.int64)
    new_ids = np.asarray(correspondence['new_vertex_id'], np.int64)
    if old_ids.ndim != 1 or old_ids.shape != new_ids.shape or len(np.unique(old_ids)) != len(old_ids):
        raise ValueError('Retained correspondence must map each old vertex at most once')
    if not len(old_ids) or old_ids.min()<0 or old_ids.max()>=len(previous['world']):
        raise ValueError('Old retained vertex IDs are out of range')
    if new_ids.min()<0 or new_ids.max()>=len(target['world']):
        raise ValueError('New retained vertex IDs are out of range')
    allowed, rules = physical_replacement_mask(previous, sections, protected_core_ids)
    present = np.zeros(len(previous['world']), bool)
    present[old_ids] = True
    representation_report = None
    if representation is not None:
        representation_report = certify_artificial_forearm_points(previous, target, representation)
        represented = np.asarray(representation_report['old_vertex_ids'], np.int64)
        if present[represented].any():
            raise ValueError('Source-face exception must be separate from strict vertex correspondence')
        present[represented] = True
    missing = ~present
    forbidden = missing & ~allowed
    if forbidden.any():
        raise ValueError('Missing protected/outside-band old physical vertices: '+repr(np.flatnonzero(forbidden).tolist()))
    old_points = np.ascontiguousarray(previous['world'][old_ids])
    new_points = np.ascontiguousarray(target['world'][new_ids])
    mismatch = np.any(old_points.view(np.uint32) != new_points.view(np.uint32), axis=1)
    if mismatch.any():
        raise ValueError('Retained physical correspondence moved vertices: '+repr(old_ids[mismatch].tolist()))
    if previous['meta']['source_context'] != target['meta']['source_context']:
        raise ValueError('Frozen source cameras or original-pixel registrations changed')
    return dict(status='PASS complete physical retained correspondence; no native/art approval',
                old_vertices=len(previous['world']), new_vertices=len(target['world']),
                retained_correspondences=len(old_ids), retained_old_ids_sha256=array_sha(old_ids),
                retained_new_ids_sha256=array_sha(new_ids),
                old_vertices_replaced=int(missing.sum()), allowed_old_replacement_vertices=int(allowed.sum()),
                forbidden_old_vertices_removed=0, retained_world_coordinates_byte_exact=True,
                protected_outside_sections_complete=True, source_cameras_registration_held=True,
                source_face_representation=representation_report,
                topology_change_allowed=True,
                old_body_triangles=len(previous['triangles']), new_body_triangles=len(target['triangles']),
                previous_guards=previous['guards'], current_guards=target['guards'], physical_rules=rules,
                limits=['This guard does not replace independent actual head corner-UV/POINT/material/native checks.',
                        'New body atlas validation and fresh seating/bake remain required.'])
