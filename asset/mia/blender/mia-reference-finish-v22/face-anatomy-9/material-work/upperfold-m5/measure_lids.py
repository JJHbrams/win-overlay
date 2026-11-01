import sys,json
from pathlib import Path
import bpy,numpy as np
ROOT=Path(__file__).resolve().parent;V22=ROOT.parents[2]
sys.path.insert(0,str(V22/'face-anatomy-9/eye-identity-work'))
from build_eye_contour import eye_loops
source=V22/'integration-wip-9-review/Mia_FaceReview_v22_WIP9.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
skin=bpy.data.objects['MIA_V14_SculptedSkin'];mesh=skin.data
P=np.array([v.co[:] for v in mesh.shape_keys.key_blocks[0].data]);loops=eye_loops(mesh,P)
uv=mesh.uv_layers['UVMap'];byvert={}
for poly in mesh.polygons:
    if poly.material_index!=7:continue
    for li in poly.loop_indices:byvert.setdefault(mesh.loops[li].vertex_index,[]).append(uv.data[li].uv[:])
rows=[]
for loop in loops:
    row={'side':loop['side']}
    for part in ['upper','lower']:
        ids=loop[part];row[part]=[{'id':int(i),'p':P[i].tolist(),'uv':np.mean(byvert[i],axis=0).tolist()} for i in ids]
    rows.append(row)
(ROOT/'measured-lid-uv.json').write_text(json.dumps(rows,indent=2))
for row in rows:
    print('SIDE',row['side'])
    for part in ['upper','lower']:
        print(part,[(r['id'],[round(x,5) for x in r['uv']]) for r in row[part][::5]])
