"""Source-defined independent brows, with existing semantic expression motion.

Only the legacy brow material slot is archived. Existing geometry, maps, keys,
mouth and eye/lash owners stay exact. Projected source targets are observations,
not an assertion about brows hidden under bangs. No bitmap is painted here.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

P = Path(__file__).resolve().parent
ROOT = P.parents[1]
HELPERS = Path('C:/Users/antio/.codex/worktrees/mia-final-face-v12/win-overlay/asset/mia/blender/mia-eye-lash-v29')
sys.path.insert(0, str(HELPERS))
from audit_mesh_helpers import snapshot

ap = argparse.ArgumentParser()
ap.add_argument('--input', required=True)
ap.add_argument('--output', required=True)
ap.add_argument('--clearance', type=float, default=.00014)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
assert .0001 <= a.clearance <= .0003
src, dest = Path(a.input).resolve(), Path(a.output).resolve()
assert src != dest and not dest.exists()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
srcsha = sha(src)
before, _, oldmats, oldimages = snapshot(src)
master = bpy.data.objects['MIA_V27_Foundation_Face']
MASTER = master.name
skin = bpy.data.objects['MIA_V27_SharedHeadBody']
names = [k.name for k in master.data.shape_keys.key_blocks]
assert all(k.value == 0 for k in master.data.shape_keys.key_blocks)
rig = next(m.object for m in master.modifiers if m.type == 'ARMATURE')
head = rig.pose.bones['J_Bip_C_Head']
assert np.max(np.abs(np.array(head.matrix_basis) - np.eye(4))) < 1e-6
assert np.max(np.abs(np.array(master.matrix_world) - np.eye(4))) < 1e-6

pkg = json.loads((ROOT / 'mia-orbit-thorax-review-v28/reviews/G2L-face/reference-review.json').read_text())
spec = pkg['views'][0]['candidate_camera']
cm = Matrix(spec['matrix'])
right, up = cm.to_3x3().col[0], cm.to_3x3().col[1]
forward = -cm.to_3x3().col[2]
scale = spec['ortho_scale']

# x,y and half width in ORIGINAL 1024px portrait, never stretched.
# Exposed left run 410..455 and right run 520..551 are observable.
# Ends behind bangs are a smooth bounded continuation, explicitly uncertain.
targets = {
    -1: [[391, 288.8, .12], [401, 282.7, 1.2], [412, 278.7, 2.8],
         [428, 276.7, 3.4], [446, 275.6, 3.35], [462, 274.7, 2.9],
         [475, 274.5, 2.2], [481, 275.0, .12]],
     1: [[518, 272.8, .12], [524, 270.0, 3.6], [540, 265.3, 3.7],
         [554, 262.0, 3.3], [574, 258.6, 2.5], [591, 256.6, 1.7],
         [607, 255.7, .7], [615, 256.0, .12]],
}

def pixel_ray(x, y):
    # Original source -> source tile -> frozen baseline model768 frame.
    tile = np.array([x, y]) * (590 / 360) + [-532.2222222222222, -261.80555555555554]
    q = (tile - [-142.01146815879025, -223.93878303771004]) / 1.1698146556808693
    return cm.translation + right * ((q[0] / 768 - .5) * scale) + up * ((.5 - q[1] / 768) * scale)

def evaluated_skin_bvh():
    bpy.context.view_layer.update()
    ev = skin.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = ev.to_mesh()
    pts = [ev.matrix_world @ v.co for v in me.vertices]
    bvh = BVHTree.FromPolygons(pts, [list(f.vertices) for f in me.polygons])
    ev.to_mesh_clear()
    return bvh

def surface_ray(bvh, origin):
    hit, normal, face, distance = bvh.ray_cast(origin, forward, 4)
    assert hit is not None, ('Source brow ray misses actual skin', list(origin))
    return np.array(hit), np.array(normal)

bvh = evaluated_skin_bvh()
oldpolys = [p for p in master.data.polygons if p.material_index == 4]
oldids = sorted({i for p in oldpolys for i in p.vertices})
masterkeys = np.array([[k.data[i].co[:] for i in oldids] for k in master.data.shape_keys.key_blocks])
created, payload, audits = [], {}, []
for side, run in targets.items():
    run = np.array(run, dtype=float)
    distance = np.r_[0., np.cumsum(np.linalg.norm(np.diff(run[:, :2], axis=0), axis=1))]
    t = np.linspace(0, distance[-1], 65)
    centers = np.column_stack([np.interp(t, distance, run[:, j]) for j in [0, 1]])
    widths = np.interp(t, distance, run[:, 2])
    tangents = np.gradient(centers, axis=0)
    normals = np.column_stack([-tangents[:, 1], tangents[:, 0]])
    normals /= np.linalg.norm(normals, axis=1)[:, None]
    pixels = np.array([c + n * w * row for c, n, w in zip(centers, normals, widths) for row in [-1., 0., 1.]])
    origins = [pixel_ray(*q) for q in pixels]
    neutral = np.array([surface_ray(bvh, q)[0] + surface_ray(bvh, q)[1] * a.clearance for q in origins])
    oldside = np.flatnonzero(masterkeys[0, :, 0] * side > 0)
    # Smooth longitudinal field from the actual old brow's named morphs.
    # Depth is then reseated on the actual posed skin instead of copying a
    # floating donor plane. No other face morph is regenerated.
    d = (neutral[:, None, 0] - masterkeys[0, oldside, 0][None, :]) ** 2
    weights = np.exp(-d / (.005 ** 2))
    weights /= weights.sum(1, keepdims=True)
    deltas = np.einsum('vi,kij->kvj', weights, masterkeys[:, oldside] - masterkeys[0, oldside])
    arrays = [neutral]
    for ki, name in enumerate(names[1:], 1):
        master.data.shape_keys.key_blocks[name].value = 1
        keybvh = evaluated_skin_bvh()
        candidate = []
        for p, delta in zip(neutral, deltas[ki]):
            wanted = Vector(p + delta)
            origin = wanted - forward * 1.0
            hit, n = surface_ray(keybvh, origin)
            candidate.append(hit + n * a.clearance)
        arrays.append(np.array(candidate))
        master.data.shape_keys.key_blocks[name].value = 0
    arrays = np.array(arrays, dtype=np.float32)
    # All rows create one thin conforming native surface, with independent UV.
    faces = [(i * 3 + j, (i + 1) * 3 + j, (i + 1) * 3 + j + 1, i * 3 + j + 1)
             for i in range(64) for j in range(2)]
    me = bpy.data.meshes.new('V31_SourceBrow_Surface_' + str(side))
    me.from_pydata(arrays[0], [], faces)
    ob = bpy.data.objects.new('V31_SourceBrow_' + str(side), me)
    bpy.context.scene.collection.objects.link(ob)
    uv = me.uv_layers.new(name='BrowParamUV')
    for poly in me.polygons:
        poly.use_smooth = True
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            uv.data[li].uv = (vi // 3 / 64, vi % 3 / 2)
    for name, coords in zip(names, arrays):
        k = ob.shape_key_add(name=name)
        k.data.foreach_set('co', coords.ravel())
        if name != names[0]:
            driver = k.driver_add('value').driver
            driver.type = 'AVERAGE'
            var = driver.variables.new(); var.name = 'source_expression'
            var.type = 'SINGLE_PROP'; var.targets[0].id_type = 'KEY'
            var.targets[0].id = master.data.shape_keys
            var.targets[0].data_path = master.data.shape_keys.key_blocks[name].path_from_id('value')
    vg = ob.vertex_groups.new(name='J_Bip_C_Head')
    vg.add(list(range(len(me.vertices))), 1., 'REPLACE')
    arm = ob.modifiers.new('V31_Brow_HeadFollow', 'ARMATURE'); arm.object = rig
    ob['source_role'] = 'Eyebrow only, not lash/eyeliner/crease. Original portrait observed runs; hair-hidden ends inferred.'
    ob['surface_clearance_m'] = a.clearance
    payload[ob.name] = arrays
    created.append(ob)
    audits.append({'owner': ob.name, 'source_run_original1024': run.tolist(),
                   'observed_x': [410, 455] if side == -1 else [520, 551],
                   'uncertain': 'Hair-covered continuation and full neutral tail. Expression sheet supports flat broad ink rather than donor arch.',
                   'vertices': len(me.vertices), 'faces': len(me.polygons), 'semantic_keys': names,
                   'neutral_bounds_m': [arrays[0].min(0).tolist(), arrays[0].max(0).tolist()]})

mat = bpy.data.materials.new('V31_SourceBrow_CharcoalInk'); mat.use_nodes = True
n = mat.node_tree.nodes; n.clear(); out = n.new('ShaderNodeOutputMaterial'); out.is_active_output = True
em = n.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (.031, .027, .030, 1); em.inputs['Strength'].default_value = 1
mat.node_tree.links.new(em.outputs[0], out.inputs['Surface'])
for ob in created: ob.data.materials.append(mat)
archive = bpy.data.materials.new('V31_ArchivedDonorBrow_Transparent'); archive.use_nodes = True
n = archive.node_tree.nodes; n.clear(); tr = n.new('ShaderNodeBsdfTransparent'); out = n.new('ShaderNodeOutputMaterial'); out.is_active_output = True
archive.node_tree.links.new(tr.outputs[0], out.inputs['Surface'])
master.data.materials[4].use_fake_user = True
master.data.materials[4] = archive
bpy.context.view_layer.update()
dest.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(dest))
after, _, am, ai = snapshot(dest)
checks = {
    'all_other_original_mesh_records_exact': all(before[n] == after[n] for n in before if n != MASTER),
    'master_only_brow_material_slot_changed': all(before[MASTER][k] == after[MASTER][k] for k in before[MASTER] if k != 'materials'),
    'mouth_and_nonbrow_slots_exact': all(before[MASTER]['materials'][i] == after[MASTER]['materials'][i] for i in range(9) if i != 4),
    'all_old_material_graphs_exact': all(oldmats[n] == am[n] for n in oldmats),
    'all_old_images_exact': all(oldimages[n] == ai[n] for n in oldimages),
    'all_new_brow_coordinates_finite': all(np.isfinite(q).all() for q in payload.values()),
    'input_native_unchanged': sha(src) == srcsha,
}
assert all(checks.values()), checks
report = {'input': str(src), 'input_sha256': srcsha, 'output': str(dest), 'sha256': sha(dest),
          'source': str(ROOT.parent / 'references/received/mia-face-reaffirmed-20261031.png'),
          'scope': 'Two source-defined conforming brows,42 expression controls/Head binding; legacy slot4 alpha archived reversibly. No skin/eye/lash/facepaint/body/hair edit.',
          'checks': checks, 'owners': audits, 'surface_clearance_m': a.clearance,
          'pending': 'Source4 actual neutral/hair ON/OFF, expression contact and normal delivery scale visual review. Not ART approval.'}
dest.with_suffix('.brow-v31.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
np.savez_compressed(dest.with_suffix('.coordinates.npz'), **payload)
print('V31_BROW_NATIVE', str(dest), report['sha256'], checks, flush=True)
