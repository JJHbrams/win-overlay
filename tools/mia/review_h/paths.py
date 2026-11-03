"""Resolve frozen input locations after the one D-to-C worktree migration.

Receipts retain their original bytes and hashes. Only known former worktree
prefixes are remapped; this does not alias drives or rewrite historical data.
"""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
_LEGACY_ROOTS = (
    'D:/MiaWorkCache/mia-reference-work/win-overlay',
    'D:/MiaWorkCache/mia-reference-work/face-live-author',
    'D:/MiaWorkCache/mia-reference-work/body-connected-author',
    'D:/MiaWorkCache/mia-reference-work/eye-roi-author',
    'D:/MiaWorkCache/mia-reference-work/assembly-h-author',
    'D:/MiaWorkCache/mia-reference-work/shape-h-author',
    'D:/MiaWorkCache/mia-reference-work/surface-h-author',
    'D:/MiaWorkCache/mia-reference-work/pipeline-author',
    'C:/Users/antio/.codex/worktrees/mia-v002-body/win-overlay',
)


def migrated_path(value, *, root=ROOT):
    """Resolve only known migrated prefixes, including not-yet-created outputs."""
    root = Path(root).resolve()
    raw = str(value).replace('\\', '/')
    for prefix in _LEGACY_ROOTS:
        if raw.casefold().startswith(prefix.casefold()+'/'):
            path = (root/raw[len(prefix)+1:]).resolve()
            assert path.is_relative_to(root), 'Legacy input escapes the migrated worktree'
            break
    else:
        if raw.casefold().startswith('d:/miaworkcache/'):
            raise ValueError('Unknown former D input; classify its ownership before reading: '+raw)
        path = Path(raw)
        if not path.is_absolute():
            path = (root/path).resolve()
            assert path.is_relative_to(root), 'Relative input escapes the worktree'
    return path


def recorded_path(value, *, root=ROOT, expected_sha256=None):
    """Return a present local input and optionally verify its frozen file hash."""
    path = migrated_path(value, root=root)
    if not path.is_file():
        raise FileNotFoundError(path)
    if expected_sha256 is not None:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != expected_sha256:
            raise ValueError('Frozen input hash mismatch: '+str(path))
    return path


def recorded_atlas(assembly_dir, metadata, *, root=ROOT):
    """Prefer the immutable capture's hash when an assembly reuses an old atlas."""
    assembly_dir = Path(assembly_dir)
    value = metadata.get('atlas_path', assembly_dir/'atlas/atlas.npz')
    capture = assembly_dir/'live-capture.json'
    expected = None
    if capture.is_file():
        atlas = json.loads(capture.read_text(encoding='utf8'))['atlas']
        expected = atlas['sha256']
        assert recorded_path(atlas['path'], root=root, expected_sha256=expected).resolve() == recorded_path(value, root=root).resolve()
    return recorded_path(value, root=root, expected_sha256=expected)
