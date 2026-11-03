"""Fresh reopen: saved10 coordinates, triangles and static scene scope. CPU."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
import bpy
data=np.load(P/'shoulder11-canonical.npz');report=read(P/'native/export-report.json')
assert sha(bpy.data.filepath)==report['sha256'];meshes=[o for o in bpy.data.objects if o.type=='MESH'];assert len(meshes)==1
ob=meshes[0];raw=np.asarray([v.co[:] for v in ob.data.vertices],np.float32);world=np.asarray([ob.matrix_world@v.co for v in ob.data.vertices],np.float32);f=np.asarray([p.vertices[:] for p in ob.data.polygons],np.int32)
assert np.array_equal(raw,data['world']) and np.array_equal(world,data['world']) and np.array_equal(f,data['triangles'])
assert np.array_equal(np.array(ob.matrix_world),np.eye(4)) and not ob.data.shape_keys and not ob.data.uv_layers and not ob.modifiers and not ob.vertex_groups
assert len(bpy.data.objects)==14 and len(bpy.data.cameras)==10 and len(bpy.data.lights)==3 and not bpy.data.armatures and not bpy.data.actions
for cam in bpy.data.cameras:assert cam.type=='ORTHO' and abs(cam.clip_start-.1)<1e-7 and cam.clip_end==10
mat=ob.data.materials[0];bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');out=mat.node_tree.get_output_node('EEVEE');assert out.inputs['Surface'].links[0].from_node==bs
assert np.allclose(bs.inputs['Base Color'].default_value,(.23,.23,.23,1),atol=1e-7,rtol=0) and abs(bs.inputs['Roughness'].default_value-.85)<1e-7
spaces=[]
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            s=area.spaces.active;assert abs(s.clip_start-.1)<1e-7 and s.clip_end==10 and s.region_3d.view_perspective=='ORTHO'
            assert np.linalg.norm(np.array(s.region_3d.view_location)-(0,-.015,1.285))<1e-6
            spaces.append(dict(center=list(s.region_3d.view_location),mode=s.region_3d.view_perspective,clip=[s.clip_start,s.clip_end]))
assert spaces and 'NO production UV' in bpy.context.scene['REVIEW_SCOPE']
for path,h in read(P/'protected-input-hashes.json').items():assert sha(path)==h,path
proof=dict(status='PASS fresh CPU reopen STATIC GUIDE ONLY',path=str(Path(bpy.data.filepath)),sha256=sha(bpy.data.filepath),bytes=Path(bpy.data.filepath).stat().st_size,
    raw_world_triangles_bitexact_to_NPZ=True,vertices=len(raw),triangles=len(f),origin0_identity=True,objects=14,cameras=10,lights=3,
    no_production_UV_weights_rig_keys_actions=True,gray_output_verified=True,stored_viewports=spaces,native_saved_by_verifier=False,GPU_used=False,
    raw_world_f32_sha256=hashlib.sha256(raw.tobytes()).hexdigest(),triangles_i32_sha256=hashlib.sha256(f.tobytes()).hexdigest())
write(P/'native/fresh-reopen.json',proof);print('SHOULDER11_FRESH_REOPEN_PASS',json.dumps(proof),flush=True)
