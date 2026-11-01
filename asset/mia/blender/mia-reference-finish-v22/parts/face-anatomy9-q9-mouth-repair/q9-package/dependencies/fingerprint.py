import bpy,numpy as np,hashlib,json
SKIN='MIA_V14_SculptedSkin'
def ah(a):return hashlib.sha256(np.asarray(a,dtype='<f4').tobytes()).hexdigest()
def jh(a):return hashlib.sha256(json.dumps(a,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def fingerprint():
 o=bpy.data.objects[SKIN];m=o.data;keys=m.shape_keys.key_blocks
 for k in keys:k.value=0.
 bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();evaluated=ah([v.co[:] for v in me.vertices]);ev.to_mesh_clear()
 return {'vertex_count':len(m.vertices),'key_names':[k.name for k in keys],'key_coordinates':{k.name:ah([v.co[:] for v in k.data]) for k in keys},'uvs':{l.name:ah([v.uv[:] for v in l.data]) for l in m.uv_layers},'topology':jh([list(p.vertices) for p in m.polygons]),'group_names':[g.name for g in o.vertex_groups],'weights':jh([[(g.group,g.weight) for g in v.groups] for v in m.vertices]),'other_meshes':{obj.name:ah([v.co[:] for v in obj.data.vertices]) for obj in bpy.data.objects if obj.type=='MESH' and obj!=o},'evaluated_neutral_coordinates':evaluated,'driver_targets':sorted([(datablock.name,fc.data_path,var.name,t.data_path) for datablock in bpy.data.shape_keys if datablock.animation_data for fc in datablock.animation_data.drivers for var in fc.driver.variables for t in var.targets if t.id==m.shape_keys])}
