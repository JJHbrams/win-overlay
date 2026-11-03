"""Read savedR3b actual posed surface/loopUV/cornernormal and limb ownership. CPU."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,re
P=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
native=Path(bpy.data.filepath);assert sha(native)=='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'
assert not (P/'donor.npz').exists(),'Do not overwrite frozen donorcapture'
s=bpy.context.scene;s.frame_set(1);owner=bpy.data.objects['MIA_V27_SharedHeadBody']
def co(data):
    a=np.empty(len(data)*3,np.float32);data.foreach_get('co',a);return a.reshape(-1,3)
keys={k.name:hashlib.sha256(co(k.data).tobytes()).hexdigest() for k in owner.data.shape_keys.key_blocks}
pose={b.name:[list(r) for r in b.matrix_basis] for b in bpy.data.objects['MIA_V06_RIG'].pose.bones}
groups=[g.name for g in owner.vertex_groups]
copy=owner.copy();copy.data=owner.data.copy();copy.name='_Review12_READONLY_DONOR_CAPTURE';s.collection.objects.link(copy)
groupinds={g.index:g.name for g in owner.vertex_groups}
attrs=['armR','armL','legR','legL']
def sided(name,right):
    low=name.lower();side='r' if right else 'l'
    return bool(re.search(r'(^|[_.])'+side+r'([_.]|$)',low)) or ('right' if right else 'left') in low
selected={}
for name in attrs:
    limb='Arm' if name.startswith('arm') else 'Leg';right=name.endswith('R')
    words=['upperarm','lowerarm','hand'] if limb=='Arm' else ['upperleg','lowerleg','foot','toe']
    gi={i for i,n in groupinds.items() if any(w in n.lower() for w in words) and sided(n,right)};selected[name]=[groupinds[i] for i in gi]
    values=np.array([sum(g.weight for g in v.groups if g.group in gi) for v in copy.data.vertices],np.float32)
    attr=copy.data.attributes.new('_Review12_'+name,'FLOAT','POINT');attr.data.foreach_set('value',values)
dg=bpy.context.evaluated_depsgraph_get();ev=copy.evaluated_get(dg);me=ev.to_mesh(preserve_all_data_layers=True,depsgraph=dg);me.calc_loop_triangles()
world=np.asarray([ev.matrix_world@v.co for v in me.vertices],np.float32);tri=np.asarray([t.vertices[:] for t in me.loop_triangles],np.int32);loops=np.asarray([t.loops[:] for t in me.loop_triangles],np.int32)
uvnames=[u.name for u in me.uv_layers];uvs={f'uv_{i}':np.asarray([[me.uv_layers[i].data[j].uv[:] for j in t.loops] for t in me.loop_triangles],np.float32) for i in range(len(uvnames))}
materials=np.asarray([me.polygons[t.polygon_index].material_index for t in me.loop_triangles],np.int16)
cn=np.asarray([[me.corner_normals[j].vector[:] for j in t.loops] for t in me.loop_triangles],np.float32)
weights={name:np.asarray([a.value for a in me.attributes['_Review12_'+name].data],np.float32) for name in attrs}
np.savez_compressed(P/'donor.npz',world=world,triangles=tri,triangle_materials=materials,corner_normals=cn,**uvs,**weights)
inventory=[]
for ob in s.objects:
    if ob==copy:continue
    if ob.type=='MESH' and not ob.hide_render:
        e=ob.evaluated_get(dg);mm=e.to_mesh();q=np.asarray([e.matrix_world@v.co for v in mm.vertices],np.float32)
        if len(q):inventory.append(dict(name=ob.name,vertices=len(q),bounds=[q.min(0).tolist(),q.max(0).tolist()],materials=[m.name if m else None for m in ob.data.materials]))
        e.to_mesh_clear()
ev.to_mesh_clear();bpy.data.objects.remove(copy,do_unlink=True)
assert keys=={k.name:hashlib.sha256(co(k.data).tobytes()).hexdigest() for k in owner.data.shape_keys.key_blocks}
assert pose=={b.name:[list(r) for r in b.matrix_basis] for b in bpy.data.objects['MIA_V06_RIG'].pose.bones} and sha(native)=='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'
report=dict(native=dict(path=str(native),sha256=sha(native)),owner=owner.name,frame=1,vertices=len(world),triangles=len(tri),uv_layers=uvnames,
    material_slots=[m.name if m else None for m in owner.data.materials],selected_limb_groups=selected,all_vertex_groups=groups,keys_sha256=keys,pose=pose,
    donor_sha256=sha(P/'donor.npz'),visible_saved_mesh_inventory=inventory,original_keys_pose_native_held=True,native_saved=False,GPU_used=False)
(P/'donor.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print('REVIEW12_DONOR_CAPTURED',json.dumps({k:report[k] for k in ['vertices','triangles','uv_layers','material_slots','selected_limb_groups']}),flush=True)
