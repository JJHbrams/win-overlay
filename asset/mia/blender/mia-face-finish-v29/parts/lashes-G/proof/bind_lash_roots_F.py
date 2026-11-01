"""F: fixed actual skin-triangle root bindings; reversible transparent-card exclusion."""
import bpy,numpy as np,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
O=Path(__file__).parent;src=O/'Mia_EyeLash_v29_E.blend';bpy.ops.wm.open_mainfile(filepath=str(src));master=bpy.data.objects['MIA_V27_Foundation_Face'];skin=bpy.data.objects['MIA_V27_SharedHeadBody'];keys=master.data.shape_keys.key_blocks;lashes=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('V29_') and 'Lashes_' in o.name]
def get(ob):return np.array([[v.co[:] for v in k.data] for k in ob.data.shape_keys.key_blocks])
def normal(p):return p/max(np.linalg.norm(p),1e-12)
def frame(pp,nn,ids,bc):
 n=normal(bc@nn[ids]);t=pp[ids[1]]-pp[ids[0]];t=normal(t-n*(t@n));b=normal(np.cross(n,t));return np.stack([t,b,n],1)
skinbefore=get(skin);masterbefore=get(master);before={o.name:get(o) for o in lashes};after={n:q.copy() for n,q in before.items()}
for k in keys:k.value=0
bpy.context.view_layer.update();ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();sp=np.array([ev.matrix_world@v.co for v in me.vertices]);sn=np.array([ev.matrix_world.to_3x3()@v.normal for v in me.vertices]);tris=np.array([t.vertices[:] for t in me.loop_triangles]);bv=BVHTree.FromPolygons([Vector(p) for p in sp],tris.tolist(),all_triangles=True);bindings={}
for ob in lashes:
 nt=4 if 'Upper' in ob.name else 3;rootids=[ti*42+c for ti in range(nt) for c in range(6)];rows=[]
 for i in rootids:
  q=np.array(ob.matrix_world@Vector(before[ob.name][0,i]));hit,_,ti,d=bv.find_nearest(Vector(q));ids=tris[ti];a,b,c=sp[ids];w=np.linalg.lstsq(np.stack([b-a,c-a],1),np.array(hit)-a,rcond=None)[0];bc=np.r_[1-w.sum(),w];bc=np.maximum(bc,0);bc/=bc.sum();surface=bc@sp[ids];F=frame(sp,sn,ids,bc);offset=F.T@(q-surface);rows.append({'root_vertex':i,'skin_evaluated_triangle_vertices':ids.tolist(),'barycentric':bc.tolist(),'local_frame_offset_m':offset.tolist(),'neutral_nearest_distance_mm':float(d*1000)})
 bindings[ob.name]=rows
ev.to_mesh_clear()
for ki,k in enumerate(keys):
 for kk in keys:kk.value=0
 if ki:k.value=1
 bpy.context.view_layer.update();ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();sp=np.array([ev.matrix_world@v.co for v in me.vertices]);sn=np.array([ev.matrix_world.to_3x3()@v.normal for v in me.vertices])
 for ob in lashes:
  q=before[ob.name][ki].copy();mw=np.array(ob.matrix_world);inv=np.linalg.inv(mw[:3,:3]);deltas={}
  for b in bindings[ob.name]:
   ids=np.array(b['skin_evaluated_triangle_vertices']);bc=np.array(b['barycentric']);world=bc@sp[ids]+frame(sp,sn,ids,bc)@np.array(b['local_frame_offset_m']);co=(world-mw[:3,3])@inv.T;deltas[b['root_vertex']]=co-q[b['root_vertex']]
  for rooti,d in deltas.items():
   ti=rooti//42;ci=rooti%6
   for ri,w in enumerate([1,.80,.45,.20,.05,0,0]):q[ti*42+ri*6+ci]+=d*w
  # Preserve the already reviewed neutral silhouette exactly. Inactive eyes
  # retain exact neutral coordinates on unilateral closure.
  if ki==0 or (k.name.endswith('Fcl_EYE_Close_R') and ob.name.endswith('_1')) or (k.name.endswith('Fcl_EYE_Close_L') and ob.name.endswith('_-1')):q=before[ob.name][0].copy()
  after[ob.name][ki]=q
 ev.to_mesh_clear()
for ob in lashes:
 for key,q in zip(ob.data.shape_keys.key_blocks,after[ob.name]):
  for v,p in zip(key.data,q):v.co=p
 for v,p in zip(ob.data.vertices,after[ob.name][0]):v.co=p
# Keep original source meshes/UV/42 keys. Remove superseded alpha-zero card
# geometry from evaluation while retaining exactly the active mouth/brow faces.
allowed=sorted({i for f in master.data.polygons if f.material_index in [0,4] for i in f.vertices});group=master.vertex_groups.new(name='V29_ActiveMouthBrow_RenderMask');group.add(allowed,1,'REPLACE');mask=master.modifiers.new('V29_Exclude_TransparentLegacyCards','MASK');mask.vertex_group=group.name;mask.invert_vertex_group=False;mask.threshold=.5
if hasattr(mask,'use_smooth'):mask.use_smooth=False
for k in keys:k.value=0
bpy.context.view_layer.update();assert np.array_equal(skinbefore,get(skin));assert np.array_equal(masterbefore,get(master));ev=master.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();visible_counts={str(i):sum(f.material_index==i for f in me.polygons) for i in range(len(master.data.materials))};ev.to_mesh_clear();expected={str(i):sum(f.material_index==i for f in master.data.polygons) for i in [0,4]};assert all(visible_counts[str(i)]==expected[str(i)] for i in [0,4]);assert sum(visible_counts.values())==sum(expected.values())
dest=O/'Mia_EyeLash_v29_F.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest));np.savez_compressed(O/'lash-F-root-deltas.npz',**{n:after[n]-before[n] for n in before});(O/'lash-F-bindings-and-mask.json').write_text(json.dumps({'input_native':str(src),'input_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'output_native':str(dest),'output_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'bindings':bindings,'neutral_newlash_coordinates_exact_E':True,'all_existing_master_and_skin_coordinates_42_exact':True,'master_mask':{'modifier':mask.name,'vertex_group':group.name,'retained_active_material_slots':[0,4],'retained_raw_vertex_indices':allowed,'actual_evaluated_material_polygon_counts':visible_counts,'original_raw_geometry_UV_and_keys_retained':True,'reason':'MasterOFF removes inherited interior marks; all alpha-zero legacy card geometry remains archived but excluded from evaluated render. No body/SharedSkin GN or shared material changes.'},'method':'Fixed neutral evaluated skin-triangle barycentric root attachment, transported local normal/tangent offsets all42; first5curve rows fade root delta. This avoids E endpoint first-hit projection jumping between lower and closed upper lid, which caused halfblink float. No added keys or corrective gating.','limits':'Fresh nearest3D contact and actual .5/1/low/unilateral rendering still required; source overallART remains unapproved.'},indent=2));print('LASH_ROOT_F_SAVED',visible_counts)
