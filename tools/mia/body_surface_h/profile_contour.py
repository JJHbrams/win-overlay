"""CPU source-edge audit of one fixed world-space brief field.

Inputs stay in the canonical workspace. Output is a small ignored cache report;
this does not generate a texture, native scene, renderer view, or art approval.
"""
from pathlib import Path
import argparse
import json
import sys

import numpy as np

sys.dont_write_bytecode = True
CANONICAL = Path('D:/MiaWorkCache/mia-reference-work/win-overlay')
APPEARANCE = CANONICAL / 'asset/mia/blender/mia-fit-v003/body/surface-appearance12'
BODY = CANONICAL / 'asset/mia/blender/mia-fit-v003/body/surface-review12'
CACHE = CANONICAL / '.mia-cache/body-h/appearance'
sys.path.insert(0, str(APPEARANCE))
from surface_api import load_surface, read_json, sha
from pattern_fields import brief_leg_height, make_recipe, seat
from bake_surface import check_storage_capacity


def contour(surface, field, allowed):
    """Find the actual mesh intersections, without a star-convex assumption."""
    world, faces = surface['world'], surface['triangles']
    value = field(world)
    hits, segments, face_ids = {}, [], []
    for fi in np.flatnonzero(allowed):
        face = faces[fi]
        crossing = []
        for i, j in [(0, 1), (1, 2), (2, 0)]:
            a, b = int(face[i]), int(face[j])
            if value[a] * value[b] >= 0:
                continue
            key = tuple(sorted((a, b)))
            if key not in hits:
                p, q = world[a].astype(float), world[b].astype(float)
                lo, hi = 0., 1.
                for _ in range(24):
                    t = (lo + hi) / 2
                    v = float(field((p * (1-t) + q*t)[None, :])[0])
                    if v * value[a] > 0:
                        lo = t
                    else:
                        hi = t
                t = (lo + hi) / 2
                hits[key] = p * (1-t) + q*t
            crossing.append(key)
        if len(crossing) == 2:
            segments.append(crossing)
            face_ids.append(int(fi))
        elif crossing:
            raise ValueError('Degenerate garment isocontour triangle')
    graph = {key: [] for key in hits}
    for a, b in segments:
        graph[a].append(b)
        graph[b].append(a)
    bad = [key for key, links in graph.items() if len(links) != 2]
    remaining, components = set(graph), []
    while remaining:
        todo = [remaining.pop()]
        component = []
        while todo:
            key = todo.pop()
            component.append(key)
            for other in graph[key]:
                if other in remaining:
                    remaining.remove(other)
                    todo.append(other)
        components.append(len(component))
    if bad or len(components) != 2:
        raise ValueError(f'Expected two closed leg openings: {components}, open nodes={len(bad)}')
    lines = np.array([[hits[a], hits[b]] for a, b in segments])
    return lines, np.asarray(face_ids), dict(closed_component_sizes=components, open_nodes=len(bad))


class ProjectedCaster:
    """Exact legacy ray test with an orthographic projected-AABB broad phase."""
    def __init__(self, surface, camera):
        self.camera = camera
        self.caster = seat.SurfaceCaster(surface, cast_triangle_ids=np.arange(len(surface['triangles'])))
        projected = seat.world_to_pixel(camera, surface['world'])
        tri = projected[surface['triangles']]
        self.lo, self.hi = tri.min(1), tri.max(1)

    def hit(self, pixel, allowed, min_facing=.025):
        pixel = np.asarray(pixel, float)
        ids = np.flatnonzero((pixel >= self.lo-1e-5).all(1) & (pixel <= self.hi+1e-5).all(1))
        if not len(ids):
            return dict(status='MISSED_RAY', accepted=False)
        # Keep EVERY projected foreground part, including the occluding arms.
        # This only accelerates the original exact nearest-hit semantics.
        local = object.__new__(seat.SurfaceCaster)
        local.__dict__ = self.caster.__dict__.copy()
        for key in ['ids', 'a', 'e1', 'e2', 'normal', 'area2']:
            setattr(local, key, getattr(self.caster, key)[ids])
        origins, directions, maximum = seat.pixel_rays(self.camera, pixel[None, :])
        return local.first_hit(origins[0], directions[0], maximum,
                               allowed_triangle_ids=allowed, min_facing_cos=min_facing,
                               uv_seam_tolerance=2.)

    def visible(self, pixel, point, allowed):
        hit = self.hit(pixel, allowed, min_facing=0.)
        if 'distance_m' not in hit:
            return False, hit
        origins, directions, _ = seat.pixel_rays(self.camera, np.asarray(pixel)[None, :])
        distance = float((point-origins[0]) @ directions[0])
        hit['target_depth_delta_m'] = float(distance-hit['distance_m'])
        # Near a triangle boundary, accept only micrometre-scale numerical drift.
        return abs(hit['target_depth_delta_m']) <= 5e-5, hit


def nearest_contour(source_pixel, lines, view, caster, allowed):
    projected = seat.render_to_source(seat.world_to_pixel(view['camera'], lines.reshape(-1, 3)),
                                      view['registration']).reshape(-1, 2, 2)
    a, b = projected[:, 0], projected[:, 1]
    edge = b-a
    den = np.einsum('ij,ij->i', edge, edge)
    t = np.clip(np.divide(np.einsum('ij,ij->i', source_pixel-a, edge), den,
                          out=np.zeros_like(den), where=den > 1e-20), 0, 1)
    q = a + t[:, None]*edge
    error = np.linalg.norm(q-source_pixel, axis=1)
    nearest = None
    for rank, i in enumerate(np.argsort(error)):
        world = lines[i, 0]*(1-t[i]) + lines[i, 1]*t[i]
        render = seat.source_to_render(q[i:i+1], view['registration'])[0]
        visible, hit = caster.visible(render, world, allowed)
        row = dict(distance_source_px=float(error[i]), source_pixel=q[i].tolist(),
                   world=world.tolist(), segment_id=int(i), visible=visible, occlusion=hit)
        if rank == 0:
            nearest = row
        if visible:
            return dict(nearest_projected=nearest, nearest_visible=row, visibility_queries=rank+1)
    return dict(nearest_projected=nearest, nearest_visible=None, visibility_queries=len(error))


def audit(surface_path=None, config_path=None, output_name='profile-contour-baseline.json', correction=None):
    check_storage_capacity()  # Inspect 100 MiB before any output creation.
    surface_path = Path(surface_path or BODY/'surface-v10-expanded-E-source-branches.npz')
    config_path = Path(config_path or APPEARANCE/'F-prebake-authoring-config.json')
    surface = load_surface(surface_path)
    config = read_json(config_path)
    curves, _, paths = make_recipe(config)
    allowed = np.isin(surface['face_region'], config['allowed_region_ids']['pelvis'])
    base_field = lambda points: points[:, 2]-brief_leg_height(points, config, curves)
    if correction is not None:
        from world_field import correction_value
        field = lambda points: base_field(points)+correction_value(points, correction)
    else:
        field = base_field
    lines, face_ids, topology = contour(surface, field, allowed)
    view = surface['meta']['source_context']['views']['profile']
    caster = ProjectedCaster(surface, view['camera'])
    rows = []
    for key in ['profile.briefs.near_leg_opening', 'profile.briefs.rear_leg_fragment']:
        path = paths[key]
        for pixel in np.asarray(path['points_px'], float):
            render = seat.source_to_render(pixel[None, :], view['registration'])[0]
            hit = caster.hit(render, allowed)
            row = dict(path=key, role=path['role'], source_pixel=pixel.tolist(), source_ray=hit,
                       source_observation_limit=path['observed_limits'])
            if hit.get('accepted'):
                point = np.array(hit['world'])
                row['same_ray_field_height_residual_m'] = float(field(point[None, :])[0])
            row.update(nearest_contour(pixel, lines, view, caster, allowed))
            for name in ['nearest_projected', 'nearest_visible']:
                if row[name] is not None:
                    row[name]['body_triangle_id'] = int(face_ids[row[name]['segment_id']])
            rows.append(row)
    observed = [r for r in config['brief_source_fit_proof']['records'] if r['original_ray_status'] == 'SEATED']
    points = np.array([r['hit']['world'] for r in observed])
    residual = field(points)
    summary = dict(surface_sha256=sha(surface_path), config_sha256=sha(config_path), topology=topology,
                   observed_front_back_knots=len(points), observed_front_back_max_field_error_m=float(abs(residual).max()),
                   source_visible_profile_samples=sum(r['source_ray'].get('accepted', False) for r in rows),
                   source_profile_occluders=[r['source_pixel'] for r in rows if r['source_ray']['status']=='WRONG_REGION_FRONT_HIT'],
                   source_profile_misses=[r['source_pixel'] for r in rows if r['source_ray']['status']=='MISSED_RAY'])
    if correction is not None:
        summary['maximum_pelvis_vertex_field_correction_m'] = float(abs(correction_value(surface['world'][np.unique(surface['triangles'][allowed])], correction)).max())
    report = dict(scope='CPU fixed-world contour projection and exact body visibility; no render/texture/geometry or ART approval',
                  inputs=dict(surface=str(surface_path), config=str(config_path)), summary=summary,
                  camera=view, rows=rows, correction=correction, geometry_changed=False, GPU_used=False,
                  limits=['Source paths are manual graphic observations; camera/pose and occluded segments remain uncertain.',
                          'Nearest visible projected contour is an image-edge metric; same-ray field height is a different diagnostic.',
                          'The field is fixed in world space and the render camera does not change its values.'])
    CACHE.mkdir(parents=True, exist_ok=True)
    output = CACHE/Path(output_name).name
    output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    print(json.dumps(dict(output=str(output), summary=summary,
                         pixels=[dict(source=r['source_pixel'], ray=r['source_ray']['status'],
                                      nearest_px=r['nearest_projected']['distance_source_px'],
                                      visible_px=r['nearest_visible']['distance_source_px'] if r['nearest_visible'] else None)
                                 for r in rows]), indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--surface')
    parser.add_argument('--config')
    parser.add_argument('--output-name', default='profile-contour-baseline.json')
    args = parser.parse_args()
    audit(args.surface, args.config, args.output_name)
