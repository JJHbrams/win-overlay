"""Read-only camera bracket; source model and geometry never saved."""
import bpy,sys,ast,json
from pathlib import Path
from mathutils import Vector
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import review_setup as r
SOURCE=H/'finish-4/Mia_FaceFinish_v22.blend';OUT=H/'finish-4/profile-bracket';OUT.mkdir(exist_ok=True);before=r.sha(SOURCE)
tree=ast.parse((H/'shape_evidence.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='rig'],type_ignores=[]),'common-rig','exec'))
records={}
for hair in [True,False]:
 bpy.ops.wm.open_mainfile(filepath=str(SOURCE));s=bpy.context.scene;s.frame_set(1);rig(s)
 if not hair:r.hairhide()
 for yaw in [60,70,80,90]:
  v=dict(id='profile',yaw=yaw,elevation=0,roll=0);r.camera(s,v);name=('hair_' if hair else 'bare_')+str(yaw);s.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True);records[name]={'camera':r.record(s,v,'Actual shared root light rig as final review'),'landmarks':r.landmarks(s,v)}
assert r.sha(SOURCE)==before
(OUT/'camera-records.json').write_text(json.dumps({'native':r.artifact(SOURCE),'native_hash_after':r.sha(SOURCE),'no_native_saved':True,'records':records},indent=2));print('PROFILE_BRACKET_DONE')
