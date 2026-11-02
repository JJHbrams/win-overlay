"""Replay bounded component deltas on the exact configured guarded baseline.

Run in background Blender. Component apply functions may not open/save a scene.
This records technical isolation; it deliberately does not grant ART approval.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, json, sys
import bpy
from mathutils import Matrix

P = Path(__file__).resolve().parent
sys.path.insert(0,str(P))
import scene_fingerprint as sfp
ap = argparse.ArgumentParser()
ap.add_argument('--config', required=True)
ap.add_argument('--out', required=True)
ap.add_argument('--audit-only', action='store_true')
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
cfg = json.loads(Path(a.config).read_text(encoding='utf-8'))
out = Path(a.out).resolve()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not out.exists(), 'Use a new immutable native path'
resolve = lambda p: (Path(p) if Path(p).is_absolute() else P/str(p)).resolve()
baseline = resolve(cfg['baseline'])
assert sha(baseline) == cfg['baseline_sha256']
bpy.ops.wm.open_mainfile(filepath=str(baseline), use_scripts=False)

def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

stages = []
for i, stage in enumerate(cfg['stages']):
    before_state = sfp.snapshot_scene()
    before = before_state['objects']
    entry = resolve(stage['entry'])
    assert sha(entry) == stage['entry_sha256'], 'Replay code changed: ' + stage['id']
    mod = load_module(entry, 'mia_integrate_' + str(i))
    kwargs = dict(stage.get('kwargs', {}))
    for key in stage.get('path_kwargs', []):
        kwargs[key] = str(resolve(kwargs[key]))
    result = getattr(mod, stage['function'])(**kwargs)
    after_state = sfp.snapshot_scene()
    after = after_state['objects']
    assert before_state['scene'] == after_state['scene'], ('Scene envelope changed',stage['id'])
    changed = {n: [k for k in before[n] if before[n][k] != after[n].get(k)]
               for n in before if n in after and before[n] != after[n]}
    removed = sorted(set(before) - set(after))
    assert not removed, ('A delta removed original scene objects', stage['id'], removed)
    allowed = set(stage.get('allowed_existing_owners', []))
    assert set(changed).issubset(allowed), ('Outside component ownership', stage['id'], changed)
    # Independent scene, camera, lamp and rest-pose protection per component.
    driver_changes = sfp.assert_existing_driver_preservation(before,after,stage)
    sfp.assert_scene_pose_owners_protected(before,after,stage)
    # Even an allowed owner may not rewrite any original facial key coordinates.
    for n, fields in changed.items():
        if 'keys' not in fields or stage['id'] == 'body-G':
            continue
        assert all(after[n]['keys'].get(k) == v for k, v in before[n].get('keys', {}).items()), ('Original facial arrays rewritten', stage['id'], n)
    stages.append(dict(id=stage['id'], entry=str(entry), entry_sha256=sha(entry),
                       actual_existing_changes=changed, actual_driver_changes=driver_changes,
                       new_owners=sorted(set(after)-set(before)), result=result))
    print('COMPONENT_REPLAY_OK', stage['id'], sorted(changed), flush=True)

# Save a useful head camera and full-body camera, with the same finite depth and
# measured source-light setup used by the review renderer. Never move origins.
reference = P.parent/'mia-orbit-thorax-review-v28/reviews/G2L-face/reference-review.json'
camera_spec = json.loads(reference.read_text())['views'][0]['candidate_camera']
s = bpy.context.scene
for ob in s.objects:
    if ob.type == 'LIGHT':
        ob.hide_render = True
lamps = []
for i, item in enumerate(camera_spec['lighting']['areas']):
    name = 'Mia_v002_SourceLight_' + str(i)
    ob = s.objects.get(name)
    if ob is None:
        d = bpy.data.lights.new(name, 'AREA')
        ob = bpy.data.objects.new(name, d)
        s.collection.objects.link(ob)
    else:
        assert ob.type == 'LIGHT' and ob.data.type == 'AREA'
        d = ob.data
    d.energy, d.size, d.shape = item['watts'], item['size'], item['shape']
    d.color = item['color']
    ob.hide_render = False
    ob.matrix_world = Matrix(item['matrix'])
    lamps.append(ob)
w = bpy.data.worlds.get('Mia_v002_SourceWorld') or bpy.data.worlds.new('Mia_v002_SourceWorld')
w.use_nodes = True
w.node_tree.nodes.clear()
bg = w.node_tree.nodes.new('ShaderNodeBackground')
wo = w.node_tree.nodes.new('ShaderNodeOutputWorld')
wo.is_active_output = True
w.node_tree.links.new(bg.outputs[0], wo.inputs['Surface'])
bg.inputs['Color'].default_value = (*camera_spec['lighting']['world_linear'], 1)
bg.inputs['Strength'].default_value = camera_spec['lighting']['world_strength']
s.world = w
cm = camera_spec['color_management']
for name in ['view_transform', 'look', 'exposure', 'gamma']:
    setattr(s.view_settings, name, cm[name])
for name, matrix, scale in [('Mia_v002_HeadCamera', camera_spec['matrix'], camera_spec['ortho_scale']),
                             ('Mia_v002_FullBodyCamera', [[1,0,0,0],[0,0,-1,-4],[0,1,0,.88],[0,0,0,1]], 1.95)]:
    ob = s.objects.get(name)
    if ob is None:
        d = bpy.data.cameras.new(name)
        ob = bpy.data.objects.new(name, d)
        s.collection.objects.link(ob)
    else:
        assert ob.type == 'CAMERA'
        d = ob.data
    d.type, d.ortho_scale, d.clip_start, d.clip_end = 'ORTHO', scale, .1, 10.
    ob.matrix_world = Matrix(matrix)
    if name.endswith('HeadCamera'):
        d.shift_x, d.shift_y = camera_spec['lens_shift']
        s.camera = ob
s.render.engine = 'BLENDER_EEVEE'
s.render.resolution_x = s.render.resolution_y = 768
s.render.resolution_percentage = 100
s.render.pixel_aspect_x = s.render.pixel_aspect_y = 1
s.render.fps = 30
s.render.fps_base = 1
s.render.image_settings.file_format = 'PNG'
s.render.image_settings.color_mode = 'RGBA'
s.render.use_freestyle = False
s.frame_set(1)
s['MiaVersion'] = 'v0.0.2 refinement review; v0.0.1 retained'
s['MiaARTStatus'] = 'UNAPPROVED until actual source, pose and independent visual review; component replay is technical evidence only.'
out.parent.mkdir(parents=True, exist_ok=True)
if not a.audit_only:
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True, check_existing=False)
assert sha(baseline) == cfg['baseline_sha256']
final_state = sfp.snapshot_scene()
report = dict(baseline=str(baseline), baseline_sha256=cfg['baseline_sha256'],
              config=cfg, stages=stages, native=None if a.audit_only else str(out), native_sha256=None if a.audit_only else sha(out), native_saved=not a.audit_only,
              active_lights=[dict(name=o.name, watts=o.data.energy, matrix=[list(r) for r in o.matrix_world]) for o in lamps],
              default_pose='All preset/manual/head/gaze controls zero; original neutral body rest preserved.',
              fingerprint_version=sfp.FINGERPRINT_VERSION,
              fingerprint_helper_sha256=sha(Path(sfp.__file__)),
              final_owners=final_state['objects'], final_scene=final_state['scene'], art_approved=False,
              scope='Single packed integration review. No garments, final physics or event action promotion.')
out.with_suffix('.integration.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
print('V002_COMPONENT_INTEGRATION_' + ('PREFLIGHT_OK' if a.audit_only else 'SAVED'), str(out), report['native_sha256'], flush=True)
