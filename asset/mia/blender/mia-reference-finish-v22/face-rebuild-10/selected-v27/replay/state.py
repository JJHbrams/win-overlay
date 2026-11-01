import hashlib,json,numpy as np
def digest(a):return hashlib.sha256(np.asarray(a).tobytes()).hexdigest()
def fingerprint(o):
 m=o.data
 return {'keys':{k.name:digest(np.array([v.co[:] for v in k.data],dtype='<f4')) for k in m.shape_keys.key_blocks},'topology':hashlib.sha256(repr([tuple(p.vertices) for p in m.polygons]).encode()).hexdigest(),'uv':{u.name:digest(np.array([d.uv[:] for d in u.data],dtype='<f4')) for u in m.uv_layers},'weights':hashlib.sha256(repr([[(o.vertex_groups[g.group].name,g.weight) for g in v.groups] for v in m.vertices]).encode()).hexdigest(),'material_slots':[s.material.name if s.material else None for s in o.material_slots],'material_indices':digest(np.array([p.material_index for p in m.polygons],dtype='<i4')),'matrix_basis':digest(np.array(o.matrix_basis,dtype='<f4'))}
