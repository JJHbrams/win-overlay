"""Actual before/after render of a frozen native; never saves source or grants art PASS."""
import argparse
import hashlib
import json
import runpy
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
p = argparse.ArgumentParser()
p.add_argument('--source', required=True)
p.add_argument('--output-dir', required=True)
a = p.parse_args(sys.argv[sys.argv.index('--')+1:])
source, out = Path(a.source).resolve(), Path(a.output_dir).resolve()
out.mkdir(parents=True, exist_ok=True)
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
before = sha(source)
bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
runpy.run_path(str(HERE/'configure_review_scene.py'))['setup']()
s = bpy.context.scene
s.render.image_settings.file_format = 'PNG'
s.render.image_settings.color_mode = 'RGBA'
s.render.film_transparent = True
record = {'source': str(source), 'source_sha256': before, 'renders': []}
for enabled in (False, True):
    if enabled:
        record['ink'] = runpy.run_path(str(HERE/'production_ink.py'))['configure_skin_ink']()
    else:
        s.render.use_freestyle = False
    for view in ('Front', 'Profile', 'LeftOblique'):
        s.camera = bpy.data.objects['MIA_REVIEW_Face_' + view]
        path = out/((('ink_' if enabled else 'no_ink_') + view) + '.png')
        s.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        record['renders'].append({'path': str(path), 'sha256': sha(path), 'ink': enabled,
                                  'camera': s.camera.name, 'matrix': [list(r) for r in s.camera.matrix_world],
                                  'projection': s.camera.data.type, 'ortho_scale': s.camera.data.ortho_scale})
assert sha(source) == before
record['native_unchanged'] = True
(out/'probe.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print('INK_PROBE_COMPLETE')
