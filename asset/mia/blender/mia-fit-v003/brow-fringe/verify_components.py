"""Fresh CPU equivalence + coexistence check for the split runtime API.

No render, scene save or original-file write. Contract capture is tied to the
immutable native and occurs before the temporary in-memory sentinel keys.
"""
from pathlib import Path
import sys, json, hashlib, importlib.util
sys.dont_write_bytecode=True
import bpy, numpy as np
P=Path(__file__).resolve().parent; sys.path.insert(0,str(P))
import apply_candidate as historical
import apply_components as current
ROOT=Path(r'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-fit-v003')
sys.path.insert(0,str(ROOT/'body/inputs')); import scene_fingerprint as guard
def load(path):
    s=importlib.util.spec_from_file_location('brow_components_compose',path)
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
native=Path(bpy.data.filepath); native_hash=sha(native)
assert native_hash=='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'
composition=load(ROOT/'integration/compose_selected.py').apply(diagnostic_guides=False,provisional_brow_ink=False)
brows=[bpy.data.objects['V31_SourceBrow_'+str(s)] for s in (-1,1)]
main=bpy.data.objects['MIA_V17_PIXAL_DetailedHair']
contract={}
for side,ob in zip((-1,1),brows):
    contract[str(side)]={'raw_sha256':current._hash([v.co[:] for v in ob.data.vertices]),
        'uv_sha256':current._hash([v.uv[:] for v in ob.data.uv_layers['BrowParamUV'].data]),
        'original_key_sha256':{k.name:current._hash([v.co[:] for v in k.data]) for k in ob.data.shape_keys.key_blocks}}
(P/'brow-contract.json').write_text(json.dumps(contract,indent=2)+'\n',encoding='utf-8',newline='\n')
for ob in [main,*brows]:
    if not ob.data.shape_keys:ob.shape_key_add(name='Basis')
    key=ob.shape_key_add(name='INMEMORY_UNRELATED_COEXISTENCE_SENTINEL')
    key.data[0].co.z+=.0001; key.value=.37
def key_state(ob):
    return {k.name:{'coords':current._hash([v.co[:] for v in k.data]),'value':float(k.value),'relative':k.relative_key.name} for k in ob.data.shape_keys.key_blocks}
sentinel_before={o.name:key_state(o) for o in [main,*brows]}
original_mats={o.name:o.data.materials[0] for o in brows}
cache={}; protected={o.name:guard.object_fingerprint(o,cache) for o in bpy.data.objects if o not in [main,*brows]}
original_materials={m.name:guard.material_signature(m,cache) for m in bpy.data.materials}
envelope=guard.scene_envelope()
def evaluated(ob):
    dg=bpy.context.evaluated_depsgraph_get(); e=ob.evaluated_get(dg); me=e.to_mesh(preserve_all_data_layers=True,depsgraph=dg)
    q=np.asarray([list(e.matrix_world@v.co) for v in me.vertices]); e.to_mesh_clear(); return q
ctrl=bpy.data.objects['Mia_FacialControls_v002']; control_before={k:ctrl[k] for k in ctrl.keys() if isinstance(ctrl[k],(int,float))}
states=[('neutral',{}),('halfblink',{'Manual_EYE_Close':.5}),('closed',{'Manual_EYE_Close':1}),('angry',{'Manual_ALL_Angry':1}),('surprise',{'Manual_ALL_Surprised':1})]
def sample():
    result={}
    for label,state in states:
        for k in ctrl.keys():
            if k.startswith('Manual_') or (len(k)>3 and k[0]=='P' and k[1:3].isdigit()):ctrl[k]=0.
        for k,v in state.items():ctrl[k]=v
        ctrl.update_tag(); bpy.context.view_layer.update()
        result[label]=[evaluated(o) for o in brows]
    for k,v in control_before.items():ctrl[k]=v
    ctrl.update_tag(); bpy.context.view_layer.update(); return result
historical.apply('C'); expected=sample(); expected_main=evaluated(main)
# Only the just-created components are removed; originals and sentinels remain.
for ob in brows:
    mod=ob.modifiers[current.PREFIX+'DynamicWidth']; group=mod.node_group
    ob.modifiers.remove(mod); bpy.data.node_groups.remove(group)
    ob.data.attributes.remove(ob.data.attributes[current.PREFIX+'WidthFactor'])
    material=ob.data.materials[0]; ob.data.materials[0]=original_mats[ob.name]
    bpy.data.materials.remove(material)
main.shape_key_remove(main.data.shape_keys.key_blocks['V003_SourceFringeFine_C'])
del main[current.PREFIX+'LogicalRoots']
bpy.context.view_layer.update()
assert all(key_state(o)==sentinel_before[o.name] for o in [main,*brows])
brow_only_main=guard.object_fingerprint(main)
brow_result=current.apply()['brow']
assert guard.object_fingerprint(main)==brow_only_main, 'Brow-only API changed Main'
assert current.apply_brows()['already_applied']
fringe_result=current.apply_fringe('C'); actual=sample(); actual_main=evaluated(main)
rows=[]
for label,_ in states:
    for i,ob in enumerate(brows):
        assert np.array_equal(expected[label][i],actual[label][i]), (label,ob.name)
        rows.append({'state':label,'owner':ob.name,'vertices':len(actual[label][i]),'actual_evaluated_bitexact_to_rendered_helper':True})
assert np.array_equal(expected_main,actual_main), 'Split fringe differs from rendered helper'
assert current.apply_fringe('C')['already_applied']
for ob in [main,*brows]:
    now=key_state(ob)
    for name,state in sentinel_before[ob.name].items():assert now[name]==state, (ob.name,name)
after_cache={}
for name,fp in protected.items():assert guard.object_fingerprint(bpy.data.objects[name],after_cache)==fp, name
for name,signature in original_materials.items():assert guard.material_signature(bpy.data.materials[name],after_cache)==signature, name
assert guard.scene_envelope()==envelope and sha(native)==native_hash
report={'status':'PASS','native_sha256':native_hash,'composition':composition,
    'brow_only_leaves_Main_fingerprint_exact':True,'unknown_relative_keys_and_values_exact':True,
    'actual_Main_and_brow_equivalent_to_historical_C_helper':True,'brow_evaluated_cases':rows,
    'protected_owners_exact':len(protected),'old_material_graphs_exact':True,'idempotent':True,
    'brow_result':brow_result,'fringe_result':fringe_result,
    'native_saved':False,'GPU_used':False,'ART':'UNVERIFIED independently of this API equivalence guard',
    'implementation_sha256':sha(P/'apply_components.py'),'contract_sha256':sha(P/'brow-contract.json')}
(P/'CPU-components-guard.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print('BROW_FRINGE_COMPONENTS_GUARD '+json.dumps({'status':'PASS','brow_cases':len(rows),'unknown_keys':'preserved','GPU_used':False}),flush=True)
