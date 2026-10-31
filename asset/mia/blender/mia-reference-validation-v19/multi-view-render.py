import bpy,sys,math,json,hashlib
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3];sys.path.insert(0,str(ROOT/'tools/mia/blender'));import refine_mia_head_v06 as h
source=Path(r'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v17/integrated-v18/Mia_HeadHair_v18.blend');sha=hashlib.sha256(source.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.context.scene;s.render.resolution_x=s.render.resolution_y=896;s.render.resolution_percentage=100;s.camera.data.ortho_scale=.48;s.render.film_transparent=False;records=[]
for angle in [20,35]:
 y=math.radians(angle);h._aim(s.camera,(2*math.sin(y),-2*math.cos(y),1.555),(0,0,1.555));s.render.filepath=str(OUT/('multi-view-model-yaw'+str(angle)+'.png'));bpy.ops.render.render(write_still=True);records.append({'yaw_deg':angle,'path':s.render.filepath,'ortho_scale':.48,'target':[0,0,1.555],'resolution':[896,896],'camera_matrix_world':[list(r) for r in s.camera.matrix_world]})
(OUT/'multi-view-new-camera-renders.json').write_text(json.dumps({'source':str(source),'sha_before':sha,'sha_after':hashlib.sha256(source.read_bytes()).hexdigest(),'native_saved':False,'renders':records},indent=2))
