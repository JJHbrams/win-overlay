import bpy,numpy as np,json,hashlib
from mathutils.kdtree import KDTree
from pathlib import Path
O=Path(__file__).parent;OUT=O/'face-shared-final';S=OUT/'Mia_Foundation_v27.blend';bpy.ops.wm.open_mainfile(filepath=str(S));old=bpy.data.objects['MIA_V06_BODY_SKIN'];new=bpy.data.objects['MIA_V27_SharedHeadBody'];old.hide_viewport=False;old.hide_set(False);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
def get(o):
 ev=o.evaluated_get(dg);m=ev.to_mesh();ids=sorted(set(i for p in m.polygons if o==old or p.material_index>0 for i in p.vertices));co=np.array([ev.matrix_world@m.vertices[i].co for i in ids]);uvs={i:[] for i in ids}
 for p in m.polygons:
  if o==new and p.material_index==0:continue
  for li in p.loop_indices:uvs[m.loops[li].vertex_index].append(tuple(m.uv_layers['UVMap'].data[li].uv))
 result=(co,[uvs[i] for i in ids]);ev.to_mesh_clear();return result
a,au=get(old);b,bu=get(new)
def match(p,q,pu,qu):
 tree=KDTree(len(q))
 for i,v in enumerate(q):tree.insert(v,i)
 tree.balance();dist=[];ud=[]
 for v,uv in zip(p,pu):
  _,j,d=tree.find(v);dist.append(d);near=tree.find_range(v,1e-6);candidates=[k for _,k,_ in near] if near else [j];alluv=[y for k in candidates for y in qu[k]];ud.append(max(min(np.linalg.norm(np.array(x)-y) for y in alluv) for x in uv))
 return np.array(dist),np.array(ud)
ab,auv=match(a,b,au,bu);ba,buv=match(b,a,bu,au);affected=np.concatenate([a[ab>1e-6],b[ba>1e-6]])
regions={}
for z in [1.35,1.4]:
 regions[str(z)]={'source_vertices':int(sum(a[:,2]<z)),'candidate_vertices':int(sum(b[:,2]<z)),'bidirectional_max_distance_m':float(max(ab[a[:,2]<z].max(),ba[b[:,2]<z].max())),'max_nearest_corner_uv_difference':float(max(auv[a[:,2]<z].max(),buv[b[:,2]<z].max()))}
report={'native_sha256':hashlib.sha256(S.read_bytes()).hexdigest(),'method':'Bidirectional evaluated original-Body vertex set correspondence; group-constrained Weld changes evaluation index order, so raw polygon order is not correspondence. Body control indices and per-corner UV are independently unchanged outside shared boundary.','whole_body_max_surface_vertex_distance_m':float(max(ab.max(),ba.max())),'affected_bbox_min':affected.min(0).tolist() if len(affected) else None,'affected_bbox_max':affected.max(0).tolist() if len(affected) else None,'affected_threshold_m':1e-6,'protected_regions':regions}
(OUT/'shared-correspondence-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
