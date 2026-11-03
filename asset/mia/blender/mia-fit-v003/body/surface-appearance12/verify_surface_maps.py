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
    skin_unique = np.unique(skin.reshape(-1, 3), axis=0)
    if len(skin_unique) != 1:
        raise ValueError('Initial plain-skin map is not uniform R3b-compatible skin')
    # Actual triangle-centroid UV lookup. Tiny faces may fall between texels;
    # both count and physical surface area are reported rather than hidden.
    world, tri, uv, region = [surface[k] for k in ['world', 'triangles', 'triangle_uv', 'face_region']]
    points = world[tri].mean(axis=1)
    center_uv = uv.mean(axis=1)
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
                  PNG_hashes_match=True, plain_skin_unique_RGB_u8=skin_unique.tolist(),
                  old_underwear_used=False,
                  triangle_centroid_samples=len(tri), actual_body_surface_area_m2=float(area.sum()),
                  forbidden_underwear_triangles=int(wrong.sum()),
                  forbidden_underwear_surface_area_m2=float(area[wrong].sum()),
                  forbidden_clavicle_triangles=int(wrong_clav.sum()),
                  texture_coverage_surface_area_m2=float(area[coverage>.5].sum()),
                  clavicle_ink_surface_area_m2=float(area[ink>.1].sum()),
                  clavicle_shade_surface_area_m2=float(area[shade>.1].sum()),
                  boundary_checks=route_checks,
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
