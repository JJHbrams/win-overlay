"""Actual Body14/candidate paired renders using the existing frozen source SRT."""
import argparse, ast, hashlib, json, math, shutil, sys
from pathlib import Path
import bpy
from mathutils import Vector, Matrix

ap = argparse.ArgumentParser()
for key in ('baseline', 'candidate', 'body-package', 'output-dir'):
    ap.add_argument('--'+key, required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--')+1:])
OUT = Path(a.output_dir).resolve()
assert not OUT.exists() or not any(OUT.iterdir()), 'Fresh output required'
sources = {r: Path(getattr(a,r)).resolve() for r in ('baseline','candidate')}
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
artifact = lambda p: {'path':str(Path(p).resolve()), 'sha256':sha(p)}
source_art = {r:artifact(p) for r,p in sources.items()}
pkg = Path(a.body_package).resolve()
package = json.loads(pkg.read_text(encoding='utf-8-sig'))
assert set(package['required_views']) == {'front','profile','back','oblique'}
assert all(r['baseline_registration']==r['candidate_registration'] for r in package['views'])
rig = Path(__file__).resolve().parents[1]/'render_integrated_review.py'
names = {'render_visible','keys','hair_hide','material','aim','setup','camera_and_lights','record','routes','production_uv'}
nodes = [n for n in ast.parse(rig.read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef) and n.name in names]
assert {n.name for n in nodes} == names
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(rig),'exec'))
OUT.mkdir(parents=True, exist_ok=True)
deps=OUT/'dependencies';deps.mkdir()
for p in (Path(__file__),rig,pkg):shutil.copyfile(p,deps/p.name)
records={}
for role,path in sources.items():
    scene,lamps=setup(path,'body')
    folder=OUT/role/'body';folder.mkdir(parents=True)
    for row in package['views']:
        camera_and_lights(scene,lamps,row['baseline_camera'],'body')
        p=folder/(row['id']+'.png');scene.render.filepath=str(p)
        bpy.ops.render.render(write_still=True)
        records[role+'/body/'+row['id']]={'render':artifact(p),'camera':record(scene,lamps)}
assert all(sha(p)==source_art[r]['sha256'] for r,p in sources.items())
(OUT/'render-records.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
(OUT/'render-manifest.json').write_text(json.dumps({'baseline_native':source_art['baseline'],'candidate_native':source_art['candidate'],
    'input_packages':{'body':artifact(pkg)},'renderer':artifact(__file__),'rig':artifact(rig),'native_saved':False,
    'art_status':'NOT_EVALUATED; source SRT retained, no per-candidate fit'},indent=2),encoding='utf-8')
print('BODY_COMPARISON_DONE',len(records),flush=True)
