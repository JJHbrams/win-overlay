import bpy,bmesh,json,hashlib,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(sys.argv[sys.argv.index('--')+1]) if '--' in sys.argv else Path(__file__).parent
bpy.ops.wm.open_mainfile(filepath=str(P/'Mia_HairStructure_v24.blend'),use_scripts=False)
rows=[]
old=bpy.data.objects['MIA_V17_PIXAL_DetailedHair'];tree=BVHTree.FromPolygons([v.co for v in old.data.vertices],[p.vertices for p in old.data.polygons])
for o in bpy.data.objects:
 if not o.name.startswith('MIA_V24_Gather_'):continue
 m=o.data;m.calc_loop_triangles();uv=m.uv_layers['MIA_V20_LongitudinalUV'];areas=[]
 for t in m.loop_triangles:
  a,b,c=[uv.data[i].uv for i in t.loops];areas.append(abs((b-a).cross(c-a))/2)
 bm=bmesh.new();bm.from_mesh(m);boundary=sum(e.is_boundary for e in bm.edges);nonmanifold=sum(not e.is_manifold for e in bm.edges);bm.free()
 root=[]
 for idx in [0,48*80]:
  c=sum((m.vertices[idx+j].co for j in range(48)),Vector())/48
  co,no,poly,d=tree.ray_cast(Vector((c.x,.3,c.z)),Vector((0,-1,0)))
  root.append(dict(center=list(c),posterior_surface=list(co) if co else None,depth_into_shell_m=co.y-c.y if co else None,poly=poly))
 rows.append(dict(name=o.name,vertices=len(m.vertices),faces=len(m.polygons),boundary_edges=boundary,nonmanifold_edges=nonmanifold,zero_uv_triangles=sum(a<1e-12 for a in areas),min_uv_area=min(areas),parent=o.parent.name if o.parent else None,matrix_world=[list(r) for r in o.matrix_world],modifiers=[m.type for m in o.modifiers],shape_keys=bool(m.shape_keys),uv=[l.name for l in m.uv_layers],roots=root))
(P/'verification.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
