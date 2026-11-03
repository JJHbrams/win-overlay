"""Replay only existing R3b eye/crease components in a private Blender process.

Default CPU mode records exact composition, existing-key preservation and actual
evaluated aperture coordinates. --render is a separately root-granted GPU batch
of the three existing compositions under the four existing source cameras.
No new eye model, source-image fitting, live Blender access or native save.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import importlib.util
import json
import sys

sys.dont_write_bytecode = True
import bpy
import numpy as np
from mathutils import Matrix

SHA = '4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'
OWNERS = ('MIA_V27_SharedHeadBody', 'MIA_V27_Foundation_Face',
          'V28G_InnerLid_-1', 'V28G_InnerLid_1',
          'V28G_Sclera_-1', 'V28G_Sclera_1', 'V28G_Iris_-1', 'V28G_Iris_1',
          'V30_UpperLashes_-1', 'V30_UpperLashes_1',
          'V30_LowerLashes_-1', 'V30_LowerLashes_1',
          'V31_SourceBrow_-1', 'V31_SourceBrow_1', 'MIA_V17_PIXAL_DetailedHair')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ah(array):
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def co(collection):
    result = np.empty(len(collection)*3, np.float32)
    collection.foreach_get('co', result)
    return result.reshape(-1, 3)


def module(path):
    spec = importlib.util.spec_from_file_location('eye_roi_'+path.stem, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def authored():
    rows = {}
    for name in OWNERS:
        ob = bpy.data.objects[name]
        uv = {}
        for layer in ob.data.uv_layers:
            array = np.empty(len(layer.data)*2, np.float32)
            layer.data.foreach_get('uv', array)
            uv[layer.name] = ah(array)
        rows[name] = dict(raw=ah(co(ob.data.vertices)), uv=uv,
                          keys={key.name: ah(co(key.data))
                                for key in ob.data.shape_keys.key_blocks}
                          if ob.data.shape_keys else {})
    return rows


def assert_originals(before):
    after = authored()
    for name, row in before.items():
        assert after[name]['raw'] == row['raw'], (name, 'raw coordinates')
        assert after[name]['uv'] == row['uv'], (name, 'UV')
        for key, digest in row['keys'].items():
            assert after[name]['keys'][key] == digest, (name, key)
        new = set(after[name]['keys'])-set(row['keys'])
        assert not new or (name in ('MIA_V27_SharedHeadBody','V28G_InnerLid_1','V30_LowerLashes_1')
                           and new == {'Mia.v003.NeutralLowerLidBalance.1'}), (name, new)


def reset(ctrl, state, frame):
    for name in ctrl.keys():
        if (name.startswith('Manual') or (name.startswith('P') and name[:3][1:].isdigit())
                or name in ('HeadPitch','HeadYaw','HeadRoll','GazeX','GazeY')):
            ctrl[name] = 0.
    ctrl['Strength'] = 1.
    ctrl['HeadPoseStrength'] = ctrl['GazeStrength'] = 0.
    for name, value in state.items():
        assert name in ctrl, name
        ctrl[name] = value
    ctrl.update_tag()
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()


def evaluated(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    mesh = ev.to_mesh(preserve_all_data_layers=True, depsgraph=dg)
    q = co(mesh.vertices)
    matrix = np.asarray(ev.matrix_world)
    world = (q @ matrix[:3,:3].T + matrix[:3,3]).astype(np.float32)
    ev.to_mesh_clear()
    return world


def aperture(rim, camera):
    skin = bpy.data.objects['MIA_V27_SharedHeadBody']
    q = evaluated(skin)
    assert len(q) == 80771, 'This diagnostic requires unchanged saved R3b evaluated topology'
    right = np.asarray(camera.matrix_world.to_3x3().col[0])
    up = np.asarray(camera.matrix_world.to_3x3().col[1])
    rows = []
    for side in (-1, 1):
        curves = {}
        for kind in ('upper','lower'):
            ids = rim['evaluated_openings'][str(side)][kind+'_evaluated_indices']
            curve = q[ids]
            xy = np.column_stack((curve@right, curve@up))
            a, b = xy[0], xy[-1]
            width = float(np.linalg.norm(b-a))
            axis = (b-a)/width
            normal = np.array([-axis[1],axis[0]]) * (-1 if side < 0 else 1)
            t = (xy-a)@axis/width
            h = (xy-a)@normal
            curves[kind] = dict(world_m=curve.tolist(), projected_width_mm=width*1000,
                                t=t.tolist(), height_over_own_width=(h/width).tolist(),
                                medial_to_lateral_depth_delta_mm=float((curve[-1,1]-curve[0,1])*1000))
        rows.append(dict(side=side, curves=curves))
    return dict(evaluated_skin_world_sha256=ah(q), eyes=rows,
                measurement='Canthus-local 2D coordinates only; never used as a display warp or symmetry target')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--output-name', required=True)
    ap.add_argument('--render', action='store_true')
    args = ap.parse_args(sys.argv[sys.argv.index('--')+1:])
    root = args.root.resolve()
    assert Path(args.output_name).name == args.output_name and '..' not in args.output_name
    guard_file = root/'asset/mia/blender/mia-fit-v003/integration/workspace-storage-20261103/storage_guard.py'
    budget = module(guard_file).inspect((100 if args.render else 8)*1024**2)
    assert not budget['violations'], budget
    out = root/'.mia-cache/eye-roi'/args.output_name
    assert not out.exists(), 'Do not overwrite actual evidence'
    out.mkdir(parents=True)
    base = root/'asset/mia/blender'
    fit = base/'mia-fit-v003/eyes'
    native = base/'mia-refinement-v002/integrated/Mia_v0.0.2_Review_R3b.blend'
    assert sha(native) == SHA
    renderer = base/'mia-visible-art-v30/render_native_review.py'
    text = renderer.read_text(encoding='utf8')
    old = "out=P/'reviews'/a.tag/a.preset"
    assert text.count(old) == 1
    # Only relocate the reused renderer's output; no fixture/geometry code change.
    text = text.replace(old, 'out=Path('+repr(str(out))+')')
    sys.argv = [str(renderer),'--','--native',str(native),'--sha256',SHA,
                '--tag','eye-roi-existing','--preset','source','--only','__setup_only_no_frames__']
    env = dict(__file__=str(renderer), __name__='eye_roi_existing_renderer')
    exec(compile(text, str(renderer), 'exec'), env)
    env['a'].only = ''
    ctrl = bpy.data.objects['Mia_FacialControls_v002']
    skin = bpy.data.objects['MIA_V27_SharedHeadBody']
    assert len(skin.data.vertices) == 4647 and len(skin.data.shape_keys.key_blocks) == 47
    reset(ctrl, {}, 1)
    original = authored()
    rim = json.loads((base/'mia-face-finish-v29/parts/medial-C2/proof/medial-baseline-inspection.json').read_text())
    states = [('neutral', {}), ('half_blink', {'Manual_EYE_Close': .5}),
              ('full_blink', {'Manual_EYE_Close': 1.}), ('smile', {'P08_small_amused_smile': 1.}),
              ('surprise', {'P12_surprised': 1.}), ('frown', {'P05_downward_irritated': 1.})]
    # Read the established panel08 property rather than guessing its spelling.
    smile_name = next(n for n in ctrl.keys() if n.startswith('P08_'))
    states[3] = ('smile', {smile_name: 1.})
    records = []
    apply_list = []
    for index, variant in enumerate(('saved_R3b','lower_only','lower_plus_crease_C')):
        reset(ctrl, {}, 1)
        front = next(row['candidate_camera'] for row in env['pkg']['views'] if row['id'] == 'front')
        env['cam'].matrix_world = Matrix(front['matrix'])
        env['cam'].data.ortho_scale = front['ortho_scale']
        env['cam'].data.shift_x, env['cam'].data.shift_y = front['lens_shift']
        bpy.context.view_layer.update()
        if index == 1:
            result = module(fit/'apply_lower_lid.py').apply()
            apply_list.append(dict(api='apply_lower_lid.py:apply', sha256=sha(fit/'apply_lower_lid.py'), result=result))
        if index == 2:
            result = module(fit/'apply_aligned_crease.py').apply(fit/'upper-crease-visible-C.json')
            apply_list.append(dict(api='apply_aligned_crease.py:apply', sha256=sha(fit/'apply_aligned_crease.py'),
                                   config_sha256=sha(fit/'upper-crease-visible-C.json'), result=result))
        # Critical: the reused render() restores this cache before every frame.
        env['original'] = {n:list(bpy.data.objects[n].data.materials) for n in env['original']}
        slots = {n:[m.name for m in materials] for n,materials in env['original'].items()}
        samples = []
        for state_index, (state, controls) in enumerate(states):
            reset(ctrl, controls, state_index+10)
            samples.append(dict(state=state, controls=controls,
                                active_keys={k.name:float(k.value) for k in skin.data.shape_keys.key_blocks if k.value},
                                aperture=aperture(rim, env['cam'])))
        reset(ctrl, {}, 1)
        if args.render:
            for view in env['pkg']['views']:
                camera = copy.deepcopy(view['candidate_camera'])
                camera['resolution'] = [768,768]
                assert all(bpy.data.objects[n].data.materials[i].name == material
                           for n,materials in slots.items() for i,material in enumerate(materials))
                env['render'](variant+'-'+view['id']+'-hairOFF', camera, True, False)
                assert all(bpy.data.objects[n].data.materials[i].name == material
                           for n,materials in slots.items() for i,material in enumerate(materials))
        assert_originals(original)
        records.append(dict(composition=variant, apply_list=copy.deepcopy(apply_list),
                            material_slots=slots, measurement_camera=copy.deepcopy(front),
                            states=samples, original_authored_arrays_exact=True))
        (out/'component-evidence.json').write_text(json.dumps(dict(
            scope='Existing eye-only recipe comparison, not a new correction or ART acceptance',
            source_native=str(native), native_sha256=SHA, renderer_sha256=sha(renderer),
            wrapper_sha256=sha(Path(__file__)),
            renderer_runtime_change='Only output-directory relocation into ignored canonical eye cache',
            GPU_used=args.render, variants=records,
            source_pose_limit='Existing source camera hypotheses retained; expression poses differ and remain explicitly uncertain.',
            source_display='No source image warp performed. Canthus-local coordinates are measurement only.',
            new_geometry_guess=False, native_saved=False, ART=False), ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    reset(ctrl, {}, 1)
    assert sha(native) == SHA
    print(json.dumps(dict(scope='CPU composition only' if not args.render else 'Actual existing-component source4 capture',
                          output=str(out), variants=len(records), GPU_used=args.render,
                          original_authored_arrays_exact=True, native_saved=False, ART=False)))


if __name__ == '__main__':
    main()
