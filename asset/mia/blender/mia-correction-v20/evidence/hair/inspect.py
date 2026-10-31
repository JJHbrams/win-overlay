import bpy,json
from pathlib import Path
bpy.ops.wm.open_mainfile(filepath=r'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v17/integrated-v18/Mia_HeadHair_v18.blend')
r=[]
for o in bpy.data.collections['MIA_V17_PIXAL_HAIR'].objects:
 q=[o.matrix_world@v.co for v in o.data.vertices] if o.type=='MESH' else []
 r.append({'name':o.name,'materials':[m.name if m else None for m in o.data.materials],'bounds':[[min(p[j] for p in q),max(p[j] for p in q)] for j in range(3)] if q else [],'matrix':[list(row) for row in o.matrix_world]})
Path(__file__).with_name('hair-owners.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
