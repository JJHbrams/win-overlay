"""Bind the actual H surface to the existing Review12 appearance functions.

prepare writes only small metadata/configuration receipts. bake requires a
separate root-authored actual-gray decision and never grants that decision.
No mesh/UV/native, original metadata, or source image is modified or copied.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import importlib.util
import json
import sys
import time
import numpy as np
from PIL import Image

sys.dont_write_bytecode = True
CANONICAL = Path(__file__).resolve().parents[3]
APPEARANCE = Path('asset/mia/blender/mia-fit-v003/body/surface-appearance12')
REVIEW = Path('asset/mia/blender/mia-fit-v003/body/surface-review12')
CACHE = Path('.mia-cache/body-h/appearance')
ASSEMBLY = Path('.mia-cache/body-h/shape/assembly')
CLAVICLE_Z = 1.37778
SIZE = 4096


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2)+'\n', encoding='utf8', newline='\n')


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def api(root):
    # Existing sibling imports must resolve to the same canonical implementation.
    directory = Path(root)/APPEARANCE
    sys.path.insert(0, str(directory))
    return load('mia_h_existing_baker', directory/'bake_surface.py')


def api_provenance(root):
    directory = Path(root)/APPEARANCE
    names = ['bake_surface.py', 'surface_api.py', 'pattern_fields.py',
             'fair_paths.py', 'neck_pigment.py', 'install_material.py',
             'tied-guide-paths.json']
    names = [directory/name for name in names]
    names.append(Path(root)/'asset/mia/blender/mia-fit-v003/underwear-source/source-paths.json')
    return [dict(path=str(path.resolve()), sha256=sha(path)) for path in names]


def output_path(root, path):
    root = Path(root).resolve(); path = Path(path).resolve()
    allowed = (root/CACHE).resolve()
    if path != allowed and allowed not in path.parents:
        raise ValueError('H appearance output must stay in canonical ignored cache')
    return path


def capacity(root, mib):
    guard = load('mia_h_appearance_capacity', Path(root)/'asset/mia/blender/mia-fit-v003/integration/workspace-storage-20261103/storage_guard.py')
    report = guard.inspect(mib*1024**2)
    if report['violations']:
        raise RuntimeError('Capacity preflight failed: '+json.dumps(report['violations']))
    return report


def prepared_metadata(original, surface_path, geometry_path, atlas_path=None):
    if original.get('payload_version') != 'H':
        raise ValueError('Only the actual fresh H atlas metadata is supported')
    result = copy.deepcopy(original)
    result['landmarks']['clavicle_anchor_z'] = CLAVICLE_Z
    result['landmarks']['clavicle_anchor_provenance'] = {
        'meaning': 'Prior source-registered graphic support height, not a skeletal landmark or recovered 3D point',
        'world_z_m': CLAVICLE_Z,
        'limit': 'Re-seat the original source graphic on the current H surface; actual four-view material review remains required.',
    }
    result['prepared_surface_npz'] = str(Path(surface_path).resolve())
    result['surface_npz_path'] = str(Path(surface_path).resolve())
    result['assembly_geometry_path'] = str(Path(geometry_path).resolve())
    if atlas_path is not None:
        result['atlas_path'] = str(Path(atlas_path).resolve())
    result['preparation_scope'] = 'Metadata overlay only; same immutable H NPZ/UV. No geometry copy, source warp or art acceptance.'
    return result


def target_paths(root, selection=None):
    """Read a root-authored candidate selection; never write/select one here."""
    root = Path(root).resolve(); base = (root/ASSEMBLY).resolve()
    chosen = Path(selection) if selection is not None else root/'.mia-cache/body-h/selected-candidate.json'
    chosen = (root/chosen).resolve() if not chosen.is_absolute() else chosen.resolve()
    result = dict(surface=base/'atlas/surface.npz', geometry=base/'geometry.npz', atlas=base/'atlas/atlas.npz')
    selection_record = None
    if selection is not None or chosen.exists():
        if root/'.mia-cache/body-h' not in chosen.parents:
            raise ValueError('Candidate selection must stay in this canonical H cache')
        migrated = load('mia_h_selected_paths', Path(__file__).resolve().parents[1]/'review_h/paths.py')
        selection_sha = sha(chosen)
        record = read(chosen)
        for role in ('geometry', 'surface', 'atlas'):
            item = record.get(role, {})
            if not isinstance(item, dict) or not item.get('path') or not item.get('sha256'):
                raise ValueError('Selection requires path and sha256: '+role)
            path = Path(item['path'])
            if not path.is_absolute():
                raise ValueError('Selected candidate paths must be absolute: '+role)
            # Keep frozen selection bytes; bind known former roots to this
            # worktree before enforcing the existing assembly-cache/hash guard.
            path = migrated.migrated_path(path, root=root).resolve()
            if base not in path.parents:
                raise ValueError('Selected candidate input must stay in assembly cache: '+role)
            if sha(path) != item['sha256']:
                raise ValueError('Selected candidate input hash differs: '+role)
            result[role] = path
        if sha(chosen) != selection_sha:
            raise ValueError('Candidate selection changed while binding inputs')
        selection_record = dict(path=str(chosen), sha256=selection_sha)
    result['original_metadata'] = result['surface'].with_suffix('.json')
    result['assembly'] = result['geometry'].with_name('assembly.json')
    return result, selection_record


def target_binding(root, selection=None):
    from surface_api import load_surface, array_sha
    root = Path(root).resolve()
    paths, selection_record = target_paths(root, selection)
    surface_path = paths['surface']
    geometry_path, atlas_path = paths['geometry'], paths['atlas']
    surface = load_surface(surface_path)
    meta = surface['meta']
    if meta.get('payload_version') != 'H':
        raise ValueError('Fresh H payload_version required')
    if meta['surface_npz_sha256'] != surface['input_sha256']:
        raise ValueError('H surface NPZ hash differs from exported metadata')
    for key, actual in [('geometry_world_sha256', array_sha(surface['world'])),
                        ('triangles_sha256', array_sha(surface['triangles'])),
                        ('loop_uv_sha256', array_sha(surface['triangle_uv']))]:
        if meta.get(key) != actual:
            raise ValueError('H exported array mismatch: '+key)
    assembly = read(paths['assembly'])
    if assembly['assembly_geometry_sha256'] != sha(geometry_path):
        raise ValueError('H assembly geometry changed after export')
    with np.load(geometry_path, allow_pickle=False) as geometry, np.load(atlas_path, allow_pickle=False) as atlas:
        if not np.array_equal(surface['world'], geometry['world']):
            raise ValueError('H surface WORLD coordinates differ from assembly')
        if not np.array_equal(surface['triangles'], geometry['triangles'][surface['meshfaceid']]):
            raise ValueError('H surface triangle ownership differs from assembly')
        if not np.array_equal(surface['triangle_uv'], atlas['loop_uv'][surface['meshfaceid']]):
            raise ValueError('H surface UV differs from installed atlas')
    binding = {name: dict(path=str(path.resolve()), sha256=sha(path)) for name, path in paths.items()}
    if selection_record is not None:
        binding['candidate_selection'] = selection_record
    return surface, binding


def prepare(root=CANONICAL, output=None, selection=None):
    root = Path(root).resolve(); out = output_path(root, output or root/CACHE/'prepared-H')
    baker = api(root)
    surface, binding = target_binding(root, selection)
    if (out/'prepare-report.json').exists():
        previous = read(out/'prepare-report.json')
        if previous['binding'] != binding:
            raise ValueError('Prepared H binding is stale; retain it and select a new cache output')
        if previous['appearance_implementation'] != api_provenance(root):
            raise ValueError('Appearance implementation/source paths changed after preparation')
        for role in ('prepared_metadata', 'config', 'neck_inputs'):
            record = previous[role]
            if sha(record['path']) != record['sha256']:
                raise ValueError('Prepared receipt changed: '+role)
        return previous
    if out.exists() and any(out.iterdir()):
        raise ValueError('Do not overwrite an incomplete H preparation')
    budget = capacity(root, 2)
    geometry_path = Path(binding['geometry']['path'])
    meta = prepared_metadata(surface['meta'], binding['surface']['path'], geometry_path,
                             binding['atlas']['path'])
    if 'candidate_selection' in binding:
        meta['root_candidate_selection'] = binding['candidate_selection']
    surface['meta'] = meta
    neck_paths = dict(head_source_npz=geometry_path, donor_npz=root/REVIEW/'donor.npz',
                      attributes_npz=root/REVIEW/'head-attributes.npz')
    neck_inputs = {key: str(path.resolve()) for key, path in neck_paths.items()}
    neck_inputs['expected_sha256'] = {key: sha(path) for key, path in neck_paths.items()}
    neck_inputs['neck_face_regions'] = [3, 12]
    overrides = dict(fair_straps=True, fit_brief_leg_from_source=True,
                     clavicle_ink_sigma_m=.00065,
                     skin_base_srgb=baker.linear_to_srgb([.92, .69, .60]).tolist())
    config = baker.derive_config(surface, overrides)
    # This checks the current shared physical interface and actual slot10 alpha
    # without rasterizing an image or changing the original head material.
    from neck_pigment import prepare as neck_prepare
    _, neck_report = neck_prepare(surface, neck_inputs)
    out.mkdir(parents=True, exist_ok=True)
    metadata_file, config_file, neck_file = out/'surface-prepared.json', out/'config.json', out/'neck-inputs.json'
    write(metadata_file, meta); write(config_file, config); write(neck_file, neck_inputs)
    write(out/'neck-interface-check.json', neck_report)
    report = dict(status='Prepared metadata/configuration only; no bake/native/render/art approval',
                  binding=binding, prepared_metadata=dict(path=str(metadata_file), sha256=sha(metadata_file)),
                  config=dict(path=str(config_file), sha256=sha(config_file)),
                  neck_inputs=dict(path=str(neck_file), sha256=sha(neck_file)),
                  neck_interface_check=dict(path=str(out/'neck-interface-check.json'), sha256=sha(out/'neck-interface-check.json')),
                  material_api=dict(path=str(root/APPEARANCE/'install_material.py'), sha256=sha(root/APPEARANCE/'install_material.py')),
                  appearance_implementation=api_provenance(root),
                  requested_maps=['SkinBaseColor', 'UnderwearBaseColor', 'UnderwearCoverage', 'ClavicleInk', 'ClavicleShade'],
                  resolution=SIZE, optional_brief_world_correction=False,
                  original_arrays_metadata_unchanged=True, capacity=budget)
    write(out/'prepare-report.json', report)
    return report


def validate_root_gray(root, gate_path, binding):
    """A root-authored decision is an input; this helper cannot create one."""
    root = Path(root).resolve(); gate_path = Path(gate_path).resolve()
    if root/'.mia-cache/body-h' not in gate_path.parents:
        raise ValueError('Root gray decision must be in this canonical H cache')
    gate = read(gate_path)
    if gate.get('decision') != 'APPROVED_FOR_APPEARANCE_PREFLIGHT':
        raise ValueError('Explicit root gray decision missing or not approved')
    if gate.get('geometry_sha256') != binding['geometry']['sha256'] or gate.get('surface_sha256') != binding['surface']['sha256']:
        raise ValueError('Root decision refers to a different H surface/geometry')
    capture = gate.get('gray_capture', {})
    if not capture.get('path') or sha(capture['path']) != capture.get('sha256'):
        raise ValueError('Gray capture is absent or stale')
    rows = read(capture['path'])['frames']
    required = {'front', 'profile', 'back', 'oblique', 'high', 'low'}
    actual = [row for row in rows if row.get('state') == 'H']
    if not required.issubset({row.get('name') for row in actual}):
        raise ValueError('Actual H gray six-view coverage missing')
    for row in actual:
        if sha(row['path']) != row['sha256']:
            raise ValueError('Gray image changed after root decision')
        payload = row.get('payload', {})
        if payload.get('sha256') != binding['geometry']['sha256']:
            raise ValueError('Gray frame was made from another H geometry')
    return dict(path=str(gate_path), sha256=sha(gate_path), declared_scope=gate.get('scope'))


def bake(root=CANONICAL, prepared=None, output=None, gray_decision=None, selection=None):
    root = Path(root).resolve()
    if gray_decision is None:
        raise ValueError('bake requires a separate --root-gray-decision; prepare never approves it')
    prepared = output_path(root, prepared or root/CACHE/'prepared-H')
    out = output_path(root, output or root/CACHE/'maps-H')
    baker = api(root)
    report = read(prepared/'prepare-report.json')
    _, current_binding = target_binding(root, selection)
    if current_binding != report['binding']:
        raise ValueError('Prepared H target binding is stale')
    if api_provenance(root) != report['appearance_implementation']:
        raise ValueError('Appearance implementation/source paths changed after preparation')
    decision = validate_root_gray(root, gray_decision, current_binding)
    for role in ('prepared_metadata', 'config', 'neck_inputs'):
        item = report[role]
        if sha(item['path']) != item['sha256']:
            raise ValueError('Prepared artifact changed: '+role)
    if out.exists() and any(out.iterdir()):
        raise ValueError('Never overwrite or silently reuse an H bake')
    budget = capacity(root, 100)
    from surface_api import load_surface, rasterize_world, pad_images
    surface = load_surface(current_binding['surface']['path'], report['prepared_metadata']['path'])
    config, neck_inputs = read(report['config']['path']), read(report['neck_inputs']['path'])
    # Orchestrate the original existing bake functions so a separate metadata
    # overlay can reference the SAME NPZ. No monkeypatch or array/native copy.
    start = time.time(); out.mkdir(parents=True, exist_ok=True)
    curves, recipe, paths = baker.make_recipe(config)
    author = baker.TargetAuthor(surface, config)
    charts, brief_proof = author.fit_brief_leg_source(paths)
    config['brief_leg_source_charts'] = charts
    config['brief_leg_surface_pairs'] = brief_proof['polar_pairs_DIAGNOSTIC_ONLY']
    config['brief_source_fit_proof'] = brief_proof
    config['brief_leg_surface_target_sha256'] = surface['input_sha256']
    curves, recipe, paths = baker.make_recipe(config)
    write(out/'brief-source-fit.json', brief_proof)
    write(out/'authoring-config.json', config)
    boundaries, clavicles = author.seat_boundaries(curves), author.clavicle(paths)
    write(out/'seated-boundaries.json', dict(surface_guards=surface['guards'], boundaries=boundaries, clavicles=clavicles))
    bad = {name: path['failures'] for name, path in boundaries.items() if not path['geometric_samples_complete']}
    if bad or not all(path['geometric_samples_complete'] for path in clavicles):
        raise ValueError('Actual H surface seating incomplete: '+json.dumps(bad))
    straps = author.strap_paths(curves)
    write(out/'seated-straps.json', dict(straps=straps, geometry_guards=surface['guards']))
    write(out/'pattern-recipe.json', recipe)
    print('H_ACTUAL_SEATING_COMPLETE', flush=True)
    raster = rasterize_world(surface, size=SIZE, filter_support=True)
    from neck_pigment import prepare as neck_prepare, sample_alpha
    alpha, neck_report = neck_prepare(surface, neck_inputs)
    raster['neck_alpha'] = sample_alpha(raster, surface, alpha)
    write(out/'neck-prelight-field.json', neck_report)
    images, stats = baker.paint_fields(raster, config, curves, clavicles, straps)
    padded, padding = pad_images(images, raster['valid'], pixels=4)
    files = []
    for name, pixels in padded.items():
        path = out/(name+'.png')
        Image.fromarray(np.rint(np.clip(pixels, 0, 1)*255).astype(np.uint8)).save(path)
        files.append(dict(path=str(path), sha256=sha(path), size=[SIZE, SIZE],
                          color_space='sRGB' if name.endswith('BaseColor') else 'Non-Color',
                          active_use='body-only pigment' if name.endswith('BaseColor') else 'body-only material control'))
    Image.fromarray(raster['valid'].astype(np.uint8)*255).save(out/'UV_ValidMask_DIAGNOSTIC.png')
    _, final_binding = target_binding(root, selection)
    if final_binding != current_binding:
        raise ValueError('Target surface/UV/metadata changed during bake')
    if api_provenance(root) != report['appearance_implementation']:
        raise ValueError('Appearance implementation/source paths changed during bake')
    validate_root_gray(root, gray_decision, current_binding)
    result = dict(status='CPU H map bake complete; actual material/native/source review still required',
                  surface_input=surface['input_path'], surface_input_sha256=surface['input_sha256'],
                  surface_metadata_sha256=report['prepared_metadata']['sha256'],
                  original_surface_metadata=current_binding['original_metadata'],
                  prepared_surface_metadata=report['prepared_metadata'], surface_guards=surface['guards'],
                  UV_numeric_quality=surface['uv_numeric_stats'], raster=raster['report'], field_stats=stats,
                  files=files, island_padding_pixels=4, padded_texels=int(padding.sum()-raster['valid'].sum()),
                  geometry_unchanged=True, GPU_used=False, elapsed_seconds=time.time()-start,
                  root_gray_decision=decision, capacity=budget,
                  reuse='Existing Review12 recipe/Cartesian brief field, target author, fair paths, raster/bilinear support, neck pigment, paint and padding functions.',
                  optional_brief_world_correction=False,
                  limits=['Actual five-map material routes/toggles and light probes remain unverified.',
                          'Source-fitted supported body shape is the same in SkinOnly/Underwear; no cloth compression simulation.',
                          'Clavicle graphic is newly seated at prior source-supported Z1.37778; four-view review still required.'])
    write(out/'bake-report.json', result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['prepare', 'bake'])
    parser.add_argument('--root', type=Path, default=CANONICAL)
    parser.add_argument('--prepared', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--root-gray-decision', type=Path)
    parser.add_argument('--selection', type=Path,
                        help='Root-authored selection; default canonical .mia-cache/body-h/selected-candidate.json when present')
    args = parser.parse_args()
    if args.command == 'prepare':
        result = prepare(args.root, args.output, args.selection)
    else:
        result = bake(args.root, args.prepared, args.output, args.root_gray_decision, args.selection)
    print(json.dumps(dict(status=result['status'], resolution=result.get('resolution', SIZE)), indent=2), flush=True)


if __name__ == '__main__': main()
