"""Small, read-only evidence adapters for Mia; never judges or promotes art."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import runpy
import struct
import sys
import tempfile

_path_spec = importlib.util.spec_from_file_location(
    'mia_review_input_paths', Path(__file__).resolve().parents[1]/'review_h/paths.py')
_paths = importlib.util.module_from_spec(_path_spec)
_path_spec.loader.exec_module(_paths)

CACHE = Path('.mia-cache/mia-pipeline')
STATE = Path('asset/mia/CURRENT_STATE.json')
FIXTURE_FIELDS = {
    'projection', 'camera_matrix', 'resolution', 'pixel_aspect', 'shift',
    'clip', 'frame', 'active_shape_keys', 'color_management', 'lights',
    'world', 'pose_sha256',
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def resolve(root: Path, value: str | Path) -> Path:
    return _paths.migrated_path(value, root=root).resolve()


def atomic_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write('\n')
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def png_size(path: Path) -> tuple[int, int]:
    with path.open('rb') as stream:
        header = stream.read(24)
    if len(header) != 24 or header[:8] != b'\x89PNG\r\n\x1a\n' or header[12:16] != b'IHDR':
        raise ValueError('not a PNG with IHDR')
    size = struct.unpack('>II', header[16:24])
    if min(size) <= 0:
        raise ValueError('nonpositive PNG dimensions')
    return size


def context(root: Path) -> dict:
    data = read_json(root / STATE)
    progress = data.get('in_progress_v003', {})
    paths = list(data.get('read_first', []))
    stage_plans = {key: value for key, value in progress.items()
                   if 'contract' in key or ('plan' in key and isinstance(value, str))}
    return {
        'canonical_worktree': data.get('canonical_worktree', str(root)),
        'selected_static_wip': data.get('selected_static_wip', data.get('active_working_correction')),
        'active_live_checkpoint': data.get('active_live_checkpoint'),
        'character_complete': data.get('character_complete', False),
        'art_approved': data.get('art_approved', False),
        'read_first': paths,
        'reference_roles': data.get('reference_roles', {}),
        'stage_plan_index': stage_plans,
        'active_body_status': progress.get('review12_status', data.get('stage_status', {}).get('body_art')),
        'face_status': data.get('stage_status', {}).get('face_head_art'),
        'skill': '.agents/skills/mia-reference-modeling/SKILL.md',
        'limits': 'Read current documents/images. The plan index includes history; do not choose an active plan '
                  'from its version name alone. This is not approval or a scene inspection.',
    }


def inspect_capture(root: Path, capture_path: str | Path, views: list[str]) -> dict:
    path = resolve(root, capture_path)
    data = read_json(path)
    if not isinstance(data, dict):
        raise ValueError('capture must be an object')
    errors, artifacts = [], []

    def artifact(item, label, image=False):
        if not isinstance(item, dict) or not item.get('path') or not item.get('sha256'):
            errors.append(f'{label}: path and sha256 required')
            return None
        target = resolve(root, item['path'])
        if not target.is_file():
            errors.append(f'{label}: missing file {target}')
            return None
        digest = sha256(target)
        if digest != str(item['sha256']).lower():
            errors.append(f'{label}: stale hash')
        stat = target.stat()
        record = {'role': label, 'path': str(target), 'sha256': digest,
                  'size': stat.st_size, 'mtime_ns': stat.st_mtime_ns}
        if image:
            try:
                record['dimensions'] = list(png_size(target))
            except ValueError as exc:
                errors.append(f'{label}: {exc}')
        artifacts.append(record)
        return record

    capture_stat = path.stat()
    artifacts.append({'role': 'capture', 'path': str(path), 'sha256': sha256(path),
                      'size': capture_stat.st_size, 'mtime_ns': capture_stat.st_mtime_ns})
    artifact(data.get('native'), 'native')
    frames = data.get('frames', [])
    if not isinstance(frames, list) or not frames:
        raise ValueError('capture.frames must be a nonempty list')
    by_name = {}
    for row in frames:
        if not isinstance(row, dict):
            errors.append('frame must be an object')
            continue
        name = row.get('name')
        if not isinstance(name, str) or not name or name in by_name:
            errors.append('frame names must be unique nonempty strings')
            continue
        by_name[name] = row
        record = artifact(row, name, image=True)
        fixture = row.get('fixture', {})
        if not isinstance(fixture, dict):
            errors.append(f'{name}: fixture must be an object')
            continue
        missing = sorted(FIXTURE_FIELDS - set(fixture))
        if missing:
            errors.append(f'{name}: missing fixture fields {missing}')
        resolution = fixture.get('resolution')
        if record and record.get('dimensions') != resolution:
            errors.append(f'{name}: PNG dimensions do not equal recorded resolution')
        clip = fixture.get('clip')
        if not (isinstance(clip, list) and len(clip) == 2
                and all(isinstance(x, (int, float)) and not isinstance(x, bool)
                        and math.isfinite(x) for x in clip) and 0 < clip[0] < clip[1]):
            errors.append(f'{name}: invalid camera clipping range')
        projection = fixture.get('projection')
        dimension = fixture.get('ortho_scale') if projection == 'ORTHO' else fixture.get('lens')
        if projection not in ('ORTHO', 'PERSP') or not isinstance(dimension, (int, float)) or dimension <= 0:
            errors.append(f'{name}: projection and positive scale/lens required')
    for name in views:
        if name not in by_name:
            errors.append(f'missing required view: {name}')
    return {'capture': str(path), 'capture_integrity_valid': not errors,
            'declared_views': list(by_name), 'errors': errors,
            'watched_files': artifacts, '_frames': by_name, '_shader': data.get('shader')}


def inspect(root: Path, baseline: str | Path, candidate: str | Path | None,
            sources: list[str], views: list[str]) -> dict:
    if not views or any(not name for name in views) or len(views) != len(set(views)):
        raise ValueError('declare unique required views for this stage')
    base = inspect_capture(root, baseline, views)
    after = inspect_capture(root, candidate, views) if candidate else None
    errors = list(base['errors'])
    watched = list(base['watched_files'])
    if after:
        errors += ['candidate: ' + x for x in after['errors']]
        watched += after['watched_files']
        for name in views:
            before_frame, after_frame = base['_frames'].get(name), after['_frames'].get(name)
            if before_frame and after_frame:
                if before_frame['fixture'] != after_frame['fixture']:
                    errors.append(f'{name}: before/after camera, pose, light or display mismatch')
                if before_frame.get('hair') != after_frame.get('hair'):
                    errors.append(f'{name}: before/after hair visibility mismatch')
        if base['_shader'] is None or base['_shader'] != after['_shader']:
            errors.append('before/after declared shader mode missing or different')
    source_records = []
    for name in sources:
        path = resolve(root, name)
        size = png_size(path)
        stat = path.stat()
        record = {'role': 'source', 'path': str(path), 'sha256': sha256(path),
                  'dimensions': list(size), 'size': stat.st_size, 'mtime_ns': stat.st_mtime_ns}
        watched.append(record)
        source_records.append(record)
    if not sources:
        errors.append('at least one original source PNG must be identified')
    for record in (base, after):
        if record:
            record.pop('_frames')
            record.pop('_shader')
    return {
        'schema_version': 1, 'kind': 'mia-capture-advisory',
        'stage': 'paired_capture' if after else 'baseline_capture',
        'evidence_integrity_valid': not errors,
        'paired_capture_checked': bool(after) and not errors,
        'source_art_reviewed': False, 'art_acceptance': 'NOT_EVALUATED',
        'required_views': views, 'sources': source_records,
        'baseline': base, 'candidate': after, 'errors': errors,
        'watched_files': watched,
        'limits': 'Checks recorded files/hashes/dimensions and declared fixtures only. '
                  'Does not inspect Blender/live state, image content, source registration, '
                  'likeness, shader ancestry, anatomy or deformation; no promotion is performed. '
                  'Use the existing source-review gate and visual review before adoption.',
    }


def reference_review(root: Path, package: str | Path) -> dict:
    validator = root / 'asset/mia/blender/mia-reference-finish-v22/validate_reference_review.py'
    if not validator.is_file():
        raise ValueError('existing source-review validator not found in requested root')
    result = runpy.run_path(str(validator))['validate'](resolve(root, package))
    result['validator'] = {'path': str(validator), 'sha256': sha256(validator)}
    return result


def activate(root: Path, output: Path, report: dict):
    if not report.get('evidence_integrity_valid'):
        raise ValueError('invalid evidence cannot be activated')
    cache = (root / CACHE).resolve()
    if not output.resolve().is_relative_to(cache):
        raise ValueError('active receipt must be inside this root\'s ignored pipeline cache')
    atomic_json(cache / 'active-review.json', {'receipt': str(output.resolve()), 'sha256': sha256(output)})


def advisory(root: Path) -> dict:
    pointer = root / CACHE / 'active-review.json'
    if not pointer.is_file():
        return {}
    data = read_json(pointer)
    receipt_path = resolve(root, data['receipt'])
    if not receipt_path.is_relative_to((root / CACHE).resolve()):
        raise ValueError('receipt escaped the project pipeline cache')
    if sha256(receipt_path) != data.get('sha256'):
        return {'state': 'RECEIPT_CHANGED', 'art_acceptance': 'NOT_EVALUATED'}
    receipt = read_json(receipt_path)
    changed = []
    for item in receipt.get('watched_files', []):
        path = Path(item['path'])
        if not path.is_file():
            changed.append({'role': item['role'], 'path': str(path), 'reason': 'missing'})
            continue
        stat = path.stat()
        if stat.st_size != item['size'] or stat.st_mtime_ns != item['mtime_ns']:
            changed.append({'role': item['role'], 'path': str(path), 'reason': 'size/mtime changed'})
    return {'state': 'STALE' if changed else 'FRESH_BY_STAT_ONLY', 'changed': changed,
            'stage': receipt.get('stage'), 'art_acceptance': 'NOT_EVALUATED',
            'limits': 'Fast advisory, not a cryptographic recheck or source/visual approval. '
                      'In-memory edits and unlisted dependencies require a new actual capture.'}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('context', 'inspect', 'reference-review', 'deactivate'):
        child = sub.add_parser(name)
        child.add_argument('--root', type=Path, required=True)
        if name == 'inspect':
            child.add_argument('--capture', required=True)
            child.add_argument('--candidate')
            child.add_argument('--source', action='append', default=[])
            child.add_argument('--views', required=True)
            child.add_argument('--output', type=Path)
            child.add_argument('--activate', action='store_true')
        elif name == 'reference-review':
            child.add_argument('--package', required=True)
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve()
        if args.command == 'context':
            result = context(root)
            ok = True
        elif args.command == 'deactivate':
            pointer = (root / CACHE / 'active-review.json').resolve()
            if not pointer.is_relative_to((root / CACHE).resolve()):
                raise ValueError('active pointer escaped the pipeline cache')
            pointer.unlink(missing_ok=True)
            result = {'pilot_hooks_enabled': False, 'models_modified': False}
            ok = True
        elif args.command == 'reference-review':
            result = reference_review(root, args.package)
            ok = result['evidence_valid']
        else:
            if args.activate and not args.output:
                raise ValueError('--activate requires --output')
            result = inspect(root, args.capture, args.candidate, args.source,
                             [x.strip() for x in args.views.split(',')])
            ok = result['evidence_integrity_valid']
            if args.output:
                output = resolve(root, args.output)
                if not output.is_relative_to((root / CACHE).resolve()):
                    raise ValueError('outputs must stay in this root\'s ignored pipeline cache')
                input_paths = {Path(x['path']).resolve() for x in result['watched_files']}
                if output in input_paths or output.name == 'active-review.json':
                    raise ValueError('receipt must not overwrite an input or active pointer')
                atomic_json(output, result)
                if args.activate:
                    activate(root, output, result)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        return 0 if ok else 1
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({'evidence_integrity_valid': False, 'art_acceptance': 'NOT_EVALUATED',
                          'error': str(exc)}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    raise SystemExit(main())
