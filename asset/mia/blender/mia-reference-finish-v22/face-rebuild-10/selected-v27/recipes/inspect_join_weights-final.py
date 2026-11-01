import bpy,json
from pathlib import Path
O=Path(__file__).parent;bpy.ops.wm.open_mainfile(filepath=str(O/'face-shared-final/Mia_Foundation_v27.blend'));a=bpy.data.objects['MIA_V06_BODY_SKIN'];b=bpy.data.objects['MIA_V27_SharedHeadBody'];bad=[]
for i,v in enumerate(a.data.vertices):
 aa={a.vertex_groups[g.group].name:g.weight for g in v.groups};bb={b.vertex_groups[g.group].name:g.weight for g in b.data.vertices[i].groups if b.vertex_groups[g.group].name!='V27_OriginalBodyWeldOnly'}
 if aa!=bb:bad.append((i,aa,bb))

(O/'face-shared-final/body-weight-audit.json').write_text(json.dumps({'original_body_vertices':len(a.data.vertices),'group_name_weight_mismatch_count':len(bad),'mismatch_samples':bad[:5],'smooth_group':next(m.vertex_group for m in b.modifiers if m.type=='SMOOTH')},indent=2));print('WEIGHT_MISMATCH',len(bad))
