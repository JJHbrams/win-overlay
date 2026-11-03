"""Live-only root emergence correction on the existing03 outer locks.

Keeps their X/Z, width, profile, long free-hanging geometry and source paths.
Only initial stem Y follows the actual parent exterior with its own thickness;
the broad section must not be chopped by the underlying cape/primary lock.
"""
from pathlib import Path
import hashlib
import json
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path('D:/MiaWorkCache/mia-reference-work/win-overlay')
OUT=ROOT/'.mia-cache/face-live/curved-rear03'
ns=bpy.app.driver_namespace
state=ns['MIA_CurvedRear03Base']
assert 'MIA_RootEmergence03' not in ns
if bpy.context.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
source=bpy.data.objects['MIA_V17_PIXAL_DetailedHair']
assert hashlib.sha256(np.array([v.co[:] for v in source.data.vertices],np.float32).tobytes()).hexdigest()==state['source_raw_sha256']
derived=next(o for o in state['objects'] if o.name.endswith('_RemainingMain'))
deps=bpy.context.evaluated_depsgraph_get();ev=derived.evaluated_get(deps);me=ev.to_mesh(preserve_all_data_layers=True,depsgraph=deps)
target_vertices=[np.array([ev.matrix_world@v.co for v in me.vertices],float)]
me.calc_loop_triangles();target_faces=[np.array([t.vertices[:] for t in me.loop_triangles],np.int32)]
ev.to_mesh_clear()
cfg=json.loads((OUT/'candidate.json').read_text());data=np.load(OUT/'curves.npz')
checkpoint={};reports=[]
for row in cfg['locks']:
    ob=bpy.data.objects['MIA_Hair_CurvedRear03Base_'+row['name']]
    before=np.array([v.co[:] for v in ob.data.vertices],np.float32)
    n=(len(before)-2)//32;assert n*32+2==len(before)
    rings=before[:-2].reshape(n,32,3).astype(float)
    center=data[row['name']+'_guide'].astype(float)
    arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(center,axis=0),axis=1))]
    vertices=np.concatenate(target_vertices);faces=np.concatenate(target_faces)
    tree=BVHTree.FromPolygons([Vector(p) for p in vertices],faces.tolist(),all_triangles=True)
    needed=np.zeros(n);valid=np.zeros(n,bool)
    # Contact includes the actual whole section, not just a point-like root cap.
    for i in np.flatnonzero(arc<=.16):
        values=[]
        for point in rings[i]:
            hit=tree.ray_cast(Vector((float(point[0]),.5,float(point[2]))),Vector((0,-1,0)),1.)
            if hit[0] is not None:values.append(float(hit[0].y)+.00035-float(point[1]))
        if values:needed[i]=max(values);valid[i]=True
    end=None
    for i in np.flatnonzero(arc>=.055):
        if i+3<n and valid[i:i+3].all() and (needed[i:i+3]<=0).all():end=int(i+2);break
    if end is None:end=int(np.flatnonzero(arc<=.16)[-1])
    assert valid[0],('No actual root parent',row['name'])
    bound=np.where(valid[:end+1],needed[:end+1],0.)
    displacement=np.maximum(bound,0.)
    # A constrained standard smooth preserves the actual nonpenetration lower
    # bound. No wave/amplitude or source silhouette coefficients are searched.
    root_value=float(bound[0]);displacement[0]=root_value
    for _ in range(24):
        q=displacement.copy()
        q[1:-1]=(displacement[:-2]+4*displacement[1:-1]+displacement[2:])/6
        displacement=np.maximum(q,bound)
        displacement[0]=root_value
        if bound[-1]<=0:displacement[-1]=0.
    dy=np.zeros(n);dy[:end+1]=displacement
    after=before.copy();after[:-2].reshape(n,32,3)[:,:,1]+=dy[:,None].astype(np.float32)
    after[-2,1]+=np.float32(dy[0]);after[-1,1]+=np.float32(dy[-1])
    assert np.array_equal(after[:,[0,2]],before[:,[0,2]])
    assert np.array_equal(after[(end+1)*32:-2],before[(end+1)*32:-2])
    triangles=np.array([p.vertices[:] for p in ob.data.polygons],np.int32)
    tri=after[triangles].astype(float);norm=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
    area=np.linalg.norm(norm,axis=1);assert (area>1e-13).all()
    volume=float(np.einsum('ij,ij->i',tri[:,0],np.cross(tri[:,1],tri[:,2])).sum()/6)
    assert volume>0
    ob.data.vertices.foreach_set('co',after.ravel());ob.data.update()
    checkpoint[ob.name]=dict(before=before,after=after)
    # Subsequent short/accent roots meet the corrected actual primary exterior.
    offset=len(vertices);target_vertices.append(after.astype(float));target_faces.append(triangles+offset)
    reports.append(dict(name=ob.name,attachment_length_m=float(arc[end]),changed_points=int(np.count_nonzero(np.any(after!=before,axis=1))),
                        max_move_mm=float(np.linalg.norm(after-before,axis=1).max()*1000),
                        root_target_clearance_m=.00035,
                        section_min_bound_margin_m=float(np.min(displacement[valid[:end+1]]-bound[valid[:end+1]])),
                        XZ_and_profile_unchanged=True,free_hanging_points_exact=True,positive_volume_m3=volume))
bpy.context.view_layer.update();ns['MIA_RootEmergence03']=checkpoint
body=bpy.data.objects['MIA_Review12_H_LiveRepair'];body_sha=hashlib.sha256(np.array([v.co[:] for v in body.data.vertices],np.float32).tobytes()).hexdigest()
assert body_sha==ns['MIA_HairReviewState']['body_sha256']
report=dict(operation='Actual parent exterior followed by complete initial section, then free-hanging original geometry',
            locks=reports,body_sha256=body_sha,original_Main_untouched=True,native_saved=False,ART=False,
            collision_limit='Actual parent-directed section nonpenetration only. Arbitrary-view/all-strand intersections are not approved.')
(OUT/'root-emergence-live.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(report))
