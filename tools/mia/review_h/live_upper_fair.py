"""Select, then perform one local live upper-surface relaxation.

Separate calls allow inspecting the true affected mask before applying. All
accepted head/face, lower surface, breast core and wide arm/waist joins are held.
"""
from pathlib import Path
import heapq
import hashlib
import json
import sys
import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT/'tools/mia/review_h'))


def ah(a): return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def smooth5(t):
    t = np.clip(t, 0., 1.)
    return t*t*t*(10-15*t+6*t*t)


def main():
    body = bpy.data.objects['MIA_Review12_H_LiveRepair']
    ns = bpy.app.driver_namespace
    if body.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
    v = np.array([x.co[:] for x in body.data.vertices], np.float32)
    d = dict(np.load(Path(ns['MIA_Live_H_Payload'])/'geometry.npz'))
    f = d['triangles']; phase = globals().get('MIA_EDIT_PHASE', 'select')
    if phase == 'select':
        protected_head = np.unique(f[d['source_part'] == 1])
        eligible = np.zeros(len(v), bool)
        eligible[np.unique(f[d['source_part'] != 1])] = True
        eligible &= v[:, 2] > 1.34
        eligible[protected_head] = False
        core = (abs(v[:,0]) <= .125)&(v[:,1] <= -.03)&(v[:,2] <= 1.35)
        eligible[core] = False
        edges = np.unique(np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1),axis=0)
        length = np.linalg.norm(v[edges[:,0]].astype(float)-v[edges[:,1]], axis=1)
        boundary_edges = edges[eligible[edges].any(1)&~eligible[edges].all(1)]
        starts = np.unique(boundary_edges[eligible[boundary_edges]])
        graph = [[] for _ in range(len(v))]
        both = eligible[edges].all(1)
        for (a,b),dist in zip(edges[both],length[both]):
            graph[a].append((int(b),float(dist))); graph[b].append((int(a),float(dist)))
        distance = np.full(len(v), np.inf); distance[starts] = 0.
        queue = [(0.,int(i)) for i in starts]; heapq.heapify(queue)
        while queue:
            dist,a = heapq.heappop(queue)
            if dist != distance[a] or dist >= .012: continue
            for b, step in graph[a]:
                value = dist+step
                if value < distance[b]: distance[b] = value; heapq.heappush(queue,(value,b))
        weight = np.zeros(len(v)); weight[eligible] = smooth5(distance[eligible]/.012)
        ns['MIA_Live_UpperFair_Weight'] = weight
        ns['MIA_Live_UpperFair_Before'] = v.copy()
        ns['MIA_Live_UpperFair_Edges'] = edges
        ns['MIA_Live_UpperFair_Head'] = protected_head
        for p in body.data.polygons: p.select = False
        for e in body.data.edges: e.select = False
        for vertex in body.data.vertices: vertex.select = bool(weight[vertex.index] > 0)
        bpy.context.tool_settings.mesh_select_mode = (True,False,False)
        group = body.vertex_groups.get('MIA_Live_UpperFair') or body.vertex_groups.new(name='MIA_Live_UpperFair')
        ids = np.flatnonzero(weight > 0)
        group.add(ids.tolist(), 1., 'REPLACE')
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type != 'VIEW_3D': continue
                space = area.spaces.active
                space.overlay.show_overlays = True
                for attr in ['show_extras','show_relationship_lines','show_bones','show_floor','show_axis_x','show_axis_y']:
                    if hasattr(space.overlay,attr): setattr(space.overlay,attr,False)
        bpy.ops.object.mode_set(mode='EDIT')
        print(json.dumps(dict(phase='SELECT ONLY', vertices=len(ids), protected_head=len(protected_head),
                              lower_and_breast_core_held=True, fade_geodesic_m=.012,
                              world_sha256=ah(v), geometry_changed=False)))
        return
    assert phase == 'apply'
    before = ns['MIA_Live_UpperFair_Before']; assert np.array_equal(v,before)
    weight = ns['MIA_Live_UpperFair_Weight']; edges = ns['MIA_Live_UpperFair_Edges']
    active_edges = edges[(weight[edges] > 0).any(1)]
    length = np.linalg.norm(v[active_edges[:,0]].astype(float)-v[active_edges[:,1]],axis=1)
    influence = 1./np.maximum(length,.00025)**2
    a = np.r_[active_edges[:,0],active_edges[:,1]]; b = np.r_[active_edges[:,1],active_edges[:,0]]
    influence = np.tile(influence,2)
    denom = np.bincount(a,weights=influence,minlength=len(v))
    q = v.astype(float)
    for _ in range(12):
        average = np.column_stack([np.bincount(a,weights=influence*q[b,k],minlength=len(v)) for k in range(3)])
        delta = np.divide(average,denom[:,None],out=q.copy(),where=denom[:,None]>0)-q
        q += .5*weight[:,None]*delta
    q = q.astype(np.float32)
    assert np.array_equal(q[weight==0],before[weight==0])
    assert np.array_equal(q[ns['MIA_Live_UpperFair_Head']],before[ns['MIA_Live_UpperFair_Head']])
    move = np.linalg.norm(q-before,axis=1)
    assert move.max() <= .006, 'Single edit exceeds6mm envelope; inspect instead of applying'
    body.data.vertices.foreach_set('co',q.ravel()); body.data.update(); bpy.context.view_layer.update()
    ns['MIA_Live_UpperFair_After'] = q.copy()
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D': area.spaces.active.overlay.show_overlays=False
    from live_neck_metrics import neck_angles
    report = dict(operation='Live localized mesh-edge relaxation,12passes/factor.5',
                  changed_vertices=int((move>0).sum()), maximum_displacement_m=float(move.max()),
                  selected_vertices=int((weight>0).sum()), boundary_fade_geodesic_m=.012,
                  unchanged_outside_vertices=int((weight==0).sum()), head_coordinates_exact=True,
                  all_coordinates_Zle1_34_exact=np.array_equal(q[before[:,2]<=1.34],before[before[:,2]<=1.34]),
                  before_world_sha256=ah(before),after_world_sha256=ah(q),
                  neck_dihedral_before=neck_angles(before,f),neck_dihedral_after=neck_angles(q,f),
                  native_saved=False, adopted=False)
    (ROOT/'.mia-cache/body-h/live/upper-fair-operation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report))


main()
