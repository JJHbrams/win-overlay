"""Render a saved WIP's own camera/light/material setup, including contour pass."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import bpy

p = argparse.ArgumentParser()
p.add_argument('--native', required=True)
p.add_argument('--output-dir', required=True)
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
native = Path(a.native).resolve()
digest = lambda f: hashlib.sha256(Path(f).read_bytes()).hexdigest()
before = digest(native)
out = Path(a.output_dir).resolve()
out.mkdir(parents=True, exist_ok=True)
assert not (out/'preview.json').exists(), 'Preserve frozen preview'
bpy.ops.wm.open_mainfile(filepath=str(native), use_scripts=False)
s = bpy.context.scene
s.render.resolution_x = s.render.resolution_y = 900
s.render.resolution_percentage = 100
s.render.film_transparent = True
s.render.image_settings.file_format = 'PNG'
s.render.image_settings.color_mode = 'RGBA'
records = []
for name in ('Front', 'LeftOblique', 'Profile'):
    s.camera = bpy.data.objects['MIA_REVIEW_Head_' + name]
    target = out/(name + '.png')
    s.render.filepath = str(target)
    bpy.ops.render.render(write_still=True)
    records.append({'path': target.name, 'sha256': digest(target), 'camera': s.camera.name,
                    'projection': s.camera.data.type, 'ortho_scale': s.camera.data.ortho_scale,
                    'matrix': [list(r) for r in s.camera.matrix_world]})
assert digest(native) == before
(out/'preview.json').write_text(json.dumps({'native': str(native), 'sha256': before,
    'native_unchanged': True, 'freestyle': s.render.use_freestyle,
    'views': records, 'scope': 'Actual saved-native production camera render. Static WIP; not animation/art approval.'}, indent=2), encoding='utf-8')
