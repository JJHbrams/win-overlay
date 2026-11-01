import bpy,bmesh,json,hashlib,numpy as np
from pathlib import Path
P=Path(__file__).parent/'paint1';handoff=json.loads((P/'handoff.json').read_text())
def scope(o):
 h=hashlib.sha256()
 for v in o.data.vertices:h.update(np.array(v.co[:],dtype=np.float32).tobytes())
 for p in o.data.polygons:h.update(np.array(p.vertices[:],dtype=np.uint32).tobytes())
 for uv in o.data.uv_layers:
  for value in uv.data:h.update(np.array(value.uv[:],dtype=np.float32).tobytes())
 return h.hexdigest()
bpy.ops.wm.open_mainfile(filepath=handoff['candidate_native']['path'],use_scripts=False)
retained=scope(bpy.data.objects['MIA_V17_PIXAL_DetailedHair']);rows=[]
for name in handoff['new_owners']:
 o=bpy.data.objects[name];m=o.data;m.calc_loop_triangles();bm=bmesh.new();bm.from_mesh(m);bad=sum(not e.is_manifold for e in bm.edges);bm.free();uvcounts={}
 for uv in m.uv_layers:
  areas=[]
  for t in m.loop_triangles:
   a,b,c=[uv.data[i].uv for i in t.loops];areas.append(abs((b-a).cross(c-a))/2)
  uvcounts[uv.name]={'zero_area_triangles':sum(a<1e-12 for a in areas),'minimum_area':min(areas)}
 mat=m.materials[0];nodes=mat.node_tree.nodes;out=next(n for n in nodes if n.type=='OUTPUT_MATERIAL');todo=[out];seen=set();images=[]
 while todo:
  n=todo.pop()
  if n.name in seen:continue
  seen.add(n.name)
  if n.type=='TEX_IMAGE' and n.image:images.append({'node':n.name,'image':n.image.name,'size':list(n.image.size),'colorspace':n.image.colorspace_settings.name,'packed':bool(n.image.packed_file),'filepath':n.image.filepath})
  todo.extend(l.from_node for socket in n.inputs for l in socket.links)
 rows.append({'owner':name,'vertices':len(m.vertices),'faces':len(m.polygons),'nonmanifold_edges':bad,'uv':uvcounts,'shape_keys':bool(m.shape_keys),'modifiers':[q.type for q in o.modifiers],'matrix_world':[list(r) for r in o.matrix_world],'parent':o.parent.name if o.parent else None,'connected_images':images,'material':mat.name,'connected_nodes':sorted(seen)})
bpy.ops.wm.open_mainfile(filepath=handoff['source_native']['path'],use_scripts=False)
source_scope=scope(bpy.data.objects['MIA_V17_PIXAL_DetailedHair'])
report={'technical_pass':retained==source_scope and all(r['nonmanifold_edges']==0 and all(u['zero_area_triangles']==0 for u in r['uv'].values()) and any(i['packed'] for i in r['connected_images']) for r in rows),'original_detailed_hair_unchanged':retained==source_scope,'detailed_hair_scope':retained,'owners':rows,'art_acceptance':'UNAPPROVED; technical validity is not source likeness','scope':'Three rear gathered owners only; original detailed hair and extraction failures unchanged'}
(P/'validation.json').write_text(json.dumps(report,indent=2));print('TECHNICAL_PASS',report['technical_pass'])
