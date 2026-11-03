"""Fresh native CPU check of the one private posed-cage installation."""
from pathlib import Path
import hashlib
import json
import bpy
import numpy as np
HERE=Path(__file__).resolve().parent
ROOT=Path('D:/MiaWorkCache/mia-reference-work/win-overlay');CACHE=ROOT/'.mia-cache/body-connected/cpu'
assert bpy.app.background
source_path=Path(bpy.data.filepath)
assert hashlib.sha256(source_path.read_bytes()).hexdigest()=='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'
source=bpy.data.objects['MIA_V27_SharedHeadBody']
def evaluate(ob):
    dg=bpy.context.evaluated_depsgraph_get();e=ob.evaluated_get(dg);me=e.to_mesh(preserve_all_data_layers=True,depsgraph=dg)
    v=np.asarray([e.matrix_world@p.co for p in me.vertices],np.float32)
    loops=np.asarray([l.vertex_index for l in me.loops],np.int32)
    uv={u.name:hashlib.sha256(np.asarray([p.uv[:]for p in u.data],np.float32).tobytes()).hexdigest()for u in me.uv_layers}
    e.to_mesh_clear();return v,loops,uv
before=evaluate(source)
ids_before={name:len(getattr(bpy.data,name))for name in ['objects','meshes','shape_keys','materials','node_groups']}
exec(compile((HERE/'live_scope.py').read_text(encoding='utf8'),str(HERE/'live_scope.py'),'exec'))
bpy.ops.object.mode_set(mode='OBJECT')
after=evaluate(bpy.data.objects['MIA_ConnectedBody_Design'])
assert np.array_equal(before[0],after[0]),'Posed-cage baseline differs from actual R3b evaluated geometry'
assert np.array_equal(before[1],after[1]) and before[2]==after[2]
exec(compile((HERE/'restore.py').read_text(encoding='utf8'),str(HERE/'restore.py'),'exec'))
ids_after={name:len(getattr(bpy.data,name))for name in ids_before}
assert ids_before==ids_after,(ids_before,ids_after)
assert hashlib.sha256(source_path.read_bytes()).hexdigest()=='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'
report=dict(runtime='CPU_BACKGROUND',private_baseline_evaluated_geometry_exact=True,evaluated_vertices=len(before[0]),
    original_loop_topology_UV_exact=True,original47_preserved=True,owned_ID_inventory_restored=True,
    original_native_unchanged=True,GPU=False,native_saved=False,ART=False)
CACHE.mkdir(parents=True,exist_ok=True)
(CACHE/'baseline-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(report),flush=True)
