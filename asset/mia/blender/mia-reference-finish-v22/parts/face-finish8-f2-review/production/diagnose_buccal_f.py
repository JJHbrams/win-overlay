"""Actual evaluated front-sheet depth and curvature samples; read-only D/E."""
import bpy,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'shape-f';OUT.mkdir(exist_ok=True);report={}
for label,path in [('D',ROOT/'look-d/Mia_FaceFinish8_AuthoredLookD.blend'),('E',ROOT/'shape-e/Mia_FaceFinish8_ConnectedCheekE.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(path));o=bpy.data.objects['MIA_V14_SculptedSkin'];keys=o.data.shape_keys.key_blocks
 for k in keys:k.value=0
 bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();p=np.array([tuple(v.co) for v in m.vertices]);faces=[list(f.vertices) for f in m.polygons];bvh=BVHTree.FromPolygons([Vector(v) for v in p],faces)
 xs=np.arange(.014,.0521,.001);zs=np.arange(1.488,1.5361,.001);grid=np.full((len(zs),len(xs)),np.nan);normals=np.zeros((len(zs),len(xs),3))
 for zi,z in enumerate(zs):
  for xi,x in enumerate(xs):
   hit,n,index,distance=bvh.ray_cast(Vector((x,.2,z)),Vector((0,-1,0)),.3)
   if hit is not None:grid[zi,xi]=hit.y;normals[zi,xi]=n
 props=[]
 for mod in o.modifiers:
  row={'name':mod.name,'type':mod.type,'show_render':mod.show_render,'show_viewport':mod.show_viewport}
  for field in ['levels','render_levels','subdivision_type','use_custom_normals','uv_smooth','use_limit_surface']:
   if hasattr(mod,field):row[field]=getattr(mod,field)
  props.append(row)
 sharp=o.data.attributes.get('sharp_edge');crease=o.data.attributes.get('crease_edge')
 report[label]={'native':{'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()},'coordinate_space':'evaluated mesh local; +Y anterior, ray+0.2Ytoward-Y. Same owner, frame, neutral keys and modifier stack.','xs':xs.tolist(),'zs':zs.tolist(),'depth_y':[[None if not np.isfinite(v) else float(v) for v in row] for row in grid],'normals':normals.tolist(),'cage':[list(v.co) for v in keys[0].data],'faces':[list(f.vertices) for f in o.data.polygons],'smooth_polygons':sum(f.use_smooth for f in o.data.polygons),'polygon_count':len(o.data.polygons),'custom_normals':getattr(o.data,'has_custom_normals',False),'sharp_edges':sum(v.value for v in sharp.data) if sharp else 0,'creases':[{'edge':list(o.data.edges[i].vertices),'value':v.value} for i,v in enumerate(crease.data) if v.value] if crease else [],'modifiers':props}
 ev.to_mesh_clear()
(OUT/'evaluated-buccal-diagnosis.json').write_text(json.dumps(report,indent=2));print('BUCCAL_DIAGNOSED')
