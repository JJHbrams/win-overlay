"""Fresh baseline CPU readback; no final garment seating, render or native save."""
from pathlib import Path
import hashlib,json,sys
import bpy,numpy as np

HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
from blender_capture import capture_surface,actual_camera_frame
from surface_seating import surface_guards
ROOT=Path(r'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-fit-v003')
BODY=ROOT/'body'
sys.path.insert(0,str(BODY/'inputs'));import scene_fingerprint as fingerprint
EXPECTED='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(name,value):
    (HERE/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')

native=Path(bpy.data.filepath);assert bpy.app.background and sha(native)==EXPECTED
owner=bpy.data.objects['MIA_V27_SharedHeadBody'];assert bpy.context.scene.frame_current==1
before={o.name:fingerprint.object_fingerprint(o) for o in bpy.data.objects}
envelope=fingerprint.snapshot_scene()['scene']
inventory=lambda:{k:sorted(x.name for x in getattr(bpy.data,k)) for k in ('objects','scenes','cameras','meshes','materials','node_groups')}
before_ids=inventory();surface=capture_surface(owner)
cache_path=BODY/'current-body-limit.npz';cache=np.load(cache_path,allow_pickle=False)
comparisons={k:bool(np.array_equal(surface[k],cache[k])) for k in ('world','triangles','triangle_uv','triangle_materials')}
assert all(comparisons.values()),comparisons
records_path=BODY/'current-source4/render-records.json';records=json.loads(records_path.read_text())
registration_path=BODY/'current-v06-boards.json';board_info=json.loads(registration_path.read_text())
s=board_info['registration']['scale'];dy=board_info['registration']['vertical_translation'];views={}
points=surface['world'][np.linspace(0,len(surface['world'])-1,20,dtype=int)]
for row in records:
    view=row['view'];camera=actual_camera_frame(row,points)
    assert camera['actual_blender_projection_max_error_px']<.001,camera
    board=next(b for b in board_info['boards'] if b['view']==view);center=board['horizontal_reference_center']
    # Conceptual uniform registration, not separately rounded board raster sizes.
    registration={'view':view,'source_sha256':board_info['source_sha256'],'source_size_px':[1536,1024],
        'source_to_render':[[1/s,0,400-center/s],[0,1/s,-dy/s],[0,0,1]],
        'quality':'PROVISIONAL','source_crop_xyxy':[board['reference_crop_x'][0],0,board['reference_crop_x'][1],1024],
        'method':'Inverse of declared common whole-height uniform scale/translation, per-view pelvis-center translation only',
        'scale_render_to_source':s,'vertical_translation_render_to_source':dy,
        'source_center_x':center,'evidence_path':str(registration_path),'evidence_sha256':sha(registration_path),
        'limits':'Actual current camera, provisionally corresponding illustration; source pose/occlusion and true camera uncertainty remain. Not a reviewed final garment registration.'}
    views[view]={'camera':camera,'registration':registration}
assert all(fingerprint.object_fingerprint(bpy.data.objects[n])==v for n,v in before.items())
assert fingerprint.snapshot_scene()['scene']==envelope and inventory()==before_ids
assert sha(native)==EXPECTED
config={'schema_version':1,'surface_cache':str(cache_path),'surface_cache_sha256':sha(cache_path),
        'uv_layer':surface['uv_layer'],'baseline_native_sha256':EXPECTED,'selection_status':'BASELINE_DIAGNOSTIC',
        'surface_guards':surface_guards(surface),'views':views,
        'camera_records_path':str(records_path),'camera_records_sha256':sha(records_path),
        'cast_material_indices':np.unique(surface['triangle_materials']).tolist(),'excluded_material_indices':[],
        'cast_scope':'All triangles of evaluated original skin/body owner, including headblend materials9/10. No guessed material exclusions. Hair/other owners are not included, so complete scene visibility is unverified'}
write('baseline-inputs.json',config)
materials=[]
for index,mat in enumerate(owner.data.materials):
    materials.append({'index':index,'name':mat.name if mat else None,
        'uv_nodes':[{'node':n.name,'uv_map':n.uv_map} for n in mat.node_tree.nodes if n.type=='UVMAP'] if mat and mat.node_tree else []})
proof={'status':'PASS','baseline_native_sha256_before':EXPECTED,'baseline_native_sha256_after':sha(native),
       'actual_evaluated_readback_equal_existing_checkpoint':comparisons,'surface_guards':surface_guards(surface),
       'actual_uv_layers':surface['uv_layers'],'read_only_material_uv_nodes':materials,
       'camera_projection_max_error_px':{v:d['camera']['actual_blender_projection_max_error_px'] for v,d in views.items()},
       'original_owners_exact':len(before),'scene_envelope_exact':True,'original_id_inventory_exact':True,
       'temporary_ids_remaining':[],'render_called':False,'native_save_called':False,
       'target01_or_target02_used':False,'body_garment_art_acceptance':'NOT_EVALUATED'}
write('blender-check.json',proof)
print('UNDERWEAR_FIT_CPU_CAPTURE '+json.dumps(proof),flush=True)
