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
    override=config.get('brief_leg_surface_pairs')
    if override is None:
        for item in leg:
            t = np.clip((item[:, 1]-source_min)/(source_side-source_min), 0, 1)
            item[:, 1] = target_crotch + t*(source_side-target_crotch)
    curves = dict(bra_top=PeriodicCurve(np.concatenate(top)), bra_bottom=PeriodicCurve(np.concatenate(bottom)),
                  bra_band_top=PeriodicCurve(np.concatenate(band_top)), brief_waist=PeriodicCurve(np.concatenate(waist)),
                  brief_leg=PeriodicCurve(np.asarray(override) if override is not None else np.concatenate(leg)))
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
                 legacy_global_crotch_lift_applied=override is None,
                 brief_surface_source_fit=config.get('brief_source_fit_proof'),
                 brief_leg_field=('Fixed original-source-camera Cartesian charts, not active-render projection; polar curve diagnostic only' if config.get('brief_leg_source_charts') else 'Legacy periodic polar chart'),
                 brief_leg_source_charts=config.get('brief_leg_source_charts'),
                 inferred=['Side angular connections between observed front/profile/back fragments', 'Hidden brief underbody/gusset return', 'Continuous strap width and hidden shoulder/back route'],
                 no_geometry_change=True, no_per_view_repaint=True)
    return curves, proof, paths


def brief_leg_height(points,config,curves,charts=None):
    """Fixed 3D source-camera chart field, independent of render camera."""
    charts=charts or config.get('brief_leg_source_charts')
    p=np.asarray(points,float)
    if charts is None:
        theta=np.arctan2(p[:,0]-config['torso_center_xy'][0],-(p[:,1]-config['torso_center_xy'][1]))
        return curves['brief_leg'](theta)
    from fair_paths import cubic_shape_preserving
    values={}
    for view in ['front','back']:
        chart=charts[view];pairs=np.asarray(chart['pairs'],float)
        coordinate=p@np.asarray(chart['horizontal_world_axis'],float)
        values[view]=cubic_shape_preserving(pairs[:,0],pairs[:,1],coordinate)
    # Only the hidden lateral return blends; observed front/back contour
    # points lie outside this narrow 16mm surface side transition.
    cy=config['torso_center_xy'][1]
    front=smooth01((cy-p[:,1]+.008)/.016)
    result=values['front']*front+values['back']*(1-front)
    if 'profile_hidden_side' in charts:
        chart=charts['profile_hidden_side'];pairs=np.asarray(chart['pairs'],float)
        coordinate=p@np.asarray(chart['horizontal_world_axis'],float)
        profile=cubic_shape_preserving(pairs[:,0],pairs[:,1],coordinate)
        # Only hidden lateral return outside every observed front/back knot;
        # preserve visible front/back contours exactly.
        inner,outer=chart['side_blend_abs_x_m']
        weight=smooth01((abs(p[:,0])-inner)/(outer-inner))*(1-smooth01(abs(p[:,1]-cy)/.016))
        result=result*(1-weight)+profile*weight
    return result


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

    def fit_brief_leg_source(self, paths):
        """Preserve valid original-pixel rays; fit only missing source tips/sides."""
        caster=seat.SurfaceCaster(self.surface,cast_triangle_ids=self.all_ids)
        points=[];records=[]
        for key in ['front.briefs.left_leg_opening','front.briefs.right_leg_opening',
                    'back.briefs.left_leg_opening','back.briefs.right_leg_opening']:
            path=paths[key];view=path['view'];reference=self.surface['meta']['source_context']['views'][view]
            pixels=np.asarray(path['points_px'],float)
            origins,directions,maximum=seat.pixel_rays(reference['camera'],seat.source_to_render(pixels,reference['registration']))
            horizontal=np.asarray(reference['camera']['matrix'],float)[:3,0]
            for pixel,origin,direction in zip(pixels,origins,directions):
                original=caster.first_hit(origin,direction,maximum,allowed_triangle_ids=self.pelvis,
                                          min_facing_cos=.025,uv_seam_tolerance=2.)
                hit=original;method='Exact valid original-source pixel ray; no position adjustment'
                source_z=float(_source_z([pixel],view,self.config)[0])
                relative=(pixel[0]-self.config['source_axes_px'][view])/self.config['source_halfwidth_px']['briefs'][view]
                if not hit.get('accepted'):
                    if hit['status']!='MISSED_RAY':raise ValueError('Source garment ray needs explicit diagnosis: '+repr(hit))
                    if abs(relative)>.8:
                        # Original outer silhouette is outside this body's skin.
                        # A same-height lateral hip return is declared inference.
                        side=np.sign(relative)*(1 if view=='front' else -1)
                        hit=self.radial(float(side*np.pi/2),source_z,'pelvis')
                        method='Inferred same-height lateral hip return for source silhouette miss; no nearest-body fallback'
                    elif abs(relative)<.2:
                        # Find the first supported projected pelvic section above
                        # this source point. Only the unsupported central tip moves.
                        facing=-(caster.normal@direction)
                        eligible=self.pelvis&(facing>=.025)
                        triangles=self.surface['world'][self.surface['triangles'][eligible]].astype(float)
                        coordinate=np.einsum('ijk,k->ij',triangles,horizontal)
                        column=float(origin@horizontal);heights=[]
                        for a,b in [(0,1),(1,2),(2,0)]:
                            den=coordinate[:,b]-coordinate[:,a]
                            t=np.divide(column-coordinate[:,a],den,out=np.full(len(den),np.nan),where=abs(den)>1e-12)
                            valid=(t>=0)&(t<=1)
                            z=triangles[valid,a,2]+t[valid]*(triangles[valid,b,2]-triangles[valid,a,2])
                            heights.extend(z[(z>=source_z)&(z<=self.config['landmarks']['crotch_z']+.015)].tolist())
                        if not heights:raise ValueError('No local supported central crotch surface')
                        # Keep the inferred closure one authored edge-AA width
                        # inside the supported surface, rather than a tangent
                        # silhouette sample with unstable visibility.
                        clearance=float(self.config.get('garment_edge_aa_m',.0011))
                        # Projected triangle edges partition visibility changes.
                        # Test their bounded interior events, not an artist
                        # parameter/grid sweep or an unrestricted nearest point.
                        events=np.unique(np.r_[source_z,heights,self.config['landmarks']['crotch_z']+.015])
                        hit=None
                        for lo,hi in zip(events[:-1],events[1:]):
                            if hi-lo<1e-8:continue
                            target_z=float(lo+min(clearance,(hi-lo)/2))
                            lifted=origin.copy();lifted[2]+=target_z-source_z
                            candidate=caster.first_hit(lifted,direction,maximum,allowed_triangle_ids=self.pelvis,
                                                       min_facing_cos=.025,uv_seam_tolerance=2.)
                            if candidate.get('accepted'):hit=candidate;break
                        if hit is None:raise ValueError('No robust local central-tip first hit within actual crotch support bound')
                        method='First robust visible support interval from actual projected pelvic triangle-edge events; local central tip only, source horizontal position held'
                    else:raise ValueError('Unexplained middle source contour miss; no broad lifting allowed')
                if not hit.get('accepted'):raise ValueError('Local source garment fit remains unsupported: '+repr(dict(path=key,pixel=pixel.tolist(),hit=hit)))
                world=np.asarray(hit['world']);theta=float(np.arctan2(world[0]-self.center_xy[0],-(world[1]-self.center_xy[1])))
                points.append([theta,float(world[2])])
                records.append(dict(source_path_id=key,source_px=pixel.tolist(),source_z=source_z,
                                    original_ray_status=original['status'],method=method,hit=hit,
                                    local_height_delta_m=float(world[2]-source_z)))
        charts={}
        for view in ['front','back']:
            reference=self.surface['meta']['source_context']['views'][view]
            axis=np.asarray(reference['camera']['matrix'],float)[:3,0]
            observed=[r for r in records if r['source_path_id'].startswith(view+'.')]
            world=np.array([r['hit']['world'] for r in observed])
            # An unobserved central closure must cover the actual connected
            # bridge, not create a tiny third leg hole at a grazing support hit.
            # This changes only inferred FIELD anchors, never a seated point or
            # any observed source contour knot.
            for i,r in enumerate(observed):
                if r['original_ray_status']=='SEATED':continue
                relative=(r['source_px'][0]-self.config['source_axes_px'][view])/self.config['source_halfwidth_px']['briefs'][view]
                if abs(relative)<.2:
                    ceiling=self.config['landmarks']['crotch_z']-float(self.config.get('garment_edge_aa_m',.0011))
                    fitted=min(float(world[i,2]),ceiling)
                    r['inferred_cartesian_closure_z']=fitted
                    r['closure_limit']='Unsupported central FIELD anchor only; below actual connected bridge by edge AA margin, not a moved/visible source contour'
                    world[i,2]=fitted
            coordinate=world@axis
            order=np.argsort(coordinate)
            charts[view]=dict(horizontal_world_axis=axis.tolist(),
                              pairs=np.column_stack((coordinate[order],world[order,2])).tolist(),
                              method='Frozen original source camera horizontal coordinate vs actual seated world height; no radial/star-convex assumption')
        profile_records=[];profile_points=[]
        reference=self.surface['meta']['source_context']['views']['profile']
        axis=np.asarray(reference['camera']['matrix'],float)[:3,0]
        for key in ['profile.briefs.near_leg_opening','profile.briefs.rear_leg_fragment']:
            pixels=np.asarray(paths[key]['points_px'],float)
            origins,directions,maximum=seat.pixel_rays(reference['camera'],seat.source_to_render(pixels,reference['registration']))
            for pixel,origin,direction in zip(pixels,origins,directions):
                hit=caster.first_hit(origin,direction,maximum,allowed_triangle_ids=self.pelvis,min_facing_cos=.025,uv_seam_tolerance=2.)
                profile_records.append(dict(source_path_id=key,source_px=pixel.tolist(),hit=hit))
                if hit.get('accepted'):
                    q=np.array(hit['world']);profile_points.append([float(q@axis),float(q[2])])
        profile_points=np.asarray(profile_points,float);order=np.argsort(profile_points[:,0])
        inner=max(abs(r['hit']['world'][0]) for r in records if r['original_ray_status']=='SEATED')+.001
        outer=max(abs(r['hit']['world'][0]) for r in profile_records if r['hit'].get('accepted'))
        if outer-inner<.005:raise ValueError('No hidden lateral return remains outside preserved source knots')
        charts['profile_hidden_side']=dict(horizontal_world_axis=axis.tolist(),pairs=profile_points[order].tolist(),side_blend_abs_x_m=[inner,outer],
                                          influence='Only inferred lateral return beyond all observed front/back contours +1mm and abs(Y-centre)<16mm; observed knots held')
        proof=dict(target_sha256=self.surface['input_sha256'],records=records,profile_records=profile_records,
                   exact_original_ray_points=sum(r['original_ray_status']=='SEATED' for r in records),
                   local_fitted_misses=sum(r['original_ray_status']!='SEATED' for r in records),
                   policy='Preserve valid original front/back source-pixel contour rays; only missing central tips/lateral closure are inferred. No global affine leg-edge lift or nearest-body projection.',
                   cartesian_charts=charts,
                   profile_source_paths=['profile.briefs.near_leg_opening','profile.briefs.rear_leg_fragment'],
                   profile_limit='Visible profile rays constrain ONLY the hidden lateral return; residuals on other visible front/back sheets remain explicit for actual source-four-view review.',
                   polar_pairs_DIAGNOSTIC_ONLY=points)
        return charts,proof

    def brief_cartesian_boundary(self, charts):
        # Isocontour intersections are bound on the ACTUAL triangle edges.
        # Bisection stays on those edges: no global nearest-point projection.
        used=self.surface['triangles'][self.pelvis];faceids=np.flatnonzero(self.pelvis)
        values=self.surface['world'][:,2]-brief_leg_height(self.surface['world'],self.config,None,charts)
        edge_hits={};segments=[]
        for fi,face in zip(faceids,used):
            crosses=[]
            for i,j in [(0,1),(1,2),(2,0)]:
                vi,vj=int(face[i]),int(face[j]);a,b=values[vi],values[vj]
                if a*b>=0:continue
                key=tuple(sorted((vi,vj)))
                if key not in edge_hits:
                    lo,hi=0.,1.;wa=self.surface['world'][vi].astype(float);wb=self.surface['world'][vj].astype(float)
                    for _ in range(24):
                        t=(lo+hi)/2;q=wa*(1-t)+wb*t
                        value=float(q[2]-brief_leg_height(q[None,:],self.config,None,charts)[0])
                        if value*a>0:lo=t
                        else:hi=t
                    t=(lo+hi)/2;bary=np.zeros(3);bary[i]=1-t;bary[j]=t;q=wa*(1-t)+wb*t
                    edge_hits[key]=dict(accepted=True,status='SEATED',triangle_id=int(fi),barycentric=bary.tolist(),world=q.tolist(),
                                        method='Cartesian fixed-source-chart isocontour; bisection confined to actual target triangle edge')
                crosses.append(key)
            if len(crosses)==2:segments.append(crosses)
            elif crosses:raise ValueError('Degenerate brief isocontour triangle')
        degree={key:0 for key in edge_hits};graph={key:[] for key in edge_hits}
        for a,b in segments:degree[a]+=1;degree[b]+=1;graph[a].append(b);graph[b].append(a)
        bad=[key for key,d in degree.items() if d!=2]
        remaining=set(degree);components=[];component_bounds=[]
        while remaining:
            pending=[remaining.pop()];count=0;component=[]
            while pending:
                a=pending.pop();count+=1;component.append(a)
                for b in graph[a]:
                    if b in remaining:remaining.remove(b);pending.append(b)
            components.append(count)
            q=np.array([edge_hits[k]['world'] for k in component]);component_bounds.append([q.min(0).tolist(),q.max(0).tolist()])
        if len(components)!=2:bad.append(('leg_opening_components',len(components)))
        return dict(points=list(edge_hits.values()),closed=not bad,authoring_region='pelvis',
                    geometric_samples_complete=not bad,failures=[list(x) for x in bad],
                    source_camera_cartesian=True,closed_component_sizes=components,closed_component_bounds=component_bounds,
                    production_garment_ART=False)

    def seat_boundaries(self, curves, samples=128):
        result = {}
        for name, curve in curves.items():
            if name == 'bra_band_top': continue
            if name=='brief_leg' and self.config.get('brief_leg_source_charts') is not None:
                result[name]=self.brief_cartesian_boundary(self.config['brief_leg_source_charts']);continue
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
        result = []
        for key in ['front.neck.left_clavicle_line', 'front.neck.right_clavicle_line']:
            from fair_paths import source_curve_c1
            path = paths[key]; observed = np.asarray(path['points_px'], float)
            pixels=source_curve_c1(observed,maximum_step=.35)
            view=self.surface['meta']['source_context']['views']['front']
            origins,directions,maximum=seat.pixel_rays(view['camera'],seat.source_to_render(pixels,view['registration']))
            origins[:,2]+=shift_z
            fitted=[self._hit('upper',origin,direction,maximum,.10) for origin,direction in zip(origins,directions)]
            for hit, pixel in zip(fitted, pixels): hit['source_px'] = pixel.tolist()
            result.append(dict(source_path_id=key, source_px=path['points_px'], points=fitted,
                               fit=dict(common_z_translation_m=shift_z, anchor_z=landmarks['clavicle_anchor_z'],
                                        original_observed_anchors=path['points_px'],curve='Source-anchor-preserving C1 shape-preserving cubic; dense actual source-camera rays to semantic upper surface',
                                        maximum_source_curve_step_px=.35,horizontal_calibration='Actual recorded original-pixel source camera/SRT, no independent X warp'),
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
            width=self.config.get('strap_width_m',.013)
            if self.config.get('fair_straps',True):
                from fair_paths import fair_surface_strap
                route=fair_surface_strap(self.surface,self.upper,ids,[a,b],width)
                route.update(side=side,vertex_ids=ids,anchors=[a,b],raw_edge_world=v[ids].tolist(),
                             inferred='Continuous shoulder/back strap construction; source endpoints/width held, raw graph stairs faired without geometry changes.')
            else:route=dict(side=side,vertex_ids=ids,world=v[ids].tolist(),anchors=[a,b],width_m=width,
                            method='Unfaired diagnostic original edge route only')
            straps.append(route)
        return straps


def distance_to_polyline(points, line):
    points, line = np.asarray(points, float), np.asarray(line, float)
    best = np.full(len(points), np.inf)
    for a, b in zip(line[:-1], line[1:]):
        ab = b-a; t = np.clip((points-a) @ ab / max(float(ab@ab), 1e-24), 0, 1)
        best = np.minimum(best, np.linalg.norm(points-a-t[:, None]*ab, axis=1))
    return best
