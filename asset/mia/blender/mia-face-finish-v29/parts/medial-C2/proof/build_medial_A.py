"""v29 A: bounded modeled medial union/recess on immutable full G2L.
No source ink-tail coordinate is used. No body, UV, material or topology edit.
"""
import bpy,numpy as np,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
O=Path(__file__).parent
N=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-orbit-thorax-review-v28/integrated-G2L/Mia_Foundation_v28_G2L.blend')
assert hashlib.sha256(N.read_bytes()).hexdigest()=='f0dead17dba4f492c47652dab62c48a93bcd0100bc2586ca3ac315d41a977ee2'
bpy.ops.wm.open_mainfile(filepath=str(N));skin=bpy.data.objects['MIA_V27_SharedHeadBody'];master=bpy.data.objects['MIA_V27_Foundation_Face'];keys=master.data.shape_keys.key_blocks
meta=json.loads((O/'medial-baseline-inspection.json').read_text());centers={int(s):np.array(d['medial_world']) for s,d in meta['evaluated_openings'].items()};cycles={int(s):d['upper_evaluated_indices']+list(reversed(d['lower_evaluated_indices']))[1:-1] for s,d in meta['evaluated_openings'].items()}
def coords(ob):return np.array([[v.co[:] for v in k.data] for k in ob.data.shape_keys.key_blocks])
def world(ob,q):
 m=np.array(ob.matrix_world);return q@m[:3,:3].T+m[:3,3]
def local(ob,q):
 m=np.array(ob.matrix_world);return (q-m[:3,3])@np.linalg.inv(m[:3,:3]).T
def warp(q):
 q=np.array(q,copy=True);out=q.copy()
 for side,c in centers.items():
  dx=q[:,0]-c[0];dz=q[:,2]-c[2];dy=q[:,1]-c[1];r=np.sqrt((dx/.0038)**2+(dz/.0045)**2+(dy/.006)**2)
  fade=np.clip((2.5-r)/.8,0,1);fade=fade*fade*(3-2*fade);g=np.exp(-.5*r*r)*fade*(q[:,0]*side>0)
  # Compact union change: shortens the sharp high medial wedge, gives the
  # junction a shallow recess and fair transition. The broad runs stay outside.
  out[:,0]+=side*.00018*g
  out[:,1]+=.00026*g
  rounding=.16*dz*np.exp(-.5*(dx/.0014)**2-.5*(dz/.0025)**2)*g
  out[:,2]+=-.00080*g+rounding
 return out
owners=[skin]+[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render and (o.name.startswith('V28G_') or 'BoundaryRibbon' in o.name or o.name.startswith('V28_LashFan_'))]
before={o.name:coords(o) for o in owners};master_before=coords(master);after={}
for ob in owners:
 a=before[ob.name].copy()
 for ki in range(len(a)):
  ii=np.arange(3957,len(a[ki])) if ob==skin else np.arange(len(a[ki]));a[ki,ii]=local(ob,warp(world(ob,a[ki,ii])))
 after[ob.name]=a
def put(ob,a):
 for k,q in zip(ob.data.shape_keys.key_blocks,a):
  for v,p in zip(k.data,q):v.co=p
 for v,p in zip(ob.data.vertices,a[0]):v.co=p
for ob in owners:put(ob,after[ob.name])
walls=[o for o in owners if o.name.startswith('V28G_InnerLid_')];ribs=[o for o in owners if 'BoundaryRibbon' in o.name];perkey=[]
for ki,k in enumerate(keys):
 for kk in keys:kk.value=0
 if ki:k.value=1
 bpy.context.view_layer.update();ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();sp=np.array([ev.matrix_world@v.co for v in me.vertices]);bv=BVHTree.FromPolygons([Vector(p) for p in sp],[list(f.vertices) for f in me.polygons]);rec={'key':k.name,'wall_seam':{}}
 for ob in walls:
  side=int(ob.name.rsplit('_',1)[1]);ii=cycles[side];assert len(ii)==96;q=world(ob,after[ob.name][ki]).reshape(6,96,3);delta=sp[ii]-q[0]
  for ri,w in enumerate([1,.92,.75,.50,.25,0]):q[ri]+=delta*w
  after[ob.name][ki]=local(ob,q.reshape(-1,3));rec['wall_seam'][str(side)]={'max_root_snap_mm':float(np.linalg.norm(delta,axis=1).max()*1000),'final_root_max_error_mm':float(np.linalg.norm(q[0]-sp[ii],axis=1).max()*1000)}
 # Preserve the old ink's conservative skin clearance after real skin change.
 for ob in ribs:
  q=world(ob,after[ob.name][ki])
  for p in q:
   h=bv.ray_cast(Vector((p[0],-.25,p[2])),Vector((0,1,0)))
   if h[0] is not None:p[1]=min(p[1],h[0].y-.00022)
  after[ob.name][ki]=local(ob,q)
 ev.to_mesh_clear();perkey.append(rec)
for ob in owners:put(ob,after[ob.name])
for k in keys:k.value=0
bpy.context.view_layer.update();assert np.array_equal(before[skin.name][:,:3957],coords(skin)[:,:3957]);assert np.array_equal(master_before,coords(master))
payload={};changes={}
for ob in owners:
 old=before[ob.name];new=coords(ob);ii=np.flatnonzero(np.max(abs(new-old),axis=(0,2))>1e-9);tag='o'+str(len(changes));payload[tag+'_indices']=ii;payload[tag+'_delta']=(new-old)[:,ii];changes[ob.name]={'payload_prefix':tag,'indices':ii.tolist(),'count':len(ii),'basis_world_bounds_before':[world(ob,old[0,ii]).min(0).tolist(),world(ob,old[0,ii]).max(0).tolist()] if len(ii) else None,'max_allkey_displacement_mm':float(np.linalg.norm(new-old,axis=2).max()*1000)}
np.savez_compressed(O/'medial-A-deltas.npz',**payload)
dest=O/'Mia_EyeLash_v29_A.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest));sha=hashlib.sha256(dest.read_bytes()).hexdigest()
audit={'input_native':str(N),'input_sha256':meta['input_sha256'],'output_native':str(dest),'output_sha256':sha,'method':'Model-inferred compact canthal union: .80mm maximum downward,.26mm posterior,.18mm lateral with local rounded tangent field. SharedSkin appended head only; active wall/ocular/ink follow same actual-position map for every key. Wall roots then recomputed from updated actual evaluated skin for all42. Not a source-black-tail fit.','changes':changes,'body_L_prefix_0_3956_exact_all42':True,'master_coordinates_exact_all42':True,'topology_UV_named_weights_materials_unchanged':True,'perkey':perkey,'all42_key_names':[k.name for k in keys],'status':'Candidate A real modeling first; actual clean3view and half/full closure required before lash/surface stage.','source_limit':'Hidden source canthus is an inferred design choice; observed aperture and anatomical continuity constrain this trial.'}
(O/'medial-A-audit.json').write_text(json.dumps(audit,indent=2));print('MEDIAL_A_SAVED',sha);print('SKIN_CHANGED',changes[skin.name]['count'],changes[skin.name]['max_allkey_displacement_mm'])
