"""Read-only exact R27-to-R28 local owner/key coordinates."""
import bpy,json,hashlib
import numpy as np
from pathlib import Path
OUT=Path(__file__).resolve().parent;H=OUT.parent;SOURCE=H/'candidate-r25/refinement-r27/Mia_FaceFinish7_OrbitalTransitionR27_v22.blend';TARGET=OUT/'Mia_FaceFinish7_MedialTransitionR28_v22.blend'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();ah=lambda p:hashlib.sha256(np.asarray(p).tobytes()).hexdigest()
def read(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));o=bpy.data.objects['MIA_V14_SculptedSkin'];return {'mesh_cache':np.array([tuple(v.co) for v in o.data.vertices]),'keys':{k.name:np.array([tuple(v.co) for v in k.data]) for k in o.data.shape_keys.key_blocks}}
hashes={str(p):sha(p) for p in [SOURCE,TARGET]};a=read(SOURCE);b=read(TARGET)
def edits(old,new):return {'before_sha256_float64':ah(old),'after_sha256_float64':ah(new),'rows':[{'id':int(i),'before':old[i].tolist(),'after':new[i].tolist(),'delta':(new[i]-old[i]).tolist()} for i in np.where(np.linalg.norm(new-old,axis=1)>1e-10)[0]]}
data={'source':{'path':str(SOURCE),'sha256':sha(SOURCE)},'target':{'path':str(TARGET),'sha256':sha(TARGET)},'owners':{'MIA_V14_SculptedSkin':{'coordinate_space':'Object local Blender meters','mesh_cache':edits(a['mesh_cache'],b['mesh_cache']),'keys':{k:edits(a['keys'][k],b['keys'][k]) for k in a['keys']}}},'apply_rule':'Exact before/after coordinates only for R27->R28. Verify before separately on each owner/key; mesh_cache separate. No unrelated owner changes. Do not treat this as a R23 baseline replay.','limits':['Frozen bounded candidate pending actual art review. No G2 or all47-motion acceptance inferred.']}
outer=[249,236,233,234,242,247,248,250,251];mapping=json.loads((H/'candidate-r25/refinement-r26/manifest.json').read_text())['actual_mirror_mapping'];outer+=list({int(mapping[str(i)]) for i in outer if str(i) in mapping})
for key in a['keys']:assert np.array_equal(a['keys'][key][outer],b['keys'][key][outer])
assert np.array_equal(a['mesh_cache'][outer],b['mesh_cache'][outer]);assert len(data['owners']['MIA_V14_SculptedSkin']['mesh_cache']['rows'])==32
for p,digest in hashes.items():assert sha(p)==digest
(OUT/'owner-key-replay-from-r27.json').write_text(json.dumps(data,indent=2));print(json.dumps({'source':data['source'],'target':data['target'],'replay_sha256':sha(OUT/'owner-key-replay-from-r27.json'),'outer_apex_keys_exact':True},indent=2))
