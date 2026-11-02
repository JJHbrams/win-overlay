"""Call after evaluating each proposed pose; flags2mm misses and axis limits."""
import math
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
OWNERS=['V31_SourceBrow_-1','V31_SourceBrow_1'];NAME='Mia.R3.BrowFinalDepthSupport'
def _mesh(ob):
    dg=bpy.context.evaluated_depsgraph_get();ev=ob.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles()
    return ev,me,np.asarray([list(ev.matrix_world@v.co) for v in me.vertices]),np.asarray([t.vertices[:] for t in me.loop_triangles])
def check_current_pose():
    originals={};flags={}
    for name in OWNERS:
        ob=bpy.data.objects[name];m=ob.modifiers[NAME];flags[name]=m.show_viewport;m.show_viewport=False
    try:
        bpy.context.view_layer.update()
        for name in OWNERS:
            ev,me,p,t=_mesh(bpy.data.objects[name]);originals[name]=p;ev.to_mesh_clear()
    finally:
        for name in OWNERS:bpy.data.objects[name].modifiers[NAME].show_viewport=flags[name]
        bpy.context.view_layer.update()
    ev,me,p,t=_mesh(bpy.data.objects['MIA_V27_SharedHeadBody']);bvh=BVHTree.FromPolygons([Vector(q) for q in p],t.tolist(),all_triangles=True)
    rows=[];weights=np.asarray([[i/4,j/4,1-(i+j)/4] for i in range(5) for j in range(5-i)])
    for name in OWNERS:
        ob=bpy.data.objects[name];e,b,pp,tt=_mesh(ob);miss=[];gap=[]
        rig=next(m.object for m in ob.modifiers if m.type=='ARMATURE');pb=rig.pose.bones['J_Bip_C_Head'];outward=((pb.matrix@pb.bone.matrix_local.inverted()).to_3x3()@Vector((0,-1,0))).normalized();axis=(ob.matrix_world.to_3x3()@Vector((0,1,0))).normalized();alignment=abs(axis.dot(outward))
        for vi,q in enumerate(originals[name]):
            hits=[]
            for sign in [-1,1]:
                hit,n,ii,dd=bvh.ray_cast(Vector(q),axis*sign,.002)
                if hit is not None:hits.append((dd,n))
            if not hits:
                hit,n,ii,dd=bvh.find_nearest(Vector(q));signed=(Vector(q)-hit).dot(n)
                miss.append(dict(vertex=vi,signed_gap_mm=signed*1000,nearest_surface_distance_mm=dd*1000,required_contact=signed<.0001))
        for tri in tt:
            for w in weights:
                q=w@pp[tri];hit,n,ii,dd=bvh.find_nearest(Vector(q));gap.append((Vector(q)-hit).dot(n))
        row=dict(owner=name,min_signed_gap_mm=min(gap)*1000,max_signed_gap_mm=max(gap)*1000,negative_samples=sum(x<-1e-6 for x in gap),projection_limit_misses=miss,required_contact_misses=sum(m['required_contact'] for m in miss),projection_axis_alignment=alignment,unsupported_axis_pose=alignment<math.cos(math.radians(25)),support_enabled=flags[name])
        rows.append(row);e.to_mesh_clear()
    ev.to_mesh_clear()
    return dict(owners=rows,mechanical_status='FAIL_OR_OUTSIDE_VALIDATED_AXIS' if any(r['negative_samples'] or r['required_contact_misses'] or r['unsupported_axis_pose'] or not r['support_enabled'] for r in rows) else 'NO_PENETRATION_TESTED_POSE',clear_projection_misses_still_reported=True,scope='Current pose only; not all animation/head angles or source ART acceptance')
