import bpy,json
from pathlib import Path
bpy.ops.wm.open_mainfile(filepath=r'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v17/integrated-v18/Mia_HeadHair_v18.blend')
o=bpy.data.objects['MIA_V06_BODY_SKIN'];m=o.data
r={'matrix':[list(v) for v in o.matrix_world],'modifiers':[(x.name,x.type) for x in o.modifiers],'keys':[(k.name,k.value) for k in m.shape_keys.key_blocks] if m.shape_keys else [],'verts':[list(o.matrix_world@v.co) for v in m.vertices],'edges':[list(e.vertices) for e in m.edges],'polys':[list(p.vertices) for p in m.polygons]}
Path(__file__).with_name('body-cage.json').write_text(json.dumps(r));print('BODY',len(m.vertices),len(m.polygons),r['matrix'],r['modifiers'],r['keys'])
