"""Read-only four-view face replay using the frozen integrated review rig.

Writes the same manifest format as render_integrated_review.py, so the existing
composer applies the original uniform SRT registrations without a new fit.
"""
import argparse, ast, hashlib, json, math, shutil, sys
from pathlib import Path
import bpy
from mathutils import Vector, Matrix

ap = argparse.ArgumentParser(description=__doc__)
for key in ['baseline', 'candidate', 'face-package', 'output-dir']:
    ap.add_argument('--' + key, required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
OUT = Path(a.output_dir).resolve()
if OUT.exists() and any(OUT.iterdir()):
    raise RuntimeError('Fresh output directory required: ' + str(OUT))
sources = {role: Path(getattr(a, role)).resolve() for role in ['baseline', 'candidate']}
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
artifact = lambda p: {'path': str(Path(p).resolve()), 'sha256': sha(p)}
source_art = {role: artifact(path) for role, path in sources.items()}
package_path = Path(a.face_package).resolve()
package = json.loads(package_path.read_text(encoding='utf-8-sig'))
assert set(package['required_views']) == {'front', 'profile', 'left_oblique', 'right_oblique'}
for row in package['views']:
    assert row['baseline_registration'] == row['candidate_registration'], 'Independent refit is forbidden'
rig_path = Path(__file__).resolve().parents[1] / 'render_integrated_review.py'
names = {'render_visible', 'keys', 'hair_hide', 'material', 'aim', 'setup',
         'camera_and_lights', 'record', 'routes', 'production_uv'}
tree = ast.parse(rig_path.read_text(encoding='utf-8'))
nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
assert {n.name for n in nodes} == names
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(rig_path), 'exec'))
OUT.mkdir(parents=True)
deps = OUT / 'dependencies'
deps.mkdir()
for p in [Path(__file__), rig_path, package_path]:
    shutil.copyfile(p, deps / p.name)
records, material_records = {}, {}
for role, path in sources.items():
    s, lamps = setup(path, 'face')
    material_records[role + '/face'] = {'production_before_review_override':
        json.loads(s['mia_review_production_routes']), 'actual_review_routes': routes()}
    folder = OUT / role / 'face'
    folder.mkdir(parents=True)
    for row in package['views']:
        camera_and_lights(s, lamps, row['baseline_camera'], 'face')
        p = folder / (row['id'] + '.png')
        s.render.filepath = str(p)
        bpy.ops.render.render(write_still=True)
        records[role + '/face/' + row['id']] = {'render': artifact(p),
            'camera': record(s, lamps), 'visible_mesh_owners': [o.name for o in render_visible()]}
assert all(sha(p) == source_art[role]['sha256'] for role, p in sources.items())
(OUT / 'render-records.json').write_text(json.dumps(records, indent=2))
(OUT / 'material-routes.json').write_text(json.dumps(material_records, indent=2))
(OUT / 'render-manifest.json').write_text(json.dumps({
    'baseline_native': source_art['baseline'], 'candidate_native': source_art['candidate'],
    'input_packages': {'face': artifact(package_path)}, 'rig_source': artifact(rig_path),
    'renderer': artifact(__file__), 'source_natives_unchanged': True,
    'art_status': 'NOT_EVALUATED', 'limitations': 'Four source-matched views; continuous matte sweep and actual expressions are separate gates.'
}, indent=2))
print('FACE_COMPARISON_DONE', len(records), flush=True)
