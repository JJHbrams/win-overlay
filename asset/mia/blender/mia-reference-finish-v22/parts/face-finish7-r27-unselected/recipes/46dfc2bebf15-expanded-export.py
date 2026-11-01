"""Read-only exact R23->R25 key replay and evaluated section comparison."""
import bpy,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
OUT=Path(__file__).resolve().parent;H=OUT.parent.parent;SOURCE=H/'candidate-r23/Mia_FaceFinish7_BlinkR23_v22.blend';TARGET=OUT/'Mia_FaceFinish7_OrbitalTransitionR27_v22.blend'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();ah=lambda p:hashlib.sha256(np.asarray(p).tobytes()).hexdigest()
def read(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));o=bpy.data.objects['MIA_V14_SculptedSkin'];return {'mesh_cache':np.array([tuple(v.co) for v in o.data.vertices]),'keys':{k.name:np.array([tuple(v.co) for v in k.data]) for k in o.data.shape_keys.key_blocks}}
source_sha=sha(SOURCE);target_sha=sha(TARGET);old=read(SOURCE);new=read(TARGET)
def edits(a,b):return {'before_sha256_float64':ah(a),'after_sha256_float64':ah(b),'rows':[{'id':int(i),'before':a[i].tolist(),'after':b[i].tolist(),'delta':(b[i]-a[i]).tolist()} for i in np.where(np.linalg.norm(b-a,axis=1)>1e-10)[0]]}
replay={'source':{'path':str(SOURCE),'sha256':source_sha},'target':{'path':str(TARGET),'sha256':target_sha},'owners':{'MIA_V14_SculptedSkin':{'coordinate_space':'Object local Blender meters','mesh_cache':edits(old['mesh_cache'],new['mesh_cache']),'keys':{k:edits(old['keys'][k],new['keys'][k]) for k in old['keys']}}},'apply_rule':'Verify exact before on source owner/key then replace after; mesh_cache separately. Only skin owner is included. Existing R23 eye/carrier/lash owners, body and hair remain untouched.'}
(OUT/'owner-key-replay-from-r23.json').write_text(json.dumps(replay,indent=2))
base=json.loads((OUT.parent/'baseline-volume-inspection.json').read_text());skin=bpy.data.objects['MIA_V14_SculptedSkin']
for k in skin.data.shape_keys.key_blocks:k.value=0.
bpy.context.view_layer.update();ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();bvh=BVHTree.FromPolygons([v.co.copy() for v in mesh.vertices],[list(p.vertices) for p in mesh.polygons]);sections=[]
for original,previous in zip(base['sources']['face6']['samples'],base['sources']['r23']['samples']):
 x,z=original['x'],original['z'];hit=bvh.ray_cast(Vector((x,.2,z)),Vector((0,-1,0)))[0]
 if hit is None:continue
 y=float(hit.y);sections.append({'x':x,'z':z,'face6_y':original['y'],'r23_y':previous['y'],'r27_y':y,'recovered_forward_mm':1000*(y-previous['y']) if previous['y'] is not None else None})
ev.to_mesh_clear();assert sha(SOURCE)==source_sha and sha(TARGET)==target_sha
(OUT/'restored-section-comparison.json').write_text(json.dumps({'source':replay['source'],'candidate':replay['target'],'method':'Actual evaluated front-sheet first hit along local-Y at fixed localX/Z. Diagnostic projection, not homologous tissue or total volume.','samples':sections},indent=2));print(json.dumps({'replay_sha256':sha(OUT/'owner-key-replay-from-r23.json'),'samples':sections},indent=2))
