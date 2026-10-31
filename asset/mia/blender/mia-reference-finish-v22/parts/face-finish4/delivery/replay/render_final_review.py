"""Fresh actual native review under common root scene lighting; no saves."""
import bpy,sys,ast,json,argparse,math
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent));import review_setup as r
ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--output-dir',required=True);ap.add_argument('--diagnostics',action='store_true');a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);SOURCE=Path(a.source).resolve();OUT=Path(a.output_dir).resolve();OUT.mkdir(parents=True,exist_ok=True);sh=r.sha(SOURCE)
tree=ast.parse((r.OUT/'shape_evidence.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['rig','constant']],type_ignores=[]),'common-rig','exec'))
def load(hair):
 bpy.ops.wm.open_mainfile(filepath=str(SOURCE));s=bpy.context.scene;s.frame_set(1);rig(s)
 if not hair:r.hairhide()
 if hasattr(s,'eevee') and hasattr(s.eevee,'taa_render_samples'):s.eevee.taa_render_samples=128
 return s
def render(s,name,v):r.camera(s,v);s.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
def record(s,v):
 d=r.record(s,v,'Actual shared root lighting');d['lighting']={'key':{'location':[-.6,-1,2.2],'watts':60,'size':1},'fill':{'location':[.8,-.8,1.8],'watts':15,'size':1.5},'rim':{'location':[0,.9,2.05],'watts':8,'size':.8},'area_shape':'DISK','color':[1,1,1],'target':[0,0,1.55],'world_linear':[.18,.18,.18],'world_strength':.1,'other_scene_lights_disabled':True};return d
records={};s=load(False)
for v in r.VIEWS:
 render(s,v['id'],v);records[v['id']]={'camera':record(s,v),'landmarks':r.landmarks(s,v)}
(OUT/'render-records.json').write_text(json.dumps(records,indent=2));s=load(True)
for v in r.VIEWS:render(s,'hair_'+v['id'],v)
if a.diagnostics:
 s=load(False);views=[dict(id=name,yaw=yaw,elevation=0,roll=0) for name,yaw in [('front0',0),('left45',45),('right45',-45),('profile90',90)]]
 for v in views:render(s,'actual_'+v['id'],v)
 # Only lighting bypassed; actual connected pigment path remains, source geometry and UV unchanged.
 for name in ['MIA_V14_SculptedSkin','MIA_V06_BODY_SKIN']:
  o=bpy.data.objects[name]
  for slot in o.material_slots:
   if not slot.material or not slot.material.use_nodes:continue
   m=slot.material.copy();slot.material=m;n=m.node_tree.nodes;mul=n.get('PigmentTimesControlledLight')
   if mul:
    em=next(x for x in n if x.type=='EMISSION');m.node_tree.links.new(mul.inputs[1].links[0].from_socket,em.inputs[0])
 for v in views[:2]:render(s,'color_only_'+v['id'],v)
 s=load(False);skin=bpy.data.objects['MIA_V14_SculptedSkin'];m=bpy.data.materials.new('V22_DIAG_ActualUV');m.use_nodes=True;n=m.node_tree.nodes;n.clear();u=n.new('ShaderNodeUVMap');u.uv_map=skin.data.uv_layers.active.name;c=n.new('ShaderNodeTexChecker');c.inputs['Scale'].default_value=40;e=n.new('ShaderNodeEmission');o=n.new('ShaderNodeOutputMaterial');l=m.node_tree.links;l.new(u.outputs[0],c.inputs[0]);l.new(c.outputs[0],e.inputs[0]);l.new(e.outputs[0],o.inputs[0]);skin.material_slots[7].material=m
 for v in views[:2]:render(s,'uv_'+v['id'],v)
 s=load(False);key=next(k for k in bpy.data.objects['MIA_V14_SculptedSkin'].data.shape_keys.key_blocks if k.name.endswith('Fcl_EYE_Close'));key.value=.5;bpy.context.view_layer.update();render(s,'blink_half_front',views[0])
assert r.sha(SOURCE)==sh;(OUT/'readonly-render-proof.json').write_text(json.dumps({'source':r.artifact(SOURCE),'source_hash_after':r.sha(SOURCE),'no_native_saved':True,'frame':1,'camera_records':'render-records.json'},indent=2));print('FINAL_REVIEW_RENDER_DONE')
