"""Fresh actual-file guard for the added local source grin key."""
from pathlib import Path
import argparse, json, sys, hashlib
import numpy as np, bpy
P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--baseline',required=True);ap.add_argument('--candidate',required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
sys.path.insert(0,str(P.parents[1]/'mia-visible-art-v30/closed-lashes-v31'))
from audit_mesh_helpers import snapshot,arr
def read(p):
 s=snapshot(p);data={}
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  data[o.name]={k.name:arr(k.data,'co',3).tobytes() for k in o.data.shape_keys.key_blocks} if o.data.shape_keys else {}
 return s,data
before,old=read(a.baseline);after,new=read(a.candidate);owners=['MIA_V27_SharedHeadBody','MIA_V27_Foundation_Face'];name='Face.M_F00_000_00_Fcl_MIA_ToothyGrin'
checks={}
checks['all_original_key_arrays_exact']=all(all(new[n][k]==v for k,v in ks.items()) for n,ks in old.items())
checks['only_two_declared_new_keys']=all(set(new[n])-set(ks)==({name} if n in owners else set()) for n,ks in old.items())
checks['original_material_graphs_exact']=before[2]==after[2];checks['all_original_images_exact']=before[3]==after[3]
checks['topology_uv_weights_transforms_modifiers_slots_exact']=all(all(before[0][n][f]==after[0][n][f] for f in ['topology','UV','weights','matrix','modifiers','materials']) for n in before[0])
checks['all_other_owner_geometry_exact']=all(before[0][n]==after[0][n] for n in before[0] if n not in owners)
checks['original_skin_drivers_plus_one']=after[0][owners[0]]['drivers'][:-1]==before[0][owners[0]]['drivers'] and len(after[0][owners[0]]['drivers'])==len(before[0][owners[0]]['drivers'])+1
checks['foundation_drivers_unchanged']=before[0][owners[1]]['drivers']==after[0][owners[1]]['drivers']
checks['new_key_defaults_neutral']=all(abs(bpy.data.objects[n].data.shape_keys.key_blocks[name].value)<1e-7 for n in owners)
record=dict(checks=checks,candidate=a.candidate,sha256=hashlib.sha256(Path(a.candidate).read_bytes()).hexdigest(),art='NOT_EVALUATED')
Path(a.candidate).with_suffix('.fresh-guard.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
assert all(checks.values()),checks
print('SOURCE_GRIN_FRESH_GUARD_OK',json.dumps(checks),flush=True)
