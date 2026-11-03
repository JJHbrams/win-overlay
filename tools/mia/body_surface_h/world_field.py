"""One bounded C2 world-field correction, not per-view garment painting.

The original-source camera is used once to estimate small edge corrections.
Evaluation then depends only on world positions, fixed centres and coefficients.
All existing front/back observations and inferred closure anchors are hard pins.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from profile_contour import (APPEARANCE, BODY, CACHE, audit, check_storage_capacity,
                             contour, load_surface, read_json, sha, brief_leg_height,
                             make_recipe, seat)


def kernel(distance, radius):
    r = np.asarray(distance, float)/radius
    s = np.clip(1-r, 0, 1)
    return s**4 * (4*r+1)


def correction_value(points, recipe):
    points = np.asarray(points, float)
    centres = np.asarray(recipe['centres_world'], float)
    weights = np.asarray(recipe['coefficients_m'], float)
    value = np.zeros(len(points))
    for centre, weight in zip(centres, weights):
        if abs(weight) < 1e-15:
            continue
        value += weight * kernel(np.linalg.norm(points-centre, axis=1), recipe['radius_m'])
    return value


def candidate_brief_height(points, config, curves, recipe):
    """Integration API: fixed world height for the unchanged lower pelvis."""
    return brief_leg_height(points, config, curves)-correction_value(points, recipe)


def certify_field_bound(surface, allowed, recipe, limit):
    """Lipschitz upper bound on every actual pelvic triangle, not vertex-only."""
    pending = surface['world'][surface['triangles'][allowed]].astype(float)
    centres = np.asarray(recipe['centres_world'])
    weights = np.abs(np.asarray(recipe['coefficients_m']))
    largest, sampled, subdivisions = 0., 0., 0
    for depth in range(9):
        middle = pending.mean(1)
        radius = np.linalg.norm(pending-middle[:, None], axis=2).max(1)
        local_lipschitz = np.zeros(len(pending))
        for centre, weight in zip(centres, weights):
            possible = np.linalg.norm(middle-centre, axis=1) <= radius+recipe['radius_m']
            # max |d Wendland(r)/dr| = 2.109375 for r in [0,1].
            local_lipschitz[possible] += weight*2.109375/recipe['radius_m']
        values = abs(correction_value(middle, recipe))
        sampled = max(sampled, float(values.max()))
        bound = values+local_lipschitz*radius
        good = bound <= limit
        if good.any():
            largest = max(largest, float(bound[good].max()))
        if good.all():
            return dict(certified_upper_bound_m=largest, sampled_centroid_max_m=sampled,
                        physical_limit_m=limit, refinement_depth=depth, subdivided_triangles=subdivisions,
                        method='Actual triangle covering radii plus analytic compact-kernel Lipschitz bounds; virtual subdivision only, no geometry changes.')
        tri = pending[~good]
        subdivisions += len(tri)
        a, b, c = tri[:, 0], tri[:, 1], tri[:, 2]
        ab, bc, ca = (a+b)/2, (b+c)/2, (c+a)/2
        pending = np.concatenate([np.stack(x, axis=1) for x in [(a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)]])
    raise ValueError('Could not certify the bounded world correction on actual surface triangles')


def projection_motion(surface, old_lines, old_faces, field):
    allowed = np.isin(surface['face_region'], surface['meta']['allowed_regions']['briefs'])
    new_lines, new_faces, _ = contour(surface, field, allowed)
    # A tiny field change can move a contour across mesh edges. Triangle IDs
    # therefore do not establish geometric curve correspondence.
    def sample(lines):
        return np.concatenate([a+np.linspace(0, 1, max(2, int(np.ceil(np.linalg.norm(b-a)/.25))+1))[:, None]*(b-a) for a, b in lines])
    def distances(points, lines):
        result = np.full(len(points), np.inf)
        for a, b in lines:
            edge = b-a
            t = np.clip((points-a)@edge/max(float(edge@edge), 1e-20), 0, 1)
            result = np.minimum(result, np.linalg.norm(points-a-t[:, None]*edge, axis=1))
        return result
    result = {}
    for name, view in surface['meta']['source_context']['views'].items():
        project = lambda p: seat.render_to_source(seat.world_to_pixel(view['camera'], p), view['registration'])
        old = project(old_lines.reshape(-1, 3)).reshape(-1, 2, 2)
        new = project(new_lines.reshape(-1, 3)).reshape(-1, 2, 2)
        measured = max(float(distances(sample(old), new).max()), float(distances(sample(new), old).max()))
        result[name] = dict(sampled_symmetric_contour_distance_px=measured, upper_bound_px=measured+.125)
    return dict(source_projection_contour_distances=result,
                meaning='Extracted polygonal curve set-distance, including hidden parts. Samples <=.25px apart plus 1-Lipschitz distance bound give <=.125px upper-bound slack; no material/visible-pixel ART claim.')


def fit_once():
    check_storage_capacity()
    baseline_path = CACHE/'profile-contour-baseline.json'
    baseline = read_json(baseline_path)
    surface_path, config_path = map(Path, [baseline['inputs']['surface'], baseline['inputs']['config']])
    if sha(surface_path) != baseline['summary']['surface_sha256'] or sha(config_path) != baseline['summary']['config_sha256']:
        raise ValueError('Baseline projection report is stale')
    surface, config = load_surface(surface_path), read_json(config_path)
    curves, _, paths = make_recipe(config)
    f0 = lambda p: p[:, 2]-brief_leg_height(p, config, curves)
    allowed = np.isin(surface['face_region'], config['allowed_region_ids']['pelvis'])
    lines, face_ids, _ = contour(surface, f0, allowed)
    camera = baseline['camera']
    source = lambda p: seat.render_to_source(seat.world_to_pixel(camera['camera'], p), camera['registration'])
    # The metres/source-pixel scale is measured from the frozen ORTHO/SRT, not
    # guessed from a body crop or a single field-height discrepancy.
    origin = np.zeros((1, 3))
    J = (source(np.eye(3))-source(origin)).T
    metres_per_pixel = 1/float(np.linalg.norm(J[1]))
    pins = np.array([r['hit']['world'] for r in config['brief_source_fit_proof']['records']])
    targets, requested, observations = [], [], []
    for row in baseline['rows']:
        if row['path'] != 'profile.briefs.rear_leg_fragment' or not row['source_ray'].get('accepted'):
            continue
        bound = float(paths[row['path']]['confidence']['pixel_uncertainty_range'][1])
        nearest = row['nearest_visible']
        if nearest is None or nearest['distance_source_px'] <= bound:
            continue
        q = np.asarray(nearest['world'], float)
        normal = np.cross(*(surface['world'][surface['triangles'][face_ids[nearest['segment_id']]]][1:]-surface['world'][surface['triangles'][face_ids[nearest['segment_id']]]][0]))
        normal /= np.linalg.norm(normal)
        step = .00025
        gradient = np.array([(f0((q+step*np.eye(3)[i])[None, :])[0]-f0((q-step*np.eye(3)[i])[None, :])[0])/(2*step) for i in range(3)])
        tangent = gradient-normal*(gradient@normal)
        response = -(J@tangent)/max(float(tangent@tangent), 1e-20)
        error = np.asarray(row['source_pixel'])-np.asarray(nearest['source_pixel'])
        desired = error * ((nearest['distance_source_px']-bound)/nearest['distance_source_px'])
        delta = float(response@desired/max(float(response@response), 1e-20))
        targets.append(q)
        requested.append(delta)
        observations.append(dict(source_pixel=row['source_pixel'], baseline_visible_distance_px=nearest['distance_source_px'],
                                 source_uncertainty_bound_px=bound, requested_field_delta_m=delta,
                                 baseline_contour_world=q.tolist()))
    if not targets:
        raise ValueError('No visible profile border exceeds its declared tracing uncertainty')
    # One kernel radius = three times the source annotation uncertainty.
    # This is one construction, not a radius/amplitude sweep.
    radius = 3*max(o['source_uncertainty_bound_px'] for o in observations)*metres_per_pixel
    centres = np.vstack((pins, targets))
    matrix = kernel(np.linalg.norm(centres[:, None]-centres[None, :], axis=2), radius)
    rhs = np.r_[np.zeros(len(pins)), requested]
    weights = np.linalg.solve(matrix, rhs)
    recipe = dict(schema_version=1, kernel='Wendland C2 compact support', radius_m=radius,
                  centres_world=centres.tolist(), coefficients_m=weights.tolist(),
                  exact_source_or_closure_pins=len(pins), fit_observations=observations,
                  construction='ONE linear interpolant solve; C2 compact world field. No runtime camera dependence or geometry change.',
                  uncertainty_rule='Correct only the excess beyond each source path\u2019s declared upper pixel uncertainty.',
                  source_surface_sha256=sha(surface_path), source_config_sha256=sha(config_path),
                  original_source_camera_sha256=seat.json_hash(camera), baseline_report_sha256=sha(baseline_path),
                  selection='OPTIONAL UNSELECTED; primary remains the base fair Cartesian pattern until actual materials show worthwhile benefit.',
                  limits='CPU candidate only. New contour visibility/topology and actual source-four-view render review remain required.')
    residual = correction_value(pins, recipe)
    all_pelvis = surface['world'][np.unique(surface['triangles'][allowed])]
    maximum = float(abs(correction_value(all_pelvis, recipe)).max())
    physical_limit = max(o['source_uncertainty_bound_px'] for o in observations)*metres_per_pixel
    if abs(residual).max() > 1e-10 or maximum > physical_limit:
        raise ValueError('Candidate failed hard pins or source-uncertainty physical correction bound')
    recipe['hard_pin_delta_error_m'] = float(abs(residual).max())
    recipe['maximum_actual_pelvis_vertex_field_delta_m'] = maximum
    recipe['surface_correction_bound'] = certify_field_bound(surface, allowed, recipe, physical_limit)
    recipe['four_view_projection_motion'] = projection_motion(surface, lines, face_ids,
                                                              lambda p: f0(p)+correction_value(p, recipe))
    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE/'brief-world-correction-once.json').write_text(json.dumps(recipe, indent=2)+'\n', encoding='utf8')
    report = audit(surface_path, config_path, 'profile-contour-candidate-once.json', correction=recipe)
    print(json.dumps(dict(recipe_path=str(CACHE/'brief-world-correction-once.json'),
                         hard_pin_error_m=recipe['hard_pin_delta_error_m'], maximum_field_delta_m=maximum,
                         requested=observations, topology=report['summary']['topology']), indent=2))
    return recipe, report


if __name__ == '__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    fit_once()
