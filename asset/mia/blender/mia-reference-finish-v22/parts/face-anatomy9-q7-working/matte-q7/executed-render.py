"""Four fixed source cameras, native pigment/matte and real evaluated motion."""
import argparse,ast,json,sys
from pathlib import Path
import bpy
from mathutils import Vector
HERE=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--output-dir',required=True);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);SOURCE=Path(a.source);OUT=Path(a.output_dir);assert not OUT.exists() or not any(OUT.iterdir());OUT.mkdir(parents=True,exist_ok=True)
D=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v22/face-feedback-7/surface-diagnosis/dependencies');sys.path.insert(0,str(D));import review_setup as r
tree=ast.parse((D/'shape_evidence.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['rig','constant']],type_ignores=[]),'frozen-rig','exec'))
source_sha=r.sha(SOURCE);records=[]
def load(hair=True,matte=False):
 bpy.ops.wm.open_mainfile(filepath=str(SOURCE));s=bpy.context.scene;s.frame_set(1);s.render.use_freestyle=False
 if not hair:r.hairhide()
 if matte:
  rig(s);clay=constant('MOTION_MATTE',(.18,.18,.18),True)
  for name in ['MIA_V14_SculptedSkin','MIA_V06_BODY_SKIN']:
   for slot in bpy.data.objects[name].material_slots:slot.material=clay
  # Keep lash/wing meshes in motion captures: actual detachment must remain
  # visible rather than being hidden by the diagnostic material mode.
  for obj in s.objects:
   if any(t in obj.name for t in ['Brow','MouthSeam','SingleUnderEyeCrease']):obj.hide_render=True
 return s
def active_keys():
 return {o.name:{k.name:float(k.value) for k in o.data.shape_keys.key_blocks if abs(k.value)>1e-8} for o in bpy.context.scene.objects if o.type=='MESH' and o.data.shape_keys and any(abs(k.value)>1e-8 for k in o.data.shape_keys.key_blocks)}
def render(s,label,view,mode):
 r.camera(s,view);s.render.filepath=str(OUT/(label+'.png'));bpy.context.view_layer.update();bpy.ops.render.render(write_still=True);rec={'label':label,'render':r.artifact(s.render.filepath),'camera':r.record(s,view,mode),'actual_active_keys_by_owner':active_keys(),'landmarks':r.landmarks(s,view)};records.append(rec)
for mode,hair,matte in [('matte',False,True)]:
 s=load(hair,matte)
 for view in r.VIEWS:render(s,mode+'_'+view['id'],view,mode)
for mode,matte in [('matte',True)]:
 s=load(False,matte);skin=bpy.data.objects['MIA_V14_SculptedSkin'];keys=skin.data.shape_keys.key_blocks
 for k in keys:k.value=0.
 close=keys['Face.M_F00_000_00_Fcl_EYE_Close'];close.value=.5;bpy.context.view_layer.update()
 for yaw in [0,30,-30]:
  view={'id':'halfblink','yaw':yaw,'elevation':0,'roll':0};render(s,mode+'_halfblink_yaw%+03d'%yaw,view,mode+' actual half blink')
 close.value=1.;bpy.context.view_layer.update()
 for yaw in [0,30,-30]:
  view={'id':'fullblink','yaw':yaw,'elevation':0,'roll':0};render(s,mode+'_fullblink_yaw%+03d'%yaw,view,mode+' actual full blink')
 close.value=0.
 for yaw in [0,30,-30]:
  view={'id':'low','yaw':yaw,'elevation':-12,'roll':0};render(s,mode+'_low_yaw%+03d'%yaw,view,mode+' low neutral')
 keys['Face.M_F00_000_00_Fcl_EYE_Sorrow'].value=.15;keys['Face.M_F00_000_00_Fcl_MTH_Sorrow'].value=.15;bpy.context.view_layer.update()
 for yaw in [0,25]:
  view={'id':'subtle_sorrow','yaw':yaw,'elevation':2,'roll':0};render(s,mode+'_subtle_sorrow_yaw%+03d'%yaw,view,mode+' actual subtle eye/mouth sorrow .15')
assert r.sha(SOURCE)==source_sha
(OUT/'render-records.json').write_text(json.dumps({'source':r.artifact(SOURCE),'recipe':r.artifact(__file__),'records':records,'limits':'Actual renders are evidence, not art/motion approval. Shape-key values include evaluated lash follower values; no geometry was saved.'},indent=2));(OUT/'executed-render.py').write_bytes(Path(__file__).read_bytes());print('SOURCE_MOTION_DONE',len(records))
