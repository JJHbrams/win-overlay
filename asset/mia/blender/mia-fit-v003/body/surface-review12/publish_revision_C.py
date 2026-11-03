"""Immutable ONE collarrevision. Keep topology/ReviewUV/regionIDs and sourcecore."""
from pathlib import Path
import hashlib,json,os
import numpy as np
P=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();ah=lambda a:hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
old=np.load(P/'joined-static.npz');new=np.load(P/'joined-geometric-C.npz');rows=np.load(P/'collar-rows-C.npz');oldsurface=np.load(P/'surface-v3-branch-regions.npz');meta=json.loads((P/'surface-v3-branch-regions.json').read_text())
assert np.array_equal(old['triangles'],new['triangles']) and np.array_equal(old['source_part'],new['source_part'])
for k in ['old_loop_uv','source_corner_normals','source_corner_bary','triangle_materials','source_face','source_vertex','guide_vertex','vertex_limb_weights']:assert np.array_equal(old[k],new[k]),k
changed=np.flatnonzero(np.any(old['world']!=new['world'],axis=1));allowed=np.unique(np.concatenate([rows[k].ravel() for k in rows.files]));assert set(changed)<=set(allowed)
target=P/'surface-v4-geometric-C.npz';assert not target.exists()
np.savez_compressed(target,world=new['world'],triangles=oldsurface['triangles'],loop_uv=oldsurface['loop_uv'],face_region=oldsurface['face_region'],meshfaceid=oldsurface['meshfaceid'])
version=dict(meta,payload_version='v4-geometric-C',surface_npz_path=str(target),surface_npz_sha256=sha(target),geometry_world_sha256=ah(new['world']),
    assembly_geometry_path=str(P/'joined-geometric-C.npz'),collar_revision='ONE actualadjacent-geometricsection chord handles; G1/tangent-aware, notparameterC1 claim',previous_geometry_world_sha256=meta['geometry_world_sha256'])
(P/'surface-v4-geometric-C.json').write_text(json.dumps(version,indent=2)+'\n',encoding='utf-8',newline='\n')
proof=dict(old_geometry_path=str(P/'joined-static.npz'),old_geometry_sha256=sha(P/'joined-static.npz'),new_geometry_path=str(P/'joined-geometric-C.npz'),new_geometry_sha256=sha(P/'joined-geometric-C.npz'),
    changed_vertex_ids=changed.tolist(),allowed_collar_row_ids=allowed.tolist(),collar_rows_npz=str(P/'collar-rows-C.npz'),changed_vertices=len(changed),maximum_delta_m=float(np.linalg.norm(new['world'].astype(float)-old['world'],axis=1).max()),
    topology_exact=True,endpoint_loops_and_all_other_vertices_exact=True,old3UV_exact=True,ReviewUV_sha256_held=meta['loop_uv_sha256'],face_region_exact=True,
    reason='Failedgray8FBAC2 waistband/armbulb. PriorloftusedCUSTOMSHADINGnormals; revisedendpointgeometry usesactualretainedsurfaceplane sections. Oneadjacentrowchord perBezierhandle. Naturalinflection/smallovershootpossiblewithheldendloops/tangents.',
    artist_core_or_head_changes=False)
(P/'collar-revision-C-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
(P/'active-assembly.json').write_text(json.dumps(dict(version='C',geometry=str(P/'joined-geometric-C.npz'),surface=str(target),surface_json=str(P/'surface-v4-geometric-C.json'),geometry_sha256=sha(P/'joined-geometric-C.npz'),surface_sha256=sha(target)),indent=2)+'\n',encoding='utf-8',newline='\n')
print('REVIEW12_C_PUBLISHED',json.dumps({k:proof[k] for k in ['changed_vertices','maximum_delta_m','topology_exact','endpoint_loops_and_all_other_vertices_exact']}),sha(target),flush=True)
