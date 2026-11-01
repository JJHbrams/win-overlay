import bpy,json
from pathlib import Path
from mathutils import Vector
p=Path(__file__).parent
bpy.ops.wm.open_mainfile(filepath='C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v22/parts/hair-ink-paint/native/0d7874821981-Mia_HairInkPaint_v22.blend',use_scripts=False)
rows=[]
for o in bpy.data.objects:
 if o.type=='MESH' and ('Hair' in o.name or 'HalfUp' in o.name or 'PIXAL' in o.name):
  pts=[o.matrix_world@v.co for v in o.data.vertices]
  rows.append(dict(name=o.name,n=len(pts),hide=o.hide_render,parent=o.parent.name if o.parent else None,matrix=[list(r) for r in o.matrix_world],bounds=[[min(v[k] for v in pts),max(v[k] for v in pts)] for k in range(3)],materials=[m.name for m in o.data.materials if m],mods=[m.type for m in o.modifiers],uv=[u.name for u in o.data.uv_layers]))
  if 'HalfUp' in o.name:
   rows[-1]['points']=[list(v) for v in pts[::max(1,len(pts)//20)]]
(p/'inspect.json').write_text(json.dumps(rows,indent=2))
print(json.dumps(rows,indent=2))
