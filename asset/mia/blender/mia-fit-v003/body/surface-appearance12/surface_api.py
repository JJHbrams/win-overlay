"""Static body-only UV/geometry contract and deterministic CPU rasterization.

No Blender scene, model, source image or old proof is mutated here.
"""
from pathlib import Path
import hashlib
import json
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def array_sha(array, dtype=None):
    return hashlib.sha256(np.ascontiguousarray(array, dtype=dtype).tobytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n',
                          encoding='utf-8', newline='\n')


def load_surface(npz_path, json_path=None):
    path = Path(npz_path)
    packed = np.load(path, allow_pickle=False)
    uv_key = 'loop_uv' if 'loop_uv' in packed else 'triangle_uv'
    out = dict(world=np.asarray(packed['world'], np.float32),
               triangles=np.asarray(packed['triangles'], np.int32),
               triangle_uv=np.asarray(packed[uv_key], np.float32),
               face_region=np.asarray(packed['face_region'], np.int16))
    out['meshfaceid'] = np.asarray(packed['meshfaceid'], np.int32) if 'meshfaceid' in packed else np.arange(len(out['triangles']), dtype=np.int32)
    meta_path = Path(json_path) if json_path else path.with_suffix('.json')
    meta = read_json(meta_path) if meta_path.is_file() else {}
    out['uv_layer'] = meta.get('uv_layer', meta.get('uv_layer_name', 'MIA_Review12UV'))
    v, f, uv = out['world'], out['triangles'], out['triangle_uv']
    assert v.ndim == 2 and v.shape[1] == 3 and f.ndim == 2 and f.shape[1] == 3
    assert uv.shape == (len(f), 3, 2) and out['face_region'].shape == (len(f),)
    assert np.isfinite(v).all() and np.isfinite(uv).all()
    assert len(f) and f.min() >= 0 and f.max() < len(v)
    assert uv.min() >= -1e-6 and uv.max() <= 1 + 1e-6
    area2 = np.cross(uv[:, 1] - uv[:, 0], uv[:, 2] - uv[:, 0])
    assert np.all(np.abs(area2) > 1e-12), 'Body atlas contains degenerate UV triangles'
    labels = meta.get('region_labels', {})
    if isinstance(labels, list):
        labels = {str(i): label for i, label in enumerate(labels)}
    out['region_labels'] = {int(k): str(value) for k, value in labels.items()}
    out['meta'] = meta
    out['input_path'] = str(path.resolve())
    out['input_sha256'] = sha(path)
    out['guards'] = dict(world_f32_sha256=array_sha(v), triangles_i32_sha256=array_sha(f),
                         triangle_uv_f32_sha256=array_sha(uv), face_region_i16_sha256=array_sha(out['face_region']),
                         vertices=len(v), body_triangles=len(f), uv_layer=out['uv_layer'])
    return out


def regions(surface, words, explicit=None):
    if explicit is not None:
        return np.isin(surface['face_region'], np.asarray(explicit, np.int16))
    labels = surface['region_labels']
    ids = [key for key, text in labels.items() if any(word in text.lower() for word in words)]
    if not ids:
        raise ValueError('Anatomical region labels required for ' + ', '.join(words))
    return np.isin(surface['face_region'], ids)


def rasterize_world(surface, size=2048, overlap_tolerance_m=.002):
    """Rasterize real loop UVs, rejecting different-world atlas overlaps.

    Texel centers are ((x+.5)/size,1-(y+.5)/size). Shared triangle edge co-hits
    are accepted only when their world positions agree. This is not a UV unwrap.
    """
    v, f, uv = surface['world'], surface['triangles'], surface['triangle_uv']
    world = np.zeros((size, size, 3), np.float32)
    normal = np.zeros_like(world)
    region = np.full((size, size), -1, np.int16)
    owner = np.full((size, size), -1, np.int32)
    conflicts, cohit, skipped = [], 0, 0
    tri_world = v[f].astype(np.float64)
    face_n = np.cross(tri_world[:, 1] - tri_world[:, 0], tri_world[:, 2] - tri_world[:, 0])
    face_n /= np.maximum(np.linalg.norm(face_n, axis=1)[:, None], 1e-30)
    for index, chart in enumerate(uv):
        pix = np.column_stack((chart[:, 0] * size - .5, (1 - chart[:, 1]) * size - .5)).astype(float)
        lo = np.maximum(np.ceil(pix.min(0)).astype(int), 0)
        hi = np.minimum(np.floor(pix.max(0)).astype(int), size - 1)
        if np.any(hi < lo):
            skipped += 1
            continue
        xx, yy = np.meshgrid(np.arange(lo[0], hi[0] + 1), np.arange(lo[1], hi[1] + 1))
        a, b, c = pix
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        w0 = ((b[1] - c[1]) * (xx - c[0]) + (c[0] - b[0]) * (yy - c[1])) / den
        w1 = ((c[1] - a[1]) * (xx - c[0]) + (a[0] - c[0]) * (yy - c[1])) / den
        w2 = 1 - w0 - w1
        inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not inside.any():
            skipped += 1
            continue
        px, py = xx[inside], yy[inside]
        bary = np.column_stack((w0[inside], w1[inside], w2[inside]))
        points = (bary @ tri_world[index]).astype(np.float32)
        old = owner[py, px]
        occupied = old >= 0
        if occupied.any():
            cohit += int(occupied.sum())
            distance = np.linalg.norm(world[py[occupied], px[occupied]] - points[occupied], axis=1)
            bad = np.flatnonzero(distance > overlap_tolerance_m)
            if len(bad):
                conflicts.append(dict(triangle=index, previous=old[occupied][bad[:5]].tolist(),
                                      max_world_distance_m=float(distance[bad].max()), texels=len(bad)))
        fresh = ~occupied
        world[py[fresh], px[fresh]] = points[fresh]
        normal[py[fresh], px[fresh]] = face_n[index]
        region[py[fresh], px[fresh]] = surface['face_region'][index]
        owner[py[fresh], px[fresh]] = index
    if conflicts:
        raise ValueError('Atlas different-world overlap: ' + json.dumps(conflicts[:8]))
    mask = owner >= 0
    report = dict(size=size, occupied_texels=int(mask.sum()), uv_cohits=cohit,
                  skipped_subtexel_triangles=skipped, different_world_overlap_count=0,
                  overlap_tolerance_m=overlap_tolerance_m, texel_center_convention='u=(x+.5)/N,v=1-(y+.5)/N')
    return dict(world=world, normal=normal, region=region, triangle_id=owner, valid=mask, report=report)


def pad_images(images, occupied, pixels=4):
    """Propagate nearest first-arrival values into atlas gutters, never repaint islands."""
    done = occupied.copy()
    result = {name: np.asarray(value).copy() for name, value in images.items()}
    shifts = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    for _ in range(pixels):
        prior = done.copy()
        for dy, dx in shifts:
            src = np.roll(np.roll(prior, dy, 0), dx, 1)
            if dy > 0: src[:dy] = False
            if dy < 0: src[dy:] = False
            if dx > 0: src[:, :dx] = False
            if dx < 0: src[:, dx:] = False
            take = src & ~done
            for name, value in result.items():
                moved = np.roll(np.roll(value, dy, 0), dx, 1)
                value[take] = moved[take]
            done |= take
    return result, done


def srgb_to_linear(rgb):
    value = np.asarray(rgb, float)
    return np.where(value <= .04045, value / 12.92, ((value + .055) / 1.055) ** 2.4)
