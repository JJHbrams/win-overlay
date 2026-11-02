"""Fresh reopen runtime checks; key propagation is not source-art acceptance."""
from pathlib import Path
import argparse, hashlib, json, sys
import bpy
P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--native',required=True);ap.add_argument('--sha256',required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);p=Path(a.native)
assert hashlib.sha256(p.read_bytes()).hexdigest()==a.sha256
bpy.ops.wm.open_mainfile(filepath=str(p),use_scripts=False)
c=bpy.data.objects['Mia_FacialControls_v002'];master=bpy.data.objects['MIA_V27_Foundation_Face']
rows=json.loads((P/'expression-intents.json').read_text(encoding='utf-8'))['panels'];results=[]
for row in rows:
 for name in list(c.keys()):
  if name.startswith('P') and name[:3][1:].isdigit():c[name]=0.
 prop=f"P{row['panel']:02}_{row['id']}";c[prop]=1.;c.update_tag()
 bpy.context.scene.frame_set(row['panel']+1);bpy.context.view_layer.update()
 actual={k.name.split('_Fcl_')[-1]:float(k.value) for k in master.data.shape_keys.key_blocks[1:]}
 expected=row['initial_key_recipe']
 assert all(abs(actual[s]-v)<1e-5 for s,v in expected.items()),(row['id'],actual,expected)
 followers={}
 for n in ['MIA_V27_SharedHeadBody','V30_UpperLashes_-1','V30_LowerLashes_1','V31_SourceBrow_1','V28G_InnerLid_1']:
  sk=bpy.data.objects[n].data.shape_keys
  values={k.name.split('_Fcl_')[-1]:float(k.value) for k in sk.key_blocks[1:]}
  assert all(abs(values[s]-v)<1e-5 for s,v in expected.items()),(row['id'],n,values,expected)
  followers[n]=True
 results.append(dict(panel=row['panel'],preset=prop,master_values=actual,followers=followers))
for name in list(c.keys()):
 if name.startswith('P') and name[:3][1:].isdigit():c[name]=0.
c.update_tag();bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
assert all(abs(k.value)<1e-7 for k in master.data.shape_keys.key_blocks[1:])
assert hashlib.sha256(p.read_bytes()).hexdigest()==a.sha256
(p.parent/'expression-controls-runtime.json').write_text(json.dumps(dict(native=str(p),sha256=a.sha256,
  panel_runtime=results,neutral_restored=True,asset_saved=False,art='NOT_EVALUATED'),indent=2)+'\n',encoding='utf-8')
print('EXPRESSION_CONTROLS_RUNTIME_16_OK',flush=True)
