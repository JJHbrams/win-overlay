"""Fresh Blender audit: navigation setup changes no model geometry, keys, UVs or origins."""
import array
import hashlib
import json
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent/'mia-correction-v20/integrated-r2/Mia_Corrected_v20.blend'
TARGET = ROOT/'Mia_ReviewSetup_v22.blend'


def coordinates(collection, prop, size, kind='f'):
    values = array.array(kind, [0])*(len(collection)*size)
    collection.foreach_get(prop, values)
    return hashlib.sha256(values.tobytes()).hexdigest()


def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path), use_scripts=False)
    rows = {}
    for obj in bpy.context.scene.objects:
        if obj.type not in {'MESH','ARMATURE'}: continue
        row = {'matrix': [list(r) for r in obj.matrix_world], 'parent': obj.parent.name if obj.parent else None}
        if obj.type == 'MESH':
            m = obj.data
            row.update(vertices=coordinates(m.vertices, 'co', 3),
                       loops=coordinates(m.loops, 'vertex_index', 1, 'i'),
                       uv={uv.name: coordinates(uv.data, 'uv', 2) for uv in m.uv_layers},
                       keys={k.name: coordinates(k.data, 'co', 3) for k in m.shape_keys.key_blocks} if m.shape_keys else {})
        rows[obj.name] = row
    return rows


before = snapshot(SOURCE)
after = snapshot(TARGET)
changed = [name for name in set(before)|set(after) if before.get(name) != after.get(name)]
prior = json.loads((ROOT.parent/'mia-correction-v20/fresh-review-r2/review-evidence.json').read_text())
projections = {r['name']: r['projection'] for r in prior['renders']}
assert len(projections) == 19 and set(projections.values()) == {'ORTHO'}
assert not changed, changed
report = {'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
          'setup_sha256': hashlib.sha256(TARGET.read_bytes()).hexdigest(),
          'protected_models_compared': len(before), 'changed_models': changed,
          'checks': ['vertex coordinates', 'ordered loop indices', 'UV coordinates', 'all shape-key coordinates', 'object world matrices', 'parents'],
          'prior_19_fresh_render_projections': projections,
          'prior_proof_limit': 'This verifies the recorded last19 saved-camera renders; it does not retrospectively certify every historical viewport screenshot.',
          'viewport_observation': 'Actual live view was PERSP50 with orbit targetY2.087344m; setup uses head-centred ORTHO and preserves model origins.',
          'art_acceptance': 'NOT_EVALUATED'}
(ROOT/'camera-audit.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('CAMERA_AUDIT', json.dumps(report))
