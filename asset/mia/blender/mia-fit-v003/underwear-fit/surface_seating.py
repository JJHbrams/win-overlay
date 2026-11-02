"""Read-only orthographic surface seating and per-corner barycentric UV transfer.

No Blender, image painting, geometry mutation or nearest-body fallback. Callers
supply the actual evaluated posed surface, its loop-triangle UVs and camera frame.
"""
from __future__ import annotations
import hashlib
import json
import numpy as np


def _hash_array(a, dtype):
    return hashlib.sha256(np.ascontiguousarray(a, dtype=dtype).tobytes()).hexdigest()


def json_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def surface_guards(surface):
    v=np.asarray(surface['world'],dtype=np.float64);t=np.asarray(surface['triangles'],dtype=np.int64)
    uv=np.asarray(surface['triangle_uv'],dtype=np.float64)
    if v.ndim!=2 or v.shape[1]!=3 or t.ndim!=2 or t.shape[1]!=3 or uv.shape!=(len(t),3,2):
        raise ValueError('Expected world[V,3], triangles[T,3], per-corner triangle_uv[T,3,2]')
    if not (np.isfinite(v).all() and np.isfinite(uv).all()) or t.min()<0 or t.max()>=len(v):
        raise ValueError('Nonfinite data or invalid triangle indices')
    return {'geometry_sha256':_hash_array(v,'<f8'),'triangles_sha256':_hash_array(t,'<i8'),
            'triangle_uv_sha256':_hash_array(uv,'<f8'),'vertices':len(v),'triangles':len(t),
            'uv_layer':surface.get('uv_layer','UNSPECIFIED')}


def validate_registration(registration):
    """Require one uniform similarity; reject feature/axis warps."""
    m=np.asarray(registration['source_to_render'],dtype=float)
    if m.shape!=(3,3) or not np.isfinite(m).all() or not np.allclose(m[2],[0,0,1],atol=1e-12):
        raise ValueError('source_to_render must be a finite affine 3x3')
    a=m[:2,:2];g=a.T@a;scale=np.sqrt(np.trace(g)/2)
    if scale<=0 or np.linalg.det(a)<=0 or not np.allclose(g,np.eye(2)*scale**2,rtol=1e-9,atol=1e-12):
        raise ValueError('Only uniform scale, rotation and translation are allowed')
    if not registration.get('source_sha256') or not registration.get('view'):
        raise ValueError('Source hash and corresponding view are required')
    return m


def source_to_render(points, registration):
    m=validate_registration(registration);p=np.asarray(points,dtype=float)
    if p.ndim!=2 or p.shape[1]!=2 or not np.isfinite(p).all():
        raise ValueError('Expected finite original-source points[N,2]')
    return p@m[:2,:2].T+m[:2,2]


def render_to_source(points, registration):
    m=np.linalg.inv(validate_registration(registration));p=np.asarray(points,dtype=float)
    return p@m[:2,:2].T+m[:2,2]


def _camera(camera):
    if camera['projection']!='ORTHO':
        raise ValueError('Only actual recorded ORTHO cameras are implemented')
    m=np.asarray(camera['matrix'],dtype=float);frame=np.asarray(camera['view_frame_local'],dtype=float)
    if m.shape!=(4,4) or frame.shape!=(4,3) or not np.isfinite(m).all() or not np.isfinite(frame).all():
        raise ValueError('Actual camera matrix and Blender view_frame_local[4,3] are required')
    if not np.allclose(m[:3,:3].T@m[:3,:3],np.eye(3),atol=1e-5):
        raise ValueError('Scaled/sheared camera transforms are unsupported')
    width,height=camera['resolution'];xlo,ylo=frame[:,:2].min(0);xhi,yhi=frame[:,:2].max(0)
    if width<=0 or height<=0 or xhi<=xlo or yhi<=ylo:
        raise ValueError('Invalid actual camera frame')
    return m,(xlo,xhi,ylo,yhi),int(width),int(height)


def pixel_rays(camera, render_pixels):
    """Integer pixel coordinates refer to centers; continuous points are allowed."""
    m,(xlo,xhi,ylo,yhi),w,h=_camera(camera);p=np.asarray(render_pixels,dtype=float)
    uv=(p+.5)/np.array([w,h]);local=np.column_stack((xlo+uv[:,0]*(xhi-xlo),yhi-uv[:,1]*(yhi-ylo),np.zeros(len(p))))
    direction=-m[:3,2];direction=direction/np.linalg.norm(direction)
    origins=local@m[:3,:3].T+m[:3,3]+direction*float(camera['clip_start'])
    return origins,np.broadcast_to(direction,origins.shape),float(camera['clip_end'])-float(camera['clip_start'])


def world_to_pixel(camera, points):
    m,(xlo,xhi,ylo,yhi),w,h=_camera(camera);p=np.asarray(points,dtype=float)
    local=(p-m[:3,3])@m[:3,:3]
    return np.column_stack(((local[:,0]-xlo)/(xhi-xlo)*w-.5,(yhi-local[:,1])/(yhi-ylo)*h-.5))


class SurfaceCaster:
    """Triangle ray caster with explicit occluder scope; no nearest-point fallback."""
    def __init__(self, surface, *, cast_triangle_ids):
        self.surface=surface;self.guards=surface_guards(surface)
        self.world=np.asarray(surface['world'],dtype=float);self.triangles=np.asarray(surface['triangles'],dtype=np.int64)
        self.uv=np.asarray(surface['triangle_uv'],dtype=float)
        self.ids=np.asarray(cast_triangle_ids,dtype=np.int64)
        if not len(self.ids) or self.ids.min()<0 or self.ids.max()>=len(self.triangles) or len(np.unique(self.ids))!=len(self.ids):
            raise ValueError('Explicit unique valid cast_triangle_ids required')
        xyz=self.world[self.triangles[self.ids]];self.a=xyz[:,0];self.e1=xyz[:,1]-xyz[:,0];self.e2=xyz[:,2]-xyz[:,0]
        n=np.cross(self.e1,self.e2);self.area2=np.linalg.norm(n,axis=1)
        self.normal=n/np.maximum(self.area2[:,None],1e-300)

    def first_hit(self, origin, direction, max_distance, *, allowed_triangle_ids=None,
                  min_facing_cos=.15, cohit_m=1e-6, uv_seam_tolerance=1e-5):
        """Closest supplied-body hit must be in the requested anatomical region.

        Does not skip a wrong-region foreground hit to reach allowed geometry.
        Does not skip a grazing/back-facing hit. Cohit UV seams are ambiguous.
        """
        origin=np.asarray(origin,float);direction=np.asarray(direction,float)
        pvec=np.cross(direction,self.e2);det=np.einsum('ij,ij->i',self.e1,pvec)
        valid=np.abs(det)>1e-14;inv=np.zeros_like(det);inv[valid]=1/det[valid]
        tv=origin-self.a;u=np.einsum('ij,ij->i',tv,pvec)*inv;q=np.cross(tv,self.e1)
        vv=q@direction*inv;distance=np.einsum('ij,ij->i',self.e2,q)*inv
        valid&=(u>=-1e-9)&(vv>=-1e-9)&(u+vv<=1+1e-9)&(distance>=0)&(distance<=max_distance)
        candidates=np.flatnonzero(valid)
        if not len(candidates):return {'status':'MISSED_RAY','accepted':False}
        nearest=candidates[np.argmin(distance[candidates])];co=candidates[distance[candidates]<=distance[nearest]+cohit_m]
        tid=int(self.ids[nearest]);facing=float(-self.normal[nearest]@direction)
        common={'nearest_triangle_id':tid,'distance_m':float(distance[nearest]),'facing_cos':facing,'cohit_count':len(co)}
        if facing<min_facing_cos:return dict(common,status='GRAZING_OR_BACKFACE',accepted=False)
        if allowed_triangle_ids is None:return dict(common,status='UNVERIFIED_ANATOMICAL_REGION',accepted=False)
        if isinstance(allowed_triangle_ids,np.ndarray) and allowed_triangle_ids.dtype==bool:
            if allowed_triangle_ids.shape!=(len(self.triangles),):raise ValueError('Region mask length mismatch')
            allowed_co=allowed_triangle_ids[self.ids[co]]
        else:
            allowed=allowed_triangle_ids if isinstance(allowed_triangle_ids,set) else set(map(int,allowed_triangle_ids))
            allowed_co=[int(self.ids[i]) in allowed for i in co]
        if not all(allowed_co):
            return dict(common,status='WRONG_REGION_FRONT_HIT',accepted=False)
        bary=np.column_stack((1-u[co]-vv[co],u[co],vv[co]));co_uv=np.einsum('ni,nij->nj',bary,self.uv[self.ids[co]])
        if np.max(np.linalg.norm(co_uv-co_uv[0],axis=1))>uv_seam_tolerance:
            return dict(common,status='UV_SEAM_AMBIGUOUS',accepted=False)
        b=np.array([1-u[nearest]-vv[nearest],u[nearest],vv[nearest]])
        uv=b@self.uv[tid];world=b@self.world[self.triangles[tid]]
        return dict(common,status='SEATED',accepted=True,triangle_id=tid,barycentric=b.tolist(),uv=uv.tolist(),world=world.tolist())


def seat_path(path, surface, camera, registration, *, cast_triangle_ids,
              allowed_triangle_ids=None, purpose='diagnostic', selection_status='UNSELECTED'):
    """Seat supplied source samples; return explicit point and path status.

    Production requires selected geometry and reviewed registration. No map bake
    is implemented here. Hidden paths must remain empty/unseated.
    """
    if purpose not in ('diagnostic','production'):raise ValueError('Unknown purpose')
    if path['view']!=registration['view']:raise ValueError('Source path/camera registration view mismatch')
    if not path.get('source_sha256') or registration.get('source_sha256')!=path['source_sha256']:
        raise ValueError('Source hash mismatch')
    if not path.get('points_px'):
        return {'path_id':path['id'],'status':'UNOBSERVED_NO_PATH','accepted':False,'points':[]}
    if purpose=='production' and (selection_status!='SELECTED_BODY' or registration.get('quality')!='REVIEWED'):
        raise ValueError('Production seating requires selected body and reviewed corresponding camera registration')
    pixels=source_to_render(path['points_px'],registration);o,d,maxdist=pixel_rays(camera,pixels)
    caster=SurfaceCaster(surface,cast_triangle_ids=cast_triangle_ids);w,h=camera['resolution'];points=[]
    x0,y0,x1,y1=registration['source_crop_xyxy']
    for src,p,origin,direction in zip(path['points_px'],pixels,o,d):
        hit=({'status':'OUTSIDE_SOURCE_VIEW','accepted':False} if not(x0<=src[0]<x1 and y0<=src[1]<y1) else
             {'status':'OUTSIDE_RENDER_FRAME','accepted':False} if not(-.5<=p[0]<w-.5 and -.5<=p[1]<h-.5)
             else caster.first_hit(origin,direction,maxdist,allowed_triangle_ids=allowed_triangle_ids))
        hit['source_px']=list(src);hit['render_px']=p.tolist();points.append(hit)
    geometric_complete=all(p['status']=='SEATED' for p in points)
    production_ready=geometric_complete and selection_status=='SELECTED_BODY' and registration.get('quality')=='REVIEWED'
    return {'path_id':path['id'],'purpose':purpose,'status':('SEATED' if production_ready else 'DIAGNOSTIC_ONLY'),
            'accepted':production_ready,'geometric_samples_complete':geometric_complete,'points':points,
            'surface_guards':caster.guards,'camera_sha256':json_hash(camera),'registration_sha256':json_hash(registration),
            'source_confidence':path.get('confidence'),'observed_limits':path.get('observed_limits'),
            'limitations':['Only supplied body occluders were tested; scene hair/cloth visibility remains a separate check.',
                           'Sample hits alone do not establish curve interpolation, complete pattern coverage or garment ART.']}


def transfer_barycentric(hit, source_guards, surface, *, allow_geometry_change=False):
    """Reconstruct one already-seated sample on exact triangle/corner UV identity."""
    if hit.get('status')!='SEATED':raise ValueError('Only an actual seated geometric sample can transfer')
    now=surface_guards(surface)
    for key in ('triangles_sha256','triangle_uv_sha256','uv_layer'):
        if now[key]!=source_guards[key]:raise ValueError('Topology/UV correspondence changed: '+key)
    if not allow_geometry_change and now['geometry_sha256']!=source_guards['geometry_sha256']:
        raise ValueError('Body shape changed; recompute source seating on the selected surface')
    b=np.asarray(hit['barycentric'],float);tid=int(hit['triangle_id'])
    if b.shape!=(3,) or abs(b.sum()-1)>1e-8 or b.min()<-1e-8:raise ValueError('Invalid barycentric weights')
    t=np.asarray(surface['triangles'])[tid]
    return {'world':(b@np.asarray(surface['world'])[t]).tolist(),
            'uv':(b@np.asarray(surface['triangle_uv'])[tid]).tolist(),'triangle_id':tid,'barycentric':b.tolist()}
