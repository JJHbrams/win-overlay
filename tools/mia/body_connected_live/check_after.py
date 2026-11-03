"""Inspect actual modifier correspondence without assuming the deformed Weld is a no-op."""
import bpy,numpy as np,json,hashlib
ns=bpy.app.driver_namespace;old=ns['MIA_Connected_Evaluated_Before'];o=bpy.data.objects['MIA_ConnectedBody_Design']
d=bpy.context.evaluated_depsgraph_get();e=o.evaluated_get(d);m=e.to_mesh(preserve_all_data_layers=True,depsgraph=d)
v=np.array([e.matrix_world@p.co for p in m.vertices],np.float32);loops=np.array([p.vertex_index for p in m.loops],np.int32)
uv={u.name:hashlib.sha256(np.array([p.uv[:]for p in u.data],np.float32).tobytes()).hexdigest()for u in m.uv_layers}
print(json.dumps(dict(before_vertices=len(old[0]),after_vertices=len(v),before_loops=len(old[1]),after_loops=len(loops),loops_equal=bool(np.array_equal(old[1],loops)),UV_before=old[2],UV_after=uv,head_max_delta_mm=float(np.linalg.norm(v[old[0][:,2]>=1.465]-old[0][old[0][:,2]>=1.465],axis=1).max()*1000)if len(old[0])==len(v)else None)))
e.to_mesh_clear()
