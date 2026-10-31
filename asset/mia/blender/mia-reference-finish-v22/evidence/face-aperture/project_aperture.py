"""Read-only actual evaluated eye rim/lash projection, same face5 front camera."""
import bpy,sys,json,numpy as np,hashlib,math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
H=Path(__file__).resolve().parent;F=H.parent/'mia-face-finish-v22/finish-5';sys.path.insert(0,str(F.parent/'finish-4/replay'));import review_setup as r
src=F/'Mia_FaceFinish5_v22.blend';before=r.sha(src);bpy.ops.wm.open_mainfile(filepath=str(src));s=bpy.context.scene;s.frame_set(1);r.camera(s,r.VIEWS[0]);deps=bpy.context.evaluated_depsgraph_get();reg=json.loads((F/'reference-review.json').read_text())['views'][0]['baseline_registration'];a=math.radians(reg['rotation_degrees']);A=reg['uniform_scale']*np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]]);t=np.array(reg['translation_xy'])
def pix(p):
 q=world_to_camera_view(s,s.camera,p);xy=np.array([q.x*1000,(1-q.y)*1000]);return {'raw':xy.tolist(),'registered':(A@xy+t).tolist()}
o=bpy.data.objects['MIA_V14_SculptedSkin'];ev=o.evaluated_get(deps);m=ev.to_mesh();p=np.array([tuple(v.co) for v in m.vertices]);uses={}
for f in m.polygons:
 ids=list(f.vertices)
 for aa,bb in zip(ids,ids[1:]+ids[:1]):edge=tuple(sorted((aa,bb)));uses[edge]=uses.get(edge,0)+1
adj={}
for (aa,bb),num in uses.items():
 if num==1:adj.setdefault(aa,set()).add(bb);adj.setdefault(bb,set()).add(aa)
seen=set();eyes=[]
for start in adj:
 if start in seen:continue
 stack=[start];seen.add(start);ids=[]
 while stack:
  i=stack.pop();ids.append(i)
  for j in adj[i]:
   if j not in seen:seen.add(j);stack.append(j)
 c=p[ids].mean(0)
 if .018<abs(c[0])<.06 and 1.53<c[2]<1.55 and c[1]>.03:
  inner=min(ids,key=lambda i:abs(p[i,0]));outer=max(ids,key=lambda i:abs(p[i,0]));points=[pix(ev.matrix_world@Vector(p[i])) for i in ids];ep={k:{**pix(ev.matrix_world@Vector(p[i])),'local':p[i].tolist()} for k,i in [('inner',inner),('outer',outer)]};q=np.array([pp['registered'] for pp in points]);eyes.append({'local_side':float(np.sign(c[0])),'endpoints':ep,'boundary':points,'registered_width_x':float(np.ptp(q[:,0])),'canthus_chord_length':float(np.linalg.norm(np.array(ep['inner']['registered'])-ep['outer']['registered']))})
ev.to_mesh_clear();ink={}
for name in ['MIA_V14_UpperLash_-1','MIA_V14_UpperLash_1','MIA_V14_OuterWing_-1','MIA_V14_OuterWing_1']:
 o=bpy.data.objects[name];ev=o.evaluated_get(deps);m=ev.to_mesh();ps=[pix(ev.matrix_world@v.co) for v in m.vertices];q=np.array([pp['registered'] for pp in ps]);ink[name]={'x_min':ps[int(np.argmin(q[:,0]))],'x_max':ps[int(np.argmax(q[:,0]))],'registered_width_x':float(np.ptp(q[:,0])),'vertices':ps};ev.to_mesh_clear()
assert r.sha(src)==before
(H/'actual-projections.json').write_text(json.dumps({'source':r.artifact(src),'registration':reg,'eyes':eyes,'lash':ink,'camera':{'matrix':[list(row) for row in s.camera.matrix_world],'ortho_scale':s.camera.data.ortho_scale,'resolution':[1000,1000]},'native_unchanged':True},indent=2));print(json.dumps({'eyes':[{k:v for k,v in e.items() if k!='boundary'} for e in eyes],'lash':{k:{kk:vv for kk,vv in v.items() if kk!='vertices'} for k,v in ink.items()}},indent=2))
