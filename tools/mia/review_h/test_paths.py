"""Migration path and MCP filename checks; no Blender connection or scene edit."""
from pathlib import Path
import ast
import hashlib
import json
import tempfile
from types import SimpleNamespace
import unittest

from paths import recorded_atlas, recorded_path


class MigrationPaths(unittest.TestCase):
    def setUp(self):
        folder = Path(__file__).resolve().parents[3]/'.mia-cache/path-tests'
        folder.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=folder)
        self.root = Path(self.temp.name).resolve()
        assert self.root.is_relative_to(folder.resolve())
        self.addCleanup(self.temp.cleanup)
        self.file = self.root/'.mia-cache/atlas.npz'
        self.file.parent.mkdir()
        self.file.write_bytes(b'known atlas bytes')
        self.sha = hashlib.sha256(self.file.read_bytes()).hexdigest()

    def test_legacy_windows_and_old_owner_are_local_and_hashed(self):
        for prefix in ['D:\\MiaWorkCache\\mia-reference-work\\win-overlay',
                       'D:/MiaWorkCache/mia-reference-work/face-live-author',
                       'C:/Users/antio/.codex/worktrees/mia-v002-body/win-overlay']:
            actual = recorded_path(prefix+'/.mia-cache/atlas.npz', root=self.root, expected_sha256=self.sha)
            self.assertEqual(actual, self.file)

    def test_missing_corrupt_and_escaping_input_fail_closed(self):
        with self.assertRaises(ValueError):
            recorded_path(self.file, root=self.root, expected_sha256='0'*64)
        with self.assertRaises(FileNotFoundError):
            recorded_path('.mia-cache/missing.npz', root=self.root)
        with self.assertRaises(ValueError):
            recorded_path('D:/MiaWorkCache/unknown/atlas.npz', root=self.root)
        with self.assertRaises(AssertionError):
            recorded_path('D:/MiaWorkCache/mia-reference-work/win-overlay/../escape', root=self.root)
        with self.assertRaises(AssertionError):
            recorded_path('../escape', root=self.root)

    def test_capture_hash_is_used_without_rewriting_receipt(self):
        old = 'D:/MiaWorkCache/mia-reference-work/win-overlay/.mia-cache/atlas.npz'
        receipt = self.root/'live-capture.json'
        receipt.write_text(json.dumps({'atlas': {'path': old, 'sha256': self.sha}}))
        original = receipt.read_bytes()
        self.assertEqual(recorded_atlas(self.root, {'atlas_path': old}, root=self.root), self.file)
        self.assertEqual(receipt.read_bytes(), original)
        self.file.write_bytes(b'wrong atlas')
        with self.assertRaises(ValueError):
            recorded_atlas(self.root, {'atlas_path': old}, root=self.root)

    def test_mcp_exec_filename_and_explicit_wrapper_phase(self):
        source = Path(__file__).with_name('lab_mcp.py')
        tree = ast.parse(source.read_text(encoding='utf8'))
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'code_arguments')
        namespace = {'Path': Path}
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), 'exec'), namespace)
        wrapper = self.root/'wrapper.py'
        wrapper.write_text("MIA_EDIT_PHASE = 'restore'\nresult = (__file__, MIA_EDIT_PHASE, MIA_VIEW_REQUEST)\n")
        args = SimpleNamespace(code_file=wrapper, phase='apply', view='high')
        code = namespace['code_arguments'](args)['code']
        result = {}
        exec(code, result)
        self.assertEqual(result['result'], (str(wrapper), 'restore', 'high'))


if __name__ == '__main__':
    unittest.main()
