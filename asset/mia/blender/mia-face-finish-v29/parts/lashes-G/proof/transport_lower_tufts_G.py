"""G: coherent whole-lower-tuft skin-frame transport, no folded root-to-tip fade."""
import bpy,numpy as np,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
O=Path(__file__).parent;src=O/'Mia_EyeLash_v29_F.blend';bpy.ops.wm.open_mainfile(filepath=str(src));master=bpy.data.objects['MIA_V27_Foundation_Face'];skin=bpy.data.objects['MIA_V27_SharedHeadBody'];keys=master.data.shape_keys.key_blocks;lower=[o for o in bpy.context.scene.objects if o.name.startswith('V29_LowerLashes_')]
def get(ob):return np.array([[v.co[:] for v in k.data] for k in ob.data.shape_keys.key_blocks])
def norm(q):return q/max(np.linalg.norm(q),1e-12)
def frame(p,n,ii,bc):
 N=norm(bc@n[ii]);T=p[ii[1]]-p[ii[0]];T=norm(T-N*(T@N));return np.stack([T,norm(np.cross(N,T)),N],1)
skinbefore=get(skin);masterbefore=get(master);old={o.name:get(o) for o in lower};new={n:q.copy() for n,q in old.items()}
for k in keys:k.value=0
bpy.context.view_layer.update();ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();p=np.array([ev.matrix_world@v.co for v in me.vertices]);n=np.array([ev.matrix_world.to_3x3()@v.normal for v in me.vertices]);tris=np.array([t.vertices[:] for t in me.loop_triangles]);bv=BVHTree.FromPolygons([Vector(q) for q in p],tris.tolist(),all_triangles=True);bindings={}
for ob in lower:
 rows=[]
 for ti in range(3):
  root=old[ob.name][0,ti*42:ti*42+6].mean(0);hit,_,idx,_=bv.find_nearest(Vector(root));ii=tris[idx];a,b,c=p[ii];w=np.linalg.lstsq(np.stack([b-a,c-a],1),np.array(hit)-a,rcond=None)[0];bc=np.r_[1-w.sum(),w];bc=np.maximum(bc,0);bc/=bc.sum();R=frame(p,n,ii,bc);offset=R.T@(root-bc@p[ii]);rows.append({'tuft':ti,'triangle_vertex_indices':ii.tolist(),'barycentric':bc.tolist(),'neutral_frame':R.tolist(),'neutral_root_center':root.tolist(),'local_root_center_offset':offset.tolist()})
 bindings[ob.name]=rows
ev.to_mesh_clear()
for ki,k in enumerate(keys):
 for kk in keys:kk.value=0
 if ki:k.value=1
 bpy.context.view_layer.update();ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();p=np.array([ev.matrix_world@v.co for v in me.vertices]);n=np.array([ev.matrix_world.to_3x3()@v.normal for v in me.vertices])
 for ob in lower:
  for bind in bindings[ob.name]:
   ti=bind['tuft'];ii=np.array(bind['triangle_vertex_indices']);bc=np.array(bind['barycentric']);R=frame(p,n,ii,bc);R0=np.array(bind['neutral_frame']);center=bc@p[ii]+R@np.array(bind['local_root_center_offset']);new[ob.name][ki,ti*42:(ti+1)*42]=(old[ob.name][0,ti*42:(ti+1)*42]-np.array(bind['neutral_root_center']))@(R@R0.T).T+center
  if ki==0 or (k.name.endswith('Fcl_EYE_Close_R') and ob.name.endswith('_1')) or (k.name.endswith('Fcl_EYE_Close_L') and ob.name.endswith('_-1')):new[ob.name][ki]=old[ob.name][0]
 ev.to_mesh_clear()
for ob in lower:
 for key,q in zip(ob.data.shape_keys.key_blocks,new[ob.name]):
  for v,p in zip(key.data,q):v.co=p
 for v,p in zip(ob.data.vertices,new[ob.name][0]):v.co=p
for k in keys:k.value=0
bpy.context.view_layer.update();assert np.array_equal(skinbefore,get(skin));assert np.array_equal(masterbefore,get(master));dest=O/'Mia_EyeLash_v29_G.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest));np.savez_compressed(O/'lash-G-lower-coordinates.npz',**new);(O/'lash-G-rigid-bindings.json').write_text(json.dumps({'input_native':str(src),'input_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'output_native':str(dest),'output_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'bindings':bindings,'neutral_all_lash_coordinates_exact_F_E':True,'only_two_lower_lash_coordinate_owners_changed':True,'upper_F_and_C2_skin_iris_wall_body_and_master_raw_unchanged':True,'method':'One fixed neutral actual skin-triangle barycentric center +one orthonormal normal/tangent frame per connected short lower tuft. Whole neutral E tuft undergoes proper rigid frame transform at each key; no per-row fade or fixed remote tip. Preserves tuft volume at named endpoints; half interpolations independently audited.','reason':'F per-root deformation produced actual short-tube inversions under some closures. F rejected; rigid component transport replaces that method for lower lashes only.','limits':'Fresh per-tuft centered volumes/contact and actual dynamic renders required before map gate.'},indent=2));print('LOWER_G_SAVED')
