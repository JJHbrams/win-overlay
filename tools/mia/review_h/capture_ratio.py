"""Actual hair-on D baseline for whole-character proportion observations only."""
from pathlib import Path
import importlib.util
import json
import sys
import bpy

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import recorded_atlas
P = ROOT/'asset/mia/blender/mia-fit-v003/body/surface-review12'
sys.path.insert(0, str(P))
import install_review
import review_fixture as fixture

guard_path = ROOT/'asset/mia/blender/mia-fit-v003/integration/workspace-storage-20261103/storage_guard.py'
spec = importlib.util.spec_from_file_location('ratio_capacity', guard_path)
guard = importlib.util.module_from_spec(spec); spec.loader.exec_module(guard)
capacity = guard.inspect(100*1024**2); assert not capacity['violations'], capacity
source = Path(bpy.data.filepath)
assert fixture.sha(source) == '4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'
out = ROOT/'.mia-cache/body-h/ratio-baseline'
assert not out.exists(); out.mkdir(parents=True)
base = ROOT/'.mia-cache/body-h/shape/assembly/live-D'
meta = json.loads((base/'assembly.json').read_text())
ob, proof = install_review.apply(geometry_path=base/'geometry.npz', atlas_path=recorded_atlas(base, meta),
    proof_path=out/'installed.json', packing_path=out/'normal-packing.json')
scene = bpy.context.scene
fixture.setup(scene); fixture.hair_visibility(scene, True)
pose = fixture.digest(fixture.pose(scene)); records = []
for label, yaw in [('front', 0), ('profile', 90), ('back', 180), ('oblique', 30)]:
    fixture.aim(scene, yaw, 0, fixture.FULL_TARGET, fixture.FULL_SCALE, fixture.FULL_RES)
    assert fixture.digest(fixture.pose(scene)) == pose
    path = out/(label+'.png'); scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True, scene=scene.name)
    records.append(dict(name=label, yaw=yaw, pitch=0, hair=True, path=str(path), sha256=fixture.sha(path),
        fixture=fixture.record(scene), geometry_sha256=fixture.sha(base/'geometry.npz'),
        source_native=dict(path=str(source), sha256=fixture.sha(source)), saved_review_native=False))
    (out/'capture.json').write_text(json.dumps(dict(scope='Unchanged saved R3b hair/head on D static body: proportion baseline only, no new hair/ART/native acceptance', frames=records), indent=2)+'\n', encoding='utf8')
    print('ACTUAL_RATIO_BASELINE', label, flush=True)
