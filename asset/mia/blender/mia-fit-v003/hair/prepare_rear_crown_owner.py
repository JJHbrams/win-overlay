"""Physical rear Crown art owner with a conservative accepted-front hold."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,heapq,collections
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent;O=P/'v29-pigment';W=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay');N=W/'asset/mia/blender/mia-refinement-v002/integrated/Mia_v0.0.2_Review_R3b.blend';SHA='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1';assert hashlib.sha256(N.read_bytes()).hexdigest()==SHA
bpy.ops.wm.open_mainfile(filepath=str(N),use_scripts=False);bpy.context.scene.frame_set(1);bpy.context.view_layer.update();ob=bpy.data.objects['MIA_V17_PIXAL_DetailedHair'];m=ob.data;d=np.load(O/'fallback-baked-payload.npz');co=np.array([v.co[:] for v in m.vertices],np.float32);points,iv=np.unique(np.round(co,6),axis=0,return_inverse=True);F=iv[d['raw_vertices']];ed=collections.defaultdict(list);adj=collections.defaultdict(list)
for i,t in enumerate(F):
 for j in range(3):ed[tuple(sorted((int(t[j]),int(t[(j+1)%3]))))].append(i)
for a,b in ed:
 length=float(np.linalg.norm(points[a]-points[b]));adj[a].append((b,length));adj[b].append((a,length))
dg=bpy.context.evaluated_depsgraph_get();allco=[];allT=[];names=[];polys=[];owner=[]
for actor in bpy.context.scene.objects:
 if actor.type!='MESH' or actor.hide_render:continue
 e=actor.evaluated_get(dg);me=e.to_mesh();me.calc_loop_triangles();off=len(allco);names.append(actor.name);index=len(names)-1;allco.extend([e.matrix_world@v.co for v in me.vertices]);allT.extend([tuple(off+v for v in t.vertices) for t in me.loop_triangles]);owner.extend([index]*len(me.loop_triangles));polys.extend([t.polygon_index for t in me.loop_triangles]);e.to_mesh_clear()
bvh=BVHTree.FromPolygons(allco,allT,all_triangles=True);camera=next(x['camera'] for x in json.loads((N.parent.parent/'review/integrated-R3b/orbit/render-records.json').read_text()) if x['id']=='000-production');direction=Matrix(camera['matrix']).to_3x3()@Vector((0,0,-1));BC=np.array([[1/3]*3,[.8,.1,.1],[.1,.8,.1],[.1,.1,.8]]);protected=[]
for i,pi in enumerate(d['polygon_indices']):
 for p in BC@co[d['raw_vertices'][i]]:
  loc,n,ti,dist=bvh.ray_cast(Vector(p)-direction*2,direction)
  if ti is not None and names[owner[ti]]==ob.name and polys[ti]==int(pi):protected.append(i);break
fixed=np.unique(F[protected]);distance=np.full(len(points),np.inf);distance[fixed]=0;queue=[(0.,int(v)) for v in fixed];heapq.heapify(queue)
while queue:
 cost,i=heapq.heappop(queue)
 if cost!=distance[i]:continue
 for j,length in adj[i]:
  new=cost+length
  if new<distance[j]:distance[j]=new;heapq.heappush(queue,(new,j))
fade=np.clip(distance/.006,0,1);fade=fade*fade*(3-2*fade);back=np.clip((points[:,1]-.005)/.030,0,1);back=back*back*(3-2*back);weight=back*fade;used=np.unique(F);outside=np.ones(len(points),bool);outside[used]=False;weight[outside]=0;corner=weight[F];assert np.all(corner[protected]==0)
np.savez_compressed(O/'rear-crown-owner.npz',corner_weight=corner.astype(np.float32),protected_face_rows=np.array(protected,np.int32),polygon_indices=d['polygon_indices'])
report=dict(native_sha256=SHA,physical_owner='Existing pure Crown 3D surface. Rear Y smoothstep5..35mm;6mm geodesic fade from held accepted-front-visible Crown vertices. Front visibility is a conservative HOLD certificate, never the paint ROI.',front_camera=camera,front_hold_samples_per_face=4,front_protected_surface_faces=len(protected),front_protected_corner_weight_exact_zero=True,rear_owner_nonzero_faces=int((corner.max(1)>0).sum()),rear_owner_full_faces=int((corner.min(1)==1).sum()),never_touches=['Fringe','Side_Nape','Rear_Waves','front forelocks','bun','braid','face/body'],payload_sha256=hashlib.sha256((O/'rear-crown-owner.npz').read_bytes()).hexdigest(),current_Main_modified=False,native_saved=False,limits='Rest-space owned mask: no camera-following paint switch or global guide removal. Actual front/oblique after integration still required; source art match cannot be certified by this field.')
(O/'rear-crown-owner-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('REAR_CROWN_OWNER_READY',len(protected),report['rear_owner_nonzero_faces'],flush=True)
