"""Fresh CPU actual-composition, scope, real-gap and brow-contact checks."""
from pathlib import Path
import hashlib,json,sys,importlib.util
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import apply_candidate as patch
V=sys.argv[sys.argv.index('--variant')+1] if '--variant' in sys.argv else 'B'
assert V in ('B','C')
ROOT=Path(r'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-fit-v003')
sys.path.insert(0,str(ROOT/'body/inputs'));import scene_fingerprint as guard
def load(path):
    spec=importlib.util.spec_from_file_location('browfringe_'+path.stem,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
native=Path(bpy.data.filepath);expected='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1';assert sha(native)==expected
composition=load(ROOT/'integration/compose_selected.py').apply(diagnostic_guides=False,provisional_brow_ink=False)
assert not any(o.name.startswith('MiaHair_BrowInkProjection_') for o in bpy.data.objects)
main=bpy.data.objects['MIA_V17_PIXAL_DetailedHair'];brow_names=['V31_SourceBrow_-1','V31_SourceBrow_1'];allowed={main.name,*brow_names}
before_cache={};before={o.name:guard.object_fingerprint(o,before_cache) for o in bpy.data.objects};scene=guard.scene_envelope()
oldmats={m.name:guard.material_signature(m,before_cache) for m in bpy.data.materials}
source_ids=np.asarray([d.value for d in main.data.attributes['MIA_SOURCE_POLYGON'].data],np.int32)
slots=np.asarray([p.material_index for p in main.data.polygons]);uvhash={u.name:guard.digest(u.data,'uv',2) for u in main.data.uv_layers}
attrs=guard.point_attribute_signatures(main.data)
cfg=json.loads((P/('candidate-'+V+'.json')).read_text());payload=np.load(P/('fringe-'+V+'.npz'));inputdata=np.load(P/'current-inputs.npz')
def mesh(ob):
    dg=bpy.context.evaluated_depsgraph_get();ev=ob.evaluated_get(dg);me=ev.to_mesh(preserve_all_data_layers=True,depsgraph=dg)
    q=np.asarray([list(ev.matrix_world@v.co) for v in me.vertices]);f=np.asarray([p.vertices[:] for p in me.polygons]);ev.to_mesh_clear();return q,f
q0,faces=mesh(main)
camera=np.asarray(json.loads((P/'current-inputs.json').read_text())['camera']['matrix']);forward=-camera[:3,2]
def visibility():
    def transparent(mat):
        if not mat or not mat.node_tree:return False
        out=mat.node_tree.get_output_node('EEVEE')
        if not out or not out.inputs['Surface'].is_linked:return False
        def pure(node):
            if node.type=='BSDF_TRANSPARENT':return True
            if node.type=='REROUTE':return all(pure(l.from_node) for l in node.inputs[0].links)
            if node.type=='MIX_SHADER':return all(i.is_linked and all(pure(l.from_node) for l in i.links) for i in [node.inputs[1],node.inputs[2]])
            return False
        return pure(out.inputs['Surface'].links[0].from_node)
    visible=set()
    def walk(collection):
        if collection.hide_render:return
        visible.update(collection.objects)
        for child in collection.children:walk(child)
    walk(bpy.context.scene.collection);trees=[]
    for ob in visible:
        if ob.type!='MESH' or ob.hide_render or ob.name in brow_names:continue
        dg=bpy.context.evaluated_depsgraph_get();e=ob.evaluated_get(dg);me=e.to_mesh();me.calc_loop_triangles()
        points=[e.matrix_world@v.co for v in me.vertices];ignore={i for i,mat in enumerate(me.materials) if transparent(mat)}
        polys=[tuple(t.vertices) for t in me.loop_triangles if me.polygons[t.polygon_index].material_index not in ignore]
        poly_ids=[t.polygon_index for t in me.loop_triangles if me.polygons[t.polygon_index].material_index not in ignore]
        if polys:trees.append((ob.name,BVHTree.FromPolygons(points,polys,all_triangles=True),poly_ids))
        e.to_mesh_clear()
    rows=[]
    for side in [-1,1]:
        bq,_=mesh(bpy.data.objects['V31_SourceBrow_'+str(side)]);centers=bq.reshape(-1,3,3)[:,1];lo,hi=cfg['brow_width_case'][str(side)]['observed_u'];samples=[]
        for i,p in enumerate(centers):
            if not(lo<=i/64<=hi):continue
            hits=[]
            for owner,tree,poly_ids in trees:
                co,no,fi,distance=tree.ray_cast(Vector(p-forward*.08),Vector(forward),.0795)
                if co is not None:hits.append((distance,owner,poly_ids[fi],list(co)))
            first=min(hits,key=lambda h:h[0]) if hits else None
            samples.append({'column':i,'visible_through_real_hair_gap':first is None,
                'first_hit_owner':first[1] if first else None,'first_hit_polygon':int(first[2]) if first else None,
                'first_hit_world':first[3] if first else None,'target_world':p.tolist()})
        rows.append({'side':side,'observed_samples':len(samples),'unoccluded':sum(x['visible_through_real_hair_gap'] for x in samples),'samples':samples})
    return rows
visibility_before=visibility();applied=patch.apply(V);q1,newfaces=mesh(main)
actual_move_mm=float(np.linalg.norm(q1-q0,axis=1).max()*1000);assert actual_move_mm>cfg['max_move_mm']*.95
assert np.array_equal(faces,newfaces)
outside=np.ones(len(q0),bool);outside[payload['indices']]=False;assert np.array_equal(q0[outside],q1[outside])
tri0=q0[faces];tri1=q1[faces];n0=np.cross(tri0[:,1]-tri0[:,0],tri0[:,2]-tri0[:,0]);n1=np.cross(tri1[:,1]-tri1[:,0],tri1[:,2]-tri1[:,0]);rev=np.flatnonzero(np.einsum('ij,ij->i',n0,n1)<-1e-15)
assert not len(rev),rev[:20]
assert np.array_equal(source_ids,np.asarray([d.value for d in main.data.attributes['MIA_SOURCE_POLYGON'].data],np.int32))
assert np.array_equal(slots,np.asarray([p.material_index for p in main.data.polygons]))
assert uvhash=={u.name:guard.digest(u.data,'uv',2) for u in main.data.uv_layers}
assert attrs==guard.point_attribute_signatures(main.data)
after_material_cache={};main_after=guard.object_fingerprint(main,after_material_cache)
for key in ('vertices','loop_vertices','polygon_sizes','uv','weight_hash','modifiers','modifier_settings','materials','material_signatures'):
    assert main_after[key]==before[main.name][key],('Main protected field changed',key)
for name,signature in oldmats.items():assert guard.material_signature(bpy.data.materials[name],after_material_cache)==signature,('Old material changed',name)
for name in brow_names:
    now=guard.object_fingerprint(bpy.data.objects[name]);old=before[name]
    for key in ('vertices','loop_vertices','polygon_sizes','uv','keys','weight_hash','drivers','key_state'):
        assert now[key]==old[key],(name,key)
visibility_after=visibility()
assert sum(r['unoccluded'] for r in visibility_after)>sum(r['unoccluded'] for r in visibility_before),'No whole-scene real-brow exposure gain'
np.savez_compressed(P/('CPU-wire-'+V+'.npz'),before=q0[faces[payload['owned_face_ids']]],after=q1[faces[payload['owned_face_ids']]])
ctrl=bpy.data.objects['Mia_FacialControls_v002'];control_before={k:ctrl[k] for k in ctrl.keys() if isinstance(ctrl[k],(float,int))}
states=[('neutral',{}),('halfblink',{'Manual_EYE_Close':.5}),('closed',{'Manual_EYE_Close':1}),('angry',{'Manual_ALL_Angry':1}),('surprise',{'Manual_ALL_Surprised':1})]
contacts=[]
for label,state in states:
    for k in ctrl.keys():
        if k.startswith('Manual_') or (len(k)>3 and k[0]=='P' and k[1:3].isdigit()):ctrl[k]=0.
    for k,v in state.items():assert k in ctrl;k0=ctrl[k];ctrl[k]=v
    ctrl.update_tag();bpy.context.view_layer.update();sq,sf=mesh(bpy.data.objects['MIA_V27_SharedHeadBody']);skin=BVHTree.FromPolygons([Vector(v) for v in sq],sf.tolist())
    distances=[];signed=[]
    for name in brow_names:
        q,_=mesh(bpy.data.objects[name])
        for p in q:
            co,no,fi,dist=skin.find_nearest(Vector(p));assert co is not None;distances.append(dist);signed.append(float((Vector(p)-co).dot(no)))
    contacts.append({'case':label,'samples':len(distances),'nearest_max_mm':max(distances)*1000,'signed_min_mm':min(signed)*1000,'signed_max_mm':max(signed)*1000})
    assert min(signed)>0 and max(distances)<.00035,(label,contacts[-1])
for k,v in control_before.items():ctrl[k]=v
ctrl.update_tag();bpy.context.view_layer.update()
after_pose_cache={}
for name,fp in before.items():
    if name not in allowed:assert guard.object_fingerprint(bpy.data.objects[name],after_pose_cache)==fp,('Protected owner changed',name)
assert guard.scene_envelope()==scene
assert patch.apply(V)['already_applied']
assert sha(native)==expected
report={'status':'PASS','baseline_native_sha256':expected,'composition_without_fake_brow_overlay':composition,
        'applied':applied,'original_owners_checked':len(before),'nonowned_owner_fingerprints_exact':len(before)-len(allowed),
        'Main_original_raw_topology_UV_material_indices_POINT_sourceIDs_weights_preserved':True,
        'all_original_material_graphs_exact':True,'brow_original42_keys_UV_weights_drivers_raw_exact':True,
        'actual_reversed_Main_triangles':len(rev),'actual_evaluated_Main_max_move_mm':actual_move_mm,'Main_outside_sparse_field_evaluated_bitexact':True,
        'visibility_scope':'Whole render-visible scene, all mesh owners except the two target brows; only provably pure Transparent material faces excluded. Other alpha routes are conservatively treated as blockers.',
        'real_hair_gap_visibility_before':visibility_before,'real_hair_gap_visibility_after':visibility_after,
        'brow_actual_skin_contact':contacts,'idempotent':True,'native_unchanged':True,'native_saved':False,'GPU_used':False,
        'ART':'UNVERIFIED until actual source-paired hairOFF/ON views'}
(P/('CPU-guard-'+V+'.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print('BROW_FRINGE_CPU_GUARD '+json.dumps({'status':report['status'],'visibility_before':[{k:r[k] for k in ['side','observed_samples','unoccluded']} for r in visibility_before],
      'visibility_after':[{k:r[k] for k in ['side','observed_samples','unoccluded']} for r in visibility_after],'contact':contacts}),flush=True)
