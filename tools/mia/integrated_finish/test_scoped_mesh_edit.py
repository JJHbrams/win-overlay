"""Scope integrity tests; no bpy import, model mutation, render or native file."""
from pathlib import Path
import runpy
import unittest
import numpy as np

API = runpy.run_path(str(Path(__file__).with_name('scoped_mesh_edit.py')))
validate = API['validate_delta']
ScopeError = API['ScopeError']


class ScopeTests(unittest.TestCase):
    def setUp(self):
        self.before = np.array([[0,0,0], [1,0,0], [0,1,0], [1,1,0]], np.float32)
        self.faces = np.array([[0,1,2], [1,3,2]], np.int32)
        self.candidate = self.before.copy(); self.candidate[3, 2] += .01

    def check(self, candidate=None, editable=(3,), transition=(), regions=None, **kw):
        return validate(self.before, self.candidate if candidate is None else candidate,
            self.faces, editable, transition, {'thorax': [0,1,2]} if regions is None else regions, **kw)

    def test_supported_arm_only_delta_and_original_unchanged(self):
        original = self.before.copy(); candidate = self.candidate.copy()
        result = self.check()
        self.assertEqual(result['changed_vertices'], 1)
        self.assertTrue(result['exact_outside_union'])
        np.testing.assert_array_equal(self.before, original)
        np.testing.assert_array_equal(self.candidate, candidate)

    def test_protected_vertex_one_e_minus_seven_rejected(self):
        bad = self.candidate.copy(); bad[0, 0] = np.float32(1.e-7)
        with self.assertRaises(ScopeError): self.check(bad)

    def test_unnamed_outside_id_overwrite_rejected(self):
        bad = self.candidate.copy(); bad[2, 2] = .1
        with self.assertRaises(ScopeError): self.check(bad, regions={'thorax': [0,1]})

    def test_signed_zero_is_exactly_held(self):
        bad = self.candidate.copy(); bad[0, 0] = np.float32(-0.)
        with self.assertRaises(ScopeError): self.check(bad)

    def test_stale_coordinate_and_topology_hashes(self):
        with self.assertRaises(ScopeError): self.check(expected_before_sha256='stale')
        with self.assertRaises(ScopeError): self.check(expected_topology_sha256='stale')

    def test_invalid_duplicate_float_and_out_of_range_ids(self):
        for values in ([3,3], [3.0], [-1], [4], [[3]]):
            with self.subTest(values=values), self.assertRaises(ScopeError): self.check(editable=values)

    def test_overlap_ids_rejected(self):
        with self.assertRaises(ScopeError): self.check(transition=[3])
        with self.assertRaises(ScopeError): self.check(regions={'thorax': [0,3]})

    def test_no_named_protection_or_bbox_only(self):
        with self.assertRaises(ScopeError): self.check(regions={})
        with self.assertRaises(ScopeError): self.check(regions={'thorax': {'bbox': [0,1]}})

    def test_unsupported_topology_or_vertex_count(self):
        with self.assertRaises(ScopeError): self.check(self.candidate[:-1])
        with self.assertRaises(ScopeError): validate(self.before, self.candidate, [self.faces,self.faces], [3], [], {'thorax':[0]})

    def test_retired_recipe_rejects_without_bpy(self):
        old = runpy.run_path(str(Path(__file__).with_name('arm_chain01_live.py')))
        for name, args in [('select', ()), ('apply', ('unused',))]:
            with self.subTest(name=name), self.assertRaisesRegex(RuntimeError, 'retired'):
                old[name](*args)


if __name__ == '__main__': unittest.main()
