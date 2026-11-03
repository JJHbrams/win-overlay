"""Actual Blender body-only UV exporter for a root-approved H assembly.

No import-time scene changes. Reuses the existing source-branch ownership rule;
does not pretend E vertex IDs or the old E-specific microtriangle IDs are H IDs.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import math
import sys
import numpy as np

sys.dont_write_bytecode = True
CANONICAL = Path('D:/MiaWorkCache/mia-reference-work/win-overlay')
REL = Path('asset/mia/blender/mia-fit-v003/body/surface-review12')


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def ah(a): return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _repair_submicron_islands(uv, world, faces, body):
    """Only a physically submicron, fully collapsed UV fan may be repaired.

    Shared (world vertex, old corner UV) keys are updated together. A normal
    sized degeneracy, line-like chart, or failed orientation remains an error.
    The generic repair has no E/H face IDs or vertex IDs encoded in it.
    """
    signed = lambda q: np.cross(q[:, 1].astype(float)-q[:, 0], q[:, 2].astype(float)-q[:, 0])
    areas = signed(uv)
    bad = np.flatnonzero(body & (areas == 0))
    if not len(bad): return []
    original = uv.copy(); pending = set(map(int, bad)); repairs = []
    while pending:
        seed = pending.pop(); group = {seed}; vids = set(map(int, faces[seed]))
        changed = True
        while changed:
            changed = False
            for fi in list(pending):
                if vids.intersection(map(int, faces[fi])):
                    pending.remove(fi); group.add(fi); vids.update(map(int, faces[fi])); changed = True
        ids = np.array(sorted(group)); q = world[faces[ids]].astype(float)
        physical = np.linalg.norm(np.cross(q[:, 1]-q[:, 0], q[:, 2]-q[:, 0]), axis=1)
        assert physical.max() < 1e-12, ('Normal-sized zero UV triangle', ids.tolist(), physical.tolist())
        origin = original[seed, 0].copy()
        assert np.all(original[ids] == origin), 'Line-like or multiple-chart degeneration needs author review'
        vertex_ids = np.array(sorted(vids)); xyz = world[vertex_ids].astype(float)
        centered = xyz-xyz.mean(0)
        _, _, axes = np.linalg.svd(centered, full_matrices=False)
        local = centered@axes[:2].T
        ulp = float(max(abs(np.nextafter(origin, np.float32(np.inf))-origin).max(), np.finfo(np.float32).eps/8))
        extent = np.max(np.linalg.norm(local, axis=1)); assert extent > 0
        targets = origin+(local/extent*(16*ulp)).astype(np.float32)
        key_target = {int(vi): target for vi, target in zip(vertex_ids, targets)}
        affected = set()
        for corner in range(3):
            hit = np.isin(faces[:, corner], vertex_ids)&np.all(original[:, corner] == origin, axis=1)
            for fi in np.flatnonzero(hit):
                uv[fi, corner] = key_target[int(faces[fi, corner])]; affected.add(int(fi))
        after = signed(uv[np.array(sorted(affected))])
        assert np.all(after != 0), ('Repair leaves collapsed chart', sorted(affected))
        old = signed(original[np.array(sorted(affected))]); keep = old != 0
        assert np.all(np.sign(after[keep]) == np.sign(old[keep])), 'Repair flips adjacent valid UV triangle'
        maximum = float(abs(uv-original).max()); assert maximum < 4e-6
        repairs.append(dict(collapsed_faces=ids.tolist(), physical_double_area_m2=physical.tolist(),
                            shared_corner_affected_faces=sorted(affected), maximum_uv_delta=maximum,
                            method='Shared-key planar projection of physically submicron fully collapsed fan into 16 float32 ULPs; no fixed face IDs'))
    assert np.all(signed(uv[body]) != 0)
    return repairs


def _regions(d, assembly, canonical):
    p = Path(canonical)/REL
    v, f = d['world'], d['triangles']; cent = v[f].mean(1)
    limb = d['vertex_limb_weights'][f].mean(1)
    region = np.where(cent[:, 1] < -.006, 1, 2).astype(np.int16)
    # Semantic source ancestry, not a global width/height mask on hands.
    transfer = load('h_inherited_arm_owner', p/'source_branch_ownership.py')
    e = dict(np.load(p/'joined-expanded-E.npz'))
    es = dict(np.load(p/'surface-v10-expanded-E-source-branches.npz'))
    inherited = transfer.inherited_donor_arm_labels(e, es, d)
    arms = inherited > 0
    # H is definition-identical below1.34. Its upper-arm primitive is unchanged.
    candidates = np.flatnonzero((d['source_part'] == 2)&(abs(cent[:, 0]) > .12)&(cent[:, 2] < 1.34))
    field = load('h_arm_semantic_frozen11', p.parent/'shoulder11/field.py')
    _, reg = field.make(json.loads((p.parent/'shoulder11/parameters.json').read_text()))
    points = cent[candidates].astype(float)
    av = np.minimum(field.evaluate(reg['upper_arm_R'], points), field.evaluate(reg['upper_arm_L'], points))
    ov = np.minimum.reduce([field.evaluate(reg[k], points) for k in
                            ['curved_tapered_thorax_neck', 'breast_pair', 'anterior_fan_R', 'anterior_fan_L',
                             'posterior_wall_R', 'posterior_wall_L', 'shoulder_R', 'shoulder_L']])
    arms[candidates[av < ov]] = True
    legs = (np.maximum(limb[:, 2], limb[:, 3]) > .55)&(cent[:, 2] < .98)&~arms
    region[legs&(cent[:, 0] >= 0)] = 10; region[legs&(cent[:, 0] < 0)] = 11
    pelvis = (cent[:, 2] < 1.10)&~arms&~legs
    region[pelvis&(cent[:, 1] < -.006)] = 8; region[pelvis&(cent[:, 1] >= -.006)] = 9
    neck = (cent[:, 2] > 1.40)&(abs(cent[:, 0]) < .085); region[neck] = 3
    shoulder = (cent[:, 2] > 1.34)&(abs(cent[:, 0]) >= .085)
    region[shoulder&(cent[:, 1] < -.006)] = 4; region[shoulder&(cent[:, 1] >= -.006)] = 5
    region[arms&(cent[:, 0] >= 0)] = 6; region[arms&(cent[:, 0] < 0)] = 7
    for kind, label in [('neck', 12), ('waist', 13), ('armR', 14), ('armL', 15)]:
        lo, hi = assembly['collar_triangle_ranges'][kind]; region[lo:hi] = label
    return region


def export(geometry_path, assembly_path, output_dir, *, canonical=CANONICAL):
    import bpy
    import bmesh
    root = Path(canonical).resolve(); p = root/REL
    out = Path(output_dir).resolve(); allowed = root/'.mia-cache/body-h/shape/assembly'
    assert out == allowed or allowed in out.parents
    guard = load('h_atlas_capacity', root/'asset/mia/blender/mia-fit-v003/integration/workspace-storage-20261103/storage_guard.py')
    budget = guard.inspect(80*1024**2); assert not budget['violations'], budget
    assert not (out/'atlas.npz').exists() and not (out/'surface.npz').exists()
    d = dict(np.load(geometry_path)); assembly = json.loads(Path(assembly_path).read_text())
    v, f = d['world'], d['triangles']; body = d['source_part'] != 1
    bpy.ops.wm.read_factory_settings(use_empty=True)
    me = bpy.data.meshes.new('H_CPU_Atlas'); me.from_pydata(v.tolist(), [], f.tolist()); me.update()
    ob = bpy.data.objects.new('H_CPU_Atlas', me); bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    names = json.loads((p/'donor.json').read_text())['uv_layers']
    for i, name in enumerate(names):
        u = me.uv_layers.new(name=name, do_init=False); u.data.foreach_set('uv', d['old_loop_uv'][:, :, i, :].ravel())
    before = [np.array([x.uv[:] for x in uv.data], np.float32) for uv in me.uv_layers]
    me.uv_layers.new(name='MIA_Review12UV', do_init=False); me.uv_layers.active_index = len(names)
    bpy.context.tool_settings.mesh_select_mode = (False, False, True)
    bpy.ops.object.mode_set(mode='EDIT'); bm = bmesh.from_edit_mesh(me); bm.faces.ensure_lookup_table()
    for face in bm.faces: face.select_set(bool(body[face.index]))
    bm.select_flush_mode(); bmesh.update_edit_mesh(me, loop_triangles=False, destructive=False)
    assert sum(x.select for x in bm.faces) == int(body.sum())
    assert bm.loops.layers.uv.active.name == 'MIA_Review12UV'
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=.004, area_weight=0., correct_aspect=True, scale_to_bounds=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    for i, old in enumerate(before):
        assert np.array_equal(old, np.array([x.uv[:] for x in me.uv_layers[i].data], np.float32))
    uv = np.array([x.uv[:] for x in me.uv_layers['MIA_Review12UV'].data], np.float32).reshape(-1, 3, 2)
    assert np.isfinite(uv).all() and uv[body].min() >= -1e-6 and uv[body].max() <= 1.000001
    repairs = _repair_submicron_islands(uv, v, f, body)
    regions = _regions(d, assembly, root); ids = np.flatnonzero(body)
    out.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out/'atlas.npz', loop_uv=uv)
    np.savez_compressed(out/'surface.npz', world=v, triangles=f[body], loop_uv=uv[body],
                        face_region=regions[body], meshfaceid=ids.astype(np.int32))
    emeta = json.loads((p/'surface-v10-expanded-E-source-branches.json').read_text())
    meta = dict(emeta, scope='Fresh H static review body-only UV/semantic payload; original face UV untouched; no rig approval',
                payload_version='H', world_shape=list(v.shape), triangles_shape=list(f[body].shape), loop_uv_shape=list(uv[body].shape),
                geometry_world_sha256=ah(v), triangles_sha256=ah(f[body]), loop_uv_sha256=ah(uv[body]),
                surface_npz_sha256=sha(out/'surface.npz'), surface_npz_path=str(out/'surface.npz'),
                assembly_geometry_path=str(Path(geometry_path).resolve()), atlas_path=str(out/'atlas.npz'),
                region_counts={str(i): int((regions[body] == i).sum()) for i in np.unique(regions[body])},
                collar_bounds=assembly['collars'], retained_old_UV_layers_exact=True,
                uv_repairs=repairs, native_saved=False, GPU_used=False,
                uv_method=dict(method='Actual Blender SmartUV body selection only, fresh H topology', angle_limit_degrees=66, island_margin=.004),
                source_registration_limit='Frozen original SRT remains provisional; new source and actual material review required.',
                semantic_owner_method='Retained donor arm labels by same original source_face; actual unchanged lower-guide component fields; explicit H collar ranges',
                capacity=budget)
    # Do not inherit stale E collar landmark coordinates into a new H payload.
    meta['landmarks'] = dict(body_center_x=0., front_direction=[0, -1, 0], up=[0, 0, 1],
                             hip_waist_join_z=[1.005, 1.145], neck_cuts=assembly['cuts'])
    (out/'surface.json').write_text(json.dumps(meta, indent=2)+'\n', encoding='utf8', newline='\n')
    return meta
