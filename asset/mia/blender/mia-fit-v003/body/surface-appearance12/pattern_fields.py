"""Source-relative 3D garment boundaries and actual target surface seating.

The pattern is author-fitted to an anatomical surface chart, not a recovered
garment or a per-view overlay. All final points retain triangle/barycentric UVs.
"""
from pathlib import Path
import heapq
import importlib.util
import math
import sys
import numpy as np
from surface_api import read_json, sha, regions

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[6]
SOURCE_DIR = REPO / 'asset/mia/blender/mia-fit-v003/underwear-source'
spec = importlib.util.spec_from_file_location('mia12_surface_seating', REPO / 'asset/mia/blender/mia-fit-v003/underwear-fit/surface_seating.py')
seat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seat)


def smooth01(x):
    x = np.clip(x, 0., 1.)
    return x * x * x * (10 - 15 * x + 6 * x * x)


class PeriodicCurve:
    """Periodic shape-preserving cubic, including independently observed back."""
    def __init__(self, pairs):
        values = np.asarray(pairs, float)
        theta = (values[:, 0] + np.pi) % (2 * np.pi) - np.pi
        bins = np.round(theta, 7)
        keys = np.unique(bins)
        self.x = np.array([np.median(theta[bins == key]) for key in keys])
        self.y = np.array([np.median(values[bins == key, 1]) for key in keys])
        order = np.argsort(self.x)
        self.x, self.y = self.x[order], self.y[order]
        assert len(self.x) >= 4 and np.isfinite(values).all()
        xx = np.r_[self.x[-1] - 2*np.pi, self.x, self.x[0] + 2*np.pi]
        yy = np.r_[self.y[-1], self.y, self.y[0]]
        h = np.diff(xx); d = np.diff(yy) / h
        slopes = []
        for i in range(len(self.x)):
            a, b = d[i], d[i+1]
            if a*b <= 0:
                slopes.append(0.)
            else:
                w1, w2 = 2*h[i+1] + h[i], h[i+1] + 2*h[i]
                slopes.append((w1+w2) / (w1/a+w2/b))
        self.m = np.asarray(slopes)
        self.pairs = np.column_stack((self.x, self.y)).tolist()

    def __call__(self, theta):
        t = (np.asarray(theta) + np.pi) % (2*np.pi) - np.pi
        t = np.where(t < self.x[0], t + 2*np.pi, t)
        x = np.r_[self.x, self.x[0] + 2*np.pi]
        y = np.r_[self.y, self.y[0]]
        m = np.r_[self.m, self.m[0]]
        i = np.minimum(np.searchsorted(x, t, side='right') - 1, len(self.x)-1)
        h = x[i+1] - x[i]
        u = (t-x[i])/h
        return (2*u**3-3*u**2+1)*y[i] + (u**3-2*u**2+u)*h*m[i] + (-2*u**3+3*u**2)*y[i+1] + (u**3-u**2)*h*m[i+1]


def _source_z(points, view, config):
    """Exact declared affine from current source camera, never a fitted shoulder crop."""
    transforms = config.get('source_z_affine', {})
    if view not in transforms:
        raise ValueError('Actual source_z_affine[view]=[slope,offset] required: ' + view)
    slope, offset = transforms[view]
    return np.asarray(points, float)[:, 1] * slope + offset


def source_curve(path, config, *, halfwidth=None):
    view = path['view']
    pixels = np.asarray(path['points_px'], float)
    axis = config.get('source_axes_px', {}).get(view, 239. if view == 'front' else 936.)
    radius = halfwidth or config.get('source_halfwidth_px', {}).get(path['component'], {}).get(view, 80.)
    ratio = np.clip((pixels[:, 0] - axis) / radius, -1., 1.)
    # Back screen-left is world-right; source asymmetry is retained.
    theta = np.arcsin(ratio) if view == 'front' else np.pi + np.arcsin(ratio)
    return np.column_stack((theta, _source_z(pixels, view, config)))


def make_recipe(config, supplement=None):
    source = read_json(SOURCE_DIR / 'source-paths.json')
    paths = {p['id']: p for p in source['paths']}
    supplement = supplement or read_json(Path(__file__).with_name('tied-guide-paths.json'))
    ext = {p['id']: p for p in supplement['paths']}
    used = []
    def curve(path_id):
        p = paths.get(path_id, ext.get(path_id))
        used.append(path_id)
        return source_curve(p, config)
    top = [curve('front.bra.scoop'), curve('tied.back.bra.scoop')]
    bottom = [curve('front.bra.band_lower_edge'), curve('tied.back.bra.band_bottom')]
    used.extend(['profile.bra.side_return_upper_fragment', 'profile.bra.band_lower_edge'])
    side_top = float(_source_z(paths['profile.bra.side_return_upper_fragment']['points_px'], 'profile', config).mean())
    side_bottom = float(_source_z(paths['profile.bra.band_lower_edge']['points_px'], 'profile', config).mean())
    top.append(np.array([[-np.pi/2, side_top], [np.pi/2, side_top]]))
    bottom.append(np.array([[-np.pi/2, side_bottom], [np.pi/2, side_bottom]]))
    band_top = [curve('front.bra.cup_band_transition')]
    band_top.append(np.array([[-np.pi, side_bottom+.019], [-np.pi/2, side_bottom+.019], [np.pi/2, side_bottom+.019], [np.pi, side_bottom+.019]]))
    waist = [curve('front.briefs.dipped_waist'), curve('back.briefs.dipped_waist')]
    leg = [curve('front.briefs.left_leg_opening'), curve('front.briefs.right_leg_opening'),
           curve('back.briefs.left_leg_opening'), curve('back.briefs.right_leg_opening')]
    landmarks = config.get('landmarks', {})
    if 'crotch_z' not in landmarks:
        raise ValueError('Actual assembled crotch_z landmark required for brief leg-opening fit')
    legpoints = np.concatenate(leg)
    source_min = float(legpoints[:, 1].min())
    source_side = float(np.median(legpoints[np.abs(np.cos(legpoints[:, 0])) < .25, 1]))
    if not np.isfinite(source_side):
        source_side = float(np.percentile(legpoints[:, 1], 90))
    target_crotch = float(landmarks['crotch_z']) + config.get('crotch_paint_clearance_m', .004)
    if target_crotch >= source_side - .025:
        raise ValueError('Actual crotch and source side openings need explicit anatomical fitting')
    for item in leg:
        t = np.clip((item[:, 1]-source_min)/(source_side-source_min), 0, 1)
        item[:, 1] = target_crotch + t*(source_side-target_crotch)
    curves = dict(bra_top=PeriodicCurve(np.concatenate(top)), bra_bottom=PeriodicCurve(np.concatenate(bottom)),
                  bra_band_top=PeriodicCurve(np.concatenate(band_top)), brief_waist=PeriodicCurve(np.concatenate(waist)),
                  brief_leg=PeriodicCurve(np.concatenate(leg)))
    theta = np.linspace(-np.pi, np.pi, 512, endpoint=False)
    if np.any(curves['bra_top'](theta) - curves['bra_bottom'](theta) < .01):
        raise ValueError('Bra fitted top/bottom curves cross or become thinner than10mm')
    if np.any(curves['brief_waist'](theta) - curves['brief_leg'](theta) < .005):
        raise ValueError('Brief fitted waist/leg curves cross or become thinner than5mm')
    proof = dict(source_path=str(SOURCE_DIR / 'source-paths.json'), source_path_sha256=sha(SOURCE_DIR / 'source-paths.json'),
                 source_image_sha256=source['source']['sha256'], supplement=supplement['source'], used_source_paths=used,
                 clavicle_source_paths=['front.neck.left_clavicle_line', 'front.neck.right_clavicle_line'],
                 curves={key: value.pairs for key, value in curves.items()},
                 fitting='Source-relative anatomical polar-chart artist fit, not literal source-image or recovered hidden garment dimensions.',
                 brief_crotch_fit=dict(source_min_z=source_min, source_side_z=source_side, actual_crotch_z=landmarks['crotch_z'], target_crotch_z=target_crotch),
                 inferred=['Side angular connections between observed front/profile/back fragments', 'Hidden brief underbody/gusset return', 'Continuous strap width and hidden shoulder/back route'],
                 no_geometry_change=True, no_per_view_repaint=True)
    return curves, proof, paths


class TargetAuthor:
    def __init__(self, surface, config):
        self.surface, self.config = surface, config
        explicit = config.get('allowed_region_ids', {})
        self.upper = regions(surface, ['torso', 'neck', 'upperbody', 'chest'], explicit.get('upper'))
        self.pelvis = regions(surface, ['torso', 'pelvis', 'thigh', 'upperleg', 'leg'], explicit.get('pelvis'))
        self.all_ids = np.arange(len(surface['triangles']))
        self.casters = {key: seat.SurfaceCaster(surface, cast_triangle_ids=np.flatnonzero(mask))
                        for key, mask in [('upper', self.upper), ('pelvis', self.pelvis)]}
        self.center_xy = np.asarray(config.get('torso_center_xy', [0., -.006]), float)

    def _hit(self, region, origin, direction, distance, facing):
        caster = self.casters[region]
        hit = caster.first_hit(origin, direction, distance, allowed_triangle_ids=caster.ids,
                               min_facing_cos=facing, uv_seam_tolerance=2e-4)
        if hit.get('status') == 'UV_SEAM_AMBIGUOUS':
            # The authoring field is3D and is evaluated separately on EVERY
            # corner-UV texel. A coincident chart seam therefore has no unique
            # UV to paint and does not permit skipping a wrong physical sheet.
            hit = caster.first_hit(origin, direction, distance, allowed_triangle_ids=caster.ids,
                                   min_facing_cos=facing, uv_seam_tolerance=2.)
            hit['multiple_UV_chart_binding'] = True
            hit['UV_policy'] = 'Representative hit only; paint evaluated from world on all actual per-corner UVs, both seam sides.'
        return hit

    def radial(self, theta, z, region):
        direction = np.array([np.sin(theta), -np.cos(theta), 0.])
        origin = np.r_[self.center_xy, z] + direction * .75
        # Explicit authoring-only local chart, not a full-scene visibility claim.
        hit = self._hit(region, origin, -direction, 1.5, .025)
        hit.update(chart_theta=float(theta), chart_z=float(z),
                   method='Actual anatomical submesh radial chart first-hit; not source visibility or nearest-body fallback')
        return hit

    def front(self, x, z, region='upper'):
        origin = np.array([x, -1., z])
        hit = self._hit(region, origin, np.array([0., 1., 0.]), 2., .10)
        hit.update(method='Actual anatomical submesh front first-hit after declared clavicle anchor fitting')
        return hit

    def seat_boundaries(self, curves, samples=128):
        result = {}
        for name, curve in curves.items():
            if name == 'bra_band_top': continue
            theta = np.linspace(-np.pi, np.pi, samples, endpoint=False)
            region = 'upper' if name.startswith('bra') else 'pelvis'
            hits = [self.radial(t, z, region) for t, z in zip(theta, curve(theta))]
            failures = [i for i, hit in enumerate(hits) if not hit.get('accepted')]
            result[name] = dict(points=hits, closed=True, authoring_region=region,
                                geometric_samples_complete=not failures, failures=failures,
                                production_garment_ART=False)
        return result

    def clavicle(self, paths):
        landmarks = self.config.get('landmarks', {})
        if 'clavicle_anchor_z' not in landmarks:
            raise ValueError('Actual fitted clavicle_anchor_z required; old worldheight cannot stand in for neck anatomy')
        source_notch = np.mean(_source_z([[236, 225], [249, 225]], 'front', self.config))
        shift_z = float(landmarks['clavicle_anchor_z']) - source_notch
        axis = self.config.get('source_axes_px', {}).get('front', 239.)
        scale = abs(self.config['source_z_affine']['front'][0])
        result = []
        for key in ['front.neck.left_clavicle_line', 'front.neck.right_clavicle_line']:
            path = paths[key]; pixels = np.asarray(path['points_px'], float)
            xx = (pixels[:, 0]-axis)*scale
            zz = _source_z(pixels, 'front', self.config)+shift_z
            fitted = [self.front(x, z) for x, z in zip(xx, zz)]
            for hit, pixel in zip(fitted, pixels): hit['source_px'] = pixel.tolist()
            result.append(dict(source_path_id=key, source_px=path['points_px'], points=fitted,
                               fit=dict(common_z_translation_m=shift_z, anchor_z=landmarks['clavicle_anchor_z'], horizontal_scale_m_per_px=scale),
                               geometric_samples_complete=all(p.get('accepted') for p in fitted),
                               limit='Graphic placement inferred from actual neck/clavicle anchor; original source comparison is not warped.'))
        return result

    def strap_paths(self, curves):
        """Actual surface edge-geodesics, constrained to shoulder anatomical chart."""
        v, f = self.surface['world'], self.surface['triangles']
        e = np.unique(np.sort(np.concatenate([f[self.upper][:, [0,1]], f[self.upper][:, [1,2]], f[self.upper][:, [2,0]]]), axis=1), axis=0)
        graph = [[] for _ in range(len(v))]
        for a, b in e:
            length = float(np.linalg.norm(v[a]-v[b]))
            graph[a].append((int(b), length)); graph[b].append((int(a), length))
        def vertex(hit):
            if not hit.get('accepted'): raise ValueError('Strap anchor did not seat: ' + repr(hit))
            return int(f[hit['triangle_id']][np.argmax(hit['barycentric'])])
        def shortest(start, end, side):
            queue, cost, previous = [(0., start)], {start: 0.}, {}
            while queue:
                distance, a = heapq.heappop(queue)
                if distance != cost[a]: continue
                if a == end: break
                for b, length in graph[a]:
                    if side*v[b, 0] < .035 or side*v[b, 0] > .135 or v[b, 2] < 1.23: continue
                    new = distance + length
                    if new < cost.get(b, math.inf):
                        cost[b] = new; previous[b] = a; heapq.heappush(queue, (new, b))
            if end not in cost: raise ValueError('No shoulder-only actual surface strap path')
            path = [end]
            while path[-1] != start: path.append(previous[path[-1]])
            return path[::-1]
        straps = []
        for side in [-1, 1]:
            theta_front, theta_back = side*.65, side*(np.pi-.72)
            a = self.radial(theta_front, float(curves['bra_top'](theta_front)), 'upper')
            b = self.radial(theta_back, float(curves['bra_top'](theta_back)), 'upper')
            ids = shortest(vertex(a), vertex(b), side)
            straps.append(dict(side=side, vertex_ids=ids, world=v[ids].tolist(), anchors=[a,b],
                               width_m=self.config.get('strap_width_m', .013),
                               method='Shortest edge-geodesic restricted to actual torso/shoulder chart; hidden route inferred from tied-hair guide.'))
        return straps


def distance_to_polyline(points, line):
    points, line = np.asarray(points, float), np.asarray(line, float)
    best = np.full(len(points), np.inf)
    for a, b in zip(line[:-1], line[1:]):
        ab = b-a; t = np.clip((points-a) @ ab / max(float(ab@ab), 1e-24), 0, 1)
        best = np.minimum(best, np.linalg.norm(points-a-t[:, None]*ab, axis=1))
    return best
