"""Open saved small09, swap same-triangle coordinates, save ONE small10."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
import bpy

assert sha(bpy.data.filepath)==sha(NATIVE09)=='7bc207b804775b9637858fed8e9faf5d831f6ae034d62da6792522fe1e9c4158'
assert not NATIVE10.exists(), 'ONE saved candidate; do not overwrite.'
audit=read(P/'CPU-audit.json');assert audit['status'].startswith('CPU technical guards PASS')
data=np.load(P/'shoulder10.npz');before=np.load(BASE/'posterior09.npz')
meshes=[o for o in bpy.data.objects if o.type=='MESH'];assert len(meshes)==1
ob=meshes[0];raw=np.asarray([v.co[:] for v in ob.data.vertices],np.float32);faces=np.asarray([p.vertices[:] for p in ob.data.polygons],np.int32)
assert np.array_equal(raw,before['world']) and np.array_equal(faces,data['triangles'])
assert np.array_equal(np.array(ob.matrix_world),np.eye(4))
ob.data.vertices.foreach_set('co',data['world'].ravel());ob.data.update();bpy.context.view_layer.update()
ob.name='10_STATIC_SHOULDER_UPPERBODY_SHAPE_GUIDE_ONLY';ob.data.name='Shoulder10_STATIC_NoProductionUV'
scope='STATIC UPPERBODY SHOULDER10 DESIGN HYPOTHESIS. NO production UV, rig, weights, facial keys, head/lowerbody integration, animation or whole-body ART approval.'
bpy.context.scene['REVIEW_SCOPE']=ob['REVIEW_SCOPE']=scope
ob['source_NPZ_sha256']=sha(P/'shoulder10.npz');ob['baseline_native_sha256']=sha(NATIVE09);ob['shoulder_map_amplitude_m']=.032
ob['actual_image_provenance']='New shoulder10 paired images must reopen saved09/saved10, with actual native hashes recorded. Old09 actuals are separate frozen provenance.'
text=bpy.data.texts.get('00_STATIC_SCOPE_README');text.clear();text.write(scope+'\n\nOne Z-only map of09, no production migration. World coordinates/origin0 held.\n')
assert len(bpy.data.objects)==14 and not ob.data.uv_layers and not ob.modifiers
assert np.array_equal(np.asarray([v.co[:] for v in ob.data.vertices],np.float32),data['world'])
NATIVE10.parent.mkdir(exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(NATIVE10),compress=True,check_existing=False)
assert sha(NATIVE09)=='7bc207b804775b9637858fed8e9faf5d831f6ae034d62da6792522fe1e9c4158' and NATIVE10.stat().st_size<15_000_000
report=dict(path=str(NATIVE10),sha256=sha(NATIVE10),bytes=NATIVE10.stat().st_size,NPZ_sha256=sha(P/'shoulder10.npz'),baseline_native=dict(path=str(NATIVE09),sha256=sha(NATIVE09)),
    objects=14,meshes=1,cameras=10,lights=3,world_identity_origin0=True,same_triangle_array=True,scope=scope,
    inherited_gray_world_lights_cameras='Unchanged from saved09; actual capture will verify exact shared semantic state.',GPU_used=False,native_saved_before_actual_capture=True)
write(P/'native/export-report.json',report);print('SHOULDER10_SAVED_BEFORE_ACTUAL',json.dumps(report),flush=True)
