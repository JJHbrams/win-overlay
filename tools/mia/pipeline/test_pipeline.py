"""Behavioral checks in tiny isolated fixtures; never edits production assets."""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest
import zlib

import mia_pipeline as pipeline
import hooks


def png(path, width=2, height=3):
    def chunk(kind, body):
        return struct.pack('>I', len(body)) + kind + body + struct.pack('>I', zlib.crc32(kind + body))
    raw = (b'\0' + b'\x80\x80\x80' * width) * height
    path.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
                     + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))


class PipelineTest(unittest.TestCase):
    def setUp(self):
        cache = Path(__file__).resolve().parents[3] / '.mia-cache/mia-pipeline-tests'
        cache.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='case-', dir=cache)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        assert self.root.parent == cache.resolve()
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True, capture_output=True)
        (self.root / pipeline.STATE).parent.mkdir(parents=True)
        pipeline.atomic_json(self.root / pipeline.STATE, {
            'canonical_worktree': str(self.root), 'character_complete': False, 'art_approved': False,
            'selected_static_wip': {'path': 'baseline.blend', 'sha256': 'fixture-only'},
            'read_first': ['WORKING_PROTOCOL.md'],
            'stage_status': {'face_head_art': 'accepted face: preserve'},
            'in_progress_v003': {'review12_status': 'upper-body pilot; unfinished',
                                 'proportion_H_contract': 'active-plan.md'},
        })
        skill = self.root / '.agents/skills/mia-reference-modeling/SKILL.md'
        skill.parent.mkdir(parents=True)
        skill.write_text('test routing marker', encoding='utf-8')
        self.native = self.root / 'baseline.blend'
        self.native.write_bytes(b'UNIT TEST placeholder, not a Blender scene')
        self.source = self.root / 'source.png'
        png(self.source)
        frames = []
        for name in ['front', 'profile', 'back', 'oblique']:
            path = self.root / (name + '.png')
            png(path)
            frames.append({'name': name, 'path': str(path), 'sha256': pipeline.sha256(path),
                           'hair': False, 'fixture': {
                               'projection': 'ORTHO', 'ortho_scale': 1.9,
                               'camera_matrix': [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
                               'resolution': [2, 3], 'pixel_aspect': [1, 1], 'shift': [0, 0],
                               'clip': [.1, 10], 'frame': 1, 'active_shape_keys': {},
                               'color_management': {'view_transform': 'Standard'},
                               'lights': [], 'world': {}, 'pose_sha256': 'test-pose',
                           }})
        self.capture = self.root / 'capture.json'
        self.data = {'native': {'path': str(self.native), 'sha256': pipeline.sha256(self.native)},
                     'shader': 'test shader', 'frames': frames}
        pipeline.atomic_json(self.capture, self.data)

    def inspect(self, candidate=None, views=None):
        return pipeline.inspect(self.root, self.capture, candidate, [str(self.source)],
                                views or ['front', 'profile', 'back', 'oblique'])

    def test_existing_baseline_is_integrity_only(self):
        result = self.inspect()
        self.assertTrue(result['evidence_integrity_valid'])
        self.assertFalse(result['paired_capture_checked'])
        self.assertFalse(result['source_art_reviewed'])
        self.assertEqual(result['art_acceptance'], 'NOT_EVALUATED')

    def test_identical_pair_does_not_mean_improvement(self):
        result = self.inspect(self.capture)
        self.assertTrue(result['paired_capture_checked'])
        self.assertEqual(result['art_acceptance'], 'NOT_EVALUATED')

    def test_stale_native_and_png_rejected(self):
        self.native.write_bytes(b'changed geometry')
        (self.root / 'front.png').write_bytes(b'not an image')
        result = self.inspect()
        self.assertFalse(result['evidence_integrity_valid'])
        self.assertIn('native: stale hash', result['errors'])
        self.assertTrue(any('not a PNG' in x for x in result['errors']))

    def test_missing_diagnostic_views_rejected(self):
        result = self.inspect(views=['front', 'profile', 'back', 'oblique', 'high', 'low'])
        self.assertFalse(result['evidence_integrity_valid'])
        self.assertEqual(sum('missing required view' in x for x in result['errors']), 2)

    def test_duplicate_view_rejected(self):
        self.data['frames'].append(copy.deepcopy(self.data['frames'][0]))
        pipeline.atomic_json(self.capture, self.data)
        self.assertFalse(self.inspect()['evidence_integrity_valid'])

    def test_changed_fixture_and_visibility_rejected(self):
        candidate = self.root / 'candidate.json'
        data = copy.deepcopy(self.data)
        data['frames'][0]['fixture']['camera_matrix'][0][3] = .3
        data['frames'][1]['hair'] = True
        pipeline.atomic_json(candidate, data)
        result = self.inspect(candidate)
        self.assertTrue(any('camera, pose, light or display mismatch' in x for x in result['errors']))
        self.assertTrue(any('hair visibility mismatch' in x for x in result['errors']))

    def test_resolution_and_clip_rejected(self):
        self.data['frames'][0]['fixture']['resolution'] = [4, 3]
        self.data['frames'][1]['fixture']['clip'] = [10, .1]
        pipeline.atomic_json(self.capture, self.data)
        self.assertFalse(self.inspect()['evidence_integrity_valid'])

    def test_changed_shader_rejected(self):
        candidate = self.root / 'candidate.json'
        data = copy.deepcopy(self.data)
        data['shader'] = 'different material mode'
        pipeline.atomic_json(candidate, data)
        self.assertIn('before/after declared shader mode missing or different', self.inspect(candidate)['errors'])

    def test_receipt_revalidation_detects_drift(self):
        output = self.root / pipeline.CACHE / 'review.json'
        result = self.inspect()
        pipeline.atomic_json(output, result)
        pipeline.activate(self.root, output, result)
        self.assertEqual(pipeline.advisory(self.root)['state'], 'FRESH_BY_STAT_ONLY')
        self.native.write_bytes(b'new model after review')
        self.assertEqual(pipeline.advisory(self.root)['state'], 'STALE')
        output.write_text('{}', encoding='utf-8')
        self.assertEqual(pipeline.advisory(self.root)['state'], 'RECEIPT_CHANGED')

    def test_invalid_or_external_activation_rejected(self):
        with self.assertRaises(ValueError):
            pipeline.activate(self.root, self.root / 'outside.json', {'evidence_integrity_valid': True})
        with self.assertRaises(ValueError):
            pipeline.activate(self.root, self.root / pipeline.CACHE / 'review.json', {'evidence_integrity_valid': False})
        self.assertFalse((self.root / pipeline.CACHE / 'active-review.json').exists())

    def test_cli_cannot_write_outside_cache_or_overwrite_input(self):
        output = self.root / 'forbidden.json'
        args = ['inspect', '--root', str(self.root), '--capture', str(self.capture),
                '--source', str(self.source), '--views', 'front', '--output', str(output)]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(pipeline.main(args), 2)
        self.assertFalse(output.exists())
        self.assertTrue(self.inspect()['evidence_integrity_valid'])

    def test_hooks_only_read_and_never_block_or_continue(self):
        output = self.root / pipeline.CACHE / 'review.json'
        report = self.inspect()
        pipeline.atomic_json(output, report)
        pipeline.activate(self.root, output, report)
        before = {p: pipeline.sha256(p) for p in self.root.rglob('*') if p.is_file()}
        for name in ['SessionStart', 'PostCompact', 'Stop']:
            result = hooks.respond({'cwd': str(self.root), 'hook_event_name': name})
            self.assertNotIn('decision', result)
            self.assertNotIn('continue', result)
            if name != 'Stop':
                text = result['hookSpecificOutput']['additionalContext']
                self.assertIn('accepted face: preserve', text)
                self.assertIn('upper-body pilot', text)
                self.assertLessEqual(len(text), 3800)
        after = {p: pipeline.sha256(p) for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before, after)

    def test_hooks_ignore_non_mia_and_bad_inputs(self):
        self.assertEqual(hooks.respond({}), {})
        self.assertEqual(hooks.respond({'cwd': str(self.root), 'hook_event_name': 'SessionStart'}), {})
        (self.root / pipeline.STATE).unlink()
        self.assertEqual(hooks.respond({'cwd': str(self.root), 'hook_event_name': 'SessionStart'}), {})

    def test_deactivate_only_removes_pilot_pointer(self):
        output = self.root / pipeline.CACHE / 'review.json'
        report = self.inspect()
        pipeline.atomic_json(output, report)
        pipeline.activate(self.root, output, report)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(pipeline.main(['deactivate', '--root', str(self.root)]), 0)
        self.assertTrue(output.is_file())
        self.assertEqual(hooks.respond({'cwd': str(self.root), 'hook_event_name': 'SessionStart'}), {})

    def test_hook_command_runs_on_windows_from_subdirectory(self):
        # Execute the exact configured command, not a substitute direct call.
        if os.name != 'nt':
            self.skipTest('Windows shell-specific check')
        destination = self.root / 'tools/mia/pipeline'
        destination.mkdir(parents=True)
        for name in ['hooks.py', 'mia_pipeline.py']:
            shutil.copyfile(Path(__file__).parent / name, destination / name)
        output = self.root / pipeline.CACHE / 'review.json'
        report = self.inspect()
        pipeline.atomic_json(output, report)
        pipeline.activate(self.root, output, report)
        config = pipeline.read_json(Path(__file__).resolve().parents[3] / '.codex/hooks.json')
        command = config['hooks']['SessionStart'][0]['hooks'][0]['command']
        before = {p: pipeline.sha256(p) for p in self.root.rglob('*') if p.is_file()}
        result = subprocess.run(['powershell', '-NoProfile', '-Command', command],
                                cwd=destination, input=json.dumps({'cwd': str(destination),
                                'hook_event_name': 'SessionStart'}).encode('utf-8'),
                                capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
        response = json.loads(result.stdout.decode('utf-8-sig'))
        self.assertEqual(response['hookSpecificOutput']['hookEventName'], 'SessionStart')
        after = {p: pipeline.sha256(p) for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before, after)


if __name__ == '__main__':
    unittest.main()
