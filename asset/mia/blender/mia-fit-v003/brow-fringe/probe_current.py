"""CPU-only fresh R3b brow/fringe ownership and real foreground ray readback."""
from pathlib import Path
import hashlib,json,sys
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE=Path(__file__).resolve().parent
CAN=Path(r'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia')
META=CAN/'blender/mia-fit-v003/brow-visibility-analysis/candidate'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
N=Path(bpy.data.filepath);assert sha(N)=='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'
meta=json.loads((META/'fringe-target-A.json').read_text());d=np.load(META/meta['payload'],allow_pickle=False)
ob=bpy.data.objects[meta['main_owner']];dg=bpy.context.evaluated_depsgraph_get();e=ob.evaluated_get(dg);me=e.to_mesh(preserve_all_data_layers=True,depsgraph=dg)
world=np.asarray([list(e.matrix_world@v.co) for v in me.vertices]);faces=np.asarray([p.vertices[:] for p in me.polygons]);e.to_mesh_clear()
raw=np.asarray([v.co[:] for v in ob.data.vertices],np.float32)
assert len(world)==meta['main_vertices'] and len(faces)==meta['main_faces']
assert hashlib.sha256(raw.tobytes()).hexdigest()==meta['main_raw_co_sha256']
fids=d['main_face_ids'];pids=d['main_point_ids'];comp=d['component_ids'];tree=BVHTree.FromPolygons([Vector(p) for p in world],[faces[int(i)].tolist() for i in fids],all_triangles=True)
specs=json.loads((CAN/'blender/mia-refinement-v002/review/integrated-R3b/source/render-records.json').read_text())
cam=next(r['camera'] for r in specs if r['id']=='front-hairON');mat=np.asarray(cam['matrix']);forward=-mat[:3,2];right=mat[:3,0];up=mat[:3,1];scale=cam['ortho_scale']
def projected(q):
    rel=q-mat[:3,3];return np.column_stack((.5+rel@right/scale,.5-rel@up/scale))*512
hist={};arrays={'fringe_point_ids':pids,'fringe_face_ids':fids,'fringe_faces':faces[fids],'fringe_component_ids':comp,
               'fringe_world':world[pids],'fringe_raw_local':raw[pids]}
global_incidence=np.bincount(faces.ravel(),minlength=len(raw));selected_incidence=np.bincount(faces[fids].ravel(),minlength=len(raw))
arrays['fringe_anchor_point_ids']=pids[global_incidence[pids]!=selected_incidence[pids]]
arrays['fringe_source_polygon_ids']=np.asarray([ob.data.attributes['MIA_SOURCE_POLYGON'].data[int(i)].value for i in fids])
brows=[]
for side in [-1,1]:
    b=bpy.data.objects['V31_SourceBrow_'+str(side)];ev=b.evaluated_get(dg);bm=ev.to_mesh(preserve_all_data_layers=True,depsgraph=dg)
    q=np.asarray([list(ev.matrix_world@v.co) for v in bm.vertices]);uv=np.asarray([u.uv[:] for u in bm.uv_layers['BrowParamUV'].data]);ev.to_mesh_clear()
    arrays['brow_world_'+str(side)]=q;arrays['brow_raw_'+str(side)]=np.asarray([v.co[:] for v in b.data.vertices])
    arrays['brow_keycoords_'+str(side)]=np.asarray([[v.co[:] for v in k.data] for k in b.data.shape_keys.key_blocks])
    hits=[]
    for i,p in enumerate(q.reshape(-1,3,3)[:,1]):
        co,no,fi,dist=tree.ray_cast(Vector(p-forward*.08),Vector(forward),.08)
        if co is not None:
            cid=int(comp[fi]);hist[cid]=hist.get(cid,0)+1
            hits.append({'column':i,'u':i/64,'component':cid,'main_face_id':int(fids[fi]),'foreground_gap_m':float(np.linalg.norm(np.array(co)-p))})
    brows.append({'name':b.name,'keys':[k.name for k in b.data.shape_keys.key_blocks],'raw_count':len(b.data.vertices),
        'modifiers':[{'name':m.name,'type':m.type,'target':getattr(getattr(m,'target',None),'name',None),'offset':getattr(m,'offset',None)} for m in b.modifiers],
        'matrix_world':[list(row) for row in b.matrix_world], 'projected_rows_front512':projected(q).reshape(-1,3,2).tolist(),
        'materials':[m.name if m else None for m in b.data.materials],'hits':hits})
components=[]
for cid in np.unique(comp):
    selected=fids[comp==cid];ids=np.unique(faces[selected]);q=world[ids]
    components.append({'id':int(cid),'faces':len(selected),'points':len(ids),'bounds_world':[q.min(0).tolist(),q.max(0).tolist()],
        'centroid':q.mean(0).tolist(),'front512_bounds':[projected(q).min(0).tolist(),projected(q).max(0).tolist()],
        'brow_center_ray_hits':hist.get(int(cid),0)})
np.savez_compressed(HERE/'current-inputs.npz',**arrays)
report={'native':str(N),'sha256':sha(N),'owner':ob.name,'main_raw_sha256':meta['main_raw_co_sha256'],
        'main_matrix_world':[list(row) for row in ob.matrix_world], 'main_vertices':len(raw),'main_faces':len(faces),
        'main_topology_sha256':hashlib.sha256(faces.astype(np.int32).tobytes()).hexdigest(),
        'main_keys':[k.name for k in ob.data.shape_keys.key_blocks] if ob.data.shape_keys else [],
        'main_modifiers':[{'name':m.name,'type':m.type} for m in ob.modifiers],
        'UV_layers':[u.name for u in ob.data.uv_layers],
        'UV_hashes':{u.name:hashlib.sha256(np.asarray([v.uv[:] for v in u.data],np.float32).tobytes()).hexdigest() for u in ob.data.uv_layers},
        'brow_material_nodes':{b.name:[{'name':n.name,'type':n.type,'color':list(n.inputs['Color'].default_value) if n.type=='EMISSION' else None} for n in b.data.materials[0].node_tree.nodes] for b in [bpy.data.objects['V31_SourceBrow_-1'],bpy.data.objects['V31_SourceBrow_1']]},
        'source_ID_attributes':[a.name for a in ob.data.attributes if 'SOURCE' in a.name.upper()],
        'fringe_selector_payload_sha256':sha(META/meta['payload']),'components':components,'brows':brows,
        'input_npz_sha256':sha(HERE/'current-inputs.npz'),'camera':cam,'native_saved':False,'gpu_used':False,
        'source_supported_windows':meta['source_supported_windows']}
(HERE/'current-inputs.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print('BROW_FRINGE_CPU_INPUTS '+json.dumps({'keys':report['main_keys'],'main_matrix_world':report['main_matrix_world'],
      'ray_hit_components':hist,'brows':[{'name':b['name'],'mods':b['modifiers']} for b in brows]}),flush=True)
