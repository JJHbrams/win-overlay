import bpy,json,sys,ast
from pathlib import Path
from mathutils import Vector
O=Path(__file__).parent;S=O/'face-shared-final/Mia_Foundation_v27.blend';OUT=O/'final-diagnostics-frozen';OUT.mkdir(exist_ok=True);D=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v22/face-feedback-7/surface-diagnosis/dependencies');sys.path.insert(0,str(D));import review_setup as r
exec(compile(ast.Module(body=[n for n in ast.parse((D/'shape_evidence.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name in ['rig','constant']],type_ignores=[]),'rig','exec'));source=r.artifact(S);records=[]
def load():
 bpy.ops.wm.open_mainfile(filepath=str(S));s=bpy.context.scene;s.frame_set(1);s.render.use_freestyle=False;r.hairhide();return s

def render(s,label,v,mode):
 r.camera(s,v);s.render.resolution_x=s.render.resolution_y=700;s.render.resolution_percentage=100;s.render.filepath=str(OUT/(label+'.png'));bpy.context.view_layer.update();bpy.ops.render.render(write_still=True);camera=r.record(s,v,mode);camera['resolution']=[700,700];camera['active_shape_keys']={o.name:{k.name:k.value for k in o.data.shape_keys.key_blocks if k.value} for o in s.objects if o.type=='MESH' and o.data.shape_keys and not o.hide_render and any(k.value for k in o.data.shape_keys.key_blocks)};records.append({'label':label,'render':r.artifact(s.render.filepath),'camera':camera})
s=load();rig(s);clay=constant('FINAL_VERIFIED_MATTE',(.18,.18,.18),True);
for slot in bpy.data.objects['MIA_V27_SharedHeadBody'].material_slots:slot.material=clay
for slot in bpy.data.objects['MIA_V06_BODY_SKIN'].material_slots:slot.material=clay
for v in r.VIEWS+[dict(id='lowfront',yaw=0,elevation=-12,roll=0)]:render(s,'matte_'+v['id'],v,'bare actual geometry matte')
s=load();keys=bpy.data.objects['MIA_V27_Foundation_Face'].data.shape_keys.key_blocks;close=next(k for k in keys if k.name.endswith('Fcl_EYE_Close'))
for val in [.5,1.]:
 close.value=val;bpy.context.view_layer.update()
 for v in [r.VIEWS[0],r.VIEWS[2]]:render(s,'native_blink_'+str(val)+'_'+v['id'],v,'actual native half/full blink')
s=load();skin=bpy.data.objects['MIA_V27_SharedHeadBody'];m=skin.material_slots[0].material.copy();skin.material_slots[0].material=m;n=m.node_tree.nodes;l=m.node_tree.links;out=next(x for x in n if x.type=='OUTPUT_MATERIAL' and x.is_active_output);em=n.new('ShaderNodeEmission');l.new(n['V27_ACTUAL_UV_PIGMENT'].outputs['Color'],em.inputs[0]);l.new(em.outputs[0],out.inputs[0])
for v in [r.VIEWS[0],r.VIEWS[2]]:render(s,'color_only_'+v['id'],v,'actual UV pigment through Emission; geometry lighting bypassed')
s=load();skin=bpy.data.objects['MIA_V27_SharedHeadBody'];m=bpy.data.materials.new('FINAL_UV_CHECKER');m.use_nodes=True;n=m.node_tree.nodes;n.clear();uv=n.new('ShaderNodeUVMap');uv.uv_map='UVMap';c=n.new('ShaderNodeTexChecker');c.inputs['Scale'].default_value=40;em=n.new('ShaderNodeEmission');out=n.new('ShaderNodeOutputMaterial');l=m.node_tree.links;l.new(uv.outputs['UV'],c.inputs['Vector']);l.new(c.outputs[0],em.inputs[0]);l.new(em.outputs[0],out.inputs[0]);skin.material_slots[0].material=m
for v in [r.VIEWS[0],r.VIEWS[2]]:render(s,'uv_'+v['id'],v,'actual UVMap checker40, no unwrap changes')
assert r.sha(S)==source['sha256'];(OUT/'diagnostics.json').write_text(json.dumps({'native':source,'recipe':r.artifact(__file__),'records':records,'limits':'Actual renders; not art or full-expression pass. All modes freshly reopened frozen native.'},indent=2));print('FINAL_DIAGNOSTICS_DONE')

