"""Explain any live-original drift before deforming the private baseline."""
from pathlib import Path
import json,hashlib
import bpy,numpy as np
ROOT=Path('D:/MiaWorkCache/mia-reference-work/win-overlay')
def ev(o):
 d=bpy.context.evaluated_depsgraph_get();e=o.evaluated_get(d);m=e.to_mesh(preserve_all_data_layers=True,depsgraph=d)
 v=np.array([e.matrix_world@p.co for p in m.vertices],np.float32)
 uv={u.name:hashlib.sha256(np.array([p.uv[:]for p in u.data],np.float32).tobytes()).hexdigest()for u in m.uv_layers}
 e.to_mesh_clear();return v,uv
a,au=ev(bpy.data.objects['MIA_ConnectedBody_Design']);b,bu=ev(bpy.data.objects['MIA_V27_SharedHeadBody'])
expected=dict(np.load(ROOT/'asset/mia/blender/mia-fit-v003/body/current-body-limit.npz'))['world']
print(json.dumps(dict(private_count=len(a),source_count=len(b),UV_private=au,UV_source=bu,private_cached_exact=bool(np.array_equal(a,expected)),source_cached_exact=bool(np.array_equal(b,expected)),max_mm=float(np.linalg.norm(a-b,axis=1).max()*1000),private_mods=[(x.name,x.type,x.show_viewport)for x in bpy.data.objects['MIA_ConnectedBody_Design'].modifiers],source_mods=[(x.name,x.type,x.show_viewport)for x in bpy.data.objects['MIA_V27_SharedHeadBody'].modifiers])))
