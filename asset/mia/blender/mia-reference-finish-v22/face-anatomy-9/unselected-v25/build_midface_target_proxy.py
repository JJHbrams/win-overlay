"""Create a disposable low-density midface target proxy for A3 design review.

This is not a skin edit.  It makes the desired one-piece carrier surface
inspectable before transfer to the dense face cage.  The proxy starts from WIP8
surface samples and applies a hand-authored displacement table across the
orbital/malar/maxillary strip; there is deliberately no per-pixel source fit.
"""
import bpy, hashlib, json
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
SOURCE=Path(r"C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v22/integration-wip-8-review/Mia_ReferenceFinish_v22.blend")
OUT=HERE/'target-proxy-a3';OUT.mkdir(parents=True,exist_ok=True)
NATIVE=OUT/'Mia_MidfaceCarrierProxy_A3.blend';SKIN='MIA_V14_SculptedSkin'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

bpy.ops.wm.open_mainfile(filepath=str(SOURCE),use_scripts=False)
assert not NATIVE.exists(),'frozen proxy exists'
skin=bpy.data.objects[SKIN]
for key in skin.data.shape_keys.key_blocks:key.value=0
points=np.array([tuple(p.co) for p in skin.data.vertices])
# Rows progress from the distinct mouth/maxilla area through the lower orbit.
# Columns progress from nose-side front cheek to lateral cheek support.  Values
# are metres along anterior +Y and are an explicit shape proposal, not sampled
# from any source drawing.
zs=np.array([1.502,1.508,1.514,1.520,1.526,1.532])
xs=np.array([.018,.028,.038,.048,.058,.068])
dy=np.array([
 [.0004,.0007,.0008,.0005,.0002,.0000],
 [.0010,.0018,.0021,.0018,.0010,.0002],
 [.0015,.0028,.0032,.0026,.0014,.0003],
 [.0008,.0022,.0029,.0015,.0002,-.0006],
 [.0001,.0010,.0014,-.0003,-.0015,-.0010],
 [.0000,.0003,.0005,-.0006,-.0013,-.0008],
])
vertices=[]; samples=[]
for sign in (1.,-1.):
  for zrow,z in enumerate(zs):
    for xcol,xabs in enumerate(xs):
      x=sign*xabs
      # Nearest source vertex in x/z is only a local carrier anchor.  y comes
      # from it, while the table makes the plane design explicit and reviewable.
      dist=(points[:,0]-x)**2+(points[:,2]-z)**2
      index=int(np.argmin(dist)); base=points[index].copy()
      base[0]=x; base[2]=z; base[1]+=dy[zrow,xcol]
      vertices.append(tuple(base));samples.append({'sign':int(sign),'row':zrow,'column':xcol,'anchor_vertex':index,'base_y':float(points[index,1]),'delta_y':float(dy[zrow,xcol]),'target':base.tolist()})
faces=[]; width=len(xs);height=len(zs)
for side in range(2):
  off=side*width*height
  for r in range(height-1):
    for c in range(width-1):
      a=off+r*width+c;faces.extend([(a,a+1,a+width+1),(a,a+width+1,a+width)])
mesh=bpy.data.meshes.new('MIA_A3_MidfaceCarrierProxyMesh');mesh.from_pydata(vertices,[],faces);mesh.update()
proxy=bpy.data.objects.new('MIA_A3_MidfaceCarrierProxy',mesh);bpy.context.scene.collection.objects.link(proxy)
mat=bpy.data.materials.new('MIA_A3_TARGET_PROXY_MATERIAL');mat.diffuse_color=(.18,.75,.70,1);mesh.materials.append(mat)
bpy.ops.wm.save_as_mainfile(filepath=str(NATIVE))
(OUT/'proxy-definition.json').write_text(json.dumps({'status':'TARGET PROXY / NOT A FACE CANDIDATE','baseline':{'path':str(SOURCE),'sha256':sha(SOURCE)},'native':{'path':str(NATIVE),'sha256':sha(NATIVE)},'grid':{'x_abs':xs.tolist(),'z':zs.tolist(),'delta_y':dy.tolist()},'samples':samples,'scope':'Preview of a continuous midface carrier: broaden inner/middle cheek and soften high lateral ridge. It has no UV, weights or shape key claims.'},indent=2),encoding='utf-8')
assert sha(SOURCE)=='ff2b61b2b2146fc4f73119cf10534571609dff75f6333fbec34d0926068b8bb4'
print('MIDFACE_PROXY_DONE',len(vertices),len(faces))
