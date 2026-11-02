"""Compare exact retained UVs and prepare a 3D-owned boundary-safe fallback gate."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,heapq,collections
P=Path(__file__).resolve().parent;O=P/'v29-pigment';W=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay');N=W/'asset/mia/blender/mia-refinement-v002/integrated/Mia_v0.0.2_Review_R3b.blend';SHA='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1';assert hashlib.sha256(N.read_bytes()).hexdigest()==SHA
bpy.ops.wm.open_mainfile(filepath=str(N),use_scripts=False);ob=bpy.data.objects['MIA_V17_PIXAL_DetailedHair'];m=ob.data;d=np.load(O/'exact-correspondence.npz');cfg=json.loads((O/'extraction-report.json').read_text());uvname=cfg['source_uv'];assert uvname in m.uv_layers;ids=d['current_polygon_indices'];UV=np.array([[m.uv_layers[uvname].data[j].uv[:] for j in m.polygons[int(i)].loop_indices] for i in ids],np.float32);assert np.array_equal(UV,d['old_loop_uv']),'Existing original UV does not match exact v29 corners'
co=np.array([v.co[:] for v in m.vertices],np.float32);T=np.array([p.vertices[:] for p in m.polygons],np.int32);assert np.array_equal(T[ids],d['raw_vertices']);assert all(m.polygons[int(i)].material_index==0 for i in ids)
# Weld only the numerical proxy: preserve all original UV seam vertex copies.
points,first,iv=np.unique(np.round(co,6),axis=0,return_index=True,return_inverse=True);F=iv[T[ids]];edge=collections.Counter(tuple(sorted((int(a),int(b)))) for t in F for a,b in [(t[0],t[1]),(t[1],t[2]),(t[2],t[0])]);boundary=np.unique([v for e,c in edge.items() if c!=2 for v in e]);used=np.unique(F);adj=collections.defaultdict(list)
for a,b in edge:
 length=float(np.linalg.norm(points[a]-points[b]));adj[a].append((b,length));adj[b].append((a,length))
distance=np.full(len(points),np.inf);distance[boundary]=0;queue=[(0.,int(v)) for v in boundary];heapq.heapify(queue)
while queue:
 cost,i=heapq.heappop(queue)
 if cost!=distance[i]:continue
 for j,length in adj[i]:
  value=cost+length
  if value<distance[j]:distance[j]=value;heapq.heappush(queue,(value,j))
fade=np.clip(distance/.004,0,1);fade=fade*fade*(3-2*fade);owned=np.zeros(len(points),bool);owned[used]=True;fade[~owned]=0;weights=fade[iv].astype(np.float32)
# Physical proxies can share points across the material boundary. All boundary
# endpoint weights must be exact0 so the old live fallback joins continuously.
assert np.all(weights[np.flatnonzero(np.isin(iv,boundary))]==0)
np.savez_compressed(O/'fallback-payload.npz',polygon_indices=ids,raw_source_ids=d['raw_source_ids'],raw_vertices=d['raw_vertices'],old_loop_uv=UV,interior_weight=weights,boundary_segments=points[np.array([e for e,c in edge.items() if c!=2])])
ma=m.materials[0];mix=ma.node_tree.nodes['V002_COHERENT_AUTHORED_PIGMENT'];assert not mix.inputs[1].is_linked and np.allclose(mix.inputs[1].default_value[:3],[.12,.115,.12]);out=next(n for n in ma.node_tree.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output);seen=set();stack=[out]
while stack:
 n=stack.pop()
 if n in seen:continue
 seen.add(n)
 for inp in n.inputs:
  for link in inp.links:stack.append(link.from_node)
report=dict(current_native_sha256=SHA,current_coords_sha256=hashlib.sha256(co.tobytes()).hexdigest(),source_uv=uvname,all4999_corner_UVs_byte_exact=True,original_six_UV_hashes={u.name:hashlib.sha256(np.array([v.uv[:] for v in u.data],np.float32).tobytes()).hexdigest() for u in m.uv_layers},new_UV_layers_needed=0,old_UV_overlap='Original source atlas may intentionally reuse regions; exact old paint/corner lineage, not a new overlapping atlas. New candidate adds no UV map and no generated color field.',real_surface_faces=len(ids),full_boundary_vertices=len(boundary),boundary_vertex_weight_exact_zero=True,interior_fade_distance_mm=4,nonzero_weight_vertices=int((weights>0).sum()),full_weight_vertices=int((weights==1).sum()),current_active_attributes=sorted({n.attribute_name for n in seen if n.type=='ATTRIBUTE'}),current_active_UV_names=sorted({n.uv_map for n in seen if n.type=='UVMAP'}),original_fallback_default=list(mix.inputs[1].default_value),original_guide_factor_source=mix.inputs[0].links[0].from_node.name,guide_input_source=mix.inputs[2].links[0].from_node.name,payload_sha256=hashlib.sha256((O/'fallback-payload.npz').read_bytes()).hexdigest(),source_image_sha256=cfg['source_image_sha256'],old_normal_map_reused=False,Main_modified=False,native_saved=False,limits='CPU identity/boundary gate only. Old alpha and actual current-model pigment+production/source views still required. Texture may align numerically while hair strokes remain artistically wrong.')
(O/'current-UV-boundary-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2),flush=True)
