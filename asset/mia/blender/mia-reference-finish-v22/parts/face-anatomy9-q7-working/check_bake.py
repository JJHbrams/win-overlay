import bpy,numpy as np,json,math
from pathlib import Path
p=Path(__file__).parent;src=p.parent/'mia-face-anatomy-v25/proportion-p2/Mia_ReferenceFinish_WIP8_ProportionP2.blend';dst=p/'Mia_ConnectedLoft_Q6b_Dense.blend';delta=np.load(p/'dense-q6b-deltas.npz')['delta'];results={}
def coords(o):
 bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();a=np.array([v.co[:] for v in m.vertices]);uv=np.array([v.uv[:] for v in m.uv_layers.active.data]);ev.to_mesh_clear();return a,uv
for role,fn in [('source',src),('bake',dst)]:
 bpy.ops.wm.open_mainfile(filepath=str(fn));o=bpy.data.objects['MIA_V14_SculptedSkin'];keys=o.data.shape_keys.key_blocks
 for k in keys:k.value=0
 if role=='bake':
  for k in keys:
   a=np.array([v.co[:] for v in k.data])-delta;k.data.foreach_set('co',a.astype(np.float32).ravel())
  o.data.vertices.foreach_set('co',np.array([v.co[:] for v in keys[0].data],dtype=np.float32).ravel());o.data.update();bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(p/'Mia_Q6b_BakeOnly_Control.blend'))
 b=bpy.data.objects['MIA_V06_RIG'].pose.bones['J_Bip_C_Head'];b.rotation_mode='XYZ'
 results[role]={}
 for state,blink,yaw in [('neutral',0,0),('halfblink',.5,0),('fullblink',1,0),('headyaw+15',0,15),('headyaw-15',0,-15)]:
  keys['Face.M_F00_000_00_Fcl_EYE_Close'].value=blink;b.rotation_euler=(0,math.radians(yaw),0);o.data.shape_keys.update_tag();results[role][state]=coords(o)
report={}
for state in results['source']:
 a,uv=results['source'][state];b,uv2=results['bake'][state];d=np.linalg.norm(a-b,axis=1);report[state]={'max_mm':float(d.max()*1000),'rms_mm':float(np.sqrt(np.mean(d*d))*1000),'uv_max_error':float(np.max(np.abs(uv-uv2))),'vertex_count':len(a)}
(p/'bake-equivalence.json').write_text(json.dumps(report,indent=2));print('BAKE_EQUIVALENCE',json.dumps(report),flush=True)
