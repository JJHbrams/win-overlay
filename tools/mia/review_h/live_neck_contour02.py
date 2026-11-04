"""Prepare or apply one reversible lower-neck/shoulder contour study in live Blender.

This is deliberately a single broad cervicothoracic transition, not a collection
of clavicle dents.  It leaves the upper neck, head, breast root, arm/waist joins,
UVs and topology untouched.  A source-art review decides whether it is retained.
"""
from pathlib import Path
import hashlib
import json
import sys

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/mia/review_h'))
import live_relax


OUT = ROOT / '.mia-cache/body-h/live/neck-contour02'
SOURCE = ROOT / '.mia-cache/body-h/shape/assembly/live-D/geometry.npz'
ROWS = ROOT / '.mia-cache/migration-to-C/row-ownership.npz'
BODY_NAME = 'MIA_Review12_H_LiveRepair'
KEY = 'MIA_NeckContour02'
BASE_SHA = '69d4d4f0ea907da2474bc74f4b55312971d137f0911bdf9089fc02509a6bf25a'
GROUP = 'MIA_NeckContour02_Selected'


def digest(values):
    return hashlib.sha256(np.ascontiguousarray(values, dtype=np.float32).tobytes()).hexdigest()


def smooth(value):
    value = np.clip(value, 0., 1.)
    return value * value * value * (10. - 15. * value + 6. * value * value)


def current_coordinates(ob):
    values = np.empty((len(ob.data.vertices), 3), np.float32)
    ob.data.vertices.foreach_get('co', values.ravel())
    return values


def make_candidate(world, faces, rows, source_part):
    """Redistribute actual lower-neck sections, then blend only their support.

    Earlier collar02 preparation only moved the outer cap.  The diagnosed flare
    lives in the lower neck rings themselves, so these are explicit section
    controls.  Their existing centroids and non-circular outlines remain; the
    operation scales their own lateral and AP radii rather than rebuilding a
    symmetric cylinder.
    """
    x, _, z = world.T
    head = np.unique(faces[source_part == 1])
    fixed = np.zeros(len(world), bool)
    fixed[head] = True
    for name in ('waist', 'armR', 'armL'):
        fixed[np.unique(rows[name])] = True
    # These rings attach to the face/head patch.  The lower twelve rings are
    # editable; freezing all 16 would preserve the diagnosed trumpet flare.
    fixed[np.unique(rows['neck'][12:])] = True
    fixed |= z <= 1.355
    fixed |= np.abs(x) >= .180

    z0, z1 = 1.355, 1.446
    lateral1 = .180
    in_band = (z > z0) & (z < z1) & (np.abs(x) < lateral1)
    eligible = in_band & ~fixed
    assert eligible.any(), 'No lower-neck transition vertices selected'

    boundary_weight, _ = live_relax.mask(world, faces, eligible, fade=.014)
    neck = rows['neck']
    ring_points = world[neck]
    ring_centers = ring_points.mean(1)
    ring_z = ring_centers[:, 2]
    # Lower root is visibly too broad/deep.  These chosen section targets taper
    # into the unchanged upper four rings; they are a single construction
    # hypothesis, not a coefficient search or an anatomical measurement.
    scale_x = np.array([.940, .948, .956, .964, .972, .980, .986, .990,
                        .994, .997, .999, .9995, 1., 1., 1., 1.])
    scale_y = np.array([.965, .970, .975, .980, .985, .990, .994, .997,
                        .999, .9995, 1., 1., 1., 1., 1., 1.])
    anchors_z = np.r_[z0, ring_z, z1]
    anchors_x = np.r_[1., scale_x, 1.]
    anchors_y = np.r_[1., scale_y, 1.]
    center_y = np.interp(z, anchors_z, np.r_[ring_centers[0, 1], ring_centers[:, 1], ring_centers[-1, 1]])
    sx = np.interp(z, anchors_z, anchors_x)
    sy = np.interp(z, anchors_z, anchors_y)
    # An elliptical support mask confines the section change to neck tissue and
    # gives the chest/root transition a tangent fade instead of a vertical band.
    radius_x = np.interp(z, anchors_z, np.r_[np.ptp(ring_points[0, :, 0]) / 2, np.abs(ring_points[:, :, 0] - ring_centers[:, None, 0]).max(1), np.ptp(ring_points[-1, :, 0]) / 2])
    radius_y = np.interp(z, anchors_z, np.r_[np.ptp(ring_points[0, :, 1]) / 2, np.abs(ring_points[:, :, 1] - ring_centers[:, None, 1]).max(1), np.ptp(ring_points[-1, :, 1]) / 2])
    radial = np.sqrt((x / np.maximum(radius_x, .001)) ** 2 + ((world[:, 1] - center_y) / np.maximum(radius_y, .001)) ** 2)
    neck_support = 1. - smooth((radial - .82) / .38)
    neck_support *= boundary_weight
    delta = np.zeros_like(world, dtype=np.float64)
    delta[:, 0] += neck_support * (sx - 1.) * x
    delta[:, 1] += neck_support * (sy - 1.) * (world[:, 1] - center_y)
    # Direct ring targets make the diagnosed section change explicit.  The
    # surrounding support field blends those targets into the chest surface.
    direct = np.zeros_like(world, dtype=np.float64)
    for index in range(12):
        ids = neck[index]
        center = ring_centers[index]
        direct[ids, 0] = (scale_x[index] - 1.) * (world[ids, 0] - center[0])
        direct[ids, 1] = (scale_y[index] - 1.) * (world[ids, 1] - center[1])
    delta[np.unique(neck[:12])] = direct[np.unique(neck[:12])]

    # The support surface receives only a small coupled ramp.  It cannot stand
    # in for the ring correction above and is bounded away from the arm passage.
    outer = boundary_weight * smooth((np.abs(x) - .070) / (.180 - .070))
    outer *= np.maximum(np.sin(np.pi * np.clip((z - z0) / (1.404 - z0), 0., 1.)), 0.)
    delta[:, 0] += -np.sign(x) * .0018 * outer
    delta[:, 2] += -.0022 * outer
    candidate = (world.astype(np.float64) + delta).astype(np.float32)
    changed = np.linalg.norm(candidate - world, axis=1) > 0
    assert not changed[fixed].any()
    assert np.isfinite(candidate).all()

    before = np.cross(world[faces[:, 1]] - world[faces[:, 0]], world[faces[:, 2]] - world[faces[:, 0]])
    after = np.cross(candidate[faces[:, 1]] - candidate[faces[:, 0]], candidate[faces[:, 2]] - candidate[faces[:, 0]])
    active = changed[faces].any(1)
    denominator = np.linalg.norm(before, axis=1) * np.linalg.norm(after, axis=1)
    cosine = np.sum(before * after, axis=1) / np.maximum(denominator, 1e-30)
    valid_before = np.linalg.norm(before, axis=1) > 1e-10
    active_valid = active & valid_before
    assert active_valid.any() and np.all(np.isfinite(cosine[active_valid]))
    assert cosine[active_valid].min() > .92, 'Transition would strain an active face'
    assert np.linalg.norm(after[active_valid], axis=1).min() > 1e-10, 'Transition would collapse an active face'

    ring_report = [dict(index=int(index), z_m=float(ring_z[index]),
                        max_abs_x_m=float(np.abs(candidate[ids, 0] - world[ids, 0]).max()),
                        max_abs_y_m=float(np.abs(candidate[ids, 1] - world[ids, 1]).max()),
                        max_abs_z_m=float(np.abs(candidate[ids, 2] - world[ids, 2]).max()),
                        half_width_before_m=float(np.abs(world[ids, 0] - center[0]).max()),
                        half_width_after_m=float(np.abs(candidate[ids, 0] - center[0]).max()))
                   for index, (ids, center) in enumerate(zip(neck, ring_centers))]
    before_width = np.array([item['half_width_before_m'] for item in ring_report])
    after_width = np.array([item['half_width_after_m'] for item in ring_report])
    before_secant = np.diff(before_width) / np.diff(ring_z)
    after_secant = np.diff(after_width) / np.diff(ring_z)
    report = dict(
        operation='ONE lower-neck cross-section redistribution: narrow/deepen-correct actual lower 12 neck rings and blend their support into a restrained clavicle-to-acromion ramp',
        visible_hypothesis='Retract the anterior lower-neck apron and reduce lateral root width before the shoulder slope begins; no local clavicle notch or independent cap-only sculpt is used.',
        baseline_sha256=digest(world), candidate_sha256=digest(candidate),
        changed_vertices=int(changed.sum()),
        maximum_displacement_m=float(np.linalg.norm(candidate - world, axis=1).max()),
        active_face_min_normal_cosine=float(cosine[active_valid].min()),
        active_face_max_turn_degrees=float(np.degrees(np.arccos(np.clip(cosine[active_valid].min(), -1., 1.)))),
        preexisting_near_degenerate_faces=int((~valid_before).sum()),
        domain=dict(z_m=[z0, z1], lateral_abs_x_m=[0., lateral1], boundary_fade_m=.014,
                    lower_ring_scale_x=scale_x[:12].tolist(), lower_ring_scale_y=scale_y[:12].tolist()),
        protected=dict(head_vertices=int(len(head)), upper_neck_rings='neck[12:16]',
                       exact_rows=['waist', 'armR', 'armL'], breast_root='z <= 1.355',
                       lateral_arm_passage='abs(x) >= .180'),
        neck_ring_displacement=ring_report,
        section_tangent_diagnostics=dict(
            meaning='Finite ring-width secants only; this records transition continuity but does not claim exact G1 continuity.',
            max_adjacent_before_width_secant_jump=float(np.abs(np.diff(before_secant)).max()),
            max_adjacent_after_width_secant_jump=float(np.abs(np.diff(after_secant)).max()),
            top_transition_before_width_secant_m_per_m=float(before_secant[11]),
            top_transition_after_width_secant_m_per_m=float(after_secant[11]),
            lower_ring_width_secants_before_m_per_m=before_secant[:4].tolist(),
            lower_ring_width_secants_after_m_per_m=after_secant[:4].tolist()),
        selection_group=GROUP, native_saved=False, art_accepted=False,
        review_required=['front', 'left_oblique', 'right_oblique', 'profile', 'back', 'high', 'low', 'hair_off_then_on'],
    )
    return candidate, changed, report


def mark_selection(ob, indices):
    group = ob.vertex_groups.get(GROUP) or ob.vertex_groups.new(name=GROUP)
    group.remove(list(range(len(ob.data.vertices))))
    group.add(indices.tolist(), 1., 'REPLACE')


def main():
    phase = globals().get('MIA_EDIT_PHASE', 'select')
    assert phase in ('select', 'apply')
    OUT.mkdir(parents=True, exist_ok=True)
    receipt = OUT / ('neck-contour02-' + phase + '.json')
    assert not receipt.exists(), 'Immutable trial phase already recorded'
    ob = bpy.data.objects[BODY_NAME]
    assert ob.mode == 'OBJECT' and np.allclose(np.asarray(ob.matrix_world), np.eye(4), atol=1e-7)
    current = current_coordinates(ob)
    namespace = bpy.app.driver_namespace

    if phase == 'select':
        assert KEY not in namespace and digest(current) == BASE_SHA
        source = np.load(SOURCE)
        baseline = source['world'].astype(np.float32)
        assert digest(baseline) == BASE_SHA and np.array_equal(current, baseline)
        rows = dict(np.load(ROWS))
        candidate, changed, report = make_candidate(baseline, source['triangles'], rows, source['source_part'])
        mark_selection(ob, np.flatnonzero(changed))
        namespace[KEY] = dict(before=baseline, after=candidate, report=report)
        report.update(phase='select', actual_live_geometry=False, group_marked_vertices=int(changed.sum()))
    else:
        state = namespace[KEY]
        assert digest(current) == digest(state['before']), 'Refuse to overwrite another live edit'
        ob.data.vertices.foreach_set('co', state['after'].ravel())
        ob.data.update(); bpy.context.view_layer.update()
        actual = current_coordinates(ob)
        assert digest(actual) == digest(state['after'])
        report = dict(state['report'], phase='apply', actual_live_geometry=True,
                      geometry_world_sha256=digest(actual), retained_as_working_sculpt=False)
    receipt.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print(json.dumps(report))


main()
