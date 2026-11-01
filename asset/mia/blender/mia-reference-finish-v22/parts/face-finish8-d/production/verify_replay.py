import bpy,ast,json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent;P=ROOT/'look-d/handoff/owner-key-replay-from-r28.json';data=json.loads(P.read_text());ah=lambda p:hashlib.sha256(np.asarray(p).tobytes()).hexdigest()
t=ast.parse((ROOT.parent/'finish-6/dependencies/legacy_snapshot_apply_interp.py').read_text());exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='snapshots'],type_ignores=[]),'guards','exec'))
bpy.ops.wm.open_mainfile(filepath=data['candidate']['path']);expected=snapshots()
bpy.ops.wm.open_mainfile(filepath=data['baseline']['path']);exec(compile((ROOT/'replay_into_r28.py').read_text(),'guarded-replay','exec'));result=apply_replay(P);actual=snapshots();assert actual==expected
rejected=False
try:apply_replay(P)
except AssertionError:rejected=True
assert rejected
(P.parent/'replay-validation.json').write_text(json.dumps({'exact_final_mesh_keys_uv_materialslots':True,'repeated_replay_rejected':True,'saved':False,'result':result},indent=2));print('EXACT_REPLAY_VERIFIED')
