"""Combine reviewed Q9 geometry, E2 eye curves and M4 look in a new native.

This saves a working review checkpoint, not an art-approved final model.
"""
import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
import bpy

HERE = Path(__file__).resolve().parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


ap = argparse.ArgumentParser()
ap.add_argument('--source', required=True)
ap.add_argument('--source-sha', required=True)
ap.add_argument('--output-dir', required=True)
args = ap.parse_args(sys.argv[sys.argv.index('--')+1:])
source = Path(args.source).resolve()
out = Path(args.output_dir).resolve()
assert sha(source) == args.source_sha
assert not out.exists(), 'Preserve previous review'
out.mkdir(parents=True)
eye_path = HERE/'eye-identity-work/build_eye_contour.py'
look_path = HERE/'material-work/apply_material_identity.py'
eye = module('mia_review9_eye', eye_path)
look = module('mia_review9_look', look_path)
bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
before = eye.snapshot()
eye_report, deltas = eye.apply_eye_contour('e2')
after_eye = eye.snapshot()
allowed = {'MIA_V14_SculptedSkin', 'MIA_V14_UpperLash_-1', 'MIA_V14_UpperLash_1',
           'MIA_V14_OuterWing_-1', 'MIA_V14_OuterWing_1'}
for name, row in before.items():
    if name not in allowed:
        assert after_eye[name] == row, name
    else:
        for key in ('uv','topology','materials','matrix'):
            assert after_eye[name][key] == row[key], (name, key)
geometry_before_look = look.snapshots()
skin = bpy.data.objects['MIA_V14_SculptedSkin']
material = look.apply_identity(skin, 'm4')
material_name = material.name if material else 'MIA_FaceAnatomy9_Identity_m4'
assert look.snapshots() == geometry_before_look
for obj in bpy.data.objects:
    if obj.type == 'MESH' and obj.data.shape_keys:
        for key in obj.data.shape_keys.key_blocks[1:]:
            key.value = 0
bpy.context.view_layer.update()
expected = eye.snapshot()
native = out/'Mia_FaceReview_v22_WIP9.blend'
bpy.context.scene['mia_review_status'] = 'WIP9: Q9 primary surface/mouth anchor, E2 eyelid arcs, M4 look. ART UNAPPROVED.'
bpy.ops.wm.save_as_mainfile(filepath=str(native))
bpy.ops.wm.open_mainfile(filepath=str(native), use_scripts=False)
assert eye.snapshot() == expected, 'Saved review differs from in-memory mesh/key/UV/material/transforms'
assert sha(source) == args.source_sha
report = {
    'status': 'WORKING REVIEW; no final character/art approval',
    'source': {'path': str(source), 'sha256': args.source_sha},
    'native': {'path': str(native), 'sha256': sha(native)},
    'recipes': {str(p.relative_to(HERE)): sha(p) for p in [Path(__file__), eye_path, look_path]},
    'eye': eye_report,
    'material': {'name': material_name,
                 'variant': 'm4', 'new_raster_maps': False},
    'verification': 'Non-target eye-stage snapshot exact; target UV/topology/material/transform exact; look does not change geometry/keys/UV; all non-Basis keys neutral at save; save/reopen snapshot exact.',
    'limits': ['Fresh combined source views, matte, half/full blink, color-only and live MCP still required.',
               'Q9 is a bounded repair of the P2 mouth drift and cheek taper, not full anatomical/source-likeness completion.',
               'Body/hair remain prior unfinished WIP8 assets. No animation completion.']}
(out/'integration-manifest.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('REVIEW9_COMBINED', native, sha(native), flush=True)
