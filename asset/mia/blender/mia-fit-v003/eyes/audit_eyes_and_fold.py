"""Read exact current neutral apertures and fold shader; never saves a scene."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,sys
P=Path(__file__).resolve().parent;P.mkdir(parents=True,exist_ok=True)
C=P.parents[1];V=C/'mia-refinement-v002'
N=V/'integrated/Mia_v0.0.2_Review_R3b.blend';SHA='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'
assert hashlib.sha256(N.read_bytes()).hexdigest()==SHA
bpy.ops.wm.open_mainfile(filepath=str(N),use_scripts=False)
ctrl=bpy.data.objects['Mia_FacialControls_v002'];skin=bpy.data.objects['MIA_V27_SharedHeadBody']
assert all(ctrl[k]==0 for k in ctrl.keys() if k.startswith('Manual') or (k.startswith('P') and k[:3][1:].isdigit()))
dg=bpy.context.evaluated_depsgraph_get();ev=skin.evaluated_get(dg);me=ev.to_mesh()
q=np.array([ev.matrix_world@v.co for v in me.vertices]);nn=np.array([ev.matrix_world.to_3x3()@v.normal for v in me.vertices]);ev.to_mesh_clear()
meta=json.loads((V/'parts/eye-A/payload/surprise-A.json').read_text())
rim=json.loads((C/'mia-face-finish-v29/parts/medial-C2/proof/medial-baseline-inspection.json').read_text())
payload={};eyes=[]
cam=bpy.context.scene.camera;right=np.array(cam.matrix_world.to_3x3().col[0]);up=np.array(cam.matrix_world.to_3x3().col[1])
for row in meta['construction']:
    side=row['side'];curves={};measure={}
    for kind in ['upper','lower']:
        ids=np.array(rim['evaluated_openings'][str(side)][kind+'_evaluated_indices'],int)
        curve=q[ids];xy=np.column_stack([curve@right,curve@up]);a,b=xy[0],xy[-1];axis=(b-a)/np.linalg.norm(b-a);normal=np.array([-axis[1],axis[0]])
        t=(xy-a)@axis/np.linalg.norm(b-a);height=(xy-a)@normal
        if side<0:height=-height
        measure[kind]=dict(width_mm=float(np.linalg.norm(b-a)*1000),height_mm=(height*1000).tolist(),t=t.tolist(),curve_world_m=curve.tolist())
        payload[f'{side}_{kind}_eval']=curve;payload[f'{side}_{kind}_normal']=nn[ids]
        payload[f'{side}_{kind}_raw_path']=np.array(row[kind+'_raw_path'],np.int32)
        curves[kind]=xy
    ids=np.array(row['boundary_ids'],int);raw=np.array([v.co[:] for v in skin.data.shape_keys.key_blocks[0].data]);payload[f'{side}_boundary']=ids
    eyes.append(dict(side=side,screen='right' if q[rim['evaluated_openings'][str(side)]['upper_evaluated_indices']].mean(axis=0)@right>0 else 'left',measure=measure,
                     raw_paths={k:row[k] for k in ['upper_raw_path','lower_raw_path']},raw_boundary_world_m=[list(skin.matrix_world@skin.data.shape_keys.key_blocks[0].data[int(i)].co) for i in ids]))
payload['skin_basis']=np.array([v.co[:] for v in skin.data.shape_keys.key_blocks[0].data],np.float32)
payload['skin_edges']=np.array([e.vertices[:] for e in skin.data.edges],np.int32)
mat=skin.material_slots[0].material;nodes=mat.node_tree.nodes;fold=[]
for node in nodes:
    if any(word in node.name.lower() for word in ['fold','crease']):
        fold.append(dict(name=node.name,type=node.bl_idname,inputs=[dict(name=i.name,value=list(i.default_value) if hasattr(getattr(i,'default_value',None),'__len__') and not isinstance(i.default_value,str) else getattr(i,'default_value',None),links=[(l.from_node.name,l.from_socket.name) for l in i.links]) for i in node.inputs if hasattr(i,'default_value')]))
for row in eyes:
    row['screen']='right' if (np.mean(row['measure']['upper']['curve_world_m'],axis=0)-np.array(cam.matrix_world.translation))@right>0 else 'left'
report=dict(native=str(N),sha256=SHA,eyes=eyes,material=mat.name,fold_nodes=fold,scope='True aperture curves, not lashes/brows. Camera projection recorded; source correspondence needs visual review.',camera=dict(matrix=[list(r) for r in cam.matrix_world],type=cam.data.type,ortho_scale=cam.data.ortho_scale),native_saved=False)
(P/'baseline-eyes-fold.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');np.savez_compressed(P/'baseline-eye-data.npz',**payload)
print('EYE_FIT_AUDIT_DONE',[(r['side'],r['screen'],[(k,round(v['width_mm'],3),round(max(v['height_mm'])-min(v['height_mm']),3)) for k,v in r['measure'].items()]) for r in eyes],flush=True)
