import bpy,sys,json
from pathlib import Path
root=Path(r'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay');sys.path.insert(0,str(root/'tools/mia/blender'))
from audit_mia_body_head_v06_independent import pose_deformation_cases,digest
p=root/'asset/mia/blender/mia-production-body-head-v06/Mia_BodyHead_v06.blend';before=digest(p)
bpy.ops.wm.open_mainfile(filepath=str(p))
r=pose_deformation_cases(bpy.data.objects['MIA_V06_BODY_SKIN'],bpy.data.objects['MIA_V06_RIG'])
r['native_sha_before']=before;r['native_sha_after']=digest(p);r['audit_script_sha256']=digest(root/'tools/mia/blender/audit_mia_body_head_v06_independent.py')
print('CHECK',json.dumps(r));assert before==digest(p)
(p.parent/'pose-world-space-corrections'/'audit-raise-direction-smoke.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
