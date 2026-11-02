"""Scoped actual evaluated-surface regression checks. No native saved."""
from pathlib import Path
import bpy, json, hashlib, importlib.util, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent; C=P.parents[1]
N=C/'mia-refinement-v002/integrated/Mia_v0.0.2_Review_R3b.blend'
SHA='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'
assert hashlib.sha256(N.read_bytes()).hexdigest()==SHA
bpy.ops.wm.open_mainfile(filepath=str(N),use_scripts=False)
cfg=json.loads((P/'lower-lid-balance.json').read_text()); payload=np.load(P/'lower-lid-balance.npz')
rim=json.loads((C/'mia-face-finish-v29/parts/medial-C2/proof/medial-baseline-inspection.json').read_text())
skin=bpy.data.objects['MIA_V27_SharedHeadBody']; ctrl=bpy.data.objects['Mia_FacialControls_v002']
def coords(c):
 a=np.empty(len(c)*3,np.float32);c.foreach_get('co',a);return a.reshape(-1,3)
def raw_hashes():
 return {r['owner']:{k.name:hashlib.sha256(coords(k.data).tobytes()).hexdigest() for k in bpy.data.objects[r['owner']].data.shape_keys.key_blocks if k.name!=r['key']} for r in cfg['entries']}
original=raw_hashes()
sp=importlib.util.spec_from_file_location('lowerlid',P/'apply_lower_lid.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);applied=m.apply()
keys=[bpy.data.objects[r['owner']].data.shape_keys.key_blocks[r['key']] for r in cfg['entries']]
marker=skin.data.attributes.new('v003_audit_support','FLOAT','POINT'); a=np.zeros(len(skin.data.vertices),np.float32);a[payload['d0_ids']]=1.;marker.data.foreach_set('value',a)
def evaluated(name,with_support=False):
 o=bpy.data.objects[name];e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();q=coords(me.vertices)@np.array(e.matrix_world.to_3x3()).T+np.array(e.matrix_world.translation)
 f=[p.vertices[:] for p in me.polygons]
 s=None
 if with_support:
  s=np.empty(len(me.vertices),np.float32);me.attributes['v003_audit_support'].data.foreach_get('value',s)
 e.to_mesh_clear();return q,f,s
changed=[r['owner'] for r in cfg['entries']]
protected=['V28G_Sclera_-1','V28G_Sclera_1','V28G_Iris_-1','V28G_Iris_1','V28G_InnerLid_-1','V30_LowerLashes_-1']
names=changed+protected; reports=[]
cases=[('neutral',{}),('half',{'EYE_Close':.5}),('closed',{'EYE_Close':1.}),('winkL',{'EYE_Close_L':1.}),('winkR',{'EYE_Close_R':1.}),('surprise',{'EYE_Surprised':.8}),('surpriseClosed',{'EYE_Surprised':.8,'EYE_Close':1.}),('angry',{'EYE_Angry':1.}),('joy',{'EYE_Joy':1.})]
frame=0
def update(mute):
 global frame
 for k in keys:k.mute=mute
 ctrl.update_tag();frame+=1;bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
def surface_stats(snapshot):
 q=snapshot[skin.name][0];wall=snapshot['V28G_InnerLid_1'][0][:96]
 ids=np.array(rim['evaluated_openings']['1']['upper_evaluated_indices']+rim['evaluated_openings']['1']['lower_evaluated_indices'],int)
 dist=np.sqrt(((wall[:,None,:]-q[ids][None,:,:])**2).sum(2).min(1))*1000
 sq,sf,_=snapshot['V28G_Sclera_1'];tree=BVHTree.FromPolygons(sq,sf)
 li=rim['evaluated_openings']['1']['lower_evaluated_indices'];depth=[];miss=[]
 for i in li:
  hit=tree.ray_cast(Vector((float(q[i,0]),-.2,float(q[i,2]))),Vector((0,1,0)),.4)[0]
  if hit is None:miss.append(int(i))
  else:depth.append(float((q[i,1]-hit.y)*1000))
 return dict(wall_root_nearest_rim_mm_max=float(dist.max()),wall_root_nearest_rim_mm_p95=float(np.percentile(dist,95)),lower_sclera_ray_misses=miss,lower_ray_y_difference_mm_range=[min(depth),max(depth)] if depth else None)
for label,values in cases:
 for k in ctrl.keys():
  if k.startswith('Manual_') or (len(k)>3 and k[0]=='P' and k[1:3].isdigit()):ctrl[k]=0.
 for k,v in values.items():ctrl['Manual_'+k]=v
 update(True);before={n:evaluated(n,n==skin.name) for n in names}
 update(False);after={n:evaluated(n,n==skin.name) for n in names}
 moves={n:float(np.linalg.norm(after[n][0]-before[n][0],axis=1).max()*1000) for n in names}
 support=after[skin.name][2]>1e-10
 # Position Smooth acts after Subsurf but does not diffuse this audit attribute.
 # Its four iterations extend coordinate influence four evaluated edges; the
 # downstream outline's normal-offset geometry needs the adjacent normal ring.
 # Two additional rings conservatively cover that derived surface dependency.
 for _ in range(6):
  grown=support.copy()
  for face in after[skin.name][1]:
   for x,y in zip(face,face[1:]+face[:1]):
    if support[x]:grown[y]=True
    if support[y]:grown[x]=True
  support=grown
 outside=~support
 outside_mm=float(np.linalg.norm(after[skin.name][0][outside]-before[skin.name][0][outside],axis=1).max()*1000)
 assert outside_mm<1e-5,(label,'outsideROI',outside_mm)
 assert all(moves[n]<1e-5 for n in protected),(label,'protected',moves)
 weights=[float(k.value) for k in keys]
 if label in ('closed','winkL','surpriseClosed','joy'):assert max(moves.values())<1e-5,(label,'closedendpoint')
 reports.append(dict(case=label,manual=values,corrective_weights=weights,movement_mm= moves,skin_outside_evaluated_support_mm=outside_mm,before=surface_stats(before),after=surface_stats(after)))
assert raw_hashes()==original
skin.data.attributes.remove(marker)
assert hashlib.sha256(N.read_bytes()).hexdigest()==SHA
result=dict(baseline_sha256=SHA,applied=applied,original_raw_key_arrays_exact=True,outsideROI_and_protected_eyes_exact=True,support_definition='Raw corrective POINT marker through Weld/Subsurf, six evaluated rings: four actual position-Smooth iterations plus two conservative rings for downstream normal-derived outlines. Zero-marker-only omitted position smoothing (0.092943mm); four rings omitted derived outline influence (0.002401mm). Both failed logs retained.',cases=reports,native_saved=False,scope='Endpoint/region regression check, not source ART or arbitrary combinations PASS. Wall nearest-vertex and Y-ray coverage are diagnostic metrics, not full collision proof.')
(P/'lower-lid-evaluated-checks.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print('LOWER_LID_EVALUATED_CHECKS_DONE',len(reports),flush=True)
