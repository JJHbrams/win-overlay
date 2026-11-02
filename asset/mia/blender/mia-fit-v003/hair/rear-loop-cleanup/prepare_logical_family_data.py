"""Explicit complete-shell U-return family plus topological backing-root branch. DATA only."""
from pathlib import Path
import numpy as np,json
P=Path(__file__).resolve().parent;d=np.load(P/'source-mesh-input.npz');labels=np.load(P/'global-components.npz')['face_component'];branch=np.load(P/'backing-branch-DATA.npz')['polygon_indices']
groups=dict(original_front_skins=[321,298,219,222,254,309],complete_exposed_lower_return_skins=[200,204,218,234,237,238,241,232,261,262,296,299,293,300,206,207,220,221,229,235,231])
parts=sorted(set(sum(groups.values(),[])));ids=np.union1d(branch,np.flatnonzero(np.isin(labels,parts))).astype(np.int32);np.savez_compressed(P/'logical-family-DATA.npz',polygon_indices=ids)
(P/'logical-family-DATA.json').write_text(json.dumps(dict(status='CPU ownership candidate; not approved or installed',groups=groups,backing_branch_faces=len(branch),total_faces=len(ids),limits='Complete global components plus one branch traced to its four-edge topological root attachment. No spatial camera ROI; retained long side curls202/193/211 and central pointed layers292/239/278 remain.'),indent=2)+'\n',encoding='utf-8');print('LOGICAL_FAMILY_DATA',len(ids),parts)
