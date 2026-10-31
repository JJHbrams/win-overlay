import bpy,sys,json,math,hashlib
from pathlib import Path
root=Path(r'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay');sys.path.insert(0,str(root/'tools/mia/blender'))
from mia_world_pose_v09 import yaw_world
from audit_mia_body_head_v06_independent import snapshot_pose,restore_pose,digest
native=root/'asset/mia/blender/mia-production-body-head-v06/Mia_BodyHead_v06.blend';out=native.parent/'pose-world-space-corrections';before=digest(native)
bpy.ops.wm.open_mainfile(filepath=str(native));rig=bpy.data.objects['MIA_V06_RIG'];saved=snapshot_pose(rig);result={}
for angle in [20,-20]:
 restore_pose(rig,saved);result[str(angle)]=yaw_world(rig,rig.pose.bones['J_Bip_C_Head'],math.radians(angle))
restore_pose(rig,saved)
result['restore_exact']=all(b.matrix_basis==saved[b.name]['basis'] and b.rotation_mode==saved[b.name]['mode'] for b in rig.pose.bones)
result['native_sha_before']=before;result['native_sha_after']=digest(native)
result['audit_script_sha256']=digest(root/'tools/mia/blender/audit_mia_body_head_v06_independent.py')
assert result['restore_exact'] and before==digest(native)
(out/'head-world-yaw-math-smoke.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
