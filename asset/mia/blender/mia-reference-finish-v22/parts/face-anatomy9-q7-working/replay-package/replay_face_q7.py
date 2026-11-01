"""Replay immutable WIP8 -> P2 -> validated dense rest bake -> exact Q7.
Run with Blender --background --python replay_face_q7.py -- --source WIP8.blend --output-dir FRESH
Only one final native is saved; no P2/control natives are needed.
"""
import argparse,ast,hashlib,json,sys
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
P=Path(__file__).resolve().parent;D=P/'dependencies';sys.path.insert(0,str(D));from fingerprint import fingerprint
ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--output-dir',required=True);args=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);src=Path(args.source).resolve();out=Path(args.output_dir).resolve();expected=json.loads((P/'expected-q7.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(src)==expected['source_sha256'],'immutable WIP8 SHA mismatch'
assert not out.exists() or not any(out.iterdir()),'fresh output directory required'
for name,h in expected['dependencies'].items():assert sha(D/name)==h,('dependency hash mismatch',name)
out.mkdir(parents=True,exist_ok=True);native=out/'Mia_ConnectedSurface_Q7_Replayed.blend'
bpy.ops.wm.open_mainfile(filepath=str(src),use_scripts=False);o=bpy.data.objects['MIA_V14_SculptedSkin'];oldmesh=o.data;oldkeys=oldmesh.shape_keys;keys=oldkeys.key_blocks
assert len(oldmesh.vertices)==728 and len(keys)==47
assert [k.name for k in keys]==expected['expected_q7']['key_names']
assert [m.type for m in o.modifiers]==['ARMATURE','SUBSURF']
# Execute only the original frozen primary field functions, never its I/O.
tree=ast.parse((D/'p2_original.py').read_text());names={'smoothstep','bell','lower_face_delta'};exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'frozen-p2-functions','exec'))
delta=np.array([lower_face_delta(np.array(v.co,dtype=float)) for v in keys[0].data]);changed=np.where(np.linalg.norm(delta,axis=1)>1e-9)[0]
for k in keys:
 for i in changed:k.data[int(i)].co+=Vector(delta[int(i)].tolist())
bpy.context.view_layer.update()
# Rest-space subdivision only; keep the actual Armature and its group mapping.
oldkeys.use_fake_user=True;info=[(k.name,k.slider_min,k.slider_max,k.relative_key.name,k.interpolation) for k in keys]
assert not oldkeys.animation_data or not oldkeys.animation_data.drivers
mods=[(m,m.show_viewport,m.show_render) for m in o.modifiers]
for m,_,_ in mods:
 if m.type!='SUBSURF':m.show_viewport=False;m.show_render=False
for k in keys:k.value=0.
bpy.context.view_layer.update();dep=bpy.context.evaluated_depsgraph_get();ev=o.evaluated_get(dep);new=bpy.data.meshes.new_from_object(ev,preserve_all_data_layers=True,depsgraph=dep);coords=[]
for j,k in enumerate(keys):
 if j:k.value=1.
 oldkeys.update_tag();bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();coords.append(np.array([v.co[:] for v in me.vertices]));ev.to_mesh_clear()
 if j:k.value=0.
assert all(a.shape==(16338,3) for a in coords)
o.vertex_groups.clear();o.data=new
for j,(name,lo,hi,relative,interpolation) in enumerate(info):
 k=o.shape_key_add(name=name,from_mix=False);k.slider_min=lo;k.slider_max=hi;k.interpolation=interpolation;k.value=0.;k.data.foreach_set('co',coords[j].astype(np.float32).ravel())
keys=new.shape_keys.key_blocks
for j,(_,_,_,relative,_) in enumerate(info):keys[j].relative_key=keys[relative]
for m,show,render in mods:
 if m.type=='SUBSURF':o.modifiers.remove(m)
 else:m.show_viewport=show;m.show_render=render
retarget=[]
for db in list(bpy.data.objects)+list(bpy.data.shape_keys):
 if db.animation_data:
  for fc in db.animation_data.drivers:
   for var in fc.driver.variables:
    for t in var.targets:
     if t.id==oldkeys:t.id=new.shape_keys;retarget.append([db.name,fc.data_path])
assert len(retarget)==4
roundtrip=np.load(D/'roundtrip-q6b.npz')['delta'];q7=np.load(D/'q7-deltas.npz')
# Q7's control passed through an add/subtract float32 round trip. Reproduce
# its exact arithmetic, without saving or retaining the rejected loft native.
for j,k in enumerate(keys):
 a=(coords[j]+roundtrip).astype(np.float32).astype(np.float64)
 a=(a-roundtrip).astype(np.float32).astype(np.float64)
 if j==0:assert np.array_equal(a,q7['basis']),'dense bake/control coordinate mismatch'
 k.data.foreach_set('co',(a+q7['delta']).astype(np.float32).ravel());k.value=0.
new.vertices.foreach_set('co',np.array([v.co[:] for v in keys[0].data],dtype=np.float32).ravel());new.update();bpy.context.view_layer.update()
assert len(o.vertex_groups)==len(expected['expected_q7']['group_names'])
bpy.ops.wm.save_as_mainfile(filepath=str(native));bpy.ops.wm.open_mainfile(filepath=str(native),use_scripts=False)
actual=json.loads(json.dumps(fingerprint()));errors=[name for name in expected['expected_q7'] if actual[name]!=expected['expected_q7'][name]]
report={'status':'EXACT_Q7_REPLAY' if not errors else 'REPLAY_MISMATCH','source':str(src),'source_sha256':sha(src),'native':str(native),'native_sha256':sha(native),'script_sha256':sha(Path(__file__)),'expected_manifest_sha256':sha(P/'expected-q7.json'),'fingerprint_equal':not errors,'mismatched_fields':errors,'actual':actual,'all_skin_keys_zero':all(k.value==0 for k in bpy.data.objects['MIA_V14_SculptedSkin'].data.shape_keys.key_blocks),'art_status':'PARTIAL MIDFACE GAIN; WHOLE FACE UNAPPROVED'}
(out/'replay-audit.json').write_text(json.dumps(report,indent=2));assert sha(src)==expected['source_sha256'];assert not errors,errors
print('Q7_REPLAY_EXACT',native,flush=True)

