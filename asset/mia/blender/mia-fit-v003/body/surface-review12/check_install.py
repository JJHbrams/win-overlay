from pathlib import Path
import sys,json
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import install_review
proportion='--revision-F' in sys.argv;wide='--revision-E' in sys.argv;revision='--revision-C' in sys.argv;discrete3='--revision-D3' in sys.argv;discrete2='--revision-D2' in sys.argv
suffix='-F' if proportion else '-E' if wide else '-D3' if discrete3 else '-D2' if discrete2 else '-C' if revision else ''
body,proof=install_review.apply(proof_path=P/('installed-source'+suffix+'-proof.json'),geometry_path=P/'proportion-F-lattice/geometry.npz' if proportion else P/'joined-expanded-E.npz' if wide else P/'joined-discrete-D3.npz' if discrete3 else P/'joined-discrete-D2.npz' if discrete2 else P/'joined-geometric-C.npz' if revision else None,packing_path=P/('head-normal-packing'+suffix+'.json'),atlas_path=P/'atlas-E.npz' if wide or proportion else None)
print('REVIEW12_INSTALLED_SOURCE_PASS',json.dumps({k:proof[k] for k in ['status','head_WORLD_corner_normal_vector_error_max','head_WORLD_corner_normal_angle_degrees_max','unchanged_saved_actor_count','head_shader_attributes']}),flush=True)
import bpy,numpy as np
d=np.load(P/'donor.npz');M=np.load('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-fit-v003/body/inputs/mapping-frame1.npz')['matrix_world'][:3,:3]
expected=np.einsum('tci,ij->tcj',d['corner_normals'].astype(float),np.linalg.inv(M));expected/=np.linalg.norm(expected,axis=2)[:,:,None]
control=bpy.data.meshes.new('_Review12_UnchangedTopology_NormalRoundtrip');control.from_pydata(d['world'].tolist(),[],d['triangles'].tolist());control.update()
for p in control.polygons:p.use_smooth=True
control.normals_split_custom_set(expected.reshape(-1,3).tolist());actual=np.asarray([n.vector[:] for n in control.corner_normals],np.float32).reshape(-1,3,3)
head=np.all(d['world'][d['triangles'],2]>=1.469,axis=1);error=np.linalg.norm(actual[head]-expected[head],axis=2);angles=np.degrees(np.arctan2(np.linalg.norm(np.cross(actual[head],expected[head]),axis=2),(actual[head]*expected[head]).sum(2)))
assert angles.max()<.05 and error.max()<8e-4
record=dict(control='Same savedR3b evaluatedgeometry/unchangedtopology, WORLDnormal input→newMesh customnormalAPI→readback; no artisticgeometry or renderer',head_faces=int(head.sum()),max_vector_error=float(error.max()),max_angle_degrees=float(angles.max()),joined_protected_max_angle=json.loads((P/('head-normal-packing'+suffix+'.json')).read_text())['protected_face_max_angle_degrees'],GPU_used=False,native_saved=False)
(P/('head-normal-roundtrip-control'+suffix+'.json')).write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n');print('REVIEW12_NORMAL_ROUNDTRIP_CONTROL',json.dumps(record),flush=True);bpy.data.meshes.remove(control)
