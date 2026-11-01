"""Read-only aligned paint input and actual evaluated UV projection metadata."""
import bpy,sys,ast,json,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'shape-a/paint-input';OUT.mkdir(exist_ok=True)
SOURCE=ROOT/'shape-a/Mia_FaceFinish8_CompactSectionsA.blend'
src=ROOT.parent/'finish-7/render_source_motion.py';tree=ast.parse(src.read_text());nodes=[]
# Share definitions without consuming its CLI or output directory.
sys.path.insert(0,'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v22/face-feedback-7/surface-diagnosis/dependencies');import review_setup as r
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));s=bpy.context.scene;s.frame_set(1);s.render.use_freestyle=False;r.hairhide()
for k in bpy.data.objects['MIA_V14_SculptedSkin'].data.shape_keys.key_blocks:k.value=0
v={'id':'paint_aligned_front','yaw':0,'elevation':0,'roll':0};r.camera(s,v)
r.aim(s.camera,(0,-2,1.552),(0,0,1.552));s.camera.rotation_mode='XYZ';s.camera.data.ortho_scale=.215
s.render.resolution_x=s.render.resolution_y=1536;s.render.filepath=str(OUT/'actual-native-face-aligned.png');bpy.context.view_layer.update();bpy.ops.render.render(write_still=True)
skin=bpy.data.objects['MIA_V14_SculptedSkin'];ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles()
def pixel(p):
 q=world_to_camera_view(s,s.camera,ev.matrix_world@p);return [float(q.x*1536),float((1-q.y)*1536)]
data={'source':r.artifact(SOURCE),'actual_plate':r.artifact(s.render.filepath),'image_size':[1536,1536],'camera_matrix':[list(row) for row in s.camera.matrix_world],'projection':'ORTHO','ortho_scale':.215,'target_world':[0,0,1.552],'world_local_matrix':[list(row) for row in ev.matrix_world],'color_management':{'view_transform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma},'uv_layers':[u.name for u in m.uv_layers],'evaluated_vertices':[list(v.co) for v in m.vertices],'pixel_vertices':[pixel(v.co) for v in m.vertices],'triangles':[{'vertices':list(t.vertices),'material':t.material_index,'uv':{u.name:[list(u.data[i].uv) for i in t.loops] for u in m.uv_layers}} for t in m.loop_triangles],'status':'PAINT ALIGNMENT INPUT ONLY; generated images are never model evidence.'}
ev.to_mesh_clear();(OUT/'projection-metadata.json').write_text(json.dumps(data));print('PAINT_PLATE_DONE')
