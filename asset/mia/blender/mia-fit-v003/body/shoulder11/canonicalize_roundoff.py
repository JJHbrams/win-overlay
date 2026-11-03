"""Root-authorized restoration of exactly4 known <=1e-7m mesher roundoff points."""
from pathlib import Path
import sys,hashlib,json,importlib.util
import numpy as np
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;B=P.parent/'posterior-union09';raw=P/'shoulder11.npz';target=P/'shoulder11-canonical.npz'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not target.exists() and sha(raw)=='61c655d1916776940b1a29d32fe1dd9fbd5633007fa465a58d36394e3efde94b'
a=np.load(B/'posterior09.npz');b=np.load(raw);v0=a['world'];v=b['world'];f=b['triangles'];q=v.copy();lookup={p.tobytes():i for i,p in enumerate(v)}
missing=[i for i,p in enumerate(v0) if p[2]>=1.465 and p.tobytes() not in lookup]
assert set(missing)=={38790,39130,42310,42699} and len(missing)==4
mapping=[];used=set()
for i in missing:
    eligible=np.flatnonzero((v[:,1]==v0[i,1])&(v[:,2]==v0[i,2])&(abs(v[:,0].astype(float)-v0[i,0])<=1e-7))
    assert len(eligible)==1; j=int(eligible[0]);assert j not in used;used.add(j)
    delta=v0[i].astype(float)-v[j];distance=float(np.linalg.norm(delta));assert 0<distance<=1e-7 and np.array_equal(v[j,1:],v0[i,1:])
    q[j]=v0[i];mapping.append(dict(old09_vertex=int(i),raw11_vertex=j,before=v[j].tolist(),after=q[j].tolist(),delta_m=delta.tolist(),distance_m=distance))
changed=np.flatnonzero(np.any(q!=v,axis=1));assert set(changed)==used and len(changed)==4
spec=importlib.util.spec_from_file_location('roundoff_readonly_geometry',P.parent/'posterior-continuity08/geometry.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
n0,_=g.normals(v.astype(float),f);n1,_=g.normals(q.astype(float),f);incident=np.flatnonzero(np.isin(f,list(used)).any(1));angles=np.degrees(np.arctan2(np.linalg.norm(np.cross(n0,n1),axis=1),(n0*n1).sum(1)))
np.savez_compressed(target,world=q,triangles=f)
assert sha(raw)=='61c655d1916776940b1a29d32fe1dd9fbd5633007fa465a58d36394e3efde94b'
proof=dict(status='EXPLICIT exact4 nanometre roundoff restoration, ONE field/meshing only',raw_NPZ_sha256=sha(raw),final_NPZ_sha256=sha(target),
    raw_world_f32_sha256=hashlib.sha256(v.tobytes()).hexdigest(),final_world_f32_sha256=hashlib.sha256(q.tobytes()).hexdigest(),
    bijective_mapping=mapping,changed_points=4,maximum_distance_m=max(m['distance_m'] for m in mapping),Y_Z_already_exact=True,all_other_coordinates_bitexact=True,triangles_bitexact=True,
    actual_incident_triangles=len(incident),actual_maximum_face_normal_change_degrees=float(angles.max()),actual_incident_normal_change_degrees=np.percentile(angles[incident],[50,95,100]).tolist(),
    authority='Root explicitly authorized only4 unique old09 upperprotected counterpart restorations <=1e-7m after raw exactguardFAIL. No tolerance relaxation: final exacttriangle/coordinate guards must pass.',
    limitation='Not a physical C0 sculpt mask; no remesh, new field/gate, width variant, GPU or native save. Savednative/actuals must useFINAL hash only.')
(P/'roundoff-canonicalization.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n');print('SHOULDER11_EXACT4_ROUNDOFF_RESTORED',json.dumps(proof),flush=True)
