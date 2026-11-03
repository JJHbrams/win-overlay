"""Actual E/H gray pairs on saved R3b. No scene/native save or model promotion."""
from pathlib import Path
import argparse
import importlib.util
import json
import sys

sys.dont_write_bytecode = True
import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
COMPONENT = ROOT/'asset/mia/blender/mia-fit-v003/body/surface-review12'
sys.path.insert(0, str(COMPONENT))
import install_review
import review_fixture as fixture


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--assembly', type=Path, default=ROOT/'.mia-cache/body-h/shape/assembly')
    parser.add_argument('--output', type=Path, default=ROOT/'.mia-cache/body-h/gray')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    spec = importlib.util.spec_from_file_location('h_gray_guard', ROOT/'asset/mia/blender/mia-fit-v003/integration/workspace-storage-20261103/storage_guard.py')
    guard = importlib.util.module_from_spec(spec); spec.loader.exec_module(guard)
    budget = guard.inspect(100*1024**2)
    assert not budget['violations'], budget
    source = Path(bpy.data.filepath)
    native_sha = fixture.sha(source)
    assert native_sha == '4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'
    out = args.output.resolve()
    assert (ROOT/'.mia-cache/body-h').resolve() in out.parents
    assert not out.exists(), 'Do not overwrite an actual candidate review'
    out.mkdir(parents=True)
    assembly = args.assembly.resolve()
    assert (ROOT/'.mia-cache/body-h/shape/assembly').resolve() == assembly or (ROOT/'.mia-cache/body-h/shape/assembly').resolve() in assembly.parents
    payloads = dict(E=COMPONENT/'joined-expanded-E.npz', H=assembly/'geometry.npz')
    assembly_meta = json.loads((assembly/'assembly.json').read_text())
    atlases = dict(E=COMPONENT/'atlas-E.npz', H=Path(assembly_meta.get('atlas_path',assembly/'atlas/atlas.npz')))
    objects, proofs = {}, {}
    for state in ['E', 'H']:
        ob, proof = install_review.apply(
            geometry_path=payloads[state], atlas_path=atlases[state],
            proof_path=out/(state+'-installed.json'),
            packing_path=out/(state+'-normal-packing.json'))
        ob.name = 'MIA_Review12_'+state+'_GrayComponent'
        ob.hide_render = True
        objects[state], proofs[state] = ob, proof
    scene = bpy.context.scene
    fixture.setup(scene); fixture.hair_visibility(scene, False)
    pose = fixture.digest(fixture.pose(scene))
    fit = json.loads((ROOT/'.mia-cache/body-h/shape/roof-fit.json').read_text())['params']
    jobs = [
        ('front', 0, 0, fixture.FULL_TARGET, fixture.FULL_SCALE, fixture.FULL_RES),
        ('profile', 90, 0, fixture.FULL_TARGET, fixture.FULL_SCALE, fixture.FULL_RES),
        ('back', 180, 0, fixture.FULL_TARGET, fixture.FULL_SCALE, fixture.FULL_RES),
        ('oblique', 30, 0, fixture.FULL_TARGET, fixture.FULL_SCALE, fixture.FULL_RES),
        ('high', 40, 25, (0, -.015, 1.335), .65, (800, 800)),
        ('low', -40, -25, (0, -.015, 1.335), .65, (800, 800)),
        ('front_fit', fit[5], fit[6], fixture.FULL_TARGET, fixture.FULL_SCALE, fixture.FULL_RES),
        ('back_fit', fit[7], fit[8], fixture.FULL_TARGET, fixture.FULL_SCALE, fixture.FULL_RES),
    ]
    records = []
    for label, yaw, pitch, target, scale, resolution in jobs:
        fixture.aim(scene, yaw, pitch, target, scale, resolution)
        for state in ['E', 'H']:
            for key, ob in objects.items(): ob.hide_render = key != state
            assert fixture.digest(fixture.pose(scene)) == pose
            path = out/(state+'-'+label+'.png')
            row = dict(name=label, state=state, yaw=yaw, pitch=pitch,
                       hair=False, path=str(path), native=dict(path=str(source), sha256=native_sha),
                       payload=dict(path=str(payloads[state]), sha256=fixture.sha(payloads[state])),
                       fixture=fixture.record(scene),
                       shader='BODY gray Principled .23/roughness .85; original saved head/actors',
                       saved_review_native=False)
            scene.render.filepath = str(path)
            bpy.ops.render.render(write_still=True, scene=scene.name)
            row['sha256'] = fixture.sha(path); records.append(row)
            (out/'capture.json').write_text(json.dumps(dict(scope='Actual E/H private unsaved gray comparison on immutable R3b; no ART approval.', frames=records), indent=2)+'\n', encoding='utf8')
            print('H_GRAY_ACTUAL', state, label, flush=True)
    assert len(records) == 16 and fixture.sha(source) == native_sha
    print('H_GRAY_COMPLETE_GPU_RELEASE', flush=True)


if __name__ == '__main__':
    main()
