"""Read-only evaluated-surface inspection of the actual integrated WIP8 head.

This is intentionally separate from candidate A1.  It reports whether legacy
protected vertices are aperture, malar or another region before any new edit.
"""
import bpy
import hashlib
import json
from collections import Counter, deque
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
SOURCE = Path(r"C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v22/integration-wip-8-review/Mia_ReferenceFinish_v22.blend")
OUT = HERE / "diagnosis-wip8"
OUT.mkdir(parents=True, exist_ok=True)
SKIN = "MIA_V14_SculptedSkin"
LEGACY = [236,242,247,248,249,250,251,252,253]
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

bpy.ops.wm.open_mainfile(filepath=str(SOURCE), use_scripts=False)
skin = bpy.data.objects[SKIN]
for key in skin.data.shape_keys.key_blocks: key.value = 0.0
bpy.context.view_layer.update()
deps = bpy.context.evaluated_depsgraph_get()
evaluated = skin.evaluated_get(deps)
mesh = evaluated.to_mesh()
points = np.array([tuple(vertex.co) for vertex in mesh.vertices])
polygons = [list(poly.vertices) for poly in mesh.polygons]
edges = Counter(tuple(sorted((face[i],face[(i+1)%len(face)]))) for face in polygons for i in range(len(face)))
neighbors = {i:set() for i in range(len(points))}
for a,b in edges:
    neighbors[a].add(b); neighbors[b].add(a)
boundary = {i for edge,count in edges.items() if count==1 for i in edge}
basis_points = np.array([tuple(point.co) for point in skin.data.shape_keys.key_blocks[0].data])
basis_faces = [list(poly.vertices) for poly in skin.data.polygons]
basis_edges = Counter(tuple(sorted((face[i], face[(i + 1) % len(face)]))) for face in basis_faces for i in range(len(face)))
basis_neighbors = {i:set() for i in range(len(basis_points))}
for a,b in basis_edges:
    basis_neighbors[a].add(b); basis_neighbors[b].add(a)
basis_boundary = {i for edge,count in basis_edges.items() if count==1 for i in edge}
basis_normals = np.array([tuple(vertex.normal) for vertex in skin.data.vertices])

def rings(seed, depth=2):
    found={seed}; frontier={seed}; result=[]
    for _ in range(depth):
        nxt=set().union(*(neighbors[index] for index in frontier))-found
        result.append(sorted(nxt)); found|=nxt; frontier=nxt
    return result

records=[]
for index in LEGACY:
    if index >= len(basis_points):
        records.append({'id':index,'exists':False}); continue
    # These are control-cage IDs.  Do not reuse their integers against the
    # subdivided evaluated mesh: that mapping is not proven by index order.
    found={index}; frontier={index}; r=[]
    for _ in range(2):
        nxt=set().union(*(basis_neighbors[i] for i in frontier))-found
        r.append(sorted(nxt)); found|=nxt; frontier=nxt
    records.append({
        'id':index,'exists':True,'basis_coordinate':basis_points[index].tolist(),
        'basis_normal':basis_normals[index].tolist(),'basis_is_boundary':index in basis_boundary,
        'basis_ring1':r[0],'basis_ring2':r[1],
        'basis_ring1_centroid':basis_points[r[0]].mean(axis=0).tolist() if r[0] else None,
        'basis_ring1_normal_mean':basis_normals[r[0]].mean(axis=0).tolist() if r[0] else None,
    })
eval_hash=hashlib.sha256(points.tobytes()).hexdigest()
report={
  'baseline':{'path':str(SOURCE),'sha256':sha(SOURCE)}, 'owner':SKIN,
  'coordinate_space':'Both meshes neutral local; +Y is anterior from existing face recipes. Basis IDs are never asserted to equal evaluated IDs.',
  'topology':{'evaluated_vertices':len(points),'evaluated_polygons':len(polygons),'evaluated_boundary_vertices':len(boundary),'basis_vertices':len(basis_points),'basis_polygons':len(basis_faces),'basis_boundary_vertices':len(basis_boundary)},
  'legacy_ids':records,
  'region_query':{'x_abs':[.018,.071],'y_min':-.006,'z':[1.503,1.545], 'vertex_count':int(np.sum((np.abs(points[:,0])>.018)&(np.abs(points[:,0])<.071)&(points[:,1]>-.006)&(points[:,2]>1.503)&(points[:,2]<1.545)))},
  'evaluated_position_sha256':eval_hash,
  'note':'This diagnostic does not infer facial anatomy from IDs. Legacy IDs are now reported only in Basis/cage topology. Candidate edits are blocked until these coordinates/neighbor rings and actual clay images are reviewed.'
}
(OUT/'surface-diagnosis.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
evaluated.to_mesh_clear()
assert sha(SOURCE)=='ff2b61b2b2146fc4f73119cf10534571609dff75f6333fbec34d0926068b8bb4'
print('WIP8_SURFACE_DIAGNOSED',json.dumps({'verts':len(points),'boundary':len(boundary),'region':report['region_query']['vertex_count']}))
