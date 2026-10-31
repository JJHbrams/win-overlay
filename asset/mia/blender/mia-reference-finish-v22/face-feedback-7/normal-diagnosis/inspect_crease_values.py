import bpy,json,math,hashlib
from pathlib import Path
from collections import Counter
H=Path(__file__).resolve().parent;data=json.loads((H/'normal-report.json').read_text());out={}
for label,row in data['sources'].items():
 path=Path(row['source']['path']);bpy.ops.wm.open_mainfile(filepath=str(path));o=bpy.data.objects['MIA_V14_SculptedSkin'];m=o.data;a=m.attributes.get('crease_edge');creases=[]
 if a:
  for e,v in zip(m.edges,a.data):
   if v.value:creases.append({'id':e.index,'crease':v.value,'vertices':list(e.vertices),'coords':[list(m.shape_keys.key_blocks[0].data[i].co) for i in e.vertices]})
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();norms=[n.vector.copy() for n in me.corner_normals];region=[]
 for p in me.polygons:
  c=p.center
  if .015<abs(c.x)<.055 and 1.490<c.z<1.540 and c.y>.025:
   for li in p.loop_indices:region.append(math.degrees(norms[li].angle(p.normal)))
 ev.to_mesh_clear();out[label]={'nonzero_crease_edges':creases,'material_polygon_counts':dict(Counter(p.material_index for p in m.polygons)),'inner_cheek_corner_vs_polygon_normal_angle':{'count':len(region),'max':max(region),'median':sorted(region)[len(region)//2]},'source_unchanged':hashlib.sha256(path.read_bytes()).hexdigest()==row['source']['sha256']}
(H/'crease-supplement.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
