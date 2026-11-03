"""CPU-only fresh actual-surface seating of a partial observed front patch.

No UV, no body deformation, no per-view repaint, no nearest-hit fallback.
Run with factory Blender; uses only NumPy and mathutils BVH.
"""
from pathlib import Path
import sys,json,hashlib
sys.dont_write_bytecode=True
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent;E=P.parent;D=E.parent/'D'
CAN=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
patterns=CAN/'blender/mia-fit-v003/underwear-source/source-paths.json';baseline=CAN/'blender/mia-fit-v003/underwear-fit/baseline-inputs.json'
src=json.loads(patterns.read_text());front=json.loads(baseline.read_text())['views']['front'];camera=front['camera'];M=np.array(camera['matrix']);A=np.array(front['registration']['source_to_render']);Ai=np.linalg.inv(A)
assert abs(A[0,0]-A[1,1])<1e-12 and A[0,1]==A[1,0]==0
assert sha(src['source']['path'])==src['source']['sha256']
paths={q['id']:q for q in src['paths']};top=np.array(paths['front.bra.scoop']['points_px'],float);bottom=np.array(paths['front.bra.band_lower_edge']['points_px'],float);polygon=np.vstack([top,bottom[::-1]])
width,height=camera['resolution'];scale=camera['ortho_scale'];direction=-M[:3,2];direction/=np.linalg.norm(direction)
def ray(pixel):
    q=A@np.r_[pixel,1.];local=np.array([(q[0]/width-.5)*scale*width/height,(.5-q[1]/height)*scale,0.,1.]);return (M@local)[:3]
def project(points):
    local=(points-M[:3,3])@M[:3,:3];render=np.column_stack([(local[:,0]/(scale*width/height)+.5)*width,(.5-local[:,1]/scale)*height,np.ones(len(points))]);return (render@Ai.T)[:,:2]
def inside_and_edge(points):
    inside=np.zeros(len(points),bool);edge=np.full(len(points),np.inf)
    for a,b in zip(polygon,np.roll(polygon,-1,axis=0)):
        crossing=(a[1]>points[:,1])!=(b[1]>points[:,1]);at=(b[0]-a[0])*(points[:,1]-a[1])/(b[1]-a[1]+1e-30)+a[0];inside^=crossing&(points[:,0]<at)
        ab=b-a;t=np.clip((points-a)@ab/(ab@ab),0,1);edge=np.minimum(edge,np.linalg.norm(points-(a+t[:,None]*ab),axis=1))
    return inside,edge
def barycentric(point,tri):
    v0,v1,v2=tri[1]-tri[0],tri[2]-tri[0],point-tri[0];d00=v0@v0;d01=v0@v1;d11=v1@v1;d20=v2@v0;d21=v2@v1;den=d00*d11-d01*d01;v=(d11*d20-d01*d21)/den;w=(d00*d21-d01*d20)/den;return [float(1-v-w),float(v),float(w)]
records=[]
for name,meshpath in [('D',D/'sculpt07-D.npz'),('E',E/'sculpt07-E.npz')]:
    data=np.load(meshpath);world=data['world'].astype(float);tri=data['triangles'].astype(int);bvh=BVHTree.FromPolygons(world.tolist(),tri.tolist(),all_triangles=True,epsilon=0.0);xy=project(world);inside,edge=inside_and_edge(xy);coverage=np.zeros(len(world),np.float32);candidates=np.flatnonzero(inside);rejected=0;maxhiterr=0.
    for i in candidates:
        hit,normal,face,dist=bvh.ray_cast(Vector(ray(xy[i])),Vector(direction),10.)
        err=np.inf if hit is None else np.linalg.norm(np.array(hit)-world[i])
        if err<=.00002:
            # Fixed one-source-pixel feather only inside the observed polygon.
            coverage[i]=min(1.,edge[i]);maxhiterr=max(maxhiterr,float(err))
        else:rejected+=1
    boundary=[]
    for segment,(a,b) in enumerate(zip(polygon,np.roll(polygon,-1,axis=0))):
        count=max(1,int(np.ceil(np.linalg.norm(b-a)/3.)));kind='diagnostic_partial_observation_clip' if segment in [len(top)-1,len(polygon)-1] else 'observed_front_neckline_or_lower_edge'
        for t in np.linspace(0,1,count,endpoint=False):
            pixel=a+(b-a)*t;hit,normal,face,dist=bvh.ray_cast(Vector(ray(pixel)),Vector(direction),10.);row=dict(source_pixel=pixel.tolist(),segment=segment,kind=kind,hit=hit is not None)
            if hit is not None:row.update(triangle=int(face),barycentric=barycentric(np.array(hit),world[tri[face]]),point_world=list(hit),normal_world=list(normal))
            boundary.append(row)
    out=P/(name+'-front-observed-coverage.npz');assert not out.exists();np.savez_compressed(out,coverage=coverage)
    records.append(dict(state=name,mesh=str(meshpath),mesh_sha256=sha(meshpath),world_array_sha256=hashlib.sha256(data['world'].tobytes()).hexdigest(),triangles_array_sha256=hashlib.sha256(data['triangles'].tobytes()).hexdigest(),coverage_path=str(out),coverage_sha256=sha(out),coverage_attribute='SourceFrontCentralBraCoverage',attribute_domain='POINT',vertices=len(world),front_projected_candidates=len(candidates),actual_first_hit_covered_vertices=int((coverage>0).sum()),rejected_hidden_projection_vertices=rejected,numeric_vertex_hit_tolerance_m=.00002,max_accepted_hit_error_m=maxhiterr,boundary_samples=boundary,boundary_hits=sum(r['hit'] for r in boundary),boundary_misses=sum(not r['hit'] for r in boundary)))
report=dict(status='CPU partial observed-front 3D coverage ready; actual render review pending',source_patterns=str(patterns),source_patterns_sha256=sha(patterns),source_sha256=src['source']['sha256'],baseline_registration_path=str(baseline),baseline_registration_sha256=sha(baseline),source_camera=camera,source_to_render=A.tolist(),polygon_original_source_pixels=polygon.tolist(),observed_edges=['P01 front.bra.scoop','P03 front.bra.band_lower_edge'],diagnostic_clip_segments=[[[286,267],[290,333]],[[190,333],[194,263]]],fixed_3D_attribute_reused_for_all_views=True,coverage_feather_source_pixels=1,records=records,limits=['Projection seating is garment placement, not an independent shape reconstruction or anatomical fit score.','Side connectors clip inside visible central cloth; they are not observed side seams.','Straps excluded: source P04/P05 show inner edges but no outer width or shoulder attachment.','F2 uses the same fixed front-observed attribute; side/underside truncation and hidden closure are UNCALIBRATED. No F2 paint or refit.','No final UV, garment thickness, cloth force or physics; no painted central cleft.','No change to legacy body support guides, numeric metrics or tolerances. Missed rays have no nearest-surface fallback.'])
(P/'coverage-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('BRA_FIXED_COVERAGE_CPU_READY',[(r['state'],r['actual_first_hit_covered_vertices'],r['boundary_hits'],r['boundary_misses']) for r in records],flush=True)
