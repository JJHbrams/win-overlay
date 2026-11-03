"""Read-only capacity gate for this Mia body review; never deletes or moves files."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys

GIB = 1024 ** 3
TASK_ROOT = Path('D:/MiaWorkCache/mia-reference-work')
RELATIVE = Path('asset/mia/blender/mia-fit-v003/body')
MIN_FREE = {'C:/': 20 * GIB, 'D:/': 20 * GIB}
OUTPUT_LIMIT = 2 * GIB


def measured_bytes(root):
    total = 0
    files = 0
    if not root.exists():
        return total, files
    pending = [root]
    while pending:
        with os.scandir(pending.pop()) as entries:
            for entry in entries:
                stat = entry.stat(follow_symlinks=False)
                if entry.is_symlink() or getattr(stat, 'st_file_attributes', 0) & 0x400:
                    raise RuntimeError(f'Reparse path inside measured output: {entry.path}')
                if entry.is_dir(follow_symlinks=False):
                    pending.append(entry.path)
                elif entry.is_file(follow_symlinks=False):
                    total += stat.st_size
                    files += 1
    return total, files


def inspect(reserve_bytes):
    if reserve_bytes < 0:
        raise ValueError('Reservation must be nonnegative')
    outputs = []
    roots = []
    for workspace in ('win-overlay', 'surface12-producer', 'appearance12-producer'):
        for component in ('surface-review12', 'surface-appearance12'):
            roots.append(TASK_ROOT / workspace / RELATIVE / component)
    roots.extend([
        TASK_ROOT / 'win-overlay/asset/mia/blender/mia-fit-v003/integration/surface12-presentation',
        TASK_ROOT / 'win-overlay/.mia-cache',
        TASK_ROOT / 'runtime-temp',
    ])
    for path in roots:
        count_bytes, count_files = measured_bytes(path)
        outputs.append({'path': str(path), 'bytes': count_bytes, 'files': count_files})
    capacity = {drive: shutil.disk_usage(drive).free for drive in MIN_FREE}
    violations = [f'{drive} below 20 GiB free plus reservation'
                  for drive, floor in MIN_FREE.items()
                  if capacity[drive] < floor + (reserve_bytes if drive == 'D:/' else 0)]
    total = sum(row['bytes'] for row in outputs)
    if total + reserve_bytes > OUTPUT_LIMIT:
        violations.append('Review12 component outputs plus reservation exceed 2 GiB')
    return {'status': 'BLOCKED' if violations else 'CAPACITY_OK',
            'meaning': 'Capacity only; no cleanup or model/art approval.',
            'coordination': 'Root grants only one heavy writer; this estimate is not an atomic reservation.',
            'reserve_bytes': reserve_bytes, 'free_bytes': capacity,
            'component_bytes': total, 'component_limit_bytes': OUTPUT_LIMIT,
            'outputs': outputs, 'violations': violations}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reserve-mib', type=int, required=True)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    if args.reserve_mib < 0:
        parser.error('Reservation must be nonnegative')
    result = inspect(args.reserve_mib * 1024 ** 2)
    text = json.dumps(result, indent=2)
    if args.report:
        destination = args.report.resolve()
        allowed = TASK_ROOT / 'win-overlay/asset/mia/blender/mia-fit-v003/integration'
        if not destination.is_relative_to(allowed.resolve()):
            parser.error('Report must remain inside canonical Mia integration evidence')
        destination.write_text(text + '\n', encoding='utf8')
    print(text)
    return 2 if result['violations'] else 0


if __name__ == '__main__':
    sys.exit(main())
