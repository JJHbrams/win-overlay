"""Actual baseline ray/UV checks and intentional failure controls. No map bake."""
from pathlib import Path
from collections import Counter
import hashlib,json
import numpy as np
from surface_seating import (SurfaceCaster,surface_guards,pixel_rays,world_to_pixel,
                            render_to_source,source_to_render,validate_registration,
                            transfer_barycentric,seat_path)
HERE=Path(__file__).resolve().parent
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
config=read(HERE/'baseline-inputs.json');assert sha(config['surface_cache'])==config['surface_cache_sha256']
cache=np.load(config['surface_cache'],allow_pickle=False)
surface={k:cache[k] for k in ('world','triangles','triangle_uv','triangle_materials')};surface['uv_layer']=config['uv_layer']
guards=surface_guards(surface);assert guards==config['surface_guards']
cast=np.flatnonzero(np.isin(surface['triangle_materials'],config['cast_material_indices']))
allowed=surface['triangle_materials']==1;caster=SurfaceCaster(surface,cast_triangle_ids=cast)
xyz=surface['world'][surface['triangles']];normal=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]);normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-300)
source_path=HERE.parent/'underwear-source/source-paths.json';source_pack=read(source_path)
positive=[];negative={};diagnostics={};max_world=0.;max_uv=0.;max_pixel=0.
for view,data in config['views'].items():
    camera=data['camera'];reg=data['registration'];direction=-np.asarray(camera['matrix'])[:3,2]
    region=np.flatnonzero(allowed&((-normal@direction)>.5));region=region[np.linspace(0,len(region)-1,min(48,len(region)),dtype=int)]
    count=0
    for tid in region:
        bary=np.array([.21,.32,.47]);point=bary@xyz[tid];pixel=world_to_pixel(camera,[point])[0]
        w,h=camera['resolution']
        if not(0<=pixel[0]<w and 0<=pixel[1]<h):continue
        origins,directions,limit=pixel_rays(camera,[pixel]);hit=caster.first_hit(origins[0],directions[0],limit,allowed_triangle_ids=allowed)
        if hit['status']!='SEATED' or hit['triangle_id']!=int(tid):continue
        actual=transfer_barycentric(hit,guards,surface)
        world_error=float(np.linalg.norm(np.asarray(actual['world'])-point));uv_error=float(np.linalg.norm(np.asarray(actual['uv'])-bary@surface['triangle_uv'][tid]))
        max_world=max(max_world,world_error);max_uv=max(max_uv,uv_error)
        back=source_to_render(render_to_source([pixel],reg),reg)[0];max_pixel=max(max_pixel,float(np.linalg.norm(back-pixel)))
        positive.append({'view':view,'triangle_id':int(tid),'barycentric':hit['barycentric'],'world_error_m':world_error,'uv_error':uv_error})
        if 'wrong_region' not in negative:
            wrong=caster.first_hit(origins[0],directions[0],limit,allowed_triangle_ids={-1})
            assert wrong['status']=='WRONG_REGION_FRONT_HIT';negative['wrong_region']=wrong['status']
            changed=dict(surface);changed['triangle_uv']=surface['triangle_uv'].copy();changed['triangle_uv'][tid,0,0]+=.001
            try:transfer_barycentric(hit,guards,changed)
            except ValueError:negative['changed_uv']='REJECTED'
            else:raise AssertionError('UV correspondence change accepted')
            # Actual triangle duplicated only in memory, with conflicting corner UVs.
            seam={'world':xyz[tid], 'triangles':np.array([[0,1,2],[0,1,2]]),
                  'triangle_uv':np.array([surface['triangle_uv'][tid],surface['triangle_uv'][tid]+[.2,0]]),'uv_layer':'negative-control'}
            seam_caster=SurfaceCaster(seam,cast_triangle_ids=[0,1]);sh=seam_caster.first_hit(origins[0],directions[0],limit,allowed_triangle_ids={0,1})
            assert sh['status']=='UV_SEAM_AMBIGUOUS';negative['coincident_uv_seam']=sh['status']
        count+=1
        if count==4:break
    assert count==4,(view,count)
    summary=Counter()
    for path in [p for p in source_pack['paths'] if p['view']==view]:
        pts=path['points_px'];sample=[pts[0],pts[len(pts)//2],pts[-1]]
        pixels=source_to_render(sample,reg);o,d,limit=pixel_rays(camera,pixels)
        for origin,di in zip(o,d):summary[caster.first_hit(origin,di,limit,allowed_triangle_ids=None)['status']]+=1
    diagnostics[view]={'source_samples':sum(summary.values()),'status_counts':dict(summary),
                       'accepted_pattern_points':0,'reason':'Baseline unselected; illustration-camera registration provisional; anatomical path regions not authored'}
    origins,directions,limit=pixel_rays(camera,[[camera['resolution'][0]*3,camera['resolution'][1]*3]])
    miss=caster.first_hit(origins[0],directions[0],limit,allowed_triangle_ids=allowed)
    assert miss['status']=='MISSED_RAY';negative['offbody_ray']=miss['status']
try:
    bad=dict(config['views']['front']['registration']);bad['source_to_render']=[[1,0,0],[0,1.01,0],[0,0,1]];validate_registration(bad)
except ValueError:negative['anisotropic_source_registration']='REJECTED'
else:raise AssertionError('Aspect warp accepted')
path=dict(next(p for p in source_pack['paths'] if p['view']=='front'),source_sha256=source_pack['source']['sha256'])
try:seat_path(path,surface,config['views']['front']['camera'],config['views']['front']['registration'],cast_triangle_ids=cast,allowed_triangle_ids=allowed,purpose='production')
except ValueError as exc:
    assert 'Production seating' in str(exc)
    negative['production_on_unselected_body']='REJECTED'
else:raise AssertionError('Unselected production seating accepted')
assert max_world<1e-8 and max_uv<1e-8 and max_pixel<1e-8
proof={'status':'PASS','scope':'Actual baseline CPU camera rays and per-corner UV correspondence only',
       'positive_actual_triangle_probes':positive,'max_world_error_m':max_world,'max_uv_error':max_uv,
       'max_registration_roundtrip_error_px':max_pixel,'negative_controls':negative,
       'source_path_diagnostics':diagnostics,'source_pack_sha256':sha(source_path),
       'baseline_inputs_sha256':sha(HERE/'baseline-inputs.json'),'final_seated_pattern_exported':False,
       'target01_or_target02_used':False,'body_garment_uv_shader_art_acceptance':'NOT_EVALUATED'}
(HERE/'checks.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({k:proof[k] for k in ('status','max_world_error_m','max_uv_error','negative_controls','source_path_diagnostics')}))
