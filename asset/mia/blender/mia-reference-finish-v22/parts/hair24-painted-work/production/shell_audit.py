import bpy,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).parent
bpy.ops.wm.open_mainfile(filepath=str(P/'Mia_HairStructure_v24.blend'),use_scripts=False)
o=bpy.data.objects['MIA_V17_PIXAL_DetailedHair'];tree=BVHTree.FromPolygons([v.co for v in o.data.vertices],[p.vertices for p in o.data.polygons])
rows=[]
for z in [1.54,1.55,1.56,1.57,1.58,1.59,1.60,1.61]:
 for x in [-.03,-.015,0,.015,.03]:
  co,no,idx,d=tree.ray_cast(Vector((x,.3,z)),Vector((0,-1,0)))
  rows.append(dict(x=x,z=z,y=co.y if co else None,poly=idx))
(P/'shell-audit.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows))
