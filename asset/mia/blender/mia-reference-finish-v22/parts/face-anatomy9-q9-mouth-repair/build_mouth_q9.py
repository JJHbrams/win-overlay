import bpy,numpy as np,json,hashlib,sys
from pathlib import Path
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).parent;SRC=P/'Mia_ConnectedLoft_Q7_SurfaceFit.blend';DST=P/'Mia_ConnectedSurface_Q9_MouthAnchor.blend';bpy.ops.wm.open_mainfile(filepath=str(SRC));o=bpy.data.objects['MIA_V14_SculptedSkin'];keys=o.data.shape_keys.key_blocks
for k in keys:k.value=0.
a=np.array([v.co[:] for v in keys[0].data]);x=np.abs(a[:,0]);y=a[:,1];z=a[:,2]
def ss(lo,hi,t):
 v=np.clip((t-lo)/(hi-lo),0,1);return v*v*(3-2*v)
# Recover the actually translated lip plane, with broad carrier support.
mouth=ss(.020,.045,y)*(1-ss(.014,.046,x))*ss(1.477,1.487,z)*(1-ss(1.501,1.518,z))
# Bounded side-wall taper. No anterior-depth subtraction, no eye-rim edits.
lower=np.interp(x,[.01,.018,.025,.035,.045,.053,.06,.08],[1.538,1.538,1.535,1.5345,1.537,1.541,1.545,1.551])
side=ss(.024,.046,x)*(1-ss(.065,.077,x))*ss(1.495,1.508,z)*(1-ss(1.524,1.540,z))*ss(.001,.006,lower-z)*ss(-.005,.022,y)
d=np.zeros_like(a);d[:,2]=.004*mouth;d[:,0]=-np.sign(a[:,0])*.0012*side
for k in keys:
 v=np.array([p.co[:] for p in k.data]);k.data.foreach_set('co',(v+d).astype(np.float32).ravel())
o.data.vertices.foreach_set('co',(a+d).astype(np.float32).ravel());o.data.update();bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(DST));np.savez_compressed(P/'q9-deltas.npz',basis=a,delta=d)
loops=json.loads((P/'mouth-q9-loop-audit.json').read_text())['boundaries'];lip=next(r['ids'] for r in loops if 1.49<r['center'][2]<1.50 and r['center'][1]>.06);eyes=[i for r in loops if 1.53<r['center'][2]<1.55 and r['center'][1]>.05 for i in r['ids']]
R=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v22/face-feedback-7/surface-diagnosis/dependencies');sys.path.insert(0,str(R));import review_setup as r
s=bpy.context.scene;r.camera(s,r.VIEWS[0]);from mathutils import Vector
project=lambda v:world_to_camera_view(s,s.camera,o.matrix_world@Vector(v))[:]
report={'source':str(SRC),'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'candidate':str(DST),'candidate_sha256':hashlib.sha256(DST.read_bytes()).hexdigest(),'lip_loop_vertex_ids':lip,'lip_before_mean':a[lip].mean(0).tolist(),'lip_after_mean':(a+d)[lip].mean(0).tolist(),'lip_projection_before':list(project(a[lip].mean(0))),'lip_projection_after':list(project((a+d)[lip].mean(0))),'eye_boundary_max_delta_mm':float(np.max(np.linalg.norm(d[eyes],axis=1))*1000),'chin_tip_max_delta_mm':float(np.max(np.linalg.norm(d[z<1.477],axis=1))*1000),'cheek_max_inset_mm':float(np.max(abs(d[:,0]))*1000),'max_mouth_lift_mm':float(d[:,2].max()*1000),'camera':r.record(s,r.VIEWS[0],'mouth projection audit'),'status':'REVIEW ONLY; actual source widths uncertain, bounded 1.2mm taper is hypothesis'}
(P/'q9-audit.json').write_text(json.dumps(report,indent=2));print('Q9_DONE',report['lip_before_mean'],report['lip_after_mean'],report['eye_boundary_max_delta_mm'],report['chin_tip_max_delta_mm'])
