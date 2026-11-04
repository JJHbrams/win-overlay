"""REJECTED CPU-only actual-edge 3D flow; import is inert, no live apply.

The asymmetric section controls come from actual front/near-oblique boundary
rays on each owned component. This is not a global width multiplier, generic
ellipse, normal/material workaround, or a parameter search. Positive Jacobians
did not prevent a near-90-degree discrete triangle turn and new intersections
with unowned upper overlap. Do not install or retune this rejected forecast.
"""
from pathlib import Path
import runpy

import numpy as np

BASE = runpy.run_path(str(Path(__file__).with_name('rejected_bend_forecast01.py')))
REJECTION = dict(status='FORECAST_REJECTED_NOT_LIVE_APPLYABLE',
    left_brow_clear_indices={
        'front': dict(before=[44, 45, 46, 47], after=[31, 32, 33, 34, 35, 44, 45, 46, 47]),
        'minus35': dict(before=[49, 50, 51, 52], after=[49, 50, 51, 52]),
        'plus35': dict(before=[], after=[])},
    right_brow_clear_sets_unchanged=True,
    root48535_observed_rail_width_mm=[5.2208444865684545, .5310583255881823],
    new_intersection_witnesses=[dict(faces=[52014, 52859], roots=[44375, 41036]),
                                dict(faces=[52859, 54479], roots=[41036, 46971]),
                                dict(faces=[53102, 53757], roots=[41036, 48544])],
    collision_limit='Stopped after3 new SAT witnesses/546 tested pairs; no head/collision PASS',
    geometry_or_material_changed=False, native_saved=False)


def quintic(x, y, slopes):
    coefficients = []
    system = np.array([[1, 1, 1], [3, 4, 5], [6, 12, 20]], float)
    for i in range(3):
        length = x[i+1]-x[i]
        a = np.array([y[i], length*slopes[i], 0., 0., 0., 0.])
        a[3:] = np.linalg.solve(system, [y[i+1]-a[0]-a[1], length*slopes[i+1]-a[1], 0])
        coefficients.append(a)
    return np.array(coefficients)


def evaluate(values, knots, coefficients, identity=False):
    result = values.copy() if identity else np.zeros_like(values)
    derivative = np.ones_like(values) if identity else np.zeros_like(values)
    for i, a in enumerate(coefficients):
        mask = (values >= knots[i])&(values <= knots[i+1])
        t = (values[mask]-knots[i])/(knots[i+1]-knots[i])
        result[mask] = np.polynomial.polynomial.polyval(t, a)
        derivative[mask] = np.polynomial.polynomial.polyval(t, np.arange(1, 6)*a[1:])/(knots[i+1]-knots[i])
    return result, derivative


def minimum_derivative(knots, coefficients):
    minima = []
    for i, a in enumerate(coefficients):
        derivative = np.arange(1, 6)*a[1:]
        critical = np.polynomial.polynomial.polyroots(np.arange(1, 5)*derivative[1:])
        positions = [0., 1.]+[float(v.real) for v in critical if abs(v.imag) < 1e-8 and 0 < v.real < 1]
        minima.append(float(np.min(np.polynomial.polynomial.polyval(positions, derivative))/(knots[i+1]-knots[i])))
    return min(minima)


def forecast(root):
    data = BASE['design'](root)
    raw, world, faces, roots = [data[k] for k in ('before', 'world', 'faces', 'roots')]
    r, up = data['right'], data['up']; depth = np.cross(r, up); origin = np.array([0., 0., 1.58])
    probe = data['probe']; curve = np.array([s['world_candidates'][0] for s in probe['current_evaluated_brow_curves']['V31_SourceBrow_-1']['samples']])
    view = {x['yaw_offset']: np.array(x['matrix']) for x in probe['ray_views']}
    direction = {yaw: -m[:3, 2]/np.linalg.norm(m[:3, 2]) for yaw, m in view.items()}
    def brow(u): return np.array([np.interp(u, np.linspace(0, 1, len(curve)), curve[:, j]) for j in range(3)])
    report0 = data['report']; gap = report0['source_gap_mm']/1000
    ul, ur = report0['current_bank_edge_u']
    target_left = (brow(ul)-origin)@r+report0['profiles']['Fine']['amplitude_mm']/1000
    target_right = (brow(ur)-origin)@r+report0['profiles']['Inner']['amplitude_mm']/1000
    pixel = report0['source_similarity_scale']
    def boundary(root_id, yaw, which):
        ids = np.flatnonzero(roots == root_id); q = world[faces[ids]].astype(float)
        positions = np.linspace(.2, .85, 261)
        hits = [bool(len(BASE['ray_hits'](q, brow(u), direction[yaw])[0])) for u in positions]
        brackets = [(positions[i], positions[i+1], hits[i]) for i in range(len(positions)-1)
                    if hits[i] != hits[i+1] and (not hits[i] if which == 'start' else hits[i])]
        assert brackets, ('No actual bounded rail', root_id, yaw, which)
        lo, hi, initial = brackets[0] if which == 'start' else brackets[-1]
        for _ in range(35):
            middle = (lo+hi)/2
            if bool(len(BASE['ray_hits'](q, brow(middle), direction[yaw])[0])) == initial: lo = middle
            else: hi = middle
        u = (lo+hi)/2; point = brow(u+(1e-9 if which == 'start' else -1e-9))
        hit, distances = BASE['ray_hits'](q, point, direction[yaw]); assert len(hit)
        # Retain all equal-depth witnesses; coordinates are one geometric rail,
        # not a claim that a coincident face has a single semantic owner.
        k = int(np.argmin(distances)); fi = int(ids[hit[k]])
        location = point+direction[yaw]*(distances[k]-2)
        triangle = world[faces[fi]].astype(float)
        uv = np.linalg.lstsq(np.column_stack((triangle[1]-triangle[0], triangle[2]-triangle[0])), location-triangle[0], rcond=None)[0]
        bary = np.r_[1-uv.sum(), uv]
        return location, dict(u=u, source_faces=ids[hit[abs(distances-distances[k]) < 5e-5]].tolist(),
                              source_vertices=faces[fi][bary > 1e-5].tolist(), world_mm=(location*1000).tolist())
    slide = np.cross(up, view[-35][:3, 0]); slide /= slide@r
    assert abs(slide@up) < 1e-10 and abs(slide@view[-35][:3, 0]) < 1e-10
    after = raw.copy(); records = []; partial_derivatives = {}
    for family in ('Fine', 'Inner'):
        for root_id in BASE['FAMILIES'][family]:
            if family == 'Inner':
                p, p_info = boundary(root_id, 0, 'start'); q, q_info = boundary(root_id, -35, 'end'); target = target_right
            else:
                p, p_info = boundary(root_id, 0, 'end'); q, q_info = boundary(root_id, 0, 'start'); target = target_left
            px, qx = (p-origin)@r, (q-origin)@r
            if (family == 'Inner' and px >= target) or (family == 'Fine' and px <= target):
                records.append(dict(root=root_id, family=family, unchanged_reason='Actual moving edge already clears source guide')); continue
            q_displacement = np.zeros(3)
            if family == 'Inner' and qx < target+pixel:
                assert root_id == 48535, ('Deep backing would require a forbidden retreat', root_id)
                q_displacement = slide*(target+pixel-qx)
            new_q = q+q_displacement; new_qx = (new_q-origin)@r
            fraction = (target-px)/(new_qx-px)
            assert 0 < fraction < 1, ('Source edge crosses protected rail', root_id, px, target, new_qx)
            new_p = p+fraction*(new_q-p)
            dp, dq = new_p-p, q_displacement
            pad = max(2*gap, abs(dp@r)+gap, abs(dq@r)+gap)
            controls = sorted([(px, target, float(dp@depth)), (qx, new_qx, float(dq@depth))])
            xs = np.array([controls[0][0]-pad, controls[0][0], controls[1][0], controls[1][0]+pad])
            ys = np.array([xs[0], controls[0][1], controls[1][1], xs[-1]])
            assert (np.diff(ys) > 0).all(), ('Section orientation contradiction', root_id, xs, ys)
            secant = (ys[2]-ys[1])/(xs[2]-xs[1]); slope = min(1., secant)
            xc = quintic(xs, ys, [1., slope, slope, 1.])
            zc = quintic(xs, [0., controls[0][2], controls[1][2], 0.], [0., 0., 0., 0.])
            minimum = minimum_derivative(xs, xc)
            assert minimum > 0, ('Nonpositive exact quintic width derivative', root_id, minimum)
            ids = np.unique(faces[roots == root_id]); values = raw[ids].astype(float)
            x, s = (values-origin)@r, (values-origin)@up
            mapped_x, mapped_dx = evaluate(x, xs, xc, True); mapped_d, mapped_ddx = evaluate(x, xs, zc)
            weight, dw = BASE['profile'](s, report0['profiles'][family]['height_bounds_m'])
            delta_x = mapped_x-x
            after[ids] = values+weight[:, None]*(delta_x[:, None]*r+mapped_d[:, None]*depth)
            jacobian = 1+weight*(mapped_dx-1)
            assert (jacobian > 0).all()
            partial_derivatives[root_id] = dict(ids=ids, dx_dx=weight*(mapped_dx-1), dx_ds=dw*delta_x,
                                               dd_dx=weight*mapped_ddx, dd_ds=dw*mapped_d)
            records.append(dict(root=root_id, family=family, moving_rail=p_info, held_near_rail=q_info,
                moving_control_mm=(dp*1000).tolist(), near_control_slide_mm=(dq*1000).tolist(),
                section_knots_mm=(xs*1000).tolist(), new_section_knots_mm=(ys*1000).tolist(),
                exact_minimum_transverse_derivative=minimum, minimum_sampled_Jacobian=float(jacobian.min()),
                original_rail_width_mm=float(abs(qx-px)*1000), new_rail_width_mm=float(abs(new_qx-target)*1000)))
    changed = np.flatnonzero(np.any(after != raw, axis=1))
    changed_faces = np.flatnonzero(np.any(np.isin(faces, changed), axis=1))
    selected_faces = np.concatenate(list(data['family_faces'].values()))
    assert np.isin(changed_faces, selected_faces).all()
    q0, q1 = raw[faces[changed_faces]].astype(float), after[faces[changed_faces]].astype(float)
    n0, n1 = np.cross(q0[:, 1]-q0[:, 0], q0[:, 2]-q0[:, 0]), np.cross(q1[:, 1]-q1[:, 0], q1[:, 2]-q1[:, 0])
    area0, area1 = np.linalg.norm(n0, axis=1), np.linalg.norm(n1, axis=1)
    turns = np.degrees(np.arccos(np.clip(np.sum(n0*n1, axis=1)/(area0*area1), -1, 1)))
    data.update(after=after, changed=changed, affected_faces=changed_faces,
                edge_records=records, partial_derivatives=partial_derivatives)
    data['edge_report'] = dict(status=REJECTION['status'], rejection=REJECTION,
        operation='Actual per-component asymmetric section-edge flow; Outer completely held',
        controls=records, changed_vertices=len(changed), affected_faces=len(changed_faces),
        maximum_move_mm=float(np.linalg.norm(after-raw, axis=1).max()*1000),
        maximum_geometric_normal_turn_degrees=float(turns.max()), minimum_area_ratio=float((area1/area0).min()),
        geometric_turns_over90=int((turns >= 90).sum()), source_gap_guide_mm=gap*1000,
        actual_head_clearance_and_intersections='NOT EVALUATED BY THIS FUNCTION',
        live_apply_implemented=False, ART=False)
    return data
