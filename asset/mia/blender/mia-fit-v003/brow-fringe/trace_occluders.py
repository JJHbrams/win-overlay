"""Read-only CPU whole-Main first-hit trace and complete logical-island cache."""
from pathlib import Path
from collections import Counter
import bpy,numpy as np,json,hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent;cfg=json.loads((P/'candidate-A.json').read_text());old=np.load(P/'current-inputs.npz')
main=bpy.data.objects[cfg['owner']];dg=bpy.context.evaluated_depsgraph_get();ev=main.evaluated_get(dg);me=ev.to_mesh()
q=np.array([list(ev.matrix_world@v.co) for v in me.vertices]);f=np.array([p.vertices[:] for p in me.polygons],np.int32);ev.to_mesh_clear()
tree=BVHTree.FromPolygons([Vector(p) for p in q],f.tolist(),all_triangles=True);camera=np.array(json.loads((P/'current-inputs.json').read_text())['camera']['matrix']);direction=-camera[:3,2]
known=set(map(int,old['fringe_face_ids']));source=np.array([x.value for x in main.data.attributes['MIA_SOURCE_POLYGON'].data],np.int32);hits=[]
for side in [-1,1]:
    ob=bpy.data.objects['V31_SourceBrow_'+str(side)];e=ob.evaluated_get(dg);mesh=e.to_mesh();bq=np.array([list(e.matrix_world@v.co) for v in mesh.vertices]);e.to_mesh_clear();lo,hi=cfg['brow_width_case'][str(side)]['observed_u']
    for col,p in enumerate(bq.reshape(-1,3,3)[:,1]):
        if not(lo<=col/64<=hi):continue
        co,no,fi,distance=tree.ray_cast(Vector(p-direction*.08),Vector(direction),.0795)
        if co is not None:hits.append({'side':side,'column':col,'face':fi,'source_polygon':int(source[fi]),'vertices':f[fi].tolist(),'in_strict_fringe':fi in known,'world':list(co)})
# Complete raw connected components; semantic subsets can cut through a real lock.
parent=np.arange(len(q))
def find(i):
    while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
    return i
for row in f:
    root=find(int(row[0]))
    for i in row[1:]:
        other=find(int(i))
        if root!=other:parent[other]=root
roots=np.array([find(i) for i in range(len(q))]);face_root=roots[f[:,0]];counts=Counter(face_root.tolist());info=[]
for root in sorted({int(face_root[h['face']]) for h in hits}):
    faces=np.flatnonzero(face_root==root);ids=np.unique(f[faces]);v=q[ids]
    info.append({'root':root,'faces':len(faces),'vertices':len(ids),'bounds':[v.min(0).tolist(),v.max(0).tolist()],
                 'strict_Fringe_faces':int(np.isin(faces,old['fringe_face_ids']).sum()),
                 'hits':sum(int(face_root[h['face']])==root for h in hits)})
for h in hits:h['complete_raw_component_root']=int(face_root[h['face']])
locked=np.zeros(len(q),np.float32);group=main.vertex_groups.get('Roots_Locked')
if group:
    for v in main.data.vertices:
        for w in v.groups:
            if w.group==group.index:locked[v.index]=w.weight
np.savez_compressed(P/'main-logical-inputs.npz',world=q,raw=np.array([v.co[:] for v in main.data.vertices],np.float32),faces=f,source_polygon=source,component_root=roots,face_component_root=face_root,root_locked=locked)
report={'hits':hits,'complete_components':info,'nonbone_vertex_groups':[g.name for g in main.vertex_groups if not g.name.startswith('J_')],
        'strict_fringe_hit_count':sum(h['in_strict_fringe'] for h in hits),'whole_Main_hits':len(hits),
        'native_saved':False,'GPU_used':False,'diagnostic_only':True}
(P/'occluder-trace.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print('WHOLE_MAIN_OCCLUDERS '+json.dumps(report),flush=True)
