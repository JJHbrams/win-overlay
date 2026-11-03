"""E v10 semantic-only successor; geometry/atlas/correspondence untouched."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));from source_branch_ownership import inherited_donor_arm_labels
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();ah=lambda a:hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
old=np.load(P/'surface-v9-expanded-E-branches.npz');joined=np.load(P/'joined-expanded-E.npz');previous=np.load(P/'joined-discrete-D3.npz');previousSurface=np.load(P/'surface-v7-discrete-D3.npz');meta=json.loads((P/'surface-v9-expanded-E-branches.json').read_text());labels=inherited_donor_arm_labels(previous,previousSurface,joined);region=old['face_region'].copy();inherit=labels[old['meshfaceid']];region[inherit!=0]=inherit[inherit!=0]
target=P/'surface-v10-expanded-E-source-branches.npz';assert not target.exists();np.savez_compressed(target,world=old['world'],triangles=old['triangles'],loop_uv=old['loop_uv'],face_region=region,meshfaceid=old['meshfaceid'])
changed=np.flatnonzero(region!=old['face_region']);proof=dict(previous_payload_sha256=sha(P/'surface-v9-expanded-E-branches.npz'),new_payload_sha256=sha(target),world_sha256=ah(old['world']),loop_uv_sha256=ah(old['loop_uv']),changed_body_face_ids=changed.tolist(),changed_faces=len(changed),policy='Retained donor hands/fingers/forearms inherit validated D3 labels6/7 via SAME original source_face. New collars exact construction ancestry; guide uses component fields. No global X/Z patch.',geometry_UV_triangles_meshfaceid_exact=True)
new=np.load(target)
for key in ['world','triangles','loop_uv','meshfaceid']:assert np.array_equal(old[key],new[key]),key
version=dict(meta,payload_version='v10-expanded-E-source-branches',surface_npz_path=str(target),surface_npz_sha256=sha(target),region_counts={str(i):int((region==i).sum()) for i in range(1,16)},donor_arm_branch_policy=proof['policy'],previous_semantic_failed_payload_sha256=proof['previous_payload_sha256'])
target.with_suffix('.json').write_text(json.dumps(version,indent=2)+'\n',encoding='utf-8',newline='\n');(P/'E-source-branch-revision-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
print('REVIEW12_E_SEMANTIC_V10',sha(target),'changed',len(changed),flush=True)
