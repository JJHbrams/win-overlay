"""Apply the reviewed Q9 lip-anchor restoration and bounded cheek taper to exact Q7."""
import argparse,hashlib,json,sys
from pathlib import Path
from collections import Counter,defaultdict
import bpy,numpy as np
P=Path(__file__).resolve().parent;D=P/'dependencies';sys.path.insert(0,str(D));from fingerprint import fingerprint
ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--output-dir',required=True);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);src=Path(a.source).resolve();out=Path(a.output_dir).resolve();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();source_sha=sha(src);expected=json.loads((P/'expected-q9.json').read_text())
assert not out.exists() or not any(out.iterdir()),'fresh output directory required'
for n,h in expected['dependencies'].items():assert sha(D/n)==h,('dependency mismatch',n)
bpy.ops.wm.open_mainfile(filepath=str(src),use_scripts=False);before=json.loads(json.dumps(fingerprint()));q7=json.loads((D/'expected-q7.json').read_text())['expected_q7'];assert before==q7,'source must have exact reviewed Q7 geometry/keys/UV/groups/driver routes'
o=bpy.data.objects['MIA_V14_SculptedSkin'];m=o.data;keys=m.shape_keys.key_blocks;basis=np.array([v.co[:] for v in keys[0].data]);packet=np.load(D/'q9-deltas.npz');assert np.array_equal(packet['basis'],basis)
# Independently locate the current actual mouth boundary, never assume cage IDs.
edges=Counter(tuple(sorted((p.vertices[j],p.vertices[(j+1)%len(p.vertices)]))) for p in m.polygons for j in range(len(p.vertices)));adj=defaultdict(set)
for (i,j),n in edges.items():
 if n==1:adj[i].add(j);adj[j].add(i)
seen=set();loops=[]
for i in adj:
 if i in seen:continue
 todo=[i];ids=[]
 while todo:
  j=todo.pop()
  if j in seen:continue
  seen.add(j);ids.append(j);todo.extend(adj[j]-seen)
 loops.append(ids)
lip=next(ids for ids in loops if 1.48<basis[ids,2].mean()<1.51 and basis[ids,1].mean()>.06);ref=json.loads((D/'wip8-mouth-baseline.json').read_text());assert sorted(lip)==sorted(ref['mouth_loop_ids']);target=np.array(ref['mouth_center']);delta=packet['delta'];assert abs(target[2]-basis[lip,2].mean()-.004)<1e-6
for k in keys:
 v=np.array([p.co[:] for p in k.data]);k.data.foreach_set('co',(v+delta).astype(np.float32).ravel());k.value=0.
m.vertices.foreach_set('co',(basis+delta).astype(np.float32).ravel());m.update();bpy.context.view_layer.update();out.mkdir(parents=True,exist_ok=True);native=out/'Mia_ConnectedSurface_Q9_Replayed.blend';bpy.ops.wm.save_as_mainfile(filepath=str(native));bpy.ops.wm.open_mainfile(filepath=str(native),use_scripts=False);actual=json.loads(json.dumps(fingerprint()));errors=[k for k in expected['expected_q9'] if actual[k]!=expected['expected_q9'][k]]
post=np.array([v.co[:] for v in bpy.data.objects['MIA_V14_SculptedSkin'].data.shape_keys.key_blocks[0].data]);report={'status':'EXACT_Q9_REPLAY' if not errors else 'MISMATCH','source':str(src),'source_sha256':source_sha,'native':str(native),'native_sha256':sha(native),'fingerprint_equal':not errors,'mismatched_fields':errors,'wip8_reference_sha256':ref['wip8_sha256'],'actual_mouth_loop_ids':lip,'lip_before':basis[lip].mean(0).tolist(),'lip_after':post[lip].mean(0).tolist(),'wip8_lip_baseline':target.tolist(),'restored_lip_z_error_mm':float(abs(post[lip,2].mean()-target[2])*1000),'lip_translation_spread_mm':float(np.max(np.ptp(post[lip]-basis[lip],axis=0))*1000),'actual':actual,'art_status':'REVIEW ONLY; mouth drift restored, cheek taper hypothesis, no whole-face approval'};(out/'replay-audit.json').write_text(json.dumps(report,indent=2));assert not errors,errors;assert sha(src)==source_sha;print('Q9_REPLAY_EXACT',native)
