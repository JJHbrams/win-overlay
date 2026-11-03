"""Independent final PNG / actual body-surface footprint checks; no render."""
from pathlib import Path
import argparse
import numpy as np
from PIL import Image
from surface_api import load_surface, read_json, write_json, sha


def bilinear(image, uv):
    a = np.asarray(image, float) / 255.
    h, w = a.shape[:2]
    x = np.clip(uv[:, 0] * w - .5, 0, w-1)
    y = np.clip((1-uv[:, 1]) * h - .5, 0, h-1)
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    x1, y1 = np.minimum(x0+1, w-1), np.minimum(y0+1, h-1)
    tx, ty = x-x0, y-y0
    if a.ndim == 3:
        tx, ty = tx[:, None], ty[:, None]
    return ((1-tx)*(1-ty)*a[y0, x0] + tx*(1-ty)*a[y0, x1]
            + (1-tx)*ty*a[y1, x0] + tx*ty*a[y1, x1])


def verify(surface_file, map_dir):
    p = Path(map_dir).resolve()
    surface = load_surface(surface_file)
    bake = read_json(p/'bake-report.json')
    if bake['surface_input_sha256'] != sha(surface_file):
        raise ValueError('Final map target fingerprint is stale')
    if bake['surface_guards'] != surface['guards']:
        raise ValueError('Final map geometry/UV/semantic fingerprints differ')
    files = {}
    for item in bake['files']:
        path = p/Path(item['path']).name
        if sha(path) != item['sha256']:
            raise ValueError('Baked PNG changed: '+str(path))
        image = Image.open(path)
        if list(image.size) != item['size']:
            raise ValueError('Baked PNG size differs: '+str(path))
        files[path.stem] = np.asarray(image)
    skin = files['SkinBaseColor']
    uniform=bool(np.all(skin==skin[0,0]))
    skin_unique=[skin[0,0].tolist()] if uniform else None
    config=read_json(p/'authoring-config.json')
    if not uniform and not config.get('neck_pigment_inputs') and not config.get('neck_tint_srgb'):
        raise ValueError('Varying body skin requires an explicit neck/source pigment recipe')
    # Actual triangle-centroid UV lookup. Tiny faces may fall between texels;
    # both count and physical surface area are reported rather than hidden.
    world, tri, uv, region = [surface[k] for k in ['world', 'triangles', 'triangle_uv', 'face_region']]
    points = world[tri].mean(axis=1)
    center_uv = uv.mean(axis=1)
    sampled_skin=bilinear(skin,center_uv)
    ordinary_skin=~np.isin(region,[3,12])
    ordinary_error=float(np.max(abs(sampled_skin[ordinary_skin]-np.rint(np.asarray(config['skin_base_srgb'])*255)/255)))
    if ordinary_error>1.01/255:
        raise ValueError('Body pigment changed outside authorized neck continuation')
    area = np.linalg.norm(np.cross(world[tri[:, 1]]-world[tri[:, 0]],
                                   world[tri[:, 2]]-world[tri[:, 0]]), axis=1)/2
    coverage = bilinear(files['UnderwearCoverage'], center_uv)
    ink = bilinear(files['ClavicleInk'], center_uv)
    shade = bilinear(files['ClavicleShade'], center_uv)
    arms = np.isin(region, [6, 7, 14, 15])
    lower_leg = np.isin(region, [10, 11]) & (points[:, 2] < .85)
    forbidden = arms | lower_leg
    wrong = forbidden & (coverage > .5)
    clav_forbidden = ~np.isin(region, [1, 3, 4, 12])
    wrong_clav = clav_forbidden & (np.maximum(ink, shade) > .2)
    if np.any(wrong) or np.any(wrong_clav):
        raise ValueError('PNG footprint crossed anatomical ownership: '+repr(dict(
            underwear=surface['meshfaceid'][wrong].tolist(),
            clavicle=surface['meshfaceid'][wrong_clav].tolist())))
    # Ownership alone cannot detect a peach puncture on a correctly labelled
    # torso triangle. Independently compare PNG lookup with deep fixed-world
    # garment interiors at every actual triangle centroid.
    from pattern_fields import make_recipe, distance_to_polyline, brief_leg_height
    curves,_,_=make_recipe(config)
    theta=np.arctan2(points[:,0]-config['torso_center_xy'][0],-(points[:,1]-config['torso_center_xy'][1]))
    z=points[:,2];margin=.004
    upper=np.isin(region,config['allowed_region_ids']['upper'])
    pelvis=np.isin(region,config['allowed_region_ids']['pelvis'])
    deep=(upper&(z>curves['bra_bottom'](theta)+margin)&(z<curves['bra_top'](theta)-margin))
    deep|=(pelvis&(z>brief_leg_height(points,config,curves)+margin)&(z<curves['brief_waist'](theta)-margin))
    for strap in read_json(p/'seated-straps.json')['straps']:
        selected=upper&(points[:,0]*strap['side']>0)&(abs(points[:,0])>.025)&(abs(points[:,0])<.145)&(z>1.235)
        distance=distance_to_polyline(points[selected],strap['world'])
        deep[selected]|=distance<strap['width_m']/2-margin
    missing_cloth=deep&(coverage<.95)
    interior=dict(deep_interior_margin_m=margin,deep_cloth_triangle_centroids=int(deep.sum()),
                  minimum_bilinear_coverage=float(coverage[deep].min()) if deep.any() else None,
                  below_point95=int(missing_cloth.sum()),
                  offending_body_triangle_ids=np.flatnonzero(missing_cloth).tolist(),
                  offending_surface_area_m2=float(area[missing_cloth].sum()))
    write_json(p/'interior-coverage-proof.json',interior)
    if missing_cloth.any():
        raise ValueError('PNG deep cloth interiors contain gaps; see interior-coverage-proof.json ('+str(int(missing_cloth.sum()))+' triangles)')
    seats = read_json(p/'seated-boundaries.json')
    route_checks = []
    for name, route in seats['boundaries'].items():
        errors = []
        for point in route['points']:
            if not point.get('accepted'):
                raise ValueError('Unaccepted fitted boundary point')
            reconstructed = np.asarray(point['barycentric']) @ world[tri[point['triangle_id']]]
            errors.append(float(np.linalg.norm(reconstructed-np.asarray(point['world']))))
        route_checks.append(dict(name=name, accepted=len(errors),
                                 max_barycentric_world_error_m=max(errors)))
    report = dict(status='PASS CPU footprint / file guards only; actual native appearance remains pending',
                  surface_sha256=sha(surface_file), surface_guards=surface['guards'],
                  PNG_hashes_match=True, plain_skin_unique_RGB_u8=skin_unique,
                  body_skin_outside_neck_max_sRGB_error=ordinary_error,
                  old_underwear_used=False,
                  triangle_centroid_samples=len(tri), actual_body_surface_area_m2=float(area.sum()),
                  forbidden_underwear_triangles=int(wrong.sum()),
                  forbidden_underwear_surface_area_m2=float(area[wrong].sum()),
                  forbidden_clavicle_triangles=int(wrong_clav.sum()),
                  texture_coverage_surface_area_m2=float(area[coverage>.5].sum()),
                  clavicle_ink_surface_area_m2=float(area[ink>.1].sum()),
                  clavicle_shade_surface_area_m2=float(area[shade>.1].sum()),
                  boundary_checks=route_checks,
                  deep_interior_coverage=interior,
                  limits=['Centroid tests are ownership/route checks, not a continuous texture filtering proof.',
                          'UV subtexel triangles and declared overlap tolerance remain in bake-report.json.',
                          'No geometry, native scene, renderer, source image or face/hair material was changed.'])
    write_json(p/'footprint-proof.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('surface')
    parser.add_argument('map_dir')
    args = parser.parse_args()
    print(verify(args.surface, args.map_dir))
