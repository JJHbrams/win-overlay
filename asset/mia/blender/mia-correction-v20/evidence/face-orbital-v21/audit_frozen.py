"""Fresh-process, read-only audit of the frozen primary candidate."""
import bpy,ast,json,hashlib,numpy as np
from pathlib import Path
OUT=Path(__file__).resolve().parent/'main';manifest=json.loads((OUT/'manifest.json').read_text())
ah=lambda p:hashlib.sha256(np.asarray(p).tobytes()).hexdigest()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
tree=ast.parse((OUT/'exact-recipe.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='snapshots'],type_ignores=[]),'snapshot-helper','exec'))
states=[]
for path in [manifest['source'],manifest['native']]:
 bpy.ops.wm.open_mainfile(filepath=path);bpy.context.view_layer.update();skin=bpy.data.objects['MIA_V14_SculptedSkin']
 keys={k.name:np.array([tuple(v.co) for v in k.data]) for k in skin.data.shape_keys.key_blocks}
 relative={k.name:keys[k.name]-keys[k.relative_key.name] for k in skin.data.shape_keys.key_blocks}
 body=bpy.data.objects['MIA_V06_BODY_SKIN'];ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();body_eval=ah([tuple(v.co) for v in me.vertices]);ev.to_mesh_clear()
 images={i.name:{'sha256':hashlib.sha256(i.packed_file.data).hexdigest(),'fake_user':i.use_fake_user,'users':i.users} for i in bpy.data.images if i.packed_file}
 finite=all(np.isfinite(v.co[:]).all() for o in bpy.context.scene.objects if o.type=='MESH' for v in o.data.vertices)
 finite_uv=all(np.isfinite(v.uv[:]).all() for o in bpy.context.scene.objects if o.type=='MESH' for l in o.data.uv_layers for v in l.data)
 states.append({'snapshot':snapshots(),'relative':relative,'body_eval':body_eval,'images':images,'visible':[o.name for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render],'neutral_keys':{k.name:k.value for k in skin.data.shape_keys.key_blocks},'finite':finite,'finite_uv':finite_uv})
a,b=states;assert json.loads(json.dumps(a['snapshot']))==manifest['before'];assert json.loads(json.dumps(b['snapshot']))==manifest['after']
changed=manifest['changed_owners'];assert len(changed)==6
assert all(a['snapshot'][n]==b['snapshot'][n] for n in a['snapshot'] if n not in changed)
assert a['visible']==b['visible'];assert a['body_eval']==b['body_eval'];assert len(b['images'])==59
assert {n:d['sha256'] for n,d in a['images'].items()}=={n:d['sha256'] for n,d in b['images'].items()}
assert all(d['fake_user'] for d in b['images'].values());assert b['finite'] and b['finite_uv']
errors={n:float(np.max(np.abs(a['relative'][n]-b['relative'][n]))) for n in a['relative']};assert len(errors)==47 and max(errors.values())<2e-7
assert all(v==0 for k,v in b['neutral_keys'].items() if k!='Basis')
assert sha(manifest['source'])==manifest['source_sha256'];assert sha(manifest['native'])==manifest['native_sha256'];assert sha(OUT/'exact-recipe.py')==manifest['recipe_sha256']
report={'source':manifest['source'],'source_sha256':sha(manifest['source']),'native':manifest['native'],'native_sha256':sha(manifest['native']),'exact_recipe':str(OUT/'exact-recipe.py'),'recipe_sha256':sha(OUT/'exact-recipe.py'),'no_native_saved':True,'changed_owner_scope':changed,'all_other_mesh_snapshot_exact':True,'visible_mesh_set_unchanged':True,'body_evaluated_hash_identical':b['body_eval'],'skin_key_count':len(errors),'skin_relative_key_max_error_m':max(errors.values()),'key_errors_m':errors,'neutral_key_values':b['neutral_keys'],'packed_image_count':59,'packed_bytes_match_source':True,'all_packed_fake_user':True,'images':b['images'],'finite_mesh_and_uv':True,'limitations':['Inherited blink deformation and fixed makeup are not a final expression pass.','Uneven triangle control cage and residual corner/temple/forehead shading remain.','Eye depth probe variants were never saved or adopted.','This preservation audit does not decide art acceptance.']}
(OUT/'readonly-freeze-audit.json').write_text(json.dumps(report,indent=2));print('FROZEN_AUDIT_OK')
