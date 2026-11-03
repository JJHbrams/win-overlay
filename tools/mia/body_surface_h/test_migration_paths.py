"""Small path-only checks; no field solve, asset load, Blender or map bake."""
from pathlib import Path
import ast
import hashlib
import importlib.util
import json
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).with_name('h_surface.py')
SPEC = importlib.util.spec_from_file_location('h_surface_paths_test', SOURCE)
SURFACE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SURFACE)


class MigrationPaths(unittest.TestCase):
    def test_all_body_defaults_follow_their_source_worktree(self):
        roots = {
            'body_surface_h/h_surface.py': 'CANONICAL',
            'body_surface_h/profile_contour.py': 'CANONICAL',
            'body_fit_h/build_mesh.py': 'C',
            'body_fit_h/field_numpy.py': 'DEFAULT_CANONICAL',
            'body_fit_h/ram_fit.py': 'CANONICAL',
            'body_fit_h/roof_fit.py': 'C',
            'body_fit_h/finalize_guide.py': 'C',
            'body_fit_h/diagnose_halo.py': 'C',
            'body_fit_h/pose_floor_bounds.py': 'C',
            'body_fit_h/window_diagnostic.py': 'C',
            'body_fit_h/competitor_floor.py': 'DEFAULT',
        }
        for relative, name in roots.items():
            with self.subTest(source=relative):
                source = ROOT/'tools/mia'/relative
                tree = ast.parse(source.read_text(encoding='utf8'))
                assignment = next(node for node in tree.body
                                  if isinstance(node, ast.Assign)
                                  and any(isinstance(target, ast.Name) and target.id == name
                                          for target in node.targets))
                # Evaluate only the path expression; the tools themselves may
                # import Blender or heavy frozen inputs at module import time.
                value = eval(compile(ast.Expression(assignment.value), str(source), 'eval'),
                             {'Path': Path, '__file__': str(source)})
                self.assertEqual(value, ROOT)

    def setUp(self):
        folder = ROOT/'.mia-cache/path-tests'
        folder.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=folder)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.base = self.root/SURFACE.ASSEMBLY
        self.base.mkdir(parents=True)
        self.records = {}
        for role, suffix in [('geometry', 'geometry.npz'), ('surface', 'atlas/surface.npz'),
                             ('atlas', 'atlas/atlas.npz')]:
            path = self.base/suffix
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(('fixture '+role).encode())
            self.records[role] = dict(path=str(path), sha256=SURFACE.sha(path))
        self.selection = self.root/'.mia-cache/body-h/selected-candidate.json'

    def write_selection(self, records):
        data = json.dumps(records).encode()
        self.selection.write_bytes(data)
        return hashlib.sha256(data).hexdigest()

    def test_frozen_legacy_selection_binds_local_paths_without_rewrite(self):
        records = json.loads(json.dumps(self.records))
        for item in records.values():
            suffix = Path(item['path']).relative_to(self.root).as_posix()
            item['path'] = 'D:/MiaWorkCache/mia-reference-work/win-overlay/'+suffix
        digest = self.write_selection(records)
        result, receipt = SURFACE.target_paths(self.root)
        self.assertEqual(SURFACE.sha(self.selection), digest)
        self.assertEqual(receipt, dict(path=str(self.selection), sha256=digest))
        for role, record in self.records.items():
            self.assertEqual(result[role], Path(record['path']))
            self.assertTrue(result[role].is_relative_to(self.base))

    def test_selection_keeps_cache_and_hash_guards(self):
        for failure in ['hash', 'outside', 'relative', 'unknown_root']:
            with self.subTest(failure=failure):
                records = json.loads(json.dumps(self.records))
                if failure == 'hash':
                    records['geometry']['sha256'] = '0'*64
                elif failure == 'outside':
                    records['geometry']['path'] = str(self.root/'outside.npz')
                elif failure == 'relative':
                    records['geometry']['path'] = 'geometry.npz'
                else:
                    records['geometry']['path'] = 'D:/MiaWorkCache/unknown/geometry.npz'
                digest = self.write_selection(records)
                with self.assertRaises(ValueError):
                    SURFACE.target_paths(self.root)
                self.assertEqual(SURFACE.sha(self.selection), digest)

    def test_new_binding_paths_remain_in_current_worktree(self):
        self.write_selection(self.records)
        result, receipt = SURFACE.target_paths(self.root)
        for role in ['geometry', 'surface', 'atlas']:
            self.assertEqual(result[role], Path(self.records[role]['path']))
        self.assertTrue(Path(receipt['path']).is_relative_to(self.root))


if __name__ == '__main__':
    unittest.main()
