"""CPU-only input ownership/raycast/API probe. No render or native save."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;N=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-refinement-v002/integrated/Mia_v0.0.2_Review_R3b.blend');SHA='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1';assert hashlib.sha256(N.read_bytes()).hexdigest()==SHA;bpy.ops.wm.open_mainfile(filepath=str(N),use_scripts=False)
ctrl=bpy.data.objects['Mia_FacialControls_v002']
for n in ctrl.keys():
 if n.startswith('Manual') or (n.startswith('P') and n[:3][1:].isdigit()) or n in ['HeadPitch','HeadYaw','HeadRoll','GazeX','GazeY']:ctrl[n]=0.
ctrl.update_tag();bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
def mesh(o):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh(preserve_all_data_layers=True,depsgraph=bpy.context.evaluated_depsgraph_get());q=[e.matrix_world@v.co for v in me.vertices];f=[tuple(p.vertices) for p in me.polygons];uv={}
 for u in me.uv_layers:
  uv[u.name]=[[float(d.uv[0]),float(d.uv[1])] for d in u.data]
 e.to_mesh_clear();return q,f,uv
targets=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render and o.name.startswith(('MiaHair_CrownFringe_','MiaHair_UnderFringe_')) and not any(s in o.name for s in ['_Edge','_Etch'])]
trees=[];target_info=[]
if not targets:
 meta=json.loads((P/'fringe-target-A.json').read_text());payload=np.load(P/meta['payload']);ob=bpy.data.objects[meta['main_owner']];raw=np.empty(len(ob.data.vertices)*3,np.float32);ob.data.vertices.foreach_get('co',raw);assert hashlib.sha256(raw.tobytes()).hexdigest()==meta['main_raw_co_sha256'];q,f,u=mesh(ob);assert len(q)==meta['main_vertices'] and len(f)==meta['main_faces'];selected=payload['main_face_ids'];faces=[f[int(i)] for i in selected];trees.append((ob.name+'::Fringe',BVHTree.FromPolygons(q,faces)));target_info.append(dict(name=ob.name,selected_faces=len(faces),selected_points=len(payload['main_point_ids']),topological_components=meta['topological_components'],material_backface_culling=[m.use_backface_culling for m in ob.data.materials],payload_sha256=meta['payload_sha256']))
for o in targets:
 q,f,u=mesh(o);trees.append((o.name,BVHTree.FromPolygons(q,f)));a=np.array(q);target_info.append(dict(name=o.name,vertices=len(q),faces=len(f),bounds=[a.min(0).tolist(),a.max(0).tolist()],component=o.get('mia_component'),materials=[m.name if m else None for m in o.data.materials]))
brows=[]
for side in [-1,1]:
 o=bpy.data.objects['V31_SourceBrow_'+str(side)];q,f,uv=mesh(o);samples=[];counts={}
 for i,p in enumerate(q):
  hits=[]
  for name,tree in trees:
   co,no,fi,d=tree.ray_cast(p+Vector((0,-.04,0)),Vector((0,1,0)),.04)
   if co is not None:hits.append((d,name,co,no,fi))
  hit=min(hits,key=lambda h:h[0]) if hits else None
  if hit:
   d,name,co,no,fi=hit;valid=co.y<p.y-.0005 and no.y<-.05;counts[name]=counts.get(name,0)+int(valid);samples.append(dict(index=i,source=list(p),target=list(co),normal=list(no),owner=name,distance_from_front_origin_m=d,foreground_depth_m=p.y-co.y,valid=valid))
 brows.append(dict(owner=o.name,vertices=len(q),faces=len(f),first_last_center=[list(q[1]),list(q[-2])],source_U_first_last=[uv['BrowParamUV'][0][0],uv['BrowParamUV'][-1][0]],active_source_color=[list(n.inputs['Color'].default_value) for n in o.material_slots[0].material.node_tree.nodes if n.type=='EMISSION'],actual_target_hit_counts=counts,miss_count=len(q)-len(samples),samples=samples))
ng=bpy.data.node_groups.new('V003_PROBE_ONLY','GeometryNodeTree');api={}
for name in ['GeometryNodeObjectInfo','GeometryNodeSubdivideMesh','GeometryNodeRaycast','GeometryNodeStoreNamedAttribute','GeometryNodeDeleteGeometry','GeometryNodeSampleIndex','GeometryNodeInputMeshEdgeVertices','GeometryNodeSetPosition','GeometryNodeSetMaterial','GeometryNodeInputNamedAttribute','GeometryNodeRealizeInstances','GeometryNodeJoinGeometry']:
 node=ng.nodes.new(name);props={}
 for prop in ['data_type','domain','mode','mapping','transform_space']:
  if hasattr(node,prop):
   try:props[prop]=[e.identifier for e in node.bl_rna.properties[prop].enum_items]
   except:props[prop]=str(getattr(node,prop))
 api[name]=dict(inputs=[dict(name=x.name,id=x.identifier,hide=x.hide,type=x.type) for x in node.inputs],outputs=[dict(name=x.name,id=x.identifier,hide=x.hide,type=x.type) for x in node.outputs],properties=props)
report=dict(native=str(N),sha256=SHA,targets=target_info,brows=brows,node_API=api,native_unchanged=hashlib.sha256(N.read_bytes()).hexdigest()==SHA,native_saved=False,GPU_used=False)
(P/'inputs-and-node-API.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('BROW_DISPLAY_INPUTS_DONE',json.dumps(dict(target_count=len(targets),brows=[dict(owner=r['owner'],hit_counts=r['actual_target_hit_counts'],misses=r['miss_count']) for r in brows])),flush=True)
