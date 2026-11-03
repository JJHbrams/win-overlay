"""Bake fixed3D body appearance into actual target UVs; CPU only."""
from pathlib import Path
import argparse
import json
import time
import numpy as np
from PIL import Image
from surface_api import load_surface, read_json, write_json, rasterize_world, pad_images, sha
from pattern_fields import make_recipe, TargetAuthor, distance_to_polyline, smooth01, seat, brief_leg_height


def linear_to_srgb(value):
    value = np.asarray(value, float)
    return np.where(value <= .0031308, 12.92*value, 1.055*value**(1/2.4)-.055)


def derive_config(surface, overrides=None):
    meta = surface['meta']
    config = dict(source_axes_px=dict(front=239., back=935., profile=568.),
                  source_halfwidth_px=dict(bra=dict(front=80., back=80.), briefs=dict(front=80., back=85.)),
                  torso_center_xy=[0., -.006], strap_width_m=.013,
                  allowed_region_ids=dict(upper=meta['allowed_regions']['bra'], pelvis=meta['allowed_regions']['briefs'],
                                          clavicle=meta['allowed_regions']['clavicle']),
                  fair_straps=True,clavicle_ink_sigma_m=.00065,fit_brief_leg_from_source=True,
                  skin_base_srgb=linear_to_srgb([.92, .69, .60]).tolist(),
                  lighting_config=dict(light_scale=.25, interpolation='EASE',
                                       ramp_stops=[[.025, [.48,.36,.34,1]], [.175,[.72,.63,.60,1]], [.55,[1,1,1,1]], [.95,[1.06,1.04,1.02,1]]]))
    transforms = {}
    views = meta['source_context']['views']
    for name, item in views.items():
        axis = item['registration'].get('source_center_x', 239.)
        pixels = seat.source_to_render([[axis, 0.], [axis, 1000.]], item['registration'])
        origin, direction, distance = seat.pixel_rays(item['camera'], pixels)
        # Recorded cameras have negligible pitch. Plane depth makes tiny matrix
        # precision differences explicit instead of treating nearplane as skin.
        axis_index = int(np.argmax(np.abs(direction[0])))
        plane = np.array([0., -.006, .86])
        amount = (plane[axis_index]-origin[:, axis_index])/direction[:, axis_index]
        points = origin + amount[:, None]*direction
        transforms[name] = [(points[1, 2]-points[0, 2])/1000., points[0, 2]]
    config['source_z_affine'] = transforms
    v, f = surface['world'], surface['triangles']
    used = np.unique(f)
    eligible = v[used]
    central = eligible[(abs(eligible[:, 0]) < .004) & (eligible[:, 2] < 1.035)]
    if not len(central): raise ValueError('Cannot derive current crotch bridge from body target')
    crotch = float(central[:, 2].min())
    if 'clavicle_source_graphic_support_world' in meta['landmarks']:
        anchor_z=float(meta['landmarks']['clavicle_source_graphic_support_world'][2])
        anchor_method='Actual current source-registered graphic support ray/barycentric landmark; not a recovered skeletal notch'
    elif 'clavicle_graphic_anchor_world' in meta['landmarks']:
        anchor_z=float(meta['landmarks']['clavicle_graphic_anchor_world'][2])
        anchor_method='Explicit current anatomical/source-aligned graphic landmark from target metadata'
    elif 'clavicle_anchor_z' in meta['landmarks']:
        anchor_z=float(meta['landmarks']['clavicle_anchor_z']);anchor_method='Explicit current target graphic anchor'
    else:
        if 'F_CPU_proof' in meta:raise ValueError('F requires actual current source graphic support metadata; no E ring-height fallback')
        guide_ring=meta['landmarks']['neck_guide_ring_center']
        anchor_z=float(guide_ring[2])-.036
        anchor_method='LEGACY E heuristic only; not accepted as final F anatomical/source anchor'
    config['landmarks'] = dict(crotch_z=crotch, clavicle_anchor_z=anchor_z)
    config['landmark_method'] = dict(crotch='Actual lowest central(|X|<4mm) body surface below waist; supported pose, not body dimensions recovered from source.',
                                    clavicle=anchor_method)
    if overrides:
        for key, value in overrides.items():
            if isinstance(value, dict) and isinstance(config.get(key), dict): config[key].update(value)
            else: config[key] = value
    return config


def _mask_regions(flat_region, allowed):
    return np.isin(flat_region, np.asarray(allowed, np.int16))


def paint_fields(raster, config, curves, clavicles, straps):
    occupied = raster['valid']; points = raster['world'][occupied].astype(float)
    region = raster['region'][occupied]
    x, y, z = points.T
    cx, cy = config['torso_center_xy']
    theta = np.arctan2(x-cx, -(y-cy))
    # This is the actual anatomical pattern chart. Boundaries come from newly
    # seated source-relative paths; it is not a uniform world-height belt.
    aa = .0011
    bra_bottom, bra_top = curves['bra_bottom'](theta), curves['bra_top'](theta)
    brief_bottom, brief_top = brief_leg_height(points,config,curves), curves['brief_waist'](theta)
    upper = _mask_regions(region, config['allowed_region_ids']['upper'])
    pelvis = _mask_regions(region, config['allowed_region_ids']['pelvis'])
    bra = smooth01((z-bra_bottom+aa)/(2*aa))*smooth01((bra_top-z+aa)/(2*aa))*upper
    brief = smooth01((z-brief_bottom+aa)/(2*aa))*smooth01((brief_top-z+aa)/(2*aa))*pelvis
    strap_alpha = np.zeros(len(points))
    strap_roi = upper & (abs(x) > .025) & (abs(x) < .145) & (z > 1.235)
    for strap in straps:
        selected = strap_roi & (x*strap['side'] > 0)
        distance = distance_to_polyline(points[selected], strap['world'])
        strap_alpha[selected] = np.maximum(strap_alpha[selected], smooth01((strap['width_m']/2+aa-distance)/(2*aa)))
    coverage = np.maximum.reduce([bra, brief, strap_alpha])
    ink, shade = np.zeros(len(points)), np.zeros(len(points))
    clavicle_domain=_mask_regions(region,config['allowed_region_ids'].get('clavicle',[1,3,4,12]))
    for path in clavicles:
        line = np.array([hit['world'] for hit in path['points']])
        # Bound by CURRENT surface-seated curves, never old E world-height bands.
        clavicle_roi=clavicle_domain & (points>=line.min(0)-.020).all(1)&(points<=line.max(0)+.020).all(1)
        distance = distance_to_polyline(points[clavicle_roi], line)
        ink[clavicle_roi] = np.maximum(ink[clavicle_roi], np.exp(-.5*(distance/config.get('clavicle_ink_sigma_m',.00065))**2))
        # Authored soft warmth below the graphic, not a geometric groove or
        # a claim that the source under-chin lighting was physically recovered.
        shifted = line.copy(); shifted[:, 2] -= .0025
        distance = distance_to_polyline(points[clavicle_roi], shifted)
        shade[clavicle_roi] = np.maximum(shade[clavicle_roi], np.exp(-.5*(distance/.0035)**2))
    skin_rgb = np.asarray(config['skin_base_srgb'], float)
    skin = np.broadcast_to(skin_rgb, (len(points), 3)).copy()
    if 'neck_alpha' in raster:
        from neck_pigment import COMMON, HEAD
        a=raster['neck_alpha'][occupied].astype(float)
        skin=linear_to_srgb(COMMON[None,:]*(1-a[:,None])+HEAD[None,:]*a[:,None])
    elif config.get('neck_tint_srgb') is not None:
        bounds = config.get('neck_tint_z', [1.425, 1.465])
        factor = smooth01((z-bounds[0])/(bounds[1]-bounds[0]))
        skin = skin*(1-factor[:, None]) + np.asarray(config['neck_tint_srgb'])*factor[:, None]
    cloth = np.broadcast_to(np.array([103., 101., 106.])/255., skin.shape).copy()
    seam_z = curves['bra_band_top'](theta)
    seam = np.exp(-.5*((z-seam_z)/.0009)**2) * np.clip(np.cos(theta), 0, 1) * upper
    band = smooth01((seam_z-z)/.002) * (z > bra_bottom) * upper
    edge_distance = np.minimum.reduce([abs(z-bra_bottom), abs(z-bra_top), abs(z-brief_bottom), abs(z-brief_top)])
    edge = np.exp(-.5*(edge_distance/.0007)**2)
    cloth *= (1-.16*seam-.045*band-.055*edge)[:, None]
    images = {}
    for name, values, background in [('SkinBaseColor', skin, skin_rgb), ('UnderwearBaseColor', cloth, np.array([103,101,106])/255),
                                      ('UnderwearCoverage', coverage, 0.), ('ClavicleInk', ink, 0.), ('ClavicleShade', shade, 0.)]:
        shape = occupied.shape + (() if np.ndim(values)==1 else (3,))
        image = np.empty(shape, np.float32); image[...] = background
        image[occupied] = values
        images[name] = image
    stats = dict(occupied_texels=int(occupied.sum()), underwear_texels_over_half=int((coverage>.5).sum()),
                 clavicle_ink_texels_over_tenth=int((ink>.1).sum()), clavicle_shade_texels_over_tenth=int((shade>.1).sum()),
                 underwear_coverage_range=[float(coverage.min()),float(coverage.max())],
                 same_fixed_world_fields_for_all_views=True, base_skin_srgb=skin_rgb.tolist(),
                 old_underwear_texture_used=False)
    stats['neck_boundary_prelight_continuation']='neck_alpha' in raster
    return images, stats


def bake(surface_path, output, *, size=2048, config_path=None, neck_inputs_path=None):
    start = time.time(); out = Path(output); out.mkdir(parents=True, exist_ok=True)
    surface = load_surface(surface_path)
    metadata_path=Path(surface_path).with_suffix('.json');metadata_sha256=sha(metadata_path)
    overrides = read_json(config_path) if config_path else None
    config = derive_config(surface, overrides)
    neck_inputs=read_json(neck_inputs_path) if neck_inputs_path else surface['meta'].get('neck_pigment_inputs')
    if neck_inputs is not None:config['neck_pigment_inputs']=neck_inputs
    write_json(out/'authoring-config.json', config)
    curves, recipe, paths = make_recipe(config)
    author = TargetAuthor(surface, config)
    if config.get('fit_brief_leg_from_source'):
        charts,brief_proof=author.fit_brief_leg_source(paths)
        config['brief_leg_source_charts']=charts
        # Legacy polar curve is retained solely as diagnostic metadata.
        config['brief_leg_surface_pairs']=brief_proof['polar_pairs_DIAGNOSTIC_ONLY']
        config['brief_source_fit_proof']=brief_proof
        config['brief_leg_surface_target_sha256']=surface['input_sha256']
        curves,recipe,paths=make_recipe(config)
        write_json(out/'brief-source-fit.json',brief_proof)
        write_json(out/'authoring-config.json',config)
    boundaries = author.seat_boundaries(curves)
    clavicles = author.clavicle(paths)
    write_json(out/'seated-boundaries.json', dict(surface_guards=surface['guards'], boundaries=boundaries, clavicles=clavicles,
                                                 scope='Actual preview surface chart bindings, not final garment/art approval.'))
    bad = {name: path['failures'] for name, path in boundaries.items() if not path['geometric_samples_complete']}
    if bad or not all(path['geometric_samples_complete'] for path in clavicles):
        raise ValueError('Seating incomplete: '+json.dumps(dict(boundaries=bad, clavicle=[p['geometric_samples_complete'] for p in clavicles])))
    straps = author.strap_paths(curves)
    write_json(out/'seated-straps.json', dict(straps=straps, geometry_guards=surface['guards']))
    write_json(out/'pattern-recipe.json', recipe)
    print('MIA12_SEATING_COMPLETE', flush=True)
    raster = rasterize_world(surface, size=size)
    if neck_inputs is not None:
        from neck_pigment import prepare, sample_alpha
        vertex_alpha,neck_report=prepare(surface,neck_inputs)
        raster['neck_alpha']=sample_alpha(raster,surface,vertex_alpha)
        write_json(out/'neck-prelight-field.json',neck_report)
    images, stats = paint_fields(raster, config, curves, clavicles, straps)
    padded, padding = pad_images(images, raster['valid'], pixels=4)
    files = []
    for name, array in padded.items():
        data = np.rint(np.clip(array, 0, 1)*255).astype(np.uint8)
        file = out/(name+'.png'); Image.fromarray(data).save(file)
        files.append(dict(path=str(file.resolve()), sha256=sha(file), size=[size,size],
                          color_space='sRGB' if name.endswith('BaseColor') else 'Non-Color',
                          active_use='body-only pigment' if name.endswith('BaseColor') else 'body-only material control'))
    diagnostic = out/'UV_ValidMask_DIAGNOSTIC.png'
    Image.fromarray(raster['valid'].astype(np.uint8)*255).save(diagnostic)
    if sha(surface_path)!=surface['input_sha256'] or sha(metadata_path)!=metadata_sha256:raise ValueError('Frozen target arrays/metadata changed during bake')
    report = dict(status='CPU UV-map bake complete; actual shader/native/source appearance review remains required',
                  surface_metadata_sha256=metadata_sha256,
                  surface_input=surface['input_path'], surface_input_sha256=surface['input_sha256'], surface_guards=surface['guards'],
                  UV_numeric_quality=surface['uv_numeric_stats'],
                  raster=raster['report'], field_stats=stats, files=files,
                  island_padding_pixels=4, padded_texels=int(padding.sum()-raster['valid'].sum()),
                  geometry_unchanged=True, GPU_used=False, elapsed_seconds=time.time()-start,
                  source_fit='Source-relative anatomical chart, actual radial first hits and triangle/barycentric UV bindings; inferred construction labelled.',
                  limits=['Same supported body shape in both material versions; no new unsupported-anatomy sculpt.',
                          'Underwear is a surface texture, not cloth thickness/compression or production rigging.',
                          'Skin tone/light transfer is cloned from saved R3b common skin; actual neck color-only seam review is still required.'])
    write_json(out/'bake-report.json', report)
    print(json.dumps(report, indent=2), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('surface')
    parser.add_argument('--output', required=True)
    parser.add_argument('--size', type=int, default=2048)
    parser.add_argument('--config')
    parser.add_argument('--neck-inputs')
    args = parser.parse_args()
    bake(args.surface, args.output, size=args.size, config_path=args.config, neck_inputs_path=args.neck_inputs)
