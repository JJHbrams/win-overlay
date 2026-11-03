"""Immutable discrete collar solve; original atlas/semantic/source inputs held."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
P=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
ah=lambda a:hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
revision='D3' if '--revision-D3' in sys.argv else 'D2' if '--revision-D2' in sys.argv else 'D';versionName={'D':'v5-discrete-D','D2':'v6-discrete-D2','D3':'v7-discrete-D3'}[revision]
geometry=P/('joined-discrete-'+revision+'.npz');rowPath=P/('collar-rows-'+revision+'.npz')
old=np.load(P/'joined-static.npz');new=np.load(geometry);rows=np.load(rowPath);surface=np.load(P/'surface-v3-branch-regions.npz');meta=json.loads((P/'surface-v3-branch-regions.json').read_text())
for key in old.files:
    if key!='world':assert np.array_equal(old[key],new[key]),key
allowed=np.unique(np.concatenate([rows[k].ravel() for k in rows.files]));changed=np.flatnonzero(np.any(old['world']!=new['world'],axis=1));assert set(changed)<=set(allowed)
target=P/('surface-'+versionName+'.npz');assert not target.exists(),'Immutable payload exists'
np.savez_compressed(target,world=new['world'],triangles=surface['triangles'],loop_uv=surface['loop_uv'],face_region=surface['face_region'],meshfaceid=surface['meshfaceid'])
version=dict(meta,payload_version=versionName,surface_npz_path=str(target),surface_npz_sha256=sha(target),geometry_world_sha256=ah(new['world']),assembly_geometry_path=str(geometry),collar_revision='Finite end-row constraints from actual sections plus one minimum discrete bending solve; no C1/ART guarantee',previous_geometry_world_sha256=meta['geometry_world_sha256'])
(P/('surface-'+versionName+'.json')).write_text(json.dumps(version,indent=2)+'\n',encoding='utf-8',newline='\n')
proof=dict(old_geometry_path=str(P/'joined-static.npz'),old_geometry_sha256=sha(P/'joined-static.npz'),new_geometry_path=str(geometry),new_geometry_sha256=sha(geometry),changed_vertex_ids=changed.tolist(),allowed_collar_row_ids=allowed.tolist(),collar_rows_npz=str(rowPath),changed_vertices=len(changed),maximum_delta_m=float(np.linalg.norm(new['world'].astype(float)-old['world'],axis=1).max()),topology_exact=True,endpoint_loops_and_all_other_vertices_exact=True,old3UV_exact=True,ReviewUV_sha256_held=meta['loop_uv_sha256'],face_region_exact=True,reason='D3 smooths ONLY endpoint derivative/displacement fields periodically at one measured physical arc scale, then same first/last-row minimum-bending solve. Endloops/core/absolute ring geometry not smoothed; no parameter sweep.' if revision=='D3' else 'B/C bare seams failed; initial two-end-row D overconstrained interior curvature. D2 fixes FIRST/LAST interior rows only and minimizes full remaining discrete bending. No handle/parameter sweep or material concealment.' if revision=='D2' else 'Initial two-row constraints: unselected CPU hypothesis, interior facet turns failed.',artist_core_or_head_changes=False)
(P/('collar-revision-'+revision+'-proof.json')).write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
print('REVIEW12_'+revision+'_PUBLISHED',sha(target),proof['changed_vertices'],proof['maximum_delta_m'],flush=True)
