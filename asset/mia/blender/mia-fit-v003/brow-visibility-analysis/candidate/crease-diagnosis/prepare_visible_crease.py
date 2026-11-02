"""CPU-only visible-crease JSON challenger. No original data edit/render/save."""
from pathlib import Path
import bpy,json,numpy as np,hashlib
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
P=Path(__file__).resolve().parent
C=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender')
E=C/'mia-fit-v003/eyes';N=C/'mia-refinement-v002/integrated/Mia_v0.0.2_Review_R3b.blend'
SHA='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'
assert hashlib.sha256(N.read_bytes()).hexdigest()==SHA
old=json.loads((E/'upper-crease-vector.json').read_text(encoding='utf-8'))
rec=json.loads((E/'crease-B/render-records.json').read_text(encoding='utf-8'))[0]
rim=json.loads((C/'mia-face-finish-v29/parts/medial-C2/proof/medial-baseline-inspection.json').read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=str(N),use_scripts=False)
for name in rec['hair_temporarily_hidden']:bpy.data.objects[name].hide_render=True
bpy.context.scene.frame_set(rec['camera']['frame']);bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get();incoming=Matrix(rec['camera']['matrix']).to_3x3().col[2].normalized();forward=-incoming
skin=bpy.data.objects['MIA_V27_SharedHeadBody'];e=skin.evaluated_get(dg);m=e.to_mesh(preserve_all_data_layers=True,depsgraph=dg);m.calc_loop_triangles()
q=[e.matrix_world@v.co for v in m.vertices];tri=[list(t.vertices) for t in m.loop_triangles]
uvtri=[[Vector((*m.uv_layers['UVMap'].data[i].uv,0.)) for i in t.loops] for t in m.loop_triangles]
skin_tree=BVHTree.FromPolygons(q,tri,all_triangles=True);e.to_mesh_clear()
trees=[]
for ob in bpy.context.scene.objects:
 if ob.type!='MESH' or ob.hide_render:continue
 ev=ob.evaluated_get(dg);me=ev.to_mesh()
 if me.polygons:trees.append((ob.name,BVHTree.FromPolygons([ev.matrix_world@v.co for v in me.vertices],[list(p.vertices) for p in me.polygons])))
 ev.to_mesh_clear()
def project(p):
 hit,no,face,dist=skin_tree.ray_cast(Vector((float(p[0]),-.2,float(p[2]))),Vector((0,1,0)),.4)
 assert hit is not None
 value=barycentric_transform(hit,*[q[i] for i in tri[face]],*uvtri[face])
 return np.array(value[:2]),hit,int(face)
def owner(point):
 hits=[]
 for name,tree in trees:
  p,no,face,dist=tree.ray_cast(point+incoming*.5,forward,2.)
  if p is not None:hits.append((float(dist),name))
 return min(hits)[1] if hits else None
rows=[];checks=[]
for oldrow in old['creases']:
 side=oldrow['side'];curve=np.array([q[i][:] for i in rim['evaluated_openings'][str(side)]['upper_evaluated_indices']]);axis=curve[-1]-curve[0];axis/=np.linalg.norm(axis);up=np.array([0.,0.,1.])-axis*axis[2];up/=np.linalg.norm(up);points=[]
 for a in oldrow['points']:
  t=a['t'];v=t*(len(curve)-1);i=min(int(v),len(curve)-2);p=curve[i]*(1-(v-i))+curve[i+1]*(v-i)
  scan=[]
  for gap in np.arange(0.,.006001,.00005):
   uv,hit,face=project(p+up*gap);scan.append(dict(gap_mm=float(gap*1000),first_owner=owner(hit)))
  lashname='V30_UpperLashes_'+str(side);hits=[s['gap_mm'] for s in scan if s['first_owner']==lashname]
  assert hits,'No measured opaque upper lash at this station'
  edge=max(hits)+.025
  gap_mm=float(np.clip(edge+.8,3.,5.))
  uv,hit,face=project(p+up*(gap_mm/1000));uv2,_,_=project(p+up*((gap_mm+.17)/1000))
  new_owner=owner(hit);before_owner=owner(Vector(a['world']))
  points.append(dict(t=t,uv=uv.tolist(),half_width_uv=float(np.linalg.norm(uv2-uv)),world=list(hit),skin_triangle=face,gap_from_rim_mm=gap_mm))
  checks.append(dict(side=side,t=t,old_gap_mm=a['gap_from_rim_mm'],before_first_owner=before_owner,opaque_lash_upper_edge_gap_mm=edge,new_gap_from_rim_mm=gap_mm,visible_gap_past_lash_mm=gap_mm-edge,after_first_owner=new_owner,half_width_mm=.17,scan=scan))
 rows.append(dict(side=side,screen=oldrow['screen'],points=points))
uv=skin.data.uv_layers['UVMap'];raw=np.empty(len(uv.data)*2,np.float32);uv.data.foreach_get('uv',raw);uvhash=hashlib.sha256(raw.tobytes()).hexdigest();assert uvhash==old['original_face_UV_sha256']
candidate=dict(baseline_sha256=SHA,UV='UVMap',original_face_UV_sha256=uvhash,creases=rows,method='Challenger only: original actual upper-rim stations; follow measured opaque upper-lash edge at each station plus0.8mm, bounded3..5mm from true rim. Same0.17mm physical half-width. No generic replacement arch, UV remap, lash/opening edit, render or native save.',native_saved=False)
visibility_pass=all(c['after_first_owner']=='MIA_V27_SharedHeadBody' and c['visible_gap_past_lash_mm']>=.6 for c in checks)
candidate['CPU_visibility']={'skin_first_stations':sum(c['after_first_owner']=='MIA_V27_SharedHeadBody' for c in checks),'stations':20,'all20_clearance_pass':visibility_pass,'limit':'Screen-right t=.10/.93 remain lash-covered at5mm cap. Three other points have only.075..575mm clear gap. Do not interpret this challenger as all-point visibility or ART approval.'}
(P/'upper-crease-vector-visible-candidate.json').write_text(json.dumps(candidate,indent=2)+'\n',encoding='utf-8')
report=dict(input_native=str(N),native_sha256=SHA,original_UV_guard=uvhash,old_crease_json_sha256=hashlib.sha256((E/'upper-crease-vector.json').read_bytes()).hexdigest(),actual_front_record_sha256=hashlib.sha256((E/'crease-B/render-records.json').read_bytes()).hexdigest(),station_checks=checks,all20_skin_first_after=visibility_pass,CPU_only=True,render_called=False,native_saved=False,source_context='Source portrait warm upper crease is above the opaque lash stroke, below the separate brow fragments. Visible spacing varies along the real rising canthus curve. Pixel-to-mm equality is not claimed;0.8mm clear gap is a bounded production trial requiring actual source review.',limits='Neutral front evaluated viewport CPU first-surface rays. Direct Emission makes actual upper lash opaque. No new render proof, oblique/closure/expressions or source-distance ART approval.')
(P/'visibility-20-stations-before-after.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
assert hashlib.sha256(N.read_bytes()).hexdigest()==SHA
print('VISIBLE_CREASE_JSON_CPU_DONE',json.dumps([dict(side=c['side'],t=c['t'],old=c['before_first_owner'],new=c['after_first_owner'],rim_gap_mm=c['new_gap_from_rim_mm'],clear_gap_mm=c['visible_gap_past_lash_mm']) for c in checks]),flush=True)
