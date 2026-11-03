"""Eight actual renders of the existing provisional brow display on R3b.

This is genuine 47-key expression evidence, not the static D head. It does not
prove physical fringe gaps, new brow shape, or source pose/whole-character ART.
"""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import runpy
import sys
import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
native = ROOT/'asset/mia/blender/mia-refinement-v002/integrated/Mia_v0.0.2_Review_R3b.blend'
source_sha = '4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
guard_path = ROOT/'asset/mia/blender/mia-fit-v003/integration/workspace-storage-20261103/storage_guard.py'
spec = importlib.util.spec_from_file_location('brow_expr_capacity', guard_path)
guard = importlib.util.module_from_spec(spec); spec.loader.exec_module(guard)
capacity = guard.inspect(80*1024**2); assert not capacity['violations'], capacity
tag = globals().get('MIA_BROW_DIAGNOSTIC_TAG', 'brow-expression4')
assert tag in ['brow-expression4', 'brow-smile1']
out = ROOT/'.mia-cache/face-live'/tag
assert not out.exists(); out.mkdir(parents=True)
old = ROOT/'asset/mia/blender/mia-visible-art-v30/render_native_review.py'
sys.argv = [str(old), '--', '--native', str(native), '--sha256', source_sha,
    '--tag', 'brow-expression-cache-setup', '--preset', 'source', '--only', '__setup_only_no_frames__']
env = runpy.run_path(str(old), run_name='brow_expression_setup')
render = env['render']; g = render.__globals__; g['out'] = out; env['a'].only = ''
ctrl = bpy.data.objects['Mia_FacialControls_v002']
camera = copy.deepcopy(env['spec']); camera['resolution'] = [512, 512]


def reset():
    for key in ctrl.keys():
        if (key.startswith('P') and key[:3][1:].isdigit()) or key.startswith('Manual') or key in ['HeadPitch', 'HeadYaw', 'HeadRoll', 'GazeX', 'GazeY']:
            ctrl[key] = 0.
    ctrl['Strength'] = 1.; ctrl['HeadPoseStrength'] = ctrl['GazeStrength'] = 0.
    ctrl.update_tag(); bpy.context.scene.frame_set(1); bpy.context.view_layer.update()


def actual_geometry(names):
    dg = bpy.context.evaluated_depsgraph_get(); result = {}
    for name in names:
        ob = bpy.data.objects[name]; evaluated = ob.evaluated_get(dg)
        me = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=dg)
        v = np.array([evaluated.matrix_world@p.co for p in me.vertices], np.float32)
        result[name] = dict(vertices=len(v), world_sha256=hashlib.sha256(v.tobytes()).hexdigest(),
            bounds=[v.min(0).tolist(), v.max(0).tolist()] if len(v) else None)
        evaluated.to_mesh_clear()
    return result


reset()
path = ROOT/'asset/mia/blender/mia-fit-v003/brow-visibility-analysis/candidate/partial_brow_display.py'
spec = importlib.util.spec_from_file_location('existing_partial_brow', path)
brow = importlib.util.module_from_spec(spec); spec.loader.exec_module(brow)
installed = brow.apply_to_current_scene(.60)
names = ['MIA_V27_SharedHeadBody', 'V31_SourceBrow_-1', 'V31_SourceBrow_1']
records = []
states = globals().get('MIA_BROW_DIAGNOSTIC_STATES', [('neutral', 'P01_neutral_observe'), ('irritated', 'P05_downward_irritated'),
          ('surprised', 'P12_surprised'), ('blink', 'Manual_EYE_Close')])
for i, (label, key) in enumerate(states):
    reset(); assert key in ctrl; ctrl[key] = 1.; ctrl.update_tag()
    bpy.context.scene.frame_set(20+i); bpy.context.view_layer.update()
    state_geometry = actual_geometry(names)
    keys = {name: {k.name: k.value for k in bpy.data.objects[name].data.shape_keys.key_blocks if k.value}
        for name in ['MIA_V27_Foundation_Face', 'MIA_V27_SharedHeadBody']}
    assert keys['MIA_V27_SharedHeadBody'] or label == 'neutral', 'Expression must affect the genuine visible head'
    for strength in [0., .60]:
        brow.set_strength(strength)
        assert actual_geometry(names) == state_geometry, 'Display must not alter source brows/head'
        active = [o.name for o in bpy.context.scene.objects if o.type == 'LIGHT' and not o.hide_render]
        assert set(active) == {o.name for o in env['lamps']}
        name = label+('-original' if not strength else '-display06')
        render(name, camera, False, False)
        records.append(dict(state=label, control=key, display_strength=strength,
            actual_visible_head_keys=keys, actual_geometry=state_geometry,
            overlay_geometry=actual_geometry(installed['overlay_objects']),
            render=g['records'][-1]))
        (out/'expression-evidence.json').write_text(json.dumps(dict(scope='Provisional graphic brow display readability, head/gaze held neutral; source pose likeness and physical fringe remain open',
            native_sha256=source_sha, installed=installed, states=records, capacity=capacity, native_saved=False,
            helper_sha256=sha(ROOT/'tools/mia/review_h/capture_brow_expressions.py'), diagnostic_tag=tag), indent=2)+'\n', encoding='utf8')
        print('ACTUAL_BROW_EXPRESSION', name, flush=True)
reset(); assert sha(native) == source_sha
print('BROW_EXPRESSION_COMPLETE_GPU_RELEASE', len(records), flush=True)
