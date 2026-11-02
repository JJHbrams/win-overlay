"""Fresh-background verifier. Opens only baseline; never saves/renders a native."""
import hashlib
import json
from pathlib import Path
import sys

import bpy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from pose_space import build_mapping, save_mapping, target_world_to_local_delta
from preservation import snapshot
import numpy as np

EXPECTED = '4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'
baseline = Path(bpy.data.filepath)
native_before = hashlib.sha256(baseline.read_bytes()).hexdigest()
assert native_before == EXPECTED, 'Wrong immutable baseline'
assert bpy.context.scene.frame_current == 1, 'Verifier requires actual saved frame1'
assert bpy.app.background, 'Fresh background process required'
owner = bpy.data.objects['MIA_V27_SharedHeadBody']
assert len(owner.data.vertices) == 4647 and len(owner.data.shape_keys.key_blocks) == 47
before = snapshot()
mapping = build_mapping(owner)
after = snapshot()
native_after = hashlib.sha256(baseline.read_bytes()).hexdigest()
differences = [k for k in before if before[k] != after[k]]
api_delta = target_world_to_local_delta(mapping, mapping['test_actual_world']) if mapping['metadata']['status'] == 'PASS' else None
recomposed_world = mapping['q0_local'] @ mapping['matrix_world'][:3, :3].T + mapping['matrix_world'][:3, 3]
local_cage_error = float(np.max(np.linalg.norm(recomposed_world - mapping['q0_world'], axis=1)))
proof = {'baseline_path': str(baseline), 'baseline_sha256_before': native_before,
         'baseline_sha256_after': native_after, 'native_hash_exact': native_before == native_after,
         'original_snapshot_exact': not differences, 'changed_snapshot_sections': differences,
         'original_objects_before': before['object_count'], 'original_objects_after': after['object_count'],
         'all_legacy_owners_preserved': before['objects'] == after['objects'],
         'keys_uv_materials_weights_rig_scene_covered': list(before),
         'snapshot_sha256_before': hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest(),
         'snapshot_sha256_after': hashlib.sha256(json.dumps(after, sort_keys=True).encode()).hexdigest(),
         'temporary_ids_remaining': [n for names in after['id_inventory_names'].values() for n in names if n.startswith('_MIA_POSE_SPACE_')],
         'public_api_field_delta_max_m': float(np.max(np.linalg.norm(api_delta - mapping['test_local_field'], axis=1))) if api_delta is not None else None,
         'posed_local_cage_world_recomposition_max_m': local_cage_error,
         'render_called': False, 'native_save_called': False, 'art_acceptance': 'NOT_EVALUATED',
         'mapping_status': mapping['metadata']['status']}
proof['status'] = 'PASS' if not differences and native_before == native_after and not proof['temporary_ids_remaining'] and mapping['metadata']['status'] == 'PASS' and local_cage_error < 1e-12 else 'FAIL'
save_mapping(mapping, HERE / 'mapping-frame1')
(HERE / 'verification.json').write_text(json.dumps(proof, indent=2, sort_keys=True), encoding='utf-8')
if differences:
    (HERE / 'preservation-diff.json').write_text(json.dumps({'before': before, 'after': after}, indent=2, sort_keys=True), encoding='utf-8')
print('POSE_SPACE_RESULT ' + json.dumps({'proof': proof, 'measurement': mapping['metadata']}, sort_keys=True))
assert proof['status'] == 'PASS', proof
