"""ONE fixed intact low-up visibility test; no camera/geometry search."""
from pathlib import Path
import json,hashlib,sys,math
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent;D=P.parent.parent;sys.path.insert(0,str(D));import field
p=json.loads((D/'parameters.json').read_text());data=np.load(D/'sculpt07-D.npz');v=data['world'];tri=data['triangles'];pts=v[tri].mean(1);norm=np.cross(v[tri[:,1]]-v[tri[:,0]],v[tri[:,2]]-v[tri[:,0]]);norm/=np.linalg.norm(norm,axis=1)[:,None];tree=BVHTree.FromPolygons(v.tolist(),tri.tolist(),all_triangles=True)
bpy.ops.wm.read_factory_settings(use_empty=True);cam=bpy.data.objects.new('OneIntactLowUpCamera',bpy.data.cameras.new('OneIntactLowUpCamera'));bpy.context.scene.collection.objects.link(cam);target=Vector((.14,0,1.31));yaw,pitch=90.,-75.;a,e=math.radians(yaw),math.radians(pitch);dist=1.2;cam.location=target+Vector((dist*math.sin(a)*math.cos(e),-dist*math.cos(a)*math.cos(e),dist*math.sin(e)));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=.2;cam.data.clip_start=.1;cam.data.clip_end=10.;bpy.context.view_layer.update();inv=cam.matrix_world.inverted();back=cam.matrix_world.col[2].xyz;right=cam.matrix_world.col[0].xyz;up=cam.matrix_world.col[1].xyz
roi=(pts[:,0]>.125)&(pts[:,0]<.180)&(pts[:,2]>1.235)&(pts[:,2]<1.315)&(norm[:,2]<.2);f,reg=field.make(p);candidate=np.flatnonzero(roi&(((pts[:,1]>-.035)&(pts[:,1]<-.002)&(norm[:,1]>.10))|((pts[:,1]>.002)&(pts[:,1]<.055)&(norm[:,1]<-.10))))
values={name:field.evaluate(expr,pts[candidate]) for name,expr in reg.items()};roles={};all_samples=[]
for role in ['anterior-side','posterior-side']:
    visible=[];total=0
    for j,fi in enumerate(candidate):
        q=pts[fi];match=(q[1]<0) if role=='anterior-side' else(q[1]>0)
        if not match:continue
        owner=min(values,key=lambda k:values[k][j])
        if owner in ['upper_arm_R','shoulder_R']:continue
        total+=1;local=inv@Vector(q)
        if abs(local.x)>.1 or abs(local.y)>.1 or not .1<-local.z<10.:continue
        origin=cam.location+right*local.x+up*local.y;hit,hn,index,distance=tree.ray_cast(origin,-back,4.)
        if hit is not None and (hit-Vector(q)).length<.0001 and Vector(norm[fi]).dot(back)>0:
            visible.append(dict(point=q.tolist(),triangle=int(fi),first_hit_triangle=int(index),first_hit_point=list(hit),normal=norm[fi].tolist(),nearest_construction_field_term=owner,pixel=[320+local.x*3200,320-local.y*3200]))
    xy=np.array([r['pixel'] for r in visible]);span=np.ptp(xy,axis=0).tolist() if len(xy) else[0,0];roles[role]=dict(candidate_nonarm_region_triangles=total,first_hit_visible_triangles=len(visible),visible_pixel_span=span,representative_samples=visible[::max(1,len(visible)//3)][:3]);all_samples+=visible
passed=all(r['first_hit_visible_triangles']>=10 and min(r['visible_pixel_span'])>=4 for r in roles.values())
report=dict(status='CPU BOTH-REGION VISIBILITY READY' if passed else'CPU VISIBILITY NOT PROVED; STOP WITHOUT NEW RENDERS',ready_for_two_renders=passed,one_fixed_candidate_only=True,geometry_unchanged=True,intact_no_material_mask=True,mesh_sha256=hashlib.sha256((D/'sculpt07-D.npz').read_bytes()).hexdigest(),camera=dict(yaw=yaw,pitch=pitch,target=list(target),distance=dist,matrix=[list(r) for r in cam.matrix_world],projection='ORTHO',ortho_scale=cam.data.ortho_scale,clip_start=cam.data.clip_start,clip_end=cam.data.clip_end,resolution=[640,640]),regions=roles,limits='Spatial anterior/posterior cavity-facing triangle regions with oppositeY normals; nearest field term only excludes arm/cap-only samples and is NOT proof of anatomical correctness. First-hit visibility is technical visibility only.')
(P/'visibility-once.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('ONE_LOWUP_CPU',json.dumps(report),flush=True)
