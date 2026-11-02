"""CPU-only diagnostic: exact source ownership, identity copy, then full rollback.

No rendering, native save, live MCP, fitting, new production candidate or adoption.
"""
from pathlib import Path
import hashlib
import json
import sys

import bpy
import numpy as np

P = Path(__file__).resolve().parent
H = P.parent
W = Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay')
N = W / 'asset/mia/blender/mia-refinement-v002/integrated/Mia_v0.0.2_Review_R3b.blend'
SHA = '4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'
assert hashlib.sha256(N.read_bytes()).hexdigest() == SHA
bpy.ops.wm.open_mainfile(filepath=str(N), use_scripts=False)
bpy.context.scene.frame_set(1)
sys.path.insert(0, str(H))
import apply_baked_v29_crown
apply_baked_v29_crown.apply(H / 'v29-pigment', mode='combined')
sys.path.insert(0, str(H / 'rear-loop-cleanup'))
import apply_loop_mask
apply_loop_mask.apply(H / 'rear-loop-cleanup')
sys.path.insert(0, str(W / 'asset/mia/blender/mia-refinement-v002'))
import scene_fingerprint as sfp
sys.path.insert(0, str(P))
import make_identity_copy

main = bpy.data.objects['MIA_V17_PIXAL_DetailedHair']
mesh = main.data


def byte_guard():
    """Fingerprint the explicit data not fully covered by scene_fingerprint."""
    h = hashlib.sha256()
    h.update(np.array([v.co[:] for v in mesh.vertices], np.float32).tobytes())
    h.update(np.array([p.vertices[:] for p in mesh.polygons], np.int32).tobytes())
    h.update(np.array([p.material_index for p in mesh.polygons], np.int32).tobytes())
    h.update(np.array([n.vector[:] for n in mesh.corner_normals], np.float32).tobytes())
    for layer in mesh.uv_layers:
        h.update(layer.name.encode())
        h.update(np.array([d.uv[:] for d in layer.data], np.float32).tobytes())
        h.update(str(layer.active_render).encode())
    for attr in mesh.attributes:
        if attr.domain != 'POINT' or attr.name == 'position':
            continue
        prop = ('color' if attr.data_type in ['FLOAT_COLOR', 'BYTE_COLOR']
                else 'vector' if attr.data_type == 'FLOAT_VECTOR' else 'value')
        h.update(attr.name.encode())
        h.update(np.array([getattr(d, prop) for d in attr.data]).tobytes())
    return h.hexdigest()


bpy.context.view_layer.update()
before = sfp.snapshot_scene()
explicit_before = byte_guard()
indices = np.array([p.material_index for p in mesh.polygons], np.int32)
slots_before = [m.name for m in mesh.materials]
payload = np.load(P / 'identity-assembly.npz')
ids = payload['source_faces']
assert len(ids) == 15922 and len(np.unique(ids)) == len(ids)
assert np.array_equal(np.array([mesh.polygons[int(i)].vertices[:] for i in ids]),
                      payload['source_triangles'])
assert np.array_equal(np.unique(payload['source_triangles']), payload['source_vertices'])
assert np.all(indices[ids] == 0), 'This benchmark must use the original opaque slot0.'
assert not np.intersect1d(ids, np.load(H / 'rear-loop-cleanup/loop-mask.npz')['polygon_indices']).size
raw = mesh.attributes['MIA_SOURCE_POLYGON']
assert np.array_equal(np.array([raw.data[int(i)].value for i in ids]), payload['source_raw_faces'])
report = make_identity_copy.apply(P)
changed = np.flatnonzero(indices != np.array([p.material_index for p in mesh.polygons]))
assert np.array_equal(changed, ids)
after = sfp.snapshot_scene()
outside_changes = [name for name, row in before['objects'].items()
                   if name != main.name and after['objects'][name] != row]
assert not outside_changes and before['scene'] == after['scene']
clone = bpy.data.objects[report['object']]
clone_mesh = clone.data
assert len(clone_mesh.polygons) == len(ids)
assert [m.name for m in clone_mesh.materials] == slots_before

# Roll back only the explicitly permitted offline diagnostic changes.
for poly, slot in zip(mesh.polygons, indices):
    poly.material_index = int(slot)
mask = mesh.materials[-1]
assert mask.name == 'MIA_IDENTITY_ONLY_OriginalAssemblyTemporarilyHidden'
mesh.materials.pop(index=len(mesh.materials) - 1)
bpy.data.objects.remove(clone, do_unlink=True)
bpy.data.meshes.remove(clone_mesh)
bpy.data.materials.remove(mask)
bpy.context.view_layer.update()
restored = sfp.snapshot_scene()
assert restored == before
assert byte_guard() == explicit_before
assert [m.name for m in mesh.materials] == slots_before
assert hashlib.sha256(N.read_bytes()).hexdigest() == SHA
out = dict(status='CPU_SOURCE_OWNERSHIP_AND_EXACT_ROLLBACK_CONFIRMED',
           source_native_sha256=SHA, existing_owners_protected=len(before['objects']),
           exact_source_faces=len(ids), original_raw_source_ids_and_triangles_exact=True,
           source_selected_faces_originally_opaque_slot0=True, prior_U_mask_disjoint=True,
           only_temporary_original_changes='Selected family material indices and one temporary slot',
           temporary_changed_faces=len(changed), outside_owner_changes=outside_changes,
           scene_before_after_restore_exact=True, explicit_Main_data_before_after_restore_exact=True,
           explicit_Main_guard_sha256=explicit_before,
           UV_count=len(mesh.uv_layers), copied_actual_evaluated_normals=True,
           fitted_normals_validated=False, rendered=False, native_saved=False,
           live_mutated=False, new_fill_selected=False, ART=False)
(P / 'checkpoint-source-ownership-guard.json').write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8')
print('CHECKPOINT_SOURCE_OWNERSHIP_EXACT_ROLLBACK_OK', json.dumps(out), flush=True)
