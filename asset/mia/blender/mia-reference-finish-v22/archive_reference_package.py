"""Copy a frozen producer's evidence into the canonical repository with portable paths.

Original metadata is retained verbatim. Artifact bytes do not change; the portable
package only rewrites paths. Source art/baseline already in the repository are reused.
"""
import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path

from validate_reference_review import validate


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def archive(package, destination, repository, supplements=()):
    package = Path(package).resolve()
    destination = Path(destination).resolve()
    repository = Path(repository).resolve()
    original = validate(package)
    assert original['evidence_valid'], original['errors']
    assert not (destination/'reference-review.json').exists(), 'Frozen package cannot be overwritten'
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(package, destination/'original-reference-review.json')
    data = json.loads(package.read_text(encoding='utf-8-sig'))
    copied = {}

    def relocate(item, folder):
        old = Path(item['path'])
        old = (old if old.is_absolute() else package.parent/old).resolve()
        # Canonical source/baseline are already versioned; derived worktree assets are not.
        if old.is_relative_to(repository):
            new = old
        else:
            new = destination/folder/(item['sha256'][:12]+'-'+old.name)
            new.parent.mkdir(parents=True, exist_ok=True)
            if not new.exists():
                shutil.copyfile(old, new)
            assert digest(new) == item['sha256']
        item['path'] = Path(os.path.relpath(new, destination)).as_posix()
        copied[str(old)] = {'path': item['path'], 'sha256': item['sha256']}

    relocate(data['baseline_native'], 'native')
    relocate(data['candidate_native'], 'native')
    for row in data['views']:
        for role in ('reference', 'baseline_render', 'candidate_render', 'comparison_board'):
            relocate(row[role], 'references' if role == 'reference' else 'images')
        crop = row['reference'].get('crop_artifact')
        if crop:
            relocate(crop, 'references')
    for src in supplements:
        src = Path(src).resolve()
        target = destination/'supplements'/src.name
        target.parent.mkdir(parents=True, exist_ok=True)
        assert not target.exists() or digest(target) == digest(src), 'Supplement basename collision'
        shutil.copyfile(src, target)
        copied[str(src)] = {'path': Path(os.path.relpath(target, destination)).as_posix(), 'sha256': digest(target)}
    output = destination/'reference-review.json'
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    validation = validate(output)
    assert validation['evidence_valid'], validation['errors']
    (destination/'reference-review-validation.json').write_text(json.dumps(validation, indent=2), encoding='utf-8')
    manifest = {'original_package_sha256': digest(package), 'portable_package_sha256': digest(output),
                'source_files_unchanged': digest(package) == digest(destination/'original-reference-review.json'),
                'artifacts': copied, 'art_acceptance': 'NOT_INFERRED_FROM_ARCHIVE'}
    (destination/'archive-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return {'package': str(output), 'candidate_native': str((destination/data['candidate_native']['path']).resolve()),
            'candidate_sha256': data['candidate_native']['sha256'], 'validation': validation['evidence_valid']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('package')
    parser.add_argument('destination')
    parser.add_argument('--repository', required=True)
    parser.add_argument('--supplement', action='append', default=[])
    args = parser.parse_args()
    print(json.dumps(archive(args.package, args.destination, args.repository, args.supplement), indent=2))
