import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
O=Path(__file__).parent;S=O/'face-shared-final/Mia_Foundation_v27.blend';OUT=O/'final-rig-body-proof-matched';OUT.mkdir(exist_ok=True);D=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v22/face-feedback-7/surface-diagnosis/dependencies');sys.path.insert(0,str(D));import review_setup as r
source=r.artifact(S);bpy.ops.wm.open_mainfile(filepath=str(S));s=bpy.context.scene;r.hairhide();arm=next(m.object for m in bpy.data.objects['MIA_V27_SharedHeadBody'].modifiers if m.type=='ARMATURE');bone=arm.pose.bones['J_Bip_C_Head'];original=bone.matrix_basis.copy();owners=[bpy.data.objects['MIA_V27_Foundation_Face']]+[o for o in s.objects if 'BoundaryRibbon' in o.name and not o.hide_render]
def pts(o):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();p=np.array([e.matrix_world@v.co for v in m.vertices]);e.to_mesh_clear();return p
bpy.context.view_layer.update();base={o.name:pts(o) for o in owners};neutral=arm.matrix_world@bone.matrix;records=[]
for degrees in [-12,12]:
 bone.matrix_basis=original@Quaternion(Vector((0,1,0)),math.radians(degrees)).to_matrix().to_4x4();bpy.context.view_layer.update();delta=(arm.matrix_world@bone.matrix)@neutral.inverted();errors={}
 for o in owners:
  expected=np.array([delta@Vector(p) for p in base[o.name]]);errors[o.name]=float(abs(pts(o)-expected).max())
 r.camera(s,r.VIEWS[0]);s.render.resolution_x=s.render.resolution_y=700;s.render.filepath=str(OUT/('head_yaw_'+str(degrees)+'.png'));bpy.ops.render.render(write_still=True);records.append({'degrees':degrees,'rigid_head_follow_error_m':errors,'render':r.artifact(s.render.filepath)})
baseline=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v22/integration-wip-9-review/Mia_FaceReview_v22_WIP9_M5.blend')
for label,path in [('baseline',baseline),('candidate',S)]:
 bpy.ops.wm.open_mainfile(filepath=str(path));s=bpy.context.scene;s.frame_set(1);s.render.use_freestyle=False;r.camera(s,r.VIEWS[0]);cam=s.camera;cam.location=(0,-4,.83);cam.rotation_euler=(Vector((0,0,.83))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.85;s.render.resolution_x=650;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.render.filepath=str(OUT/('whole_body_'+label+'.png'));bpy.ops.render.render(write_still=True)
assert r.sha(S)==source['sha256'];(OUT/'rig-body-proof.json').write_text(json.dumps({'native':source,'head_follow':records,'whole_body_renders':['whole_body_baseline.png','whole_body_candidate.png'],'limits':'Two small head rotations and neutral body comparison only, not full motion rig/animation acceptance.'},indent=2));print('RIG_BODY_PROOF_DONE')
