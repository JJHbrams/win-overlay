"""Capture the four immutable R3b baseline views for the H review, without saving."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

sys.dont_write_bytecode = True
import bpy

ROOT = Path(__file__).resolve().parents[3]
COMPONENT = ROOT / 'asset/mia/blender/mia-fit-v003/body/surface-review12'
OUT = ROOT / '.mia-cache/body-h/baseline4'
SOURCE = ROOT / 'asset/mia/blender/mia-refinement-v002/integrated/Mia_v0.0.2_Review_R3b.blend'
EXPECTED = '4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    guard = load('h_storage', ROOT / 'asset/mia/blender/mia-fit-v003/integration/workspace-storage-20261103/storage_guard.py')
    budget = guard.inspect(100 * 1024 ** 2)
    assert not budget['violations'], budget
    assert Path(bpy.data.filepath).resolve() == SOURCE.resolve()
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
    assert not OUT.exists(), 'Never overwrite a captured baseline batch'
    OUT.mkdir(parents=True)
    fixture = load('h_fixture', COMPONENT / 'review_fixture.py')
    scene = bpy.context.scene
    fixture.setup(scene)
    fixture.hair_visibility(scene, False)
    geometry = fixture.original_body_geometry(scene)
    pose_hash = fixture.digest(fixture.pose(scene))
    capture = {
        'scope': 'Actual immutable saved R3b, hair hidden, common H fixture; no native save or shape change.',
        'native': {'path': str(SOURCE), 'sha256': EXPECTED},
        'geometry': geometry,
        'shader': 'Original saved R3b routes, not the new body material.',
        'frames': [],
    }
    for label, yaw in [('front', 0), ('profile', 90), ('back', 180), ('oblique', 30)]:
        fixture.aim(scene, yaw)
        assert fixture.digest(fixture.pose(scene)) == pose_hash
        frame = OUT / (label + '.png')
        record = {'name': label, 'yaw': yaw, 'hair': False, 'path': str(frame), 'fixture': fixture.record(scene)}
        scene.render.filepath = str(frame)
        bpy.ops.render.render(write_still=True, scene=scene.name)
        record['sha256'] = fixture.sha(frame)
        capture['frames'].append(record)
        (OUT / 'capture.json').write_text(json.dumps(capture, indent=2) + '\n', encoding='utf8')
        print('H_BASELINE_ACTUAL', label, flush=True)
    assert fixture.sha(SOURCE) == EXPECTED
    assert len(capture['frames']) == 4
    print('H_BASELINE_COMPLETE_GPU_RELEASE', flush=True)


if __name__ == '__main__':
    main()
