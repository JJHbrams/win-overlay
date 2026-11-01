"""Corrected, transform-aware target proxy for reviewing the midface carrier.

It samples the evaluated local front sheet with +Y-to--Y rays, then copies the
skin world matrix.  It is explicitly a quadrilateral design proxy, never a
candidate skin or a substitute for source-art verification.
"""
import bpy, hashlib, json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import numpy as np

HERE=Path(__file__).resolve().parent
SOURCE=Path(r"C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v22/integration-wip-8-review/Mia_ReferenceFinish_v22.blend")
OUT=HERE/'target-proxy-a3b';OUT.mkdir(parents=True,exist_ok=True)
NATIVE=OUT/'Mia_MidfaceCarrierProxy_A3b.blend';SKIN='MIA_V14_SculptedSkin'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

bpy.ops.wm.open_mainfile(filepath=str(SOURCE),use_scripts=False);assert not NATIVE.exists(),'frozen proxy exists'
skin=bpy.data.objects[SKIN]
for key in skin.data.shape_keys.key_blocks:key.value=0
bpy.context.view_layer.update();dep=bpy.context.evaluated_depsgraph_get();ev=skin.evaluated_get(dep);m=ev.to_mesh()
verts=[Vector(v.co) for v in m.vertices];faces=[list(p.vertices) for p in m.polygons];bvh=BVHTree.FromPolygons(verts,faces)
# The lower/lateral grid cells at z=1.502/1.508 have no continuous front-sheet
# hit on this actual mesh.  Do not bridge that gap with invented proxy faces.
zs=np.array([1.514,1.520,1.526,1.532]);xs=np.array([.018,.028,.038,.048,.058,.068])
dy=np.array([[.0015,.0028,.0032,.0026,.0014,.0003],[.0008,.0022,.0029,.0015,.0002,-.0006],[.0001,.001,.0014,-.0003,-.0015,-.001],[0,.0003,.0005,-.0006,-.0013,-.0008]])
vertices=[];samples=[]
for sign in (1.,-1.):
 for row,z in enumerate(zs):
  for col,xabs in enumerate(xs):
   x=sign*xabs; hit,normal,face_index,distance=bvh.ray_cast(Vector((x,.20,z)),Vector((0,-1,0)),.30)
   assert hit is not None,(sign,row,col)
   target=Vector((x,hit.y+float(dy[row,col]),z));vertices.append(tuple(target));samples.append({'side':int(sign),'row':row,'column':col,'source_hit_local':list(hit),'source_normal_local':list(normal),'face':int(face_index),'delta_y':float(dy[row,col]),'target_local':list(target)})
width=len(xs);height=len(zs);quads=[]
for side in range(2):
 off=side*width*height
 for row in range(height-1):
  for col in range(width-1):
   a=off+row*width+col;quads.append((a,a+1,a+width+1,a+width))
mesh=bpy.data.meshes.new('MIA_A3b_MidfaceCarrierProxyMesh');mesh.from_pydata(vertices,[],quads);mesh.update()
proxy=bpy.data.objects.new('MIA_A3b_MidfaceCarrierProxy',mesh);bpy.context.scene.collection.objects.link(proxy);proxy.matrix_world=skin.matrix_world.copy()
mat=bpy.data.materials.new('MIA_A3b_TARGET_PROXY_MATERIAL');mat.diffuse_color=(.18,.75,.70,1);mesh.materials.append(mat)
bpy.ops.wm.save_as_mainfile(filepath=str(NATIVE));ev.to_mesh_clear()
(OUT/'proxy-definition.json').write_text(json.dumps({'status':'TARGET PROXY / NOT A FACE CANDIDATE','baseline':{'path':str(SOURCE),'sha256':sha(SOURCE)},'native':{'path':str(NATIVE),'sha256':sha(NATIVE)},'local_front_sampling':'+Y origin ray toward -Y on evaluated neutral skin, with each hit recorded','skin_matrix_world':[list(row) for row in skin.matrix_world],'grid':{'x_abs':xs.tolist(),'z':zs.tolist(),'delta_y':dy.tolist(),'faces':'quads'},'samples':samples,'limits':'No UV, weights, topology transfer or art approval. This only makes a proposed connected carrier surface inspectable.'},indent=2),encoding='utf-8')
assert sha(SOURCE)=='ff2b61b2b2146fc4f73119cf10534571609dff75f6333fbec34d0926068b8bb4'
print('MIDFACE_PROXY_A3B_DONE',len(vertices),len(quads))
