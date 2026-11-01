"""Read-only exact R28 -> final owner/key export for root integration."""
import bpy,json,hashlib,ast
from pathlib import Path
import numpy as np
from collections import Counter
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'shape-f2/handoff';OUT.mkdir(exist_ok=True)
BASE=ROOT/'look-d/Mia_FaceFinish8_AuthoredLookD.blend';FINAL=ROOT/'shape-f2/Mia_FaceFinish8_ConnectedBuccalF2.blend'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();ah=lambda p:hashlib.sha256(np.asarray(p).tobytes()).hexdigest()
t=ast.parse((ROOT.parent/'finish-6/dependencies/legacy_snapshot_apply_interp.py').read_text());exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='snapshots'],type_ignores=[]),'guards','exec'))
OWNERS=['MIA_V14_SculptedSkin','MIA_V06_BODY_SKIN','MIA_V14_MouthSeam','MIA_V14_SmoothJawInk']
def data():
 return {name:{'mesh_cache':np.array([tuple(v.co) for v in bpy.data.objects[name].data.vertices]),'keys':{k.name:np.array([tuple(v.co) for v in k.data]) for k in bpy.data.objects[name].data.shape_keys.key_blocks} if bpy.data.objects[name].data.shape_keys else {}} for name in OWNERS}
def aperture():
 skin=bpy.data.objects['MIA_V14_SculptedSkin'];out={}
 for value in [0,.5,1]:
  for k in skin.data.shape_keys.key_blocks:k.value=0
  skin.data.shape_keys.key_blocks['Face.M_F00_000_00_Fcl_EYE_Close'].value=value;bpy.context.view_layer.update();ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();p=np.array([tuple(v.co) for v in m.vertices]);ec=Counter(tuple(sorted((f.vertices[i],f.vertices[(i+1)%len(f.vertices)]))) for f in m.polygons for i in range(len(f.vertices)));ids=sorted({i for e,n in ec.items() if n==1 for i in e if .010<abs(p[i,0])<.061 and p[i,1]>.035 and 1.525<p[i,2]<1.558});out[str(value)]=(ids,p[ids]);ev.to_mesh_clear()
 return out
bpy.ops.wm.open_mainfile(filepath=str(BASE));before=data();bs=snapshots();ba=aperture()
bpy.ops.wm.open_mainfile(filepath=str(FINAL));after=data();fs=snapshots();fa=aperture()
rows={};summary={};guard={}
for name in OWNERS:
 item={};count=0
 for kind in ['mesh_cache','keys']:
  for key,a in (before[name]['keys'].items() if kind=='keys' else [('mesh_cache',before[name]['mesh_cache'])]):
   b=after[name]['keys'][key] if kind=='keys' else after[name]['mesh_cache'];ids=np.where(np.any(a!=b,axis=1))[0]
   if len(ids):item[key]=[{'id':int(i),'before':a[i].tolist(),'after':b[i].tolist(),'delta':(b[i]-a[i]).tolist()} for i in ids];count=max(count,len(ids))
 rows[name]=item;delta=after[name]['mesh_cache']-before[name]['mesh_cache'];summary[name]={'count':count,'max_delta_m':float(np.linalg.norm(delta,axis=1).max())}
 if name=='MIA_V06_BODY_SKIN':
  o=bpy.data.objects[name];z=np.array([(o.matrix_world@v.co).z for v in o.data.vertices]);assert np.max(abs(delta[z<=1.46]))==0;guard['body_below_world_1_46_exact']=True
for name in bs:
 for field in bs[name]:
  if name in OWNERS and field in ['co','keys']:continue
  if name=='MIA_V14_SculptedSkin' and field=='materials':continue
  assert bs[name][field]==fs[name][field],(name,field)
for value in ba:
 assert ba[value][0]==fa[value][0];guard['evaluated_eye_boundary_'+value]={'count':len(ba[value][0]),'max_delta_m':float(np.linalg.norm(ba[value][1]-fa[value][1],axis=1).max())}
report={'schema_version':1,'baseline':{'path':str(BASE),'sha256':sha(BASE)},'candidate':{'path':str(FINAL),'sha256':sha(FINAL)},'owners':rows,'summary':summary,'guards':guard,'material_transfer':{'skin_slot':7,'material':'MIA_Finish8_AuthoredFacePigment','method':'UNCHANGED from D; do not transfer or replace any material for F2. Maps and UV exact.'},'limits':['Root-owned integration only; this export does not operate on live scene.','Per-key before/after values must be checked before applying; no replay over a non-D face.','Existing UVMap preserved. Eye/lash owners and old R23 key-specific fixes survive; symmetric blink only is tested.']}
(OUT/'owner-key-replay-from-d.json').write_text(json.dumps(report,indent=2));(OUT/'guard-summary.json').write_text(json.dumps({'summary':summary,'guards':guard},indent=2));print('REPLAY_EXPORTED',json.dumps(summary))
