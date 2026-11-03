"""Read-only physical/field diagnostics for one final H RAM parameter vector.

analyze(model, params, canonical) returns JSON-serializable data; never writes,
opens a scene, meshes, renders, copies inputs or claims artistic acceptance.
"""
from pathlib import Path
import hashlib
import sys
import numpy as np

sys.dont_write_bytecode = True


def _evaluate(fn, points, chunk=8192):
    if not len(points):
        return np.empty(0, float)
    return np.concatenate([np.asarray(fn(points[i:i+chunk]), float) for i in range(0, len(points), chunk)])


def _crossings(fn, fixed_points, axis, low, high, samples=181, iterations=24):
    """All bracketed inside/outside transitions on parallel physical lines."""
    fixed = np.asarray(fixed_points, float)
    grid = np.linspace(low, high, samples)
    points = np.repeat(fixed, samples, axis=0)
    points[:, axis] = np.tile(grid, len(fixed))
    values = _evaluate(fn, points).reshape(len(fixed), samples)
    inside = values <= 0.
    lines, cells = np.nonzero(inside[:, :-1] != inside[:, 1:])
    lo, hi = grid[cells].copy(), grid[cells+1].copy()
    left_inside = inside[lines, cells]
    queries = fixed[lines].copy()
    for _ in range(iterations):
        mid = (lo+hi)*.5
        queries[:, axis] = mid
        current_inside = _evaluate(fn, queries) <= 0.
        same = current_inside == left_inside
        lo = np.where(same, mid, lo)
        hi = np.where(same, hi, mid)
    roots = (lo+hi)*.5
    result = []
    for i in range(len(fixed)):
        selected = np.flatnonzero(lines == i)
        result.append(dict(
            roots=[dict(coordinate=float(roots[j]), inside_before=bool(left_inside[j]), inside_after=not bool(left_inside[j])) for j in selected],
            inside_at_low=bool(inside[i, 0]), inside_at_high=bool(inside[i, -1]),
            sampled_material=bool(inside[i].any())))
    return result


def _gradients(fn, points, step=2e-5):
    result = np.empty((len(points), 3), float)
    for axis in range(3):
        delta = np.zeros_like(points)
        delta[:, axis] = step
        result[:, axis] = (_evaluate(fn, points+delta)-_evaluate(fn, points-delta))/(2*step)
    return result


def _summary(values):
    values = np.asarray(values, float)
    values = values[np.isfinite(values)]
    if not len(values):
        return dict(count=0, min=None, median=None, p95=None, p99=None, max=None)
    return dict(count=len(values), min=float(values.min()), median=float(np.median(values)),
                p95=float(np.percentile(values, 95)), p99=float(np.percentile(values, 99)), max=float(values.max()))


def _section_curve(fn, x, y, guide_cut):
    fixed = np.column_stack((x, np.full(len(x), y), np.zeros(len(x))))
    crossings = _crossings(fn, fixed, 2, 1.20, guide_cut, samples=124)
    z = np.full(len(x), np.nan)
    cut, nohit = [], []
    below_cut_exits = []
    for i, row in enumerate(crossings):
        exits = [r['coordinate'] for r in row['roots'] if r['inside_before'] and not r['inside_after']]
        limited = row['inside_at_high']
        cut.append(limited)
        nohit.append(not row['sampled_material'])
        below_cut_exits.append(None if not exits else float(exits[-1]))
        # An artificial guide cut is not a body zero or an actual roof root.
        if exits and not limited:
            z[i] = exits[-1]
    valid = np.isfinite(z)
    points = np.column_stack((x[valid], np.full(valid.sum(), y), z[valid]))
    gradient = _gradients(fn, points)
    norms = np.linalg.norm(gradient, axis=1)
    normal = np.full((len(x), 3), np.nan)
    norm_by_x = np.full(len(x), np.nan)
    good = norms > 1e-12
    valid_ids = np.flatnonzero(valid)
    normal[valid_ids[good]] = gradient[good]/norms[good, None]
    norm_by_x[valid_ids] = norms
    neighboring = valid[:-1] & valid[1:] & np.isfinite(normal[:-1]).all(axis=1) & np.isfinite(normal[1:]).all(axis=1)
    edges = np.flatnonzero(neighboring)
    turn = np.degrees(np.arccos(np.clip(np.einsum('ij,ij->i', normal[edges], normal[edges+1]), -1., 1.)))
    arc = np.sqrt(np.diff(x)[edges]**2+np.diff(z)[edges]**2)
    worst = np.argsort(turn)[-5:][::-1]
    normal_cases = [dict(x_interval=[float(x[edges[j]]), float(x[edges[j]+1])],
                         z_interval=[float(z[edges[j]]), float(z[edges[j]+1])],
                         normal_turn_degrees=float(turn[j]), physical_chord_mm=float(arc[j]*1000)) for j in worst]
    triple = np.flatnonzero(valid[:-2] & valid[1:-1] & valid[2:])
    angle_left = np.arctan2(z[triple+1]-z[triple], x[triple+1]-x[triple])
    angle_right = np.arctan2(z[triple+2]-z[triple+1], x[triple+2]-x[triple+1])
    tangent_turn = np.degrees(abs(angle_right-angle_left))
    dz = np.diff(z)[edges]
    positive = np.maximum(dz, 0.)
    max_up = int(np.argmax(positive)) if len(positive) else None
    upturn = dict(positive_steps=int((dz > 1e-7).sum()), total_positive_Z_m=float(positive.sum()),
                  maximum_single_step_Z_m=None if max_up is None else float(positive[max_up]),
                  maximum_step_x_interval=None if max_up is None else [float(x[edges[max_up]]), float(x[edges[max_up]+1])])
    return dict(
        roof_z=[None if not np.isfinite(v) else float(v) for v in z],
        below_cut_exit_z=below_cut_exits, cut_limited=cut, no_sampled_hit=nohit,
        gradient_norm=[None if not np.isfinite(v) else float(v) for v in norm_by_x],
        gradient_norm_distribution=_summary(norms), numerically_zero_gradient_count=int((~good).sum()),
        neighboring_surface_normal_turn_degrees=_summary(turn),
        neighboring_turn_per_chord_mm=_summary(turn/(arc*1000)),
        largest_normal_turn_cases=normal_cases, section_tangent_turn_degrees=_summary(tangent_turn),
        positive_roof_steps=upturn)


def analyze(model, params, canonical):
    """Analyze one supplied final vector; returns data only, with no I/O writes."""
    canonical = Path(canonical)
    source = canonical/'asset/mia/blender/mia-fit-v003/body/shoulder11/shoulder11-canonical.npz'
    with np.load(source) as cache:
        world = np.asarray(cache['world'], float)
    if len(world) != 67410:
        raise ValueError('Unexpected immutable guide vertex count')
    baseline = lambda points: model.baseline(points, version='11')
    current = lambda points: model.evaluate(points, params)
    old_values = _evaluate(baseline, world)
    values = _evaluate(current, world)
    delta = values-old_values
    if not np.isfinite(values).all():
        raise ValueError('Nonfinite H field on immutable guide')
    lower = world[:, 2] <= 1.34
    core = (abs(world[:, 0]) <= .125) & (world[:, 1] <= -.03) & (world[:, 2] >= 1.18) & (world[:, 2] <= 1.35)
    core_ids = np.flatnonzero(core)
    worst = core_ids[np.argsort(abs(delta[core_ids]))[-5:][::-1]]
    protection = dict(
        meaning='Complete old-guide sample FIELD deltas, not geometric distances or final meshed coordinate preservation.',
        lower_Z134_count=int(lower.sum()), lower_field_byte_exact=bool(np.array_equal(values[lower], old_values[lower])),
        lower_max_abs_field_delta=float(abs(delta[lower]).max()),
        breast_core_definition='absX<=.125,Y<=-.03,Z1.18..1.35 on every immutable guide vertex',
        breast_core_count=int(core.sum()), breast_core_field_byte_exact=bool(np.array_equal(values[core], old_values[core])),
        breast_core_exact_nonzero_count=int(np.count_nonzero(delta[core])),
        breast_core_abs_field_delta_distribution=_summary(abs(delta[core])),
        breast_core_worst_samples=[dict(old_guide_id=int(i), world=world[i].tolist(),
                                       baseline_field=float(old_values[i]), H_field=float(values[i]), field_delta=float(delta[i])) for i in worst],
        minimum_H_minus_baseline_field=float(delta.min()), maximum_H_minus_baseline_field=float(delta.max()))

    breast_fixed = np.array([(x, 0., z) for z in [1.24, 1.28, 1.32, 1.34, 1.345, 1.35] for x in [.04, .08, .12]])
    breast = []
    breast_roots = {name: _crossings(fn, breast_fixed, 1, -.23, .12, samples=176) for name, fn in [('baseline11', baseline), ('H', current)]}
    for i, point in enumerate(breast_fixed):
        row = dict(x=float(point[0]), z=float(point[2]), states={})
        anterior = {}
        for name in ['baseline11', 'H']:
            record = breast_roots[name][i]
            roots = [v['coordinate'] for v in record['roots'] if not v['inside_before'] and v['inside_after']]
            anterior[name] = None if not roots else roots[0]
            row['states'][name] = dict(anterior_y=anterior[name], no_entry_hit=not bool(roots),
                                        clipped_at_anterior_scan_boundary=record['inside_at_low'], all_y_roots=record['roots'])
        row['H_minus_baseline_anterior_y_mm'] = None if any(v is None for v in anterior.values()) else float((anterior['H']-anterior['baseline11'])*1000)
        breast.append(row)

    gap_planes = [(0., 1.26, 'main_lower_passage'), (.035, 1.28, 'posterior_passage'),
                  (.020, 1.26, 'existing_local_roof_closure_A'), (.025, 1.265, 'existing_local_roof_closure_B')]
    gap_fixed = np.array([[0., y, z] for y, z, _ in gap_planes])
    gaps = []
    for name, fn in [('baseline11', baseline), ('H', current)]:
        crossings = _crossings(fn, gap_fixed, 0, .08, .26, samples=361)
        for i, (y, z, label) in enumerate(gap_planes):
            roots = crossings[i]['roots'];air = []
            for left, right in zip(roots[:-1], roots[1:]):
                a, b = left['coordinate'], right['coordinate']
                if _evaluate(fn, np.array([[(a+b)/2, y, z]]))[0] > 0:
                    air.append(dict(x_interval=[a, b], width_m=b-a, width_mm=(b-a)*1000))
            gaps.append(dict(state=name, label=label, y=y, z=z, x_roots=[v['coordinate'] for v in roots],
                             bounded_internal_air_intervals=air, no_bounded_internal_gap=not bool(air)))

    x = np.linspace(.04, .18, 141)
    sections = []
    for y in [-.035, 0., .035]:
        sections.append(dict(y=y, x_m=x.tolist(), states={name: _section_curve(fn, x, y, 1.445) for name, fn in [('baseline11', baseline), ('H', current)]}))
    return dict(
        status='RAM_PHYSICAL_DIAGNOSTICS_NOT_ART_OR_MESH_PASS',
        immutable_guide=dict(path=str(source), sha256=hashlib.sha256(source.read_bytes()).hexdigest(), vertices=len(world)),
        model=model.metadata(params), protection=protection,
        breast_anterior_root_scope='Same physical X/Z planes. Positive deltaY means posterior retraction/less anterior protrusion. Root dimensions are metres/mm, field deltas are not.',
        breast_anterior_roots=breast,
        gap_scope='Actual same-plane analytic-field zero intersections, not mesh topology/3D connectivity or self-intersection proof.',
        gap_planes=gaps,
        section_scope=dict(y_planes=[-.035, 0., .035], x_range=[.04, .18], x_step_m=.001,
                           z_scan=[1.20, 1.445], guide_cut=1.445, scan_Z_step_m=.245/123,
                           flags='cut_limited is material at guidecut, not an actual roof zero; no_sampled_hit is scan-limited and does not prove no subgrid feature.',
                           normal_scope='Field gradient normals on actual zero roots; neighboring turns follow 1mm-X section sampling, not mesh facet dihedrals or a C1/C2 skin guarantee.',
                           gradient_central_difference_step_m=2e-5),
        roof_sections=sections, mesh_created=False, GPU_used=False, native_saved=False,
        limitations=['Only three positive-X roof sections sampled; actual opposite/oblique/high/low visual review remains required.',
                     'No mesh manifold/orientation/intersection, new neck loft, UV/skin seam, material or artistic acceptance follows from these RAM diagnostics.'])
