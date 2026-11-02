"""Fresh automatic normals from actual evaluated geometry, private data only."""
import bpy,numpy as np
def rebuild_evaluated(obj,name='V003_FreshAutoNormals'):
    dg=bpy.context.evaluated_depsgraph_get();eo=obj.evaluated_get(dg);me=eo.to_mesh(preserve_all_data_layers=True,depsgraph=dg);fresh=bpy.data.meshes.new(name)
    fresh.from_pydata([v.co[:] for v in me.vertices],[],[p.vertices[:] for p in me.polygons])
    for a,b in zip(fresh.polygons,me.polygons):a.use_smooth=b.use_smooth;a.material_index=b.material_index
    for mat in me.materials:fresh.materials.append(mat)
    for uv in me.uv_layers:
        dst=fresh.uv_layers.new(name=uv.name);coords=np.empty(len(uv.data)*2,dtype=np.float32);uv.data.foreach_get('uv',coords);dst.data.foreach_set('uv',coords)
    # Sharp edge/face policy is explicit; body is audited separately fromhead.
    for name in ['sharp_face','sharp_edge']:
        if name not in me.attributes:continue
        src=me.attributes[name]
        if name=='sharp_face':
            dst=fresh.attributes.get(name) or fresh.attributes.new(name,'BOOLEAN','FACE')
            for a,b in zip(dst.data,src.data):a.value=b.value
        else:
            values={tuple(sorted(e.vertices[:])):bool(src.data[e.index].value) for e in me.edges};dst=fresh.attributes.get(name) or fresh.attributes.new(name,'BOOLEAN','EDGE')
            for e in fresh.edges:dst.data[e.index].value=values.get(tuple(sorted(e.vertices[:])),False)
    fresh.update();eo.to_mesh_clear();return fresh
