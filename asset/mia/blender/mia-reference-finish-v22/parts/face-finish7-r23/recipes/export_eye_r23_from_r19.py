"""Export exact owner/local coordinates for one R19 -> R23 live replay.

This reads frozen natives only. Key-specific target replacements are separate
from the neutral mesh-cache edit; adding one delta to every key is insufficient.
"""
import bpy,ast,hashlib,json
import numpy as np
from pathlib import Path
HERE=Path(__file__).resolve().parent;OUT=HERE/'candidate-r23';SOURCE=HERE/'candidate-r19/Mia_FaceFinish7_PositionFairR19_v22.blend';TARGET=OUT/'Mia_FaceFinish7_BlinkR23_v22.blend';R22=HERE/'candidate-r22/Mia_FaceFinish7_EyeArcR22_v22.blend'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();ah=lambda p:hashlib.sha256(np.asarray(p).tobytes()).hexdigest()
tree=ast.parse((HERE.parent/'finish-6/dependencies/legacy_snapshot_apply_interp.py').read_text(encoding='utf-8'));exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='snapshots'],type_ignores=[]),'snapshot','exec'))
owners=['MIA_V14_SculptedSkin','MIA_V14_UpperLash_-1','MIA_V14_UpperLash_1','MIA_V14_OuterWing_-1','MIA_V14_OuterWing_1']
def read(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));data={}
 for name in owners:
  obj=bpy.data.objects[name];data[name]={'mesh_cache':np.array([tuple(v.co) for v in obj.data.vertices]),'keys':{k.name:np.array([tuple(v.co) for v in k.data]) for k in obj.data.shape_keys.key_blocks},'matrix_world':[list(r) for r in obj.matrix_world]}
 return data,snapshots()
hashes={str(p):sha(p) for p in [SOURCE,TARGET,R22]};source,snap0=read(SOURCE);target,snap1=read(TARGET);neutral,snap22=read(R22)
assert set(snap0)==set(snap1)
for name in snap0:
 if name not in owners:assert snap0[name]==snap1[name],name
 else:
  for field in ['uv','topology','weights','materials','matrix','modifiers']:assert snap0[name][field]==snap1[name][field],(name,field)
for name in owners:
 assert np.array_equal(target[name]['mesh_cache'],neutral[name]['mesh_cache']),name
 assert np.array_equal(target[name]['keys']['Basis'],neutral[name]['keys']['Basis']),name
def rows(old,new):return [{'id':int(i),'before':old[i].tolist(),'after':new[i].tolist(),'delta':(new[i]-old[i]).tolist()} for i in np.where(np.linalg.norm(new-old,axis=1)>1e-10)[0]]
payload={}
for name in owners:
 old,new=source[name],target[name];payload[name]={'coordinate_space':'Object local Blender meters','matrix_world':new['matrix_world'],'mesh_cache':{'before_sha256_float64':ah(old['mesh_cache']),'after_sha256_float64':ah(new['mesh_cache']),'rows':rows(old['mesh_cache'],new['mesh_cache'])},'keys':{}}
 for key in old['keys']:
  rr=rows(old['keys'][key],new['keys'][key])
  if rr:payload[name]['keys'][key]={'before_sha256_float64':ah(old['keys'][key]),'after_sha256_float64':ah(new['keys'][key]),'rows':rr}
for p,digest in hashes.items():assert sha(p)==digest,p
bundle={'source':{'path':str(SOURCE),'sha256':sha(SOURCE)},'target':{'path':str(TARGET),'sha256':sha(TARGET)},'neutral_r22':{'path':str(R22),'sha256':sha(R22)},'recipe_sha256':sha(__file__),'all_unrelated_owner_snapshots_exact':True,'owner_topology_uv_weights_materials_matrix_modifiers_exact':True,'neutral_basis_cache_exact_r22':True,'apply_rule':'Verify each exact before coordinate on the owner/key, then replace with after. Apply mesh_cache separately. These are R19-to-R23 complete target edits; do NOT combine with R22/R23 intermediate deltas, and do NOT broadcast one delta to all keys. Body14/Hair0d belong to integration and are not included.','owners':payload,'limits':['Selected local eye WIP, not final likeness approval. Symmetric blink + subtle expression only; asymmetric driver coordination and all47 expressions are not claimed.','R23 evaluated full gap max0.121mm under lash, no visible leak at reviewed0/+/-30; steeper/combo review recorded separately.']}
dest=OUT/'owner-key-replay-from-r19.json';assert not dest.exists();dest.write_text(json.dumps(bundle,indent=2));print(json.dumps({'replay':str(dest),'sha256':sha(dest),'source':bundle['source'],'target':bundle['target'],'owner_key_rows':{name:{'mesh_cache':len(v['mesh_cache']['rows']),'keys':{key:len(value['rows']) for key,value in v['keys'].items()}} for name,v in payload.items()}},indent=2))
