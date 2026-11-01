"""Validate source-art review evidence. Never grants art acceptance."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def validate(path):
    path = Path(path).resolve()
    data = json.loads(path.read_text(encoding='utf-8-sig'))
    errors, checked = [], []

    def fail(message):
        errors.append(message)

    def artifact(item, label):
        if not isinstance(item, dict) or not item.get('path') or not item.get('sha256'):
            fail(label + ': path and sha256 required')
            return
        target = Path(item['path'])
        if not target.is_absolute():
            target = path.parent / target
        if not target.is_file():
            fail(label + ': missing ' + str(target))
            return
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual != item['sha256'].lower():
            fail(label + ': stale hash')
        checked.append({'role': label, 'path': str(target.resolve()), 'sha256': actual})

    if data.get('schema_version') != 1:
        fail('schema_version must be 1')
    for key in ('baseline_native', 'candidate_native'):
        artifact(data.get(key), key)
    required = data.get('required_views', [])
    if not isinstance(required, list) or not required:
        fail('nonempty required_views required')
        required = []
    rows = data.get('views', [])
    if not isinstance(rows, list):
        fail('views must be a list')
        rows = []
    seen = set()
    fields = ('projection', 'matrix', 'frame', 'active_shape_keys',
              'lighting', 'color_management', 'resolution', 'pixel_aspect', 'lens_shift')
    for row in rows:
        name = row.get('id', '')
        if not name or name in seen:
            fail('each view requires a unique id')
        seen.add(name)
        for role in ('reference', 'baseline_render', 'candidate_render', 'comparison_board'):
            artifact(row.get(role), name + '/' + role)
        ref = row.get('reference', {})
        crop = ref.get('crop_xyxy')
        if not isinstance(crop, list) or len(crop) != 4 or crop[2] <= crop[0] or crop[3] <= crop[1]:
            fail(name + ': reference crop_xyxy required')
        for role in ('baseline_camera', 'candidate_camera'):
            camera = row.get(role, {})
            if any(key not in camera for key in fields):
                fail(name + '/' + role + ': incomplete camera/pose/light/display record')
            if camera.get('projection') == 'ORTHO' and not camera.get('ortho_scale'):
                fail(name + '/' + role + ': ortho_scale required')
            elif camera.get('projection') == 'PERSP' and not camera.get('lens'):
                fail(name + '/' + role + ': lens required')
        if row.get('baseline_camera') != row.get('candidate_camera'):
            fail(name + ': baseline/candidate camera, pose, light or display mismatch')
        for role in ('reference_registration', 'baseline_registration', 'candidate_registration'):
            reg = row.get(role, {})
            scale = reg.get('uniform_scale')
            if not isinstance(scale, (float, int)) or isinstance(scale, bool) or not math.isfinite(scale) or scale <= 0:
                fail(name + '/' + role + ': positive scalar uniform_scale required')
            if not isinstance(reg.get('translation_xy'), list) or len(reg['translation_xy']) != 2:
                fail(name + '/' + role + ': translation_xy required')
            if not isinstance(reg.get('rotation_degrees'), (float, int)):
                fail(name + '/' + role + ': rotation_degrees required')
            if set(reg) - {'uniform_scale', 'translation_xy', 'rotation_degrees', 'normalization_basis', 'notes'}:
                fail(name + '/' + role + ': unsupported registration fields; no per-feature or anisotropic warp')
            if not reg.get('normalization_basis'):
                fail(name + '/' + role + ': normalization basis and excluded measurement required')
        for key in ('pose_uncertainty', 'observed_differences', 'unresolved', 'material_mode'):
            if key not in row or row[key] is None or row[key] == '':
                fail(name + ': ' + key + ' required')
    missing = sorted(set(required) - seen)
    if missing:
        fail('missing required source views: ' + ', '.join(missing))
    if data.get('part') in ('face', 'head', 'body', 'surface'):
        expected = {'front', 'profile', 'back', 'oblique'} if data['part'] == 'body' else {'front', 'profile', 'left_oblique', 'right_oblique'}
        if not expected.issubset(set(required)):
            fail('required_views omits mandatory ' + data['part'] + ' coverage')
    else:
        fail('part must be face, head, body or surface')
    return {'evidence_valid': not errors, 'art_acceptance': 'NOT_EVALUATED',
            'package': str(path), 'checked_artifacts': checked, 'errors': errors,
            'limits': 'Hashes and declared coverage are checked; actual image correspondence and likeness need independent visual review.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('package')
    p.add_argument('--report')
    a = p.parse_args()
    result = validate(a.package)
    if a.report:
        Path(a.report).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'evidence_valid': result['evidence_valid'], 'art_acceptance': result['art_acceptance'], 'errors': result['errors']}, ensure_ascii=False))
    raise SystemExit(0 if result['evidence_valid'] else 1)
