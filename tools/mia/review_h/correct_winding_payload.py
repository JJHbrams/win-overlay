"""One root-authorized orientation-only correction of the frozen first H.

Writes a separate cache variant; no world coordinates, undirected connectivity,
UV mapping, vertex IDs, normals smoothing, unwrap, bpy or native changes.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import numpy as np

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT/'.mia-cache/body-h/shape/assembly'
OUT = BASE/'winding-fixed'


def ah(a): return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main():
    guard = load('h_winding_capacity', ROOT/'asset/mia/blender/mia-fit-v003/integration/workspace-storage-20261103/storage_guard.py')
    budget = guard.inspect(50*1024**2); assert not budget['violations'], budget
    assert not OUT.exists(), 'Do not overwrite the frozen corrected variant'
    source_geometry = BASE/'geometry.npz'; source_atlas = BASE/'atlas/atlas.npz'; source_surface = BASE/'atlas/surface.npz'
    source_files = [source_geometry, source_atlas, source_surface, BASE/'assembly.json', BASE/'atlas/surface.json', BASE/'verify.json']
    source_hashes = {str(p): sha(p) for p in source_files}
    source = dict(np.load(source_geometry)); data = {k: v.copy() for k, v in source.items()}
    atlas0 = dict(np.load(source_atlas)); atlas = {k: v.copy() for k, v in atlas0.items()}
    surface0 = dict(np.load(source_surface)); surface = {k: v.copy() for k, v in surface0.items()}
    api = load('h_winding_assembly', Path(__file__).with_name('assemble.py'))
    flips = api.collar_orientation_flips(data['triangles'], data['source_part'])
    assert flips.tolist() == [212463, 212757, 213493], ('Unexpected changed scope', flips.tolist())
    assert np.all(data['source_part'][flips] == 3)
    assert np.array_equal(np.sort(data['triangles'][flips], axis=1), np.sort(source['triangles'][flips], axis=1))
    data['triangles'][flips] = data['triangles'][flips][:, [0, 2, 1]]
    for key in ['old_loop_uv', 'source_corner_normals', 'source_corner_bary']:
        data[key][flips] = data[key][flips][:, [0, 2, 1]]
    atlas['loop_uv'][flips] = atlas['loop_uv'][flips][:, [0, 2, 1]]
    ids = surface['meshfaceid']; places = np.searchsorted(ids, flips)
    assert np.array_equal(ids[places], flips)
    for key in ['triangles', 'loop_uv']:
        surface[key][places] = surface[key][places][:, [0, 2, 1]]
    assert np.array_equal(data['world'], source['world'])
    assert np.array_equal(surface['world'], surface0['world'])
    assert np.array_equal(np.sort(data['triangles'], axis=1), np.sort(source['triangles'], axis=1))
    assert not len(api.collar_orientation_flips(data['triangles'], data['source_part']))
    # Inverse the same permutation: every world-vertex/corner-UV association
    # must recover the original mapping, rather than merely matching UV bounds.
    for key in ['triangles', 'old_loop_uv', 'source_corner_normals', 'source_corner_bary']:
        back = data[key].copy(); back[flips] = back[flips][:, [0, 2, 1]]
        assert np.array_equal(back, source[key]), key
    back = atlas['loop_uv'].copy(); back[flips] = back[flips][:, [0, 2, 1]]
    assert np.array_equal(back, atlas0['loop_uv'])
    for key in ['triangles', 'loop_uv']:
        back = surface[key].copy(); back[places] = back[places][:, [0, 2, 1]]
        assert np.array_equal(back, surface0[key]), key
    for key in source:
        if key not in ['triangles', 'old_loop_uv', 'source_corner_normals', 'source_corner_bary']:
            assert np.array_equal(data[key], source[key]), key
    OUT.mkdir(); (OUT/'atlas').mkdir()
    np.savez_compressed(OUT/'geometry.npz', **data)
    np.savez_compressed(OUT/'atlas/atlas.npz', **atlas)
    np.savez_compressed(OUT/'atlas/surface.npz', **surface)
    assembly = json.loads((BASE/'assembly.json').read_text())
    correction = dict(reason='Curved neck per-face radial orientation defect; coherent winding anchored to retained endpoints',
                      flipped_faces=flips.tolist(), flipped_body_surface_rows=places.tolist(), world_coordinates_exact=True,
                      undirected_connectivity_exact=True, world_vertex_UV_mapping_exact=True,
                      nonpermuted_arrays_exact=True, source_files_unchanged=source_hashes,
                      native_saved=False, GPU_used=False, unwrap_run=False, normals_smoothing=False)
    assembly.update(status='Orientation-only corrected static payload; actual gray/ART pending',
                    assembly_geometry_sha256=sha(OUT/'geometry.npz'), triangles_sha256=ah(data['triangles']),
                    collar_rows_path=str(BASE/'collar-rows.npz'), collar_rows_sha256=sha(BASE/'collar-rows.npz'),
                    winding_correction=correction)
    (OUT/'assembly.json').write_text(json.dumps(assembly, indent=2)+'\n', encoding='utf8', newline='\n')
    meta = json.loads((BASE/'atlas/surface.json').read_text())
    meta.update(payload_version='H-winding-fixed', geometry_world_sha256=ah(data['world']),
                triangles_sha256=ah(surface['triangles']), loop_uv_sha256=ah(surface['loop_uv']),
                surface_npz_sha256=sha(OUT/'atlas/surface.npz'), surface_npz_path=str(OUT/'atlas/surface.npz'),
                assembly_geometry_path=str(OUT/'geometry.npz'), atlas_path=str(OUT/'atlas/atlas.npz'),
                winding_correction=correction)
    (OUT/'atlas/surface.json').write_text(json.dumps(meta, indent=2)+'\n', encoding='utf8', newline='\n')
    assert all(sha(p) == h for p, h in source_hashes.items()), 'Frozen failed input changed'
    report = dict(correction, capacity=budget,
                  outputs={str(p): dict(sha256=sha(p), bytes=p.stat().st_size) for p in
                           [OUT/'geometry.npz', OUT/'atlas/atlas.npz', OUT/'atlas/surface.npz', OUT/'assembly.json', OUT/'atlas/surface.json']},
                  raw_bytes_written=sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file()),
                  fresh_CPU_verification='Pending separate verify_h.py run; curvature warning remains')
    (OUT/'winding-correction.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf8', newline='\n')
    print('H_WINDING_FIXED', json.dumps(dict(output=str(OUT), faces=flips.tolist(), bytes=report['raw_bytes_written'],
                                          geometry_sha256=sha(OUT/'geometry.npz'), surface_sha256=sha(OUT/'atlas/surface.npz'))), flush=True)


if __name__ == '__main__': main()
