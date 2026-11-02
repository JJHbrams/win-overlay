"""Whole natural-shell U assembly; no spatial/camera triangle selection."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,sys,collections
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent;W=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay');N=W/'asset/mia/blender/mia-refinement-v002/integrated/Mia_v0.0.2_Review_R3b.blend';SHA='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1';assert hashlib.sha256(N.read_bytes()).hexdigest()==SHA
d=np.load(P/'source-mesh-input.npz');labels=np.load(P/'global-components.npz')['face_component'];family=json.loads((P/'logical-family-DATA.json').read_text());parts=sorted(set(sum(family['groups'].values(),[])));branch=np.load(P/'backing-branch-DATA.npz')['polygon_indices'];ids=np.load(P/'logical-family-DATA.npz')['polygon_indices'];assert len(ids)==1781;co=d['co'];T=d['faces'];raw=d['raw_ids'];sem=d['semantic_weights'];assert sem[T[ids],3].min()>.99 and sem[T[ids]][:,:,[0,1,2,5]].max()<1e-6
points,iv=np.unique(np.round(co,6),axis=0,return_inverse=True);F=iv[T];all_edges=collections.defaultdict(list)
for i,t in enumerate(F):
 for a,b in [(t[0],t[1]),(t[1],t[2]),(t[2],t[0])]:all_edges[tuple(sorted((int(a),int(b))))].append(i)
selected=set(ids.tolist());external=[];part_reports=[]
for k in parts:
 rows=np.flatnonzero(labels==k);counts=collections.Counter(tuple(sorted((int(a),int(b)))) for t in F[rows] for a,b in [(t[0],t[1]),(t[1],t[2]),(t[2],t[0])]);boundary=[e for e,c in counts.items() if c==1];cuts=[e for e in boundary if any(f not in set(rows.tolist()) for f in all_edges[e])];assert not cuts;part_reports.append(dict(component=k,faces=len(rows),natural_boundary_edges=len(boundary),artificial_attachment_cuts=0,bounds=[co[np.unique(T[rows])].min(0).tolist(),co[np.unique(T[rows])].max(0).tolist()],source_ids=d['raw_ids'][rows].tolist()))
branchset=set(branch.tolist());root_edges=[e for e,fs in all_edges.items() if any(f in branchset for f in fs) and any(f not in branchset for f in fs)];assert len(root_edges)==4;root_points=points[np.array(root_edges)].mean(1);part_reports.append(dict(component='488/U-root-branch',faces=len(branch),topological_join_z=1.4541616439819336,artificial_attachment_cuts=4,root_edge_coordinates=points[np.array(root_edges)].tolist(),root_points=root_points.tolist(),bounds=[co[np.unique(T[branch])].min(0).tolist(),co[np.unique(T[branch])].max(0).tolist()],source_ids=raw[branch].tolist()))
bpy.ops.wm.open_mainfile(filepath=str(N),use_scripts=False);s=bpy.context.scene;s.frame_set(1);sys.path.insert(0,str(P.parent));import apply_baked_v29_crown;apply_baked_v29_crown.apply(P.parent/'v29-pigment',mode='combined');bpy.context.view_layer.update();main=bpy.data.objects['MIA_V17_PIXAL_DetailedHair'];m=main.data;assert np.array_equal(np.array([v.co[:] for v in m.vertices],np.float32),co);dg=bpy.context.evaluated_depsgraph_get();geo=[]
for ob in s.objects:
 if ob.type!='MESH' or ob.hide_render:continue
 e=ob.evaluated_get(dg);me=e.to_mesh();me.calc_loop_triangles();verts=np.array([e.matrix_world@v.co for v in me.vertices]);tris=np.array([t.vertices[:] for t in me.loop_triangles]);polys=np.array([t.polygon_index for t in me.loop_triangles]);geo.append((ob.name,verts,tris,polys,ob.get('mia_component')=='hair'));e.to_mesh_clear()
def bvh(hidden):
 coords=[];tri=[];owner=[];poly=[];hair=[]
 for name,c,t,p,is_hair in geo:
  use=~np.isin(p,ids) if hidden and name==main.name else np.ones(len(t),bool);off=len(coords);coords.extend(c.tolist());tri.extend((t[use]+off).tolist());owner.extend([name]*int(use.sum()));poly.extend(p[use].tolist());hair.extend([is_hair]*int(use.sum()))
 return BVHTree.FromPolygons(coords,tri,all_triangles=True),owner,poly,hair
before,bo,bp,bh=bvh(False);after,ao,ap,ah=bvh(True);records=json.loads((N.parent.parent/'review/integrated-R3b/orbit/render-records.json').read_text());views={v:next(x['camera'] for x in records if x['id']==v+'-production') for v in ['000','003','021','006','018']};views.update({x['name']:x for x in json.loads((P/'firsthit-views.json').read_text()) if x['name'] in ['back_full','rear_low_full','oblique_low_full']});world=d['world_matrix'];xyz=co[T[ids]]@world[:3,:3].T+world[:3,3];BC=np.array([[1/3]*3,[.9,.05,.05],[.05,.9,.05],[.05,.05,.9],[.475,.475,.05],[.475,.05,.475],[.05,.475,.475]]);coverage=[]
for name,v in views.items():
 direction=Matrix(v['matrix']).to_3x3()@Vector((0,0,-1));counts=collections.Counter();parts_seen=collections.Counter();visible_positions=[];visible_source_faces=set()
 for fi,tri in zip(ids,xyz):
  for p in BC@tri:
   origin=Vector(p)-direction*2;hit,n,ti,dist=before.ray_cast(origin,direction)
   if ti is None or bo[ti]!=main.name or bp[ti] not in selected:continue
   counts['baseline_selected_visible_samples']+=1;parts_seen[int(labels[bp[ti]])]+=1;visible_positions.append(list(hit));visible_source_faces.add(int(raw[bp[ti]]));hit,n,ti,dist=after.ray_cast(origin,direction)
   if ti is None:counts['background']+=1
   elif ah[ti]:counts['retained_hair']+=1
   elif ao[ti]=='MIA_V27_SharedHeadBody':counts['retained_body']+=1
   else:counts['other_retained_surface']+=1
 root_visibility=[]
 for p in root_points@world[:3,:3].T+world[:3,3]:
  hit,n,ti,dist=after.ray_cast(Vector(p)-direction*2,direction);root_visibility.append(dict(first_owner=ao[ti] if ti is not None else None,first_hair=bool(ah[ti]) if ti is not None else False,depth_to_root=float(np.linalg.norm(np.array(hit)-p)) if ti is not None else None,first_before_root=bool(ti is not None and dist<2-.00005)))
 coverage.append(dict(view=name,counts=dict(counts),complete_pieces_seen=dict(parts_seen),visible_hit_bounds=[np.min(visible_positions,axis=0).tolist(),np.max(visible_positions,axis=0).tolist()] if visible_positions else None,visible_source_faces=sorted(visible_source_faces),backing_root_edge_midpoints=root_visibility))
(P/'candidate-family-coverage-DATA.json').write_text(json.dumps(coverage,indent=2)+'\n',encoding='utf-8')
if '--ownership-data' in sys.argv:
 maps={};size=384
 for name in ['000','003','021','018','back_full']:
  v=views[name];cam=Matrix(v['matrix']);scale=v['ortho_scale'];direction=cam.to_3x3()@Vector((0,0,-1));owner_map=np.zeros((size,size),np.uint8);normal_map=np.zeros((size,size,3),np.float32);source_map=np.full((size,size),-1,np.int32)
  for y in range(size):
   for x in range(size):
    origin=cam@Vector((((x+.5)/size-.5)*scale,(.5-(y+.5)/size)*scale,0));hit,n,ti,dist=before.ray_cast(origin,direction)
    if ti is None:continue
    owner_map[y,x]=4 if bo[ti]==main.name and bp[ti] in selected else 3 if bh[ti] else 2 if bo[ti]=='MIA_V27_SharedHeadBody' else 1;normal_map[y,x]=n;source_map[y,x]=bp[ti] if bo[ti]==main.name else -1
  maps[name+'_owner']=owner_map;maps[name+'_normal']=normal_map;maps[name+'_source_polygon']=source_map;print('OWNERSHIP_DATA',name,flush=True)
 np.savez_compressed(P/'fullscene-family-ownership-DATA.npz',**maps);(P/'fullscene-family-views-DATA.json').write_text(json.dumps({name:views[name] for name in ['000','003','021','018','back_full']},indent=2)+'\n',encoding='utf-8')
assert '--authorize-lower-rear-front-visibility' in sys.argv or next(x for x in coverage if x['view']=='000')['counts'].get('baseline_selected_visible_samples',0)==0,'Selected loop is visible in accepted front; inspect candidate-family-coverage-DATA.json before any production authorization'
old_indices=np.array([m.polygons[int(i)].material_index for i in ids],np.int32);assert np.all(old_indices==0);np.savez_compressed(P/'loop-mask.npz',polygon_indices=ids.astype(np.int32),raw_source_ids=raw[ids],raw_vertices=T[ids],original_material_indices=old_indices)
manifest=dict(native_sha256=SHA,main_co_sha256=hashlib.sha256(co.tobytes()).hexdigest(),main_topology_sha256=hashlib.sha256(T.tobytes()).hexdigest(),payload_sha256=hashlib.sha256((P/'loop-mask.npz').read_bytes()).hexdigest(),selected_complete_components=parts,selected_faces=len(ids),parts=part_reports,ownership='Twenty-seven complete natural-boundary U/return skin components plus the438-face backing branch traced to its first narrow topological join (four attachment edges). Initial6-skin mask was rejected because the backing U remained. Runtime uses explicit source face IDs, never a camera ROI or dynamic coordinate threshold.',front_sample_visibility_zero=False,scope_exception='Root reviewed full-scene CPU ownership and original-aspect v22 back/profile; explicitly accepted lower nape/shoulder pure Rear_Waves visibility. Accepted facial forelocks, bangs, braid and bun remain outside ownership.',coverage=coverage,samples='Seven inset/edge/centre barycentric samples per selected face, duplicate rays allowed; counts are diagnostic samples, not projected area. Four exact backing root-edge midpoints also tested against retained full scene.',all_original_geometry_UV_fields_weights_keys_normals_unchanged=True,mask_type='Reversible exact-face transparent material only; hidden raw geometry remains and must be excluded if a future collision proxy uses this source.',ART=False,native_saved=False,source_limit='Source v22 rear/profile show flowing individual ends rather than this wide suspended U. Qualitative source design comparison, not uniquely recovered hidden anatomy/strand depth. Actual root review required.')
(P/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(selected_faces=len(ids),whole_pieces=len(parts),backing_branch_faces=len(branch),artificial_attachment_cuts=4,coverage=coverage),indent=2),flush=True)
