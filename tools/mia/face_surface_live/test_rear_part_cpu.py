"""Fresh background CPU install/readback/rollback check; not visual acceptance."""
from pathlib import Path
import hashlib
import importlib.util
import json
import bpy
import numpy as np

ROOT=Path('D:/MiaWorkCache/mia-reference-work/win-overlay')
FOLDER=ROOT/'.mia-cache/face-live/rear-part01'
path=Path(__file__).with_name('rear_part.py')
spec=importlib.util.spec_from_file_location('mia_rear_part01',path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
geometry=np.load(ROOT/'.mia-cache/body-h/shape/assembly/live-D/geometry.npz')
body_mesh=bpy.data.meshes.new('CPU_only_frozen_body_guard')
body_mesh.from_pydata(geometry['world'].tolist(),[],[])
body=bpy.data.objects.new('MIA_Review12_H_LiveRepair',body_mesh);bpy.context.scene.collection.objects.link(body)
body_sha=hashlib.sha256(np.array([v.co[:] for v in body.data.vertices],np.float32).tobytes()).hexdigest()
bpy.app.driver_namespace['MIA_HairReviewState']={'body_sha256':body_sha}
names={o.name for o in bpy.data.objects};mesh_names={m.name for m in bpy.data.meshes};group_names={g.name for g in bpy.data.node_groups}
report=mod.apply(runtime='background_cpu');part=bpy.data.objects[mod.PREFIX];deps=bpy.context.evaluated_depsgraph_get();ev=part.evaluated_get(deps);mesh=ev.to_mesh(preserve_all_data_layers=True,depsgraph=deps)
q=np.array([ev.matrix_world@v.co for v in mesh.vertices],np.float32);ev.to_mesh_clear()
desired=np.load(FOLDER/'ownership.npz')['candidate_world']
error=float(np.linalg.norm(q-desired,axis=1).max())
assert error < 2e-6, ('Unexpected current binding transform',error)
rollback=mod.restore()
assert {o.name for o in bpy.data.objects}==names
assert {m.name for m in bpy.data.meshes}==mesh_names
assert {g.name for g in bpy.data.node_groups}==group_names
report.update(test='CPU fresh install/readback/rollback only',evaluated_current_pose_max_error_m=error,
              rollback=rollback,object_mesh_nodegroup_inventory_exact_after_restore=True,
              intended_live_runtime_exercised=False,rendered=False,ART=False)
(FOLDER/'cpu-check.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(report))
