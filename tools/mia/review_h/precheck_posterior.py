"""CPU-only technical check of the single prepared live operation; no save."""
from pathlib import Path
import bpy
import numpy as np
ROOT = Path(__file__).resolve().parents[3]
d = dict(np.load(ROOT/'.mia-cache/body-h/shape/assembly/live-D/geometry.npz'))
me = bpy.data.meshes.new('Posterior_Precheck_Only')
me.from_pydata(d['world'].tolist(), [], d['triangles'].tolist()); me.update()
ob = bpy.data.objects.new('MIA_Review12_H_LiveRepair', me); bpy.context.scene.collection.objects.link(ob)
bpy.context.view_layer.objects.active = ob
bpy.app.driver_namespace['MIA_Live_H_Rows'] = dict(np.load(ROOT/'.mia-cache/body-h/shape/assembly/collar-rows.npz'))
path = ROOT/'tools/mia/review_h/live_posterior_leaf.py'
try:
    exec(compile(path.read_text(encoding='utf8'), str(path), 'exec'))
except AssertionError as exc:
    print('PREAPPLY_GUARD_REJECTION', str(exc), flush=True)
print((ROOT/'.mia-cache/body-h/live/posterior-selection-precheck.json').read_text(encoding='utf8'))
