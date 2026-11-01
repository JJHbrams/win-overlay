"""WIP8-based primary-form trial: soften a high malar ridge and widen its bridge.

The source is the actual integrated WIP8, not a face-only producer file.  The
delta is applied to every relative key of the skin owner so expressions retain
their pre-existing deformation relative to the carrier surface.
"""
import bpy
import hashlib
import json
from collections import Counter
from pathlib import Path
from mathutils import Vector
import numpy as np

HERE=Path(__file__).resolve().parent
SOURCE=Path(r"C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v22/integration-wip-8-review/Mia_ReferenceFinish_v22.blend")
OUT=HERE/'candidate-a2'; OUT.mkdir(parents=True,exist_ok=True)
NATIVE=OUT/'Mia_ReferenceFinish_WIP8_AnatomyA2.blend'
SKIN='MIA_V14_SculptedSkin'
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def bell(x,centre,width): return np.exp(-((x-centre)/width)**2)
def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1); return t*t*(3-2*t)

bpy.ops.wm.open_mainfile(filepath=str(SOURCE),use_scripts=False)
assert not NATIVE.exists(),'frozen candidate already exists'
skin=bpy.data.objects[SKIN]
for key in skin.data.shape_keys.key_blocks:key.value=0
bpy.context.view_layer.update()
mesh=skin.data
points=np.array([tuple(point.co) for point in mesh.shape_keys.key_blocks[0].data])
faces=[list(poly.vertices) for poly in mesh.polygons]
edges=Counter(tuple(sorted((face[i],face[(i+1)%len(face)]))) for face in faces for i in range(len(face)))
boundary={index for edge,count in edges.items() if count==1 for index in edge}
normals=np.zeros_like(points)
for poly in mesh.polygons:
    for index in poly.vertices: normals[index]+=np.array(poly.normal)
normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-12)
eye_boundary={index for index in boundary if .010<abs(points[index,0])<.072 and points[index,1]>.020 and 1.520<points[index,2]<1.560}
mouth_boundary={index for index in boundary if abs(points[index,0])<.065 and points[index,1]>.010 and 1.480<points[index,2]<1.515}

# Three coupled *surface roles*, not depth sections:  high malar support is
# softened, maxillary/front cheek expands into it, then the lateral cheek fades
# into the F2 lower-cheek carrier.  The structures have wide overlapping masks
# so there is no thin artificial trough or spherical cheek lobe.
delta=np.zeros_like(points); selected=[]
for index,(x,y,z) in enumerate(points):
    ax=abs(x)
    if index in eye_boundary or index in mouth_boundary or index in boundary:
        continue
    if not (.016<ax<.072 and .002<y<.085 and 1.500<z<1.542):
        continue
    anterior=smooth(.002,.020,y)
    under_orbit=bell(ax,.036,.020)*bell(z,1.521,.018)
    malar=bell(ax,.048,.016)*bell(z,1.528,.012)
    maxilla=bell(ax,.028,.014)*bell(z,1.515,.016)
    lateral=bell(ax,.058,.015)*bell(z,1.516,.019)
    lower_join=bell(ax,.040,.023)*bell(z,1.507,.015)
    # The old high point retreats slightly; broad neighbouring planes advance.
    dy=anterior*(-.00165*malar + .00300*maxilla + .00170*lateral + .00070*lower_join)
    dx=np.sign(x)*anterior*(.00024*lateral + .00010*malar - .00008*maxilla)
    dz=anterior*(-.00022*malar + .00017*maxilla - .00010*lateral)
    # Fade all roles together at the component boundary, rather than clipping
    # a hard elliptical patch into the lower face.
    edge=smooth(.016,.023,ax)*(1-smooth(.064,.072,ax))*smooth(1.500,1.506,z)*(1-smooth(1.535,1.542,z))
    delta[index]=[dx*edge,dy*edge,dz*edge]
    if np.linalg.norm(delta[index])>1e-9:
        selected.append({'id':int(index),'position':points[index].tolist(),'normal':normals[index].tolist(),'delta':delta[index].tolist(), 'roles':{'under_orbit':float(under_orbit),'malar':float(malar),'maxilla':float(maxilla),'lateral':float(lateral),'lower_join':float(lower_join)}})

baseline_keys={key.name:np.array([tuple(point.co) for point in key.data]) for key in mesh.shape_keys.key_blocks}
non_skin={}
for obj in bpy.data.objects:
    if obj.type=='MESH' and obj.name!=SKIN:
        non_skin[obj.name]={'coords':np.array([tuple(v.co) for v in obj.data.vertices]),'materials':[slot.material.name if slot.material else None for slot in obj.material_slots], 'uv':[np.array([tuple(loop.uv) for loop in layer.data]) for layer in obj.data.uv_layers]}
for key in mesh.shape_keys.key_blocks:
    for index in np.where(np.linalg.norm(delta,axis=1)>1e-10)[0]: key.data[int(index)].co+=Vector(delta[int(index)].tolist())
bpy.context.view_layer.update()
errors=[]
for key in mesh.shape_keys.key_blocks:
    now=np.array([tuple(point.co) for point in key.data])
    if not np.allclose(now,baseline_keys[key.name]+delta,atol=1e-10):errors.append('relative_key_delta:'+key.name)
for name,old in non_skin.items():
    obj=bpy.data.objects[name]
    now=np.array([tuple(v.co) for v in obj.data.vertices])
    uvs=[np.array([tuple(loop.uv) for loop in layer.data]) for layer in obj.data.uv_layers]
    materials=[slot.material.name if slot.material else None for slot in obj.material_slots]
    if not np.array_equal(now,old['coords']):errors.append('non_skin_coords:'+name)
    if materials!=old['materials'] or len(uvs)!=len(old['uv']) or any(not np.array_equal(a,b) for a,b in zip(uvs,old['uv'])):errors.append('non_skin_surface:'+name)
assert not errors,errors
bpy.ops.wm.save_as_mainfile(filepath=str(NATIVE))
report={'status':'WORKING CANDIDATE / ART UNAPPROVED','baseline':{'path':str(SOURCE),'sha256':sha(SOURCE)},'native':{'path':str(NATIVE),'sha256':sha(NATIVE)},'coordinate_space':'Basis local; +Y anterior; bounds and protection evaluated against actual WIP8 source','method':'Coupled broad maxilla/lateral cheek advance with slight high-malar retreat. No global smoothing or image fit.','changed_vertices':len(selected),'max_delta_m':float(np.linalg.norm(delta,axis=1).max()),'protected':{'eye_boundary_count':len(eye_boundary),'mouth_boundary_count':len(mouth_boundary),'all_boundary_count':len(boundary)},'guards':{'non_skin_uv_and_coordinates_exact':True,'skin_relative_keys_replayed':True,'errors':errors},'limits':['No art acceptance. Actual lower eyelid contact is only boundary-protected; inner rings remain tested but need deformation review.','No source-art dimension was treated as a numerical anatomy target.']}
(OUT/'manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
(OUT/'vertex-deltas.json').write_text(json.dumps(selected,indent=2),encoding='utf-8')
print('WIP8_ANATOMY_A2_DONE',len(selected),float(np.linalg.norm(delta,axis=1).max()),len(eye_boundary),len(mouth_boundary))
