"""One small11 staticnative saved beforeactuals; saved09 fixture, FINAL11 mesh."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True;sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
import bpy
assert sha(bpy.data.filepath)==sha(NATIVE09)=='7bc207b804775b9637858fed8e9faf5d831f6ae034d62da6792522fe1e9c4158'
assert not NATIVE11.exists(),'ONE small11 native; do not overwrite'
assert all(x['exact'] for x in read(P/'protected-physical-triangles.json').values())
cpu=read(P/'CPU-audit.json');assert not cpu['new_nonadjacent_intersections'] and cpu['main_lower_passage_open']
data=np.load(P/'shoulder11-canonical.npz');assert sha(P/'shoulder11-canonical.npz')=='9382e21638e35ce36e3818cc0eb8e060994cc05227a5c56b262dcea7f4b843e9'
obs=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(obs)==1;body=obs[0];old=body.data;gray=old.materials[0]
mesh=bpy.data.meshes.new('Shoulder11_FINAL_STATIC_NoProductionUV');mesh.from_pydata(data['world'].tolist(),[],data['triangles'].tolist());mesh.update();mesh.materials.append(gray)
for poly in mesh.polygons:poly.use_smooth=True
body.data=mesh;bpy.data.meshes.remove(old);body.name='11_STATIC_UPPERBODY_NESTED_FIELD_UNSELECTED'
scope='STATIC HEADLESS UPPERBODY SHOULDER11 HYPOTHESIS. NO production UV, rig, weights, keys, head/lowerbody integration, animation or fullMia ART approval.'
body['REVIEW_SCOPE']=bpy.context.scene['REVIEW_SCOPE']=scope;body['source_NPZ_sha256']=sha(P/'shoulder11-canonical.npz');body['raw_mesher_NPZ_sha256']=sha(P/'shoulder11.npz');body['numerical_restoration_proof_sha256']=sha(P/'roundoff-canonicalization.json')
body['actual_image_provenance']='New11 actuals must freshly open this savedFINAL11 native and saved09 baseline; hashes recorded, no R3bcontext.'
for key in ['shoulder_map_amplitude_m']:
    if key in body:del body[key]
body['nested_trapezius_scale']=.8;body['field_gate_zero_z']=1.3689655172413795;body['field_gate_full_z']=1.395
text=bpy.data.texts.get('00_STATIC_SCOPE_README');text.clear();text.write(scope+'\n\nONE nativeVolumeCube field reconstruction. FINAL includes explicitly authorized4nanometre-roundoff restorations only. Retainedrawproof available.\nPosterior retraction/upturn/normal risks unselected until actualsource4/highlow/Normal review.\n')
assert np.array_equal(np.asarray([v.co[:] for v in mesh.vertices],np.float32),data['world']) and np.array_equal(np.asarray([p.vertices[:] for p in mesh.polygons],np.int32),data['triangles'])
assert len(bpy.data.objects)==14 and np.array_equal(np.array(body.matrix_world),np.eye(4))
NATIVE11.parent.mkdir(exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(NATIVE11),compress=True,check_existing=False)
report=dict(path=str(NATIVE11),sha256=sha(NATIVE11),bytes=NATIVE11.stat().st_size,FINAL_NPZ_sha256=sha(P/'shoulder11-canonical.npz'),raw_NPZ_sha256=sha(P/'shoulder11.npz'),
    source_saved09_native_sha256=sha(NATIVE09),raw_roundoff_proof_sha256=sha(P/'roundoff-canonicalization.json'),objects=14,meshes=1,cameras=10,lights=3,origin0_identity=True,
    saved_before_actual_capture=True,GPU_used=False,scope=scope)
write(P/'native/export-report.json',report);print('SHOULDER11_SAVED_FINAL_BEFORE_ACTUAL',json.dumps(report),flush=True)
