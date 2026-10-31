"""Read-only evaluated geometry landmarks and exact canonical camera, no native save."""
import bpy,sys,math,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
OUT=Path(__file__).resolve().parent;ROOT=Path(r'C:/Users/antio/.codex/worktrees/mia-final-face-v12/win-overlay');sys.path.insert(0,str(ROOT/'tools/mia/blender'));import refine_mia_head_v06 as h
SOURCE=OUT/'Mia_FaceCorrection_v20.blend'
REF=Path(r'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/references/received/mia-face-reaffirmed-20261031.png')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source_sha=sha(SOURCE);bpy.ops.wm.open_mainfile(filepath=str(SOURCE));s=bpy.context.scene;cam=s.camera
s.render.resolution_x=s.render.resolution_y=1000;s.render.resolution_percentage=100;s.render.pixel_aspect_x=s.render.pixel_aspect_y=1;cam.data.type='ORTHO';cam.data.ortho_scale=.29;cam.data.shift_x=cam.data.shift_y=0;h._aim(cam,(0,-2,1.55),(0,0,1.55));bpy.context.view_layer.update()
def point(p):
 q=world_to_camera_view(s,cam,p)
 return {'world_m':list(p),'pixel_top_left':[q.x*1000,(1-q.y)*1000],'camera_ndc':[q.x,q.y,q.z]}
def evaluated(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh(preserve_all_data_layers=True,depsgraph=bpy.context.evaluated_depsgraph_get());return ev,me,[ev.matrix_world@v.co for v in me.vertices]
skin=bpy.data.objects['MIA_V14_SculptedSkin'];eyes=bpy.data.objects['MIA_V14_EyeSurface'];body=bpy.data.objects[h.BODY_NAME]
ev,me,pts=evaluated(skin);faces=[list(p.vertices) for p in me.polygons];bvh=BVHTree.FromPolygons(pts,faces)
adj=[set() for p in pts];edgeuse={}
for f in faces:
 for i,j in zip(f,f[1:]+[f[0]]):
  adj[i].add(j);adj[j].add(i);edge=tuple(sorted((i,j)));edgeuse[edge]=edgeuse.get(edge,0)+1
seen=set();components=[]
for start in range(len(pts)):
 if start in seen:continue
 stack=[start];seen.add(start);comp=[]
 while stack:
  i=stack.pop();comp.append(i)
  for j in adj[i]:
   if j not in seen:seen.add(j);stack.append(j)
 components.append(comp)
components.sort(key=len,reverse=True);main=set(components[0])
# Separate UV charts: the geometry joins ears to the head, but their UV seams
# provide an actual mesh-defined anatomical exclusion without a shadow threshold.
parent=list(range(len(me.polygons)))
def find(i):
 while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
 return i
uedges={};uvlayer=me.uv_layers.active
for poly in me.polygons:
 corners=[(me.loops[i].vertex_index,round(uvlayer.data[i].uv.x,6),round(uvlayer.data[i].uv.y,6)) for i in poly.loop_indices]
 for ca,cb in zip(corners,corners[1:]+[corners[0]]):
  key=tuple(sorted((ca,cb)))
  if key in uedges:parent[find(poly.index)]=find(uedges[key])
  else:uedges[key]=poly.index
charts={}
for poly in me.polygons:charts.setdefault(find(poly.index),[]).append(poly.index)
chartlist=sorted(charts.values(),key=len,reverse=True);facechart=set(chartlist[0]);chartinfo=[]
for chart in chartlist:
 ids={i for f in chart for i in me.polygons[f].vertices};ar=np.array([tuple(pts[i]) for i in ids]);chartinfo.append({'polygons':len(chart),'vertices':len(ids),'min':ar.min(0).tolist(),'max':ar.max(0).tolist(),'center':ar.mean(0).tolist()})
badj={}
for edge,n in edgeuse.items():
 if n==1:
  i,j=edge;badj.setdefault(i,set()).add(j);badj.setdefault(j,set()).add(i)
visited=set();loops=[]
for start in badj:
 if start in visited:continue
 order=[];prev=None;cur=start
 while cur not in visited:
  visited.add(cur);order.append(cur);nxt=[j for j in badj[cur] if j!=prev]
  if not nxt:break
  prev,cur=cur,nxt[0]
 ar=np.array([tuple(pts[i]) for i in order]);loops.append({'ids':order,'count':len(order),'center':ar.mean(0).tolist(),'min':ar.min(0).tolist(),'max':ar.max(0).tolist(),'points':[point(pts[i]) for i in order]})
mouth_candidates=[l for l in loops if abs(l['center'][0])<.025 and 1.478<l['center'][2]<1.510 and l['center'][1]<-.035 and l['max'][0]-l['min'][0]<.08]
mouth=max(mouth_candidates,key=lambda l:l['count']) if mouth_candidates else None
eye_loops=[l for l in loops if .012<abs(l['center'][0])<.065 and 1.524<l['center'][2]<1.559 and l['center'][1]<-.025 and l['max'][0]-l['min'][0]<.08]
landmarks={'chin_actual_mesh_min_z':point(min((pts[i] for i in main),key=lambda p:p.z))}
if mouth:
 mp=[pts[i] for i in mouth['ids']];left=min(mp,key=lambda p:p.x);right=max(mp,key=lambda p:p.x);center=min(mp,key=lambda p:abs(p.x));mouthz=sum(p.z for p in mp)/len(mp)
 landmarks['mouth_geometric_boundary']={'center_sample_nearest_midline':point(center),'center_mean':point(sum(mp,Vector())/len(mp)),'left_corner':point(left),'right_corner':point(right),'upper_extreme':point(max(mp,key=lambda p:p.z)),'lower_extreme':point(min(mp,key=lambda p:p.z)),'contour':[point(p) for p in mp],'definition':'Actual evaluated skin opening boundary, not painted mouth mark or hidden seam guide.'}
else:mouthz=1.493
eyeout=[]
for loop in eye_loops:
 ep=[pts[i] for i in loop['ids']];inner=min(ep,key=lambda p:abs(p.x));outer=max(ep,key=lambda p:abs(p.x));cx=sum(p.x for p in ep)/len(ep)
 # Upper/lower curves split by the line joining geometric canthi.
 upper=[];lower=[]
 for p in ep:
  t=(p.x-inner.x)/(outer.x-inner.x);linez=inner.z+t*(outer.z-inner.z);(upper if p.z>=linez else lower).append(point(p))
 eyeout.append({'side_world_x':1 if cx>0 else -1,'inner_canthus':point(inner),'outer_canthus':point(outer),'upper_contour':upper,'lower_contour':lower,'full_ordered_boundary':[point(p) for p in ep],'definition':'Evaluated open-skin rim. Actual visible black upper-lash silhouette is separate and exported below.'})
landmarks['geometric_eyelid_contours']=eyeout
# Exact fixed UV shader centers mapped onto actual evaluated curved iris triangles.
ee,em,eps=evaluated(eyes);em.calc_loop_triangles();uv=em.uv_layers.active;iris=[]
for U in [.25,.75]:
 for kind,V in [('iris_nominal_center',.5),('pupil_shader_center',.5-.29*.222)]:
  matches=[]
  for tri in em.loop_triangles:
   if em.polygons[tri.polygon_index].material_index!=5:continue
   t=np.array([tuple(uv.data[i].uv) for i in tri.loops]);A=np.column_stack((t[1]-t[0],t[2]-t[0]));det=np.linalg.det(A)
   if abs(det)<1e-12:continue
   w=np.linalg.solve(A,np.array([U,V])-t[0]);weights=[1-w.sum(),w[0],w[1]]
   if min(weights)<-1e-6:continue
   p=sum((eps[i]*float(a) for i,a in zip(tri.vertices,weights)),Vector());hit=bvh.ray_cast(Vector((p.x,-.3,p.z)),Vector((0,1,0)))[0]
   matches.append({**point(p),'triangle_index':tri.index,'uv':[U,V],'skin_occluded':hit is not None and hit.y<p.y-.00001})
  if matches:iris.append({'kind':kind,'u_eye':U,'points':sorted(matches,key=lambda d:d['world_m'][1])})
landmarks['iris_pupil_uv_centers']=iris
# Plane/triangle intersection gives true projected face extents, not shadows.
me.calc_loop_triangles();eyez=sum(l['center'][2] for l in eye_loops)/len(eye_loops) if eye_loops else 1.5393
heights={'malar_defined_10mm_below_eye_rim_mean':eyez-.010,'midcheek_halfway_eye_mouth':(eyez+mouthz)/2,'mouth_geometric_boundary_mean':mouthz};widths=[]
for label,z in heights.items():
 candidates=[]
 for tri in me.loop_triangles:
  if tri.polygon_index not in facechart:continue
  vs=[pts[i] for i in tri.vertices]
  for p,q in zip(vs,vs[1:]+[vs[0]]):
   if (p.z-z)*(q.z-z)<0:
    v=p+(q-p)*((z-p.z)/(q.z-p.z));hit=bvh.ray_cast(Vector((v.x,-.3,z)),Vector((0,1,0)))[0]
    if hit is not None and abs(hit.y-v.y)<.00015:candidates.append(v)
 if candidates:
  L=min(candidates,key=lambda p:p.x);R=max(candidates,key=lambda p:p.x);widths.append({'label':label,'world_z_m':z,'left':point(L),'right':point(R),'width_m':R.x-L.x,'width_pixels':abs(point(R)['pixel_top_left'][0]-point(L)['pixel_top_left'][0]),'method':'Frontal visible triangle-plane intersections of largest UV-connected evaluated skin chart. Check UV-chart bounds for ear exclusion; no image/shadow threshold.'})
landmarks['face_widths']=widths
ink={}
for o in s.objects:
 if o.type=='MESH' and not o.hide_render and any(t in o.name for t in ['UpperLash','OuterWing']):
  oe,om,op=evaluated(o);ink[o.name]={'points':[point(p) for p in op],'polygons':[list(f.vertices) for f in om.polygons]};oe.to_mesh_clear()
keys={o.name:{k.name:k.value for k in o.data.shape_keys.key_blocks} for o in [skin,eyes,body] if o.data.shape_keys}
arm=next((m.object for m in skin.modifiers if m.type=='ARMATURE'),None)
pose={b.name:{'rotation_mode':b.rotation_mode,'matrix_basis':[list(r) for r in b.matrix_basis]} for b in arm.pose.bones if any(t in b.name.lower() for t in ['head','neck','eye'])} if arm else {}
def component_info(c):
 ar=np.array([tuple(pts[i]) for i in c]);return {'vertex_count':len(c),'min':ar.min(0).tolist(),'max':ar.max(0).tolist(),'centroid':ar.mean(0).tolist()}
be,bm,bpts=evaluated(body);headcap=[p for p in bpts if p.z>1.45];allhead=pts+headcap
landmarks['head_shape_extrema']={'crown_skin_plus_cap':point(max(allhead,key=lambda p:p.z)),'occipital_max_world_y_above_z1_55':point(max([p for p in allhead if p.z>1.55],key=lambda p:p.y)),'forehead_frontmost_above_z1_56':point(min([p for p in allhead if p.z>1.56],key=lambda p:p.y)),'left_ear_extreme':point(min(pts,key=lambda p:p.x)),'right_ear_extreme':point(max(pts,key=lambda p:p.x))}
bodybounds={'min':[min(p[i] for p in bpts) for i in range(3)],'max':[max(p[i] for p in bpts) for i in range(3)]};be.to_mesh_clear()
report={'source':str(SOURCE),'source_sha_before':source_sha,'reference':str(REF),'reference_sha':sha(REF),'coordinate_convention':'World metres; image pixel(0,0)=top-left, continuous coordinates;1000x1000. No image resizing/roll or nonuniform registration applied.','camera':{'name':cam.name,'type':cam.data.type,'ortho_scale':cam.data.ortho_scale,'location':list(cam.location),'target':[0,0,1.55],'matrix_world':[list(r) for r in cam.matrix_world],'world_to_camera_matrix':[list(r) for r in cam.matrix_world.inverted()],'rotation_euler_radians':list(cam.rotation_euler),'roll_about_view_axis_deg':0,'resolution':[1000,1000],'shift':[cam.data.shift_x,cam.data.shift_y],'pixel_aspect':[1,1]},'frame':s.frame_current,'shape_key_values':keys,'head_neck_eye_pose_basis':pose,'skin_object_matrix_world':[list(r) for r in skin.matrix_world],'evaluated_skin_components':[component_info(c) for c in components],'uv_chart_inventory':chartinfo,'evaluated_body_bounds':bodybounds,'boundary_loop_inventory':[{k:v for k,v in l.items() if k!='points'} for l in loops],'landmarks':landmarks,'visible_upper_lash_mesh_projection':ink,'lighting':'Inherited source lighting/materials unchanged for these geometric registration renders. This does not validate diffuse/specular calibration; root owns lighting setup.'}
ee.to_mesh_clear();ev.to_mesh_clear()
# Two fresh exact-framing RGBA previews; no file save of scene/native.
s.render.film_transparent=True;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.render.filepath=str(OUT/'front_hair_rgba.png')
if '--no-render' not in sys.argv:bpy.ops.render.render(write_still=True)
hairnames={o.name for c in bpy.data.collections if 'HAIR' in c.name.upper() for o in c.all_objects}
for o in s.objects:
 if o.type=='MESH' and (o.name in hairnames or any(t in o.name for t in ['Hair','HAIR','PIXAL'])):o.hide_render=True
s.render.filepath=str(OUT/'front_bare_rgba.png')
if '--no-render' not in sys.argv:bpy.ops.render.render(write_still=True)
def reproject_tree(obj):
 if isinstance(obj,dict):
  if 'world_m' in obj:return {**obj,**point(Vector(obj['world_m']))}
  return {k:reproject_tree(v) for k,v in obj.items()}
 if isinstance(obj,list):return [reproject_tree(v) for v in obj]
 return obj
views={};target=Vector((0,0,1.55))
for name,yaw,elev in [('front',0,0),('left45',45,0),('right45',-45,0),('left_profile',90,0),('right_profile',-90,0),('back',180,0),('upper20_left45',45,20),('upper20_right45',-45,20),('upper35_left45',45,35),('upper35_right45',-45,35)]:
 y=math.radians(yaw);e=math.radians(elev);h._aim(cam,target+Vector((2*math.sin(y)*math.cos(e),-2*math.cos(y)*math.cos(e),2*math.sin(e))),target);bpy.context.view_layer.update()
 views[name]={'yaw_deg':yaw,'elevation_deg':elev,'ortho_scale':.29,'target':list(target),'resolution':[1000,1000],'camera_matrix_world':[list(r) for r in cam.matrix_world],'world_to_camera_matrix':[list(r) for r in cam.matrix_world.inverted()],'landmarks':reproject_tree(landmarks),'occlusion_note':'All projections are from identical evaluated geometry. Back/profile projections may be hidden; projection is not a visibility assertion. Iris skin_occluded flag refers to FRONT only.'}
(OUT/'multiview-projections.json').write_text(json.dumps({'source_sha':source_sha,'frame':s.frame_current,'views':views,'body_bounds':bodybounds,'same_geometry_all_views':True},indent=2))
report['source_sha_after']=sha(SOURCE);report['no_native_saved']=True
(OUT/'front-landmarks.json').write_text(json.dumps(report,indent=2));print('V19_DONE',json.dumps({'components':report['evaluated_skin_components'],'loops':[{k:l[k] for k in ['count','center','min','max']} for l in loops],'eye_loops':len(eyeout),'mouth_found':mouth is not None,'iris_centers':len(iris),'widths':widths,'chin':landmarks['chin_actual_mesh_min_z']}),flush=True)
