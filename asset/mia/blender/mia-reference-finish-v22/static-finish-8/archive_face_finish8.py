"""Freeze Face8 producer recipes/maps/diagnostics without altering artifact bytes."""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
SRC = Path('C:/Users/antio/.codex/worktrees/mia-final-face-v12/win-overlay/asset/mia/blender/mia-face-finish-v22/finish-8')
DEST = Path(__file__).resolve().parents[1] / 'parts/face-finish8-d/production'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    handoff = SRC / 'look-d/handoff/handoff-manifest.json'
    data = json.loads(handoff.read_text(encoding='utf-8-sig'))
    paths = {Path(r['path']) for r in data['recipes']}
    for folder in ('look-d/maps', 'look-d/uv-light-blink', 'look-d/color-only-corrected', 'look-d/handoff', 'shape-b/targeted'):
        paths.update(p for p in (SRC / folder).rglob('*') if p.is_file() and p.suffix in ('.json', '.png', '.exr', '.py', '.md'))
    rows = []
    for p in sorted(paths):
        rel = p.relative_to(SRC)
        target = DEST / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        assert not target.exists() or sha(target) == sha(p), f'Frozen artifact changed: {target}'
        shutil.copyfile(p, target)
        assert sha(target) == sha(p)
        rows.append({'original': str(p), 'path': rel.as_posix(), 'sha256': sha(target), 'bytes': target.stat().st_size})
    manifest = {'status': 'Frozen candidate evidence; ART unapproved', 'source_handoff_sha256': sha(handoff),
                'recipes': 'Exact producer recipe bytes; some original absolute dependency paths remain. Use archived native for viewing; integration recipe and exact delta replay are separately retained.',
                'map_note': 'Actual consumed maps are EXR. PNGs are inspection previews. Earlier mixed-lit color_only files superseded by color-only-corrected.',
                'artifacts': rows}
    (DEST / 'production-archive.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps({'files': len(rows), 'bytes': sum(r['bytes'] for r in rows), 'destination': str(DEST)}, indent=2))

if __name__ == '__main__':
    main()
