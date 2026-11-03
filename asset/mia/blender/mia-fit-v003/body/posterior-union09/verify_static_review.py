"""Fresh background reopen; no render/save/edit of the small review file."""
from pathlib import Path
import json,hashlib
import bpy,numpy as np
P=Path(__file__).resolve().parent;data=np.load(P/'posterior09.npz');report=json.loads((P/'native/export-report.json').read_text(encoding='utf-8'));native=Path(bpy.data.filepath);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert sha(native)==report['sha256']
meshes=[o for o in bpy.data.objects if o.type=='MESH'];assert len(meshes)==1;ob=meshes[0];me=ob.data
raw=np.asarray([v.co[:] for v in me.vertices],np.float32);world=np.asarray([ob.matrix_world@v.co for v in me.vertices],np.float32);faces=np.asarray([p.vertices[:] for p in me.polygons],np.int32)
assert np.array_equal(raw,data['world']) and np.array_equal(world,data['world']) and np.array_equal(faces,data['triangles'])
assert np.array_equal(np.array(ob.matrix_world),np.eye(4)) and not me.shape_keys and not me.uv_layers and not ob.vertex_groups and not ob.modifiers
assert not bpy.data.armatures and not bpy.data.actions and not any(im.source=='FILE' for im in bpy.data.images)
cams=[o for o in bpy.data.objects if o.type=='CAMERA'];lights=[o for o in bpy.data.objects if o.type=='LIGHT'];assert len(cams)==10 and len(lights)==3 and len(bpy.data.objects)==14
for cam in cams:assert cam.data.type=='ORTHO' and abs(cam.data.clip_start-.1)<1e-7 and cam.data.clip_end==10
material=me.materials[0];bs=next(n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED');out=material.node_tree.get_output_node('EEVEE');assert out and out.inputs['Surface'].links[0].from_node==bs
assert np.allclose(bs.inputs['Base Color'].default_value,(.23,.23,.23,1),rtol=0,atol=1e-7) and abs(bs.inputs['Roughness'].default_value-.85)<1e-7
spaces=[]
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            s=area.spaces.active;assert abs(s.clip_start-.1)<1e-7 and s.clip_end==10;assert np.linalg.norm(np.array(s.region_3d.view_location)-(0,-.015,1.285))<1e-6;spaces.append(dict(center=list(s.region_3d.view_location),clip=[s.clip_start,s.clip_end],mode=s.region_3d.view_perspective))
assert spaces and 'NO production UV' in bpy.context.scene['REVIEW_SCOPE'] and sha(native)==report['sha256']
proof=dict(status='PASS fresh CPU reopen of STATIC GUIDE ONLY',path=str(native),sha256=sha(native),bytes=native.stat().st_size,raw_world_triangle_arrays_bitexact_to_NPZ=True,raw_f32_sha256=hashlib.sha256(raw.tobytes()).hexdigest(),world_f32_sha256=hashlib.sha256(world.tobytes()).hexdigest(),triangles_i32_sha256=hashlib.sha256(faces.tobytes()).hexdigest(),objects=14,cameras=10,lights=3,origin0_matrix_identity=True,no_UV_weights_rig_keys_actions=True,actual_gray_output_constants_verified=True,stored_viewports=spaces,GPU_used=False,native_saved_by_verifier=False,scope=bpy.context.scene['REVIEW_SCOPE'])
(P/'native/fresh-reopen.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n');print('POSTERIOR09_STATIC_FRESH_REOPEN_PASS',json.dumps({k:proof[k] for k in ['sha256','bytes','raw_world_triangle_arrays_bitexact_to_NPZ','objects','cameras','lights']}),flush=True)
