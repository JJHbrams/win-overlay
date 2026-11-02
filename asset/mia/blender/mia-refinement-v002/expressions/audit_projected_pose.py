"""Read actual projected iris-axis response before accepting a pose critique."""
from pathlib import Path
import bpy,json,numpy as np,math,hashlib
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
P=Path(__file__).resolve().parent;native=P.parent/'integrated/Mia_v0.0.2_Review_R2.blend';digest=hashlib.sha256(native.read_bytes()).hexdigest();assert digest=='eed408b82e9a6160377e92e97fe94ce9619a51393e1ec1d4c928f4a4fd498d82'
bpy.ops.wm.open_mainfile(filepath=str(native),use_scripts=False);s=bpy.context.scene;c=bpy.data.objects['Mia_FacialControls_v002'];cam=s.camera;rows=[]
for panel in [1,4,6]:
 for k in c.keys():
  if k.startswith('P') and k[:3][1:].isdigit():c[k]=1. if int(k[1:3])==panel else 0.
 for manual in [0.,-3.,-5.]:
  c['HeadRoll']=manual;c.update_tag();s.frame_set(panel*10+int(abs(manual)));bpy.context.view_layer.update();dep=bpy.context.evaluated_depsgraph_get();centers=[]
  for sign in [-1,1]:
   o=bpy.data.objects['V28G_Iris_'+str(sign)];ev=o.evaluated_get(dep);mesh=ev.to_mesh();world=np.array([ev.matrix_world@v.co for v in mesh.vertices]);center=Vector((world.min(0)+world.max(0))/2);uv=world_to_camera_view(s,cam,center);centers.append([float(uv.x*512),float((1-uv.y)*512)]);ev.to_mesh_clear()
  centers.sort(key=lambda x:x[0]);angle=math.degrees(math.atan2(centers[1][1]-centers[0][1],centers[1][0]-centers[0][0]));rows.append(dict(panel=panel,manual_roll_delta_deg=manual,iris_bbox_centers_px=centers,projected_axis_deg_y_down=angle))
assert hashlib.sha256(native.read_bytes()).hexdigest()==digest
(P/'actual-projected-pose-axes.json').write_text(json.dumps(dict(native=str(native),sha256=digest,rows=rows,limit='Projected3D iris-box centers, not observed source lid contours. Source hand-marking and gaze/head uncertainty remain; no automatic pose edit or ART claim.'),indent=2)+'\n',encoding='utf-8');print('PROJECTED_POSE_AXES_AUDITED',json.dumps(rows),flush=True)
