"""Read-only finish4/finish5 same-camera source views and local-mask diagnostic."""
import bpy,sys,json,ast,hashlib
from pathlib import Path
from mathutils import Vector
H=Path(__file__).resolve().parent;deps=H.parent/'finish-4/replay';sys.path.insert(0,str(deps));import review_setup as r
tree=ast.parse((deps/'shape_evidence.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='rig'],type_ignores=[]),'fixed-root-rig','exec'))
lights=json.loads((H.parent/'finish-4/renders/render-records.json').read_text())['front']['camera']['lighting'];record={}
def rec(s,v):
 d=r.record(s,v,'Actual fixed root rig');d['lighting']=lights;d['active_shape_keys']={o.name:{k.name:k.value for k in o.data.shape_keys.key_blocks[1:] if abs(k.value)>1e-8} for o in s.objects if o.type=='MESH' and not o.hide_render and o.data.shape_keys and any(abs(k.value)>1e-8 for k in o.data.shape_keys.key_blocks[1:])};return d
for role,source in [('baseline',H.parent/'finish-4/Mia_FaceFinish_v22.blend'),('candidate',H/'Mia_FaceFinish5_v22.blend')]:
 before=r.sha(source);bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.context.scene;s.frame_set(1);rig(s);s.render.use_freestyle=False;folder=H/role;folder.mkdir(exist_ok=True)
 for v in r.VIEWS:
  r.camera(s,v);p=folder/(v['id']+'.png');s.render.filepath=str(p);bpy.ops.render.render(write_still=True);record[role+'/'+v['id']]={'camera':rec(s,v),'render':r.artifact(p)}
 r.hairhide()
 for v in [r.VIEWS[0],r.VIEWS[2]]:
  r.camera(s,v);p=folder/('bare_'+v['id']+'.png');s.render.filepath=str(p);bpy.ops.render.render(write_still=True);record[role+'/bare_'+v['id']]={'camera':rec(s,v),'render':r.artifact(p)}
 if role=='candidate':
  m=bpy.data.objects['MIA_V14_SculptedSkin'].material_slots[7].material.copy();bpy.data.objects['MIA_V14_SculptedSkin'].material_slots[7].material=m;nodes=m.node_tree.nodes;em=next(n for n in nodes if n.type=='EMISSION');m.node_tree.links.new(nodes['V22_F5_LOCAL_CRESCENT_MASK'].outputs[0],em.inputs[0]);r.camera(s,r.VIEWS[0]);s.render.filepath=str(folder/'actual_uv_mask_front.png');bpy.ops.render.render(write_still=True)
 assert r.sha(source)==before
for v in r.VIEWS:assert record['baseline/'+v['id']]['camera']==record['candidate/'+v['id']]['camera']
(H/'render-records.json').write_text(json.dumps(record,indent=2));print('FINISH5_AB_DONE')
